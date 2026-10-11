"""
SQL layer for PatientFlow AI.

Uses SQLAlchemy 2.x + PyMySQL against a MySQL / MariaDB server.

Configure via environment (or a .env file at the project root):

    PATIENTFLOW_DB_URL=mysql+pymysql://user:password@127.0.0.1:3306/patientflow

If PATIENTFLOW_DB_URL is not set, the individual pieces are used:

    PATIENTFLOW_DB_HOST=127.0.0.1
    PATIENTFLOW_DB_PORT=3306
    PATIENTFLOW_DB_USER=root
    PATIENTFLOW_DB_PASSWORD=
    PATIENTFLOW_DB_NAME=patientflow
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _build_url() -> str:
    url = os.getenv("PATIENTFLOW_DB_URL")
    if url:
        return url
    host = os.getenv("PATIENTFLOW_DB_HOST", "127.0.0.1")
    port = os.getenv("PATIENTFLOW_DB_PORT", "3306")
    user = os.getenv("PATIENTFLOW_DB_USER", "root")
    pw = os.getenv("PATIENTFLOW_DB_PASSWORD", "")
    name = os.getenv("PATIENTFLOW_DB_NAME", "patientflow")
    return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{name}?charset=utf8mb4"


DB_URL = _build_url()


def _server_url(url: str) -> tuple[str, str]:
    """Split 'mysql+pymysql://.../dbname?...' into (server_url_without_db, dbname)."""
    # crude parse - we only need it to CREATE DATABASE IF NOT EXISTS
    head, _, tail = url.rpartition("/")
    dbname, _, query = tail.partition("?")
    server = head + "/"
    if query:
        server = server + "?" + query
    return server, dbname


def ensure_database_exists() -> None:
    """Create the target database if it doesn't exist yet."""
    server_url, dbname = _server_url(DB_URL)
    if not dbname:
        return
    tmp_engine = create_engine(server_url, pool_pre_ping=True)
    with tmp_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{dbname}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    tmp_engine.dispose()


engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=1800, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
