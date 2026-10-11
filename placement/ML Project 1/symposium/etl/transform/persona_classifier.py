"""Persona classifier - a *rule-based, feature-driven* pre-tagger.

At ETL time we score each chunk against every persona's retrieval bias
so the vector store can filter/rank per persona at query time. We
DON'T use an LLM here (cost + latency); a lightweight lexicon does 95%
of the job. The Naive-Bayes and SVM models in ``symposium.ml`` are
trained ON TOP of these features later.

Features per chunk:
- date_density        : fraction of tokens that look like years/dates
- evidence_density    : fraction of "evidence" words (data, study, ...)
- narrative_density   : fraction of "narrative" words (story, dream, ...)
- reading_ease        : proxy for Flesch score using average word length
- counterexample_hits : occurrences of "however", "but", "except", ...
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict

from symposium.config.personas import PERSONAS

# ------------------------------------------------------------------
# Lexicons (small but discriminative)
# ------------------------------------------------------------------

_EVIDENCE_WORDS = {
    "study", "studies", "data", "evidence", "experiment", "trial",
    "hypothesis", "theorem", "measured", "measurement", "statistic",
    "significant", "correlation", "causation", "peer-reviewed",
    "sample", "control", "regression", "mechanism", "empirical",
}

_NARRATIVE_WORDS = {
    "story", "tale", "myth", "legend", "hero", "journey", "dream",
    "memory", "voice", "shadow", "light", "wonder", "sorrow", "love",
    "silence", "whisper", "river", "bridge", "veil", "song",
}

_COUNTER_WORDS = {
    "however", "but", "except", "although", "though", "nevertheless",
    "yet", "conversely", "unlike", "contrary", "despite", "whereas",
}

_DATE_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9]|19[0-9]{2})\b")
_TOKEN_RE = re.compile(r"[A-Za-z]+")


# ------------------------------------------------------------------
# Feature extraction
# ------------------------------------------------------------------

def extract_features(chunk: str) -> Dict[str, float]:
    """Return a stable feature dict for downstream models."""
    tokens = _TOKEN_RE.findall(chunk.lower())
    n = max(len(tokens), 1)

    dates = _DATE_RE.findall(chunk)
    evidence_hits = sum(1 for t in tokens if t in _EVIDENCE_WORDS)
    narrative_hits = sum(1 for t in tokens if t in _NARRATIVE_WORDS)
    counter_hits = sum(1 for t in tokens if t in _COUNTER_WORDS)

    avg_word_len = sum(len(t) for t in tokens) / n
    # simple reading-ease proxy: shorter avg word -> higher score
    reading_ease = max(0.0, 1.0 - (avg_word_len - 3.5) / 3.5)

    return {
        "date_density": len(dates) / n,
        "evidence_density": evidence_hits / n,
        "narrative_density": narrative_hits / n,
        "counter_density": counter_hits / n,
        "reading_ease": reading_ease,
        "avg_word_len": avg_word_len,
        "token_count": float(n),
    }


# ------------------------------------------------------------------
# Persona affinity scoring
# ------------------------------------------------------------------

def score_chunk_for_personas(chunk: str) -> Dict[str, float]:
    """Return {persona_key: affinity_score in [0, 1+]} for one chunk."""
    feats = extract_features(chunk)
    out: Dict[str, float] = {}
    for key, persona in PERSONAS.items():
        b = persona.retrieval
        raw = (
            b.prefers_dated_events    * feats["date_density"]      * 6.0
          + b.prefers_evidence_words  * feats["evidence_density"]  * 8.0
          + b.prefers_narrative_words * feats["narrative_density"] * 8.0
          + b.prefers_simple_language * feats["reading_ease"]      * 1.0
          + b.prefers_counterexamples * feats["counter_density"]   * 6.0
        )
        # squash to (0, ~1.5) so scores are comparable across chunks
        out[key] = round(1.0 / (1.0 + math.exp(-raw + 1.0)), 4)
    return out


def features_and_scores(chunk: str) -> Dict[str, Any]:
    """Convenience: return features + persona scores together."""
    return {
        "features": extract_features(chunk),
        "persona_scores": score_chunk_for_personas(chunk),
    }
