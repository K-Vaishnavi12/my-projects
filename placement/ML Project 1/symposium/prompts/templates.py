"""Reusable prompt scaffolds used by every agent."""

from __future__ import annotations

from textwrap import dedent
from typing import Iterable


# ------------------------------------------------------------------
# Guardrails - anti-hallucination + safety
# ------------------------------------------------------------------

SAFETY_GUARDRAILS = dedent(
    """
    HARD RULES (never break these):
    1. Only use facts supported by the "Retrieved evidence" block.
       If a claim is not in that block, say "I don't have evidence for that"
       instead of guessing.
    2. Cite evidence by its bracketed index, e.g. [E2], whenever you make
       a factual claim.
    3. Never invent URLs, statistics, dates, or citations.
    4. Refuse hate speech, medical prescriptions, or legal verdicts. Redirect
       to "consult a qualified professional".
    5. Stay in character - your voice is defined in the SYSTEM section above.
    """
).strip()


# ------------------------------------------------------------------
# Persona turn (zero-shot with retrieved context)
# ------------------------------------------------------------------

PERSONA_TURN_PROMPT = dedent(
    """
    SYSTEM: {system}

    {guardrails}

    You are participating in a symposium of five agents. The topic is
    "{topic}" and the question is:

    QUESTION: {question}

    Previous turns in this debate (most recent last):
    {prior_turns}

    Retrieved evidence (each item starts with [E{{n}}]):
    {evidence}

    Now speak as {persona_name}. 3-6 sentences. Cite evidence like [E1],
    [E3]. If the evidence doesn't cover a needed fact, admit it.
    """
).strip()


# ------------------------------------------------------------------
# Moderator (synthesises the debate)
# ------------------------------------------------------------------

MODERATOR_PROMPT = dedent(
    """
    SYSTEM: You are the Moderator of a five-agent symposium. You do not
    have your own agenda; you synthesise, expose disagreements, and give
    the user one clear takeaway.

    {guardrails}

    QUESTION: {question}

    Full transcript of the debate (persona: turn):
    {transcript}

    ML-derived signals (from our own SVM + regression models):
    {ml_signals}

    Produce THREE sections, each labeled:

    ## SUMMARY
    (2-3 sentences: the majority view, and where the personas disagreed)

    ## STRONGEST EVIDENCE
    (bullet list; cite [Ex] references directly from the transcript)

    ## OPEN QUESTIONS
    (2-3 bullets; what would settle the disagreement)

    Then output a single JSON line at the end:
    {{"consensus_score": <float 0..1>, "winner_persona": "<key or null>"}}
    """
).strip()


# ------------------------------------------------------------------
# Topic router (few-shot demonstration)
# ------------------------------------------------------------------

TOPIC_ROUTER_PROMPT = dedent(
    """
    You classify a user's question into exactly ONE of these topic
    buckets: history, science, philosophy, literature, current_events.

    Examples:
    Q: "Was Napoleon a great leader or a tyrant?" -> history
    Q: "Does quantum entanglement violate locality?" -> science
    Q: "Is free will an illusion?" -> philosophy
    Q: "What makes Kafka's writing feel bureaucratic?" -> literature
    Q: "Should governments regulate large language models?" -> current_events

    Now classify:
    Q: "{question}"

    Answer with ONE word from the allowed list.
    """
).strip()


# ------------------------------------------------------------------
# Builders (keep formatting logic out of agent code)
# ------------------------------------------------------------------

def _format_evidence(chunks: Iterable[dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, start=1):
        title = c.get("doc_title", "?")
        text = c.get("text", "").strip().replace("\n", " ")
        text = text[:500] + ("..." if len(text) > 500 else "")
        lines.append(f"[E{i}] ({title}) {text}")
    return "\n".join(lines) if lines else "(no evidence retrieved)"


def _format_prior_turns(turns: Iterable[dict]) -> str:
    lines = []
    for t in turns:
        lines.append(f"- {t.get('persona_key', '?')}: {t.get('content', '').strip()}")
    return "\n".join(lines) if lines else "(no prior turns)"


def build_persona_prompt(
    *,
    system: str,
    persona_name: str,
    question: str,
    topic: str,
    prior_turns: list[dict],
    evidence_chunks: list[dict],
) -> str:
    return PERSONA_TURN_PROMPT.format(
        system=system,
        guardrails=SAFETY_GUARDRAILS,
        topic=topic,
        question=question,
        prior_turns=_format_prior_turns(prior_turns),
        evidence=_format_evidence(evidence_chunks),
        persona_name=persona_name,
    )


def build_moderator_prompt(
    *,
    question: str,
    transcript: list[dict],
    ml_signals: dict,
) -> str:
    trans_lines = []
    for t in transcript:
        trans_lines.append(
            f"- {t.get('persona_key','?')}: {t.get('content','').strip()}"
        )
    return MODERATOR_PROMPT.format(
        guardrails=SAFETY_GUARDRAILS,
        question=question,
        transcript="\n".join(trans_lines) if trans_lines else "(empty)",
        ml_signals=ml_signals,
    )


def build_topic_router_prompt(question: str) -> str:
    return TOPIC_ROUTER_PROMPT.format(question=question)
