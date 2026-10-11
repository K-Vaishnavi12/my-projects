"""Prompt-engineering templates.

Every syllabus concept from **Prompt Engineering + GenAI** is
represented here:
- system prompts (persona voices)
- zero-shot and few-shot templates
- chain-of-thought scaffolds
- explicit guardrails against hallucination
- retrieval-augmented context blocks
"""

from symposium.prompts.templates import (
    PERSONA_TURN_PROMPT,
    MODERATOR_PROMPT,
    TOPIC_ROUTER_PROMPT,
    SAFETY_GUARDRAILS,
    build_persona_prompt,
    build_moderator_prompt,
    build_topic_router_prompt,
)

__all__ = [
    "PERSONA_TURN_PROMPT",
    "MODERATOR_PROMPT",
    "TOPIC_ROUTER_PROMPT",
    "SAFETY_GUARDRAILS",
    "build_persona_prompt",
    "build_moderator_prompt",
    "build_topic_router_prompt",
]
