"""Typed settings loader.

Uses ``pydantic-settings`` so every environment variable is:
- documented (via field descriptions),
- type-checked (int/bool/str/path),
- overridable by ``.env`` or real env vars,
- cached with ``functools.lru_cache`` so we only parse once.

On Streamlit Cloud, secrets are exposed via ``st.secrets`` (a dict-like
object). We shim them into the process environment BEFORE Pydantic
runs so the same ``get_settings()`` call works everywhere.

This is the ONE and ONLY place environment variables are read.
Every other module imports :func:`get_settings`.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _hydrate_from_streamlit_secrets() -> None:
    """Copy Streamlit Cloud secrets into os.environ if present.

    Silent no-op in local dev (no Streamlit runtime running).
    """
    try:
        import streamlit as st  # noqa: WPS433
        # st.secrets raises if secrets.toml is missing; catch broadly.
        for key, value in dict(st.secrets).items():
            # Don't override anything already set (local .env wins over cloud secrets)
            if key not in os.environ and value is not None:
                os.environ[key] = str(value)
    except Exception:
        # Not running under Streamlit, or no secrets configured - fine.
        pass


class Settings(BaseSettings):
    """Immutable, type-checked settings for the whole app."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- LLM ----
    # Provider = 'groq' (default, free, fast) or 'gemini'
    llm_provider: str = Field(default="groq")

    # Gemini
    gemini_api_key: str = Field(default="", description="Google AI Studio API key")
    gemini_model: str = Field(default="gemini-2.0-flash")

    # Groq (free, fast, Llama family models)
    groq_api_key: str = Field(default="", description="Groq API key (starts with gsk_)")
    groq_model: str = Field(default="llama-3.3-70b-versatile")

    # ---- MongoDB ----
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db: str = Field(default="symposium")
    use_local_vector_store: bool = Field(default=False)

    # ---- Embeddings ----
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim: int = Field(default=384)

    # ---- SQLite DWH ----
    sqlite_path: Path = Field(default=Path("data/processed/symposium_dwh.sqlite"))

    # ---- Paths ----
    raw_data_dir: Path = Field(default=Path("data/raw"))
    staging_data_dir: Path = Field(default=Path("data/staging"))
    processed_data_dir: Path = Field(default=Path("data/processed"))
    model_dir: Path = Field(default=Path("data/models"))
    export_dir: Path = Field(default=Path("data/exports"))

    # ---- ETL knobs ----
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=80, ge=0, le=500)
    max_articles_per_topic: int = Field(default=40, ge=1, le=500)

    # ---- Debate runtime ----
    max_turns_per_debate: int = Field(default=6, ge=1, le=20)
    retrieval_top_k: int = Field(default=5, ge=1, le=50)
    consensus_threshold: float = Field(default=0.75, ge=0.0, le=1.0)

    # ---- AWS ----
    aws_region: str = Field(default="ap-south-1")
    aws_s3_bucket: str = Field(default="symposium-raw-staging")

    def ensure_dirs(self) -> None:
        """Create data directories on disk if they're missing."""
        for p in (
            self.raw_data_dir,
            self.staging_data_dir,
            self.processed_data_dir,
            self.model_dir,
            self.export_dir,
            self.sqlite_path.parent,
        ):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a memoised :class:`Settings` instance.

    Cached so we don't re-parse ``.env`` on every call. Tests can bust
    the cache with ``get_settings.cache_clear()``.
    """
    _hydrate_from_streamlit_secrets()
    s = Settings()
    s.ensure_dirs()
    return s
