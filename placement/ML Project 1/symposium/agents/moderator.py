"""Moderator agent.

Reads the whole transcript, calls the LLM once with a synthesis
prompt, extracts the JSON footer, and returns a structured verdict.
Also folds in signals from our own ML models (SVM stance / regressor).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from loguru import logger

from symposium.agents.llm import get_llm
from symposium.prompts import build_moderator_prompt


_JSON_TAIL_RE = re.compile(r"\{[^{}]*\}\s*$", re.DOTALL)


@dataclass
class ModeratorVerdict:
    summary_markdown: str
    consensus_score: float
    winner_persona: str | None
    raw_text: str


class Moderator:
    def __init__(self) -> None:
        self._llm = get_llm()

    def synthesise(
        self,
        question: str,
        transcript: list[dict],
        ml_signals: dict[str, Any],
    ) -> ModeratorVerdict:
        prompt = build_moderator_prompt(
            question=question,
            transcript=transcript,
            ml_signals=ml_signals,
        )
        text = self._llm.generate(prompt, temperature=0.3, max_tokens=700)

        # Parse the trailing JSON line
        consensus = 0.5
        winner: str | None = None
        m = _JSON_TAIL_RE.search(text)
        if m:
            try:
                payload = json.loads(m.group(0))
                consensus = float(payload.get("consensus_score", 0.5))
                winner = payload.get("winner_persona")
                summary = text[: m.start()].strip()
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[mod] JSON parse failed ({exc}); using defaults")
                summary = text
        else:
            summary = text

        return ModeratorVerdict(
            summary_markdown=summary,
            consensus_score=max(0.0, min(1.0, consensus)),
            winner_persona=winner,
            raw_text=text,
        )
