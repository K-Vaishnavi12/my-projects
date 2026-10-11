"""Cleaner: apply Data-Quality rules to raw Wikipedia articles.

Represents the classical "Data Quality" and "Data Format Consistency"
step from the ETL syllabus. Every rule is a small pure function so
they can be unit-tested individually and swapped without breaking
downstream code.
"""

from __future__ import annotations

import re
from typing import Any

from symposium.utils import normalize_whitespace, strip_wiki_refs

# ------------------------------------------------------------------
# Section blacklist - drop these headings entirely
# ------------------------------------------------------------------

_BLACKLIST_HEADERS = {
    "See also",
    "References",
    "External links",
    "Further reading",
    "Notes",
    "Bibliography",
    "Sources",
}

# Wikipedia sections come with "== Section ==" markers when using WIKI
# extract format. We split on them (allowing surrounding whitespace on
# the line) so we can drop the trash sections.
_SECTION_RE = re.compile(r"^[ \t]*={2,6}\s*(.+?)\s*={2,6}[ \t]*$", re.MULTILINE)


def drop_bad_sections(text: str) -> str:
    """Remove the boilerplate sections that add noise (see-also, refs, ...)."""
    parts = _SECTION_RE.split(text)
    # split gives: [preamble, header1, body1, header2, body2, ...]
    if len(parts) == 1:
        return text
    preamble = parts[0]
    kept = [preamble]
    for header, body in zip(parts[1::2], parts[2::2]):
        if header.strip() not in _BLACKLIST_HEADERS:
            kept.append(f"\n\n## {header.strip()}\n{body}")
    return "".join(kept)


def looks_like_content(text: str) -> bool:
    """Basic length + alphanumeric ratio rule."""
    if len(text) < 300:
        return False
    letters = sum(c.isalpha() for c in text)
    return (letters / max(len(text), 1)) > 0.6


def clean_article(article: dict[str, Any]) -> dict[str, Any]:
    """Apply every cleaning rule to a raw extractor record.

    Returns a NEW dict with a ``clean_text`` field. Raises
    :class:`ValueError` if the article fails the DQ rules so the
    orchestrator can skip it.
    """
    text = article.get("text", "")
    text = strip_wiki_refs(text)
    text = drop_bad_sections(text)
    text = normalize_whitespace(text)

    if not looks_like_content(text):
        raise ValueError(f"DQ rule failed for '{article.get('title')}'")

    out = dict(article)
    out["clean_text"] = text
    return out
