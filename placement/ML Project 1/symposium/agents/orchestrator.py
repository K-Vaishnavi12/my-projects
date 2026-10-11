"""Symposium orchestrator.

Runs one whole debate:
    1. Route the question to a topic (Naive Bayes model, if trained).
    2. For each round, every persona speaks in a fixed order.
    3. After each turn, our SVM stance model + regressor score it.
    4. The moderator synthesises the debate.
    5. Everything is written to the SQL DWH via :class:`DebateRecorder`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

from loguru import logger

from symposium.agents.moderator import Moderator, ModeratorVerdict
from symposium.agents.persona_agent import PersonaAgent, TurnResult
from symposium.agents.recorder import DebateRecorder
from symposium.config import get_settings
from symposium.config.personas import PERSONAS
from symposium.ml.agreement_regressor import AgreementRegressor
from symposium.ml.stance_svm import StanceSVM
from symposium.ml.topic_naive_bayes import TopicNaiveBayes


@dataclass
class DebateTurn:
    turn_id: str
    persona_key: str
    turn_index: int
    content: str
    latency_ms: int
    stance_label: str | None = None
    stance_score: float | None = None
    agreement_score: float | None = None
    retrievals: list[dict] = field(default_factory=list)


@dataclass
class DebateResult:
    query_id: str
    question: str
    topic: str
    turns: list[DebateTurn]
    verdict: ModeratorVerdict | None
    ml_signals: dict[str, Any]


class Symposium:
    """The top-level object the UI + CLI drive."""

    def __init__(
        self,
        persona_order: list[str] | None = None,
        rounds: int | None = None,
    ) -> None:
        s = get_settings()
        self.persona_keys = persona_order or [
            "historian", "scientist", "poet", "skeptic", "child"
        ]
        self.rounds = rounds if rounds is not None else max(1, s.max_turns_per_debate // len(self.persona_keys))
        self.agents = {k: PersonaAgent(k) for k in self.persona_keys}
        self.moderator = Moderator()
        self.recorder = DebateRecorder()

        # Optional ML augmentations (loaded only if available on disk)
        self._svm: StanceSVM | None = None
        self._reg: AgreementRegressor | None = None
        self._router: TopicNaiveBayes | None = None
        self._load_optional_ml(s.model_dir)

    # --------------------------------------------------------------
    def _load_optional_ml(self, model_dir: Path) -> None:
        def _try(cls, name):
            path = model_dir / name
            if not path.exists():
                logger.info(f"[ml] {name} not found (train_models.py hasn't run yet)")
                return None
            obj = cls()
            try:
                obj.load(path)
                logger.info(f"[ml] loaded {name}")
                return obj
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[ml] failed to load {name}: {exc}")
                return None

        self._svm = _try(StanceSVM, "stance_svm.joblib")
        self._reg = _try(AgreementRegressor, "agreement_regressor.joblib")
        self._router = _try(TopicNaiveBayes, "topic_naive_bayes.joblib")

    # --------------------------------------------------------------
    # Topic routing (uses our Naive Bayes)
    # --------------------------------------------------------------

    def route_topic(self, question: str, fallback: str = "current_events") -> str:
        if self._router is None:
            return fallback
        try:
            pred = self._router.predict([question])[0]
            return pred["label"]
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[route] falling back to '{fallback}' ({exc})")
            return fallback

    # --------------------------------------------------------------
    # Main entry: run and stream turns as they happen
    # --------------------------------------------------------------

    def run(
        self,
        question: str,
        topic: str | None = None,
        on_turn: Callable[[DebateTurn], None] | None = None,
    ) -> DebateResult:
        topic = topic or self.route_topic(question)
        query_id = self.recorder.start_debate(question, topic)
        prior_turns_dicts: list[dict] = []
        collected: list[DebateTurn] = []

        turn_index = 0
        for r in range(self.rounds):
            for pkey in self.persona_keys:
                agent = self.agents[pkey]
                result: TurnResult = agent.speak(
                    question=question,
                    topic=topic,
                    prior_turns=prior_turns_dicts,
                )
                turn_index += 1

                # ---- ML scoring ----
                stance_label: str | None = None
                stance_score: float | None = None
                agreement_score: float | None = None
                if self._svm is not None:
                    p = self._svm.predict([result.content])[0]
                    stance_label = p["label"]
                    stance_score = p["score"]
                if self._reg is not None:
                    agreement_score = float(self._reg.predict([result.content])[0])

                turn = DebateTurn(
                    turn_id=result.turn_id,
                    persona_key=pkey,
                    turn_index=turn_index,
                    content=result.content,
                    latency_ms=result.latency_ms,
                    stance_label=stance_label,
                    stance_score=stance_score,
                    agreement_score=agreement_score,
                    retrievals=[
                        {
                            "turn_id": result.turn_id,
                            "chunk_id": c.chunk_id,
                            "rank": c.rank,
                            "similarity": c.similarity,
                        }
                        for c in result.retrieved
                    ],
                )
                collected.append(turn)
                prior_turns_dicts.append(
                    {"persona_key": pkey, "content": result.content}
                )

                # ---- persist ----
                self.recorder.record_turn(
                    query_id=query_id,
                    turn_id=turn.turn_id,
                    persona_key=turn.persona_key,
                    turn_index=turn.turn_index,
                    content=turn.content,
                    stance_label=turn.stance_label,
                    stance_score=turn.stance_score,
                    agreement_score=turn.agreement_score,
                    latency_ms=turn.latency_ms,
                    retrievals=turn.retrievals,
                )

                if on_turn:
                    on_turn(turn)

        # ---- moderator synthesis ----
        ml_signals = self._aggregate_signals(collected)
        verdict = self.moderator.synthesise(
            question=question,
            transcript=[{"persona_key": t.persona_key, "content": t.content} for t in collected],
            ml_signals=ml_signals,
        )
        self.recorder.finish_debate(query_id, verdict.consensus_score, verdict.summary_markdown)

        return DebateResult(
            query_id=query_id,
            question=question,
            topic=topic,
            turns=collected,
            verdict=verdict,
            ml_signals=ml_signals,
        )

    # --------------------------------------------------------------
    def _aggregate_signals(self, turns: list[DebateTurn]) -> dict[str, Any]:
        by_persona: dict[str, list[float]] = {}
        for t in turns:
            if t.agreement_score is not None:
                by_persona.setdefault(t.persona_key, []).append(t.agreement_score)

        avgs = {
            p: (sum(scores) / len(scores)) if scores else None
            for p, scores in by_persona.items()
        }
        return {
            "avg_agreement_per_persona": avgs,
            "n_turns": len(turns),
            "stance_distribution": self._stance_dist(turns),
        }

    def _stance_dist(self, turns: list[DebateTurn]) -> dict[str, int]:
        dist: dict[str, int] = {}
        for t in turns:
            if t.stance_label:
                dist[t.stance_label] = dist.get(t.stance_label, 0) + 1
        return dist

    def close(self) -> None:
        self.recorder.close()
