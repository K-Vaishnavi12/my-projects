"""Database helper — single place for the SQLAlchemy engine."""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _build_url() -> str:
    user = os.getenv("PG_USER", "retail")
    pwd  = os.getenv("PG_PASSWORD", "retail")
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    db   = os.getenv("PG_DB", "retail_dwh")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine."""
    return create_engine(_build_url(), pool_pre_ping=True, future=True)
