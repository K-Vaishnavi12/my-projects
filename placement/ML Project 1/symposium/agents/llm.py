"""LLM adapter - supports Groq (default) or Gemini.

Selected by ``LLM_PROVIDER`` env var (`groq` or `gemini`).

Provides:
- retry with exponential backoff
- a tiny in-memory cache keyed by prompt hash so re-runs during
  demos don't hit quota
- an offline stub so the UI still works without an API key (returns
  deterministic placeholder text)
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

from loguru import logger

from symposium.config import get_settings
from symposium.utils import retry


class BaseLLM:
    """Common interface + shared behaviour for LLM providers."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self._offline = False

    def generate(self, prompt: str, temperature: float = 0.6, max_tokens: int = 512) -> str:
        h = hashlib.sha1(f"{temperature}|{max_tokens}|{prompt}".encode()).hexdigest()
        if h in self._cache:
            return self._cache[h]

        if self._offline:
            text = self._stub_response(prompt)
        else:
            text = self._call(prompt, temperature, max_tokens)

        self._cache[h] = text
        return text

    def _call(self, prompt: str, temperature: float, max_tokens: int) -> str:
        raise NotImplementedError

    def _stub_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "moderator" in prompt_lower:
            return (
                "## SUMMARY\nThe personas broadly agree that the question is "
                "important, though they emphasise different aspects.\n\n"
                "## STRONGEST EVIDENCE\n- [E1] provides the clearest anchor.\n"
                "- [E2] gives a useful counter-example.\n\n"
                "## OPEN QUESTIONS\n- Would more recent data change the picture?\n"
                "- How generalisable is the mechanism?\n\n"
                '{"consensus_score": 0.62, "winner_persona": null}'
            )
        return (
            "This is a stub response (no LLM API key set). The persona would "
            "normally cite retrieved evidence like [E1] and speak in its own voice."
        )


class GroqLLM(BaseLLM):
    """Groq client (llama-3.x models). Free tier is very generous."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        super().__init__()
        s = get_settings()
        self.api_key = api_key or s.groq_api_key
        self.model_name = model or s.groq_model
        self._client = None
        self._offline = not bool(self.api_key)
        if self._offline:
            logger.warning(
                "[llm] GROQ_API_KEY missing - running in OFFLINE stub mode."
            )

    def _ensure(self) -> None:
        if self._client is not None or self._offline:
            return
        from groq import Groq
        self._client = Groq(api_key=self.api_key)

    @retry(times=3, delay=2.0)
    def _call(self, prompt: str, temperature: float, max_tokens: int) -> str:
        self._ensure()
        assert self._client is not None
        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (completion.choices[0].message.content or "").strip()


class GeminiLLM(BaseLLM):
    """Google Gemini client (kept for parity; use LLM_PROVIDER=gemini)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        super().__init__()
        s = get_settings()
        self.api_key = api_key or s.gemini_api_key
        self.model_name = model or s.gemini_model
        self._client = None
        self._offline = not bool(self.api_key)
        if self._offline:
            logger.warning(
                "[llm] GEMINI_API_KEY missing - running in OFFLINE stub mode."
            )

    def _ensure(self) -> None:
        if self._client is not None or self._offline:
            return
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self._client = genai.GenerativeModel(self.model_name)

    @retry(times=3, delay=2.0)
    def _call(self, prompt: str, temperature: float, max_tokens: int) -> str:
        self._ensure()
        assert self._client is not None
        resp = self._client.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        return (resp.text or "").strip()


@lru_cache(maxsize=1)
def get_llm() -> BaseLLM:
    """Factory: pick the LLM based on settings.llm_provider."""
    s = get_settings()
    provider = s.llm_provider.lower()
    if provider == "gemini":
        return GeminiLLM()
    # default: groq
    return GroqLLM()
