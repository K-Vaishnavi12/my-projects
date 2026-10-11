"""A single debating persona.

Owns:
- its own persona spec (voice, retrieval bias)
- retrieval from its dedicated MongoDB collection
- prompt construction + LLM call
- its own turn logging
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from loguru import logger

from symposium.agents.llm import get_llm
from symposium.config import get_persona
from symposium.config.personas import Persona
from symposium.etl.transform.embedder import get_embedder
from symposium.prompts import build_persona_prompt
from symposium.vectorstore.base import RetrievedChunk
from symposium.vectorstore.factory import get_vector_store


@dataclass
class TurnResult:
    turn_id: str
    persona_key: str
    content: str
    retrieved: list[RetrievedChunk]
    latency_ms: int


class PersonaAgent:
    def __init__(self, persona_key: str, top_k: int = 5) -> None:
        self.persona: Persona = get_persona(persona_key)
        self.top_k = top_k
        self._llm = get_llm()
        self._embedder = get_embedder()
        self._vs = get_vector_store()

    def _retrieve(self, question: str) -> list[RetrievedChunk]:
        vec = self._embedder.encode(question).tolist()[0]
        chunks = self._vs.search(
            query_embedding=vec,
            persona_key=self.persona.key,
            top_k=self.top_k,
        )
        # Fallback: if persona-scoped store is empty, try the global one
        if not chunks:
            chunks = self._vs.search(
                query_embedding=vec, persona_key=None, top_k=self.top_k
            )
        return chunks

    def speak(
        self,
        question: str,
        topic: str,
        prior_turns: list[dict],
    ) -> TurnResult:
        t0 = time.perf_counter()
        chunks = self._retrieve(question)
        evidence = [
            {"doc_title": c.doc_title, "text": c.text}
            for c in chunks
        ]

        prompt = build_persona_prompt(
            system=self.persona.system,
            persona_name=self.persona.name,
            question=question,
            topic=topic,
            prior_turns=prior_turns,
            evidence_chunks=evidence,
        )
        response = self._llm.generate(prompt, temperature=0.6)
        dt = int((time.perf_counter() - t0) * 1000)
        logger.info(f"[{self.persona.key}] spoke in {dt} ms ({len(response)} chars)")

        return TurnResult(
            turn_id=str(uuid.uuid4()),
            persona_key=self.persona.key,
            content=response,
            retrieved=chunks,
            latency_ms=dt,
        )
