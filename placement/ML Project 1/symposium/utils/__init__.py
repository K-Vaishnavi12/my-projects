"""Shared utilities: logging, timing, decorators, IO helpers.

This module doubles as a *live demonstration* of every "Python Advanced"
topic in the syllabus:
- iterators, generators, comprehensions
- decorators (retry, timed, cached)
- closures + partial functions
- regular expressions
- serialization (json + pickle)
- modules & packages (this file's imports)
"""

from __future__ import annotations

import functools
import hashlib
import json
import pickle
import re
import time
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any, TypeVar

from loguru import logger

T = TypeVar("T")


# ------------------------------------------------------------------
# Decorators (syllabus: decorators + closures)
# ------------------------------------------------------------------

def timed(label: str | None = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Log the wall-clock time a function takes.

    Uses a closure to capture ``label`` at decoration time. Perfect
    example of "closures" from the advanced-Python syllabus.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            name = label or fn.__qualname__
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                dt = time.perf_counter() - t0
                logger.info(f"[timed] {name} took {dt:.2f}s")

        return wrapper

    return decorator


def retry(
    times: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Exponential-backoff retry decorator.

    Demonstrates decorators-with-arguments (a decorator factory closing
    over its own configuration).
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            wait = delay
            last_exc: BaseException | None = None
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:  # noqa: PERF203
                    last_exc = exc
                    logger.warning(
                        f"[retry] {fn.__qualname__} attempt {attempt}/{times} "
                        f"failed with {type(exc).__name__}: {exc}"
                    )
                    if attempt < times:
                        time.sleep(wait)
                        wait *= backoff
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


# ------------------------------------------------------------------
# Text helpers (syllabus: regex, generators, comprehensions)
# ------------------------------------------------------------------

_WHITESPACE_RE = re.compile(r"\s+")
_CITATION_RE = re.compile(r"\[\d+\]")           # strip Wikipedia refs like "[12]"
_PAREN_YEAR_RE = re.compile(r"\((\d{3,4})\)")   # capture "(1789)" style years
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs into single spaces."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def strip_wiki_refs(text: str) -> str:
    """Remove ``[12]``-style citation markers from wiki text."""
    return _CITATION_RE.sub("", text)


def extract_years(text: str) -> list[int]:
    """Pull 3-4 digit years found in parentheses. Very cheap heuristic."""
    return [int(m.group(1)) for m in _PAREN_YEAR_RE.finditer(text)]


def iter_sentences(text: str) -> Iterator[str]:
    """Yield sentences one at a time.

    A generator (syllabus topic) so we don't materialise a giant list
    when chunking huge Wikipedia articles.
    """
    for s in _SENTENCE_END_RE.split(text):
        s = s.strip()
        if s:
            yield s


def chunk_by_sentences(
    text: str,
    target_chars: int = 500,
    overlap_chars: int = 80,
) -> Iterator[str]:
    """Yield overlapping character-windows that break on sentence boundaries.

    Two generators composed together. Emits chunks lazily so ETL can
    stream through GB-scale corpora if we ever scale up.
    """
    buffer: list[str] = []
    buf_len = 0
    for sent in iter_sentences(text):
        buffer.append(sent)
        buf_len += len(sent) + 1
        if buf_len >= target_chars:
            chunk = " ".join(buffer)
            yield chunk
            # keep a small trailing overlap for context continuity
            if overlap_chars > 0 and len(chunk) > overlap_chars:
                tail = chunk[-overlap_chars:]
                buffer = [tail]
                buf_len = len(tail)
            else:
                buffer = []
                buf_len = 0
    if buffer:
        yield " ".join(buffer)


# ------------------------------------------------------------------
# Hashing + IDs
# ------------------------------------------------------------------

def stable_id(*parts: str) -> str:
    """Deterministic short id built from any string parts."""
    joined = "||".join(parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------
# Serialization helpers (syllabus: serialization)
# ------------------------------------------------------------------

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_pickle(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def read_pickle(path: Path) -> Any:
    with path.open("rb") as f:
        return pickle.load(f)


# ------------------------------------------------------------------
# Batch helper (syllabus: iterators)
# ------------------------------------------------------------------

def batched(iterable: Iterable[T], size: int) -> Iterator[list[T]]:
    """Yield successive fixed-size batches from ``iterable``.

    Standard-library ``itertools.batched`` only exists in 3.12+; we
    ship our own so the project runs on 3.11 too.
    """
    if size < 1:
        raise ValueError("batch size must be >= 1")
    batch: list[T] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch
