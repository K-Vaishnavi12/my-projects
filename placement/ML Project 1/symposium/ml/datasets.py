"""Synthetic labeled data for the ML models.

Real "stance / agreement" datasets are large and off-topic; we
generate a small, deterministic training set from templates so:
- the demo trains in seconds
- the models are reproducible
- no external download is needed

Every generator returns a Pandas DataFrame with the label column
named ``label`` (categorical) or ``target`` (continuous), plus a
``text`` column.
"""

from __future__ import annotations

import random
from typing import List

import pandas as pd


_RNG = random.Random(42)


# ------------------------------------------------------------------
# Stance detection
# ------------------------------------------------------------------

_AGREE_PATTERNS = [
    "I agree that {claim}.",
    "Indeed, {claim} is well-established.",
    "The evidence supports the view that {claim}.",
    "It is fair to say that {claim}.",
    "As several studies show, {claim}.",
    "Historically speaking, {claim} has been repeatedly confirmed.",
    "This aligns with the point that {claim}.",
    "Yes, and building on this: {claim}.",
]

_DISAGREE_PATTERNS = [
    "I disagree - {claim} overstates the case.",
    "However, {claim} ignores important counter-examples.",
    "But wait - {claim} does not follow from the evidence.",
    "Actually, {claim} has been challenged by recent findings.",
    "That claim is too strong: {claim}.",
    "Contrary to that, {claim} is at best partially true.",
    "The data does not support {claim} as stated.",
    "This is a common misconception; in fact {claim}'s opposite holds.",
]

_NEUTRAL_PATTERNS = [
    "It is worth noting that {claim}.",
    "One perspective is that {claim}, another is not.",
    "The situation with {claim} is nuanced.",
    "Both interpretations of {claim} have merit.",
    "Depending on the frame, {claim} may or may not hold.",
    "There is ongoing debate about {claim}.",
    "Evidence for and against {claim} is mixed.",
    "Let me set out the terms of {claim} before judging.",
]

_CLAIMS = [
    "renewable energy replaces fossil fuels quickly",
    "AI will improve education",
    "history repeats itself",
    "quantum mechanics is deterministic",
    "climate change is human-caused",
    "free will exists",
    "democracy is the best system",
    "literature reveals the mind of a culture",
    "market economies self-regulate",
    "consciousness emerges from neurons",
    "language shapes thought",
    "art reflects politics",
    "vaccines are safe and effective",
    "civilisations decline slowly",
    "empires always fall",
]


def _gen(patterns: List[str], label: str, n: int) -> pd.DataFrame:
    rows = []
    for _ in range(n):
        pat = _RNG.choice(patterns)
        claim = _RNG.choice(_CLAIMS)
        rows.append({"text": pat.format(claim=claim), "label": label})
    return pd.DataFrame(rows)


def stance_dataset(n_per_class: int = 200) -> pd.DataFrame:
    df = pd.concat(
        [
            _gen(_AGREE_PATTERNS, "agree", n_per_class),
            _gen(_DISAGREE_PATTERNS, "disagree", n_per_class),
            _gen(_NEUTRAL_PATTERNS, "neutral", n_per_class),
        ],
        ignore_index=True,
    ).sample(frac=1, random_state=42).reset_index(drop=True)
    return df


# ------------------------------------------------------------------
# Topic classification
# ------------------------------------------------------------------

_TOPIC_TEMPLATES = {
    "history": [
        "In {year} a revolution broke out in {place}, changing the political map.",
        "The reign of {ruler} lasted {n} years and was marked by war.",
        "Trade along the {route} shaped economies for centuries.",
        "The battle of {place} in {year} was a turning point.",
    ],
    "science": [
        "The study measured {metric} across {n} samples with p < 0.05.",
        "A mechanism involving {particle} explains the observed data.",
        "Experiments in {year} confirmed the theory of {topic}.",
        "The hypothesis was tested using a randomised control design.",
    ],
    "philosophy": [
        "The distinction between {a} and {b} lies at the heart of ethics.",
        "As {thinker} argued, existence precedes essence.",
        "Free will and determinism are not necessarily incompatible.",
        "Epistemology asks how we can know what we {verb}.",
    ],
    "literature": [
        "The protagonist's descent into {thing} echoes {work}.",
        "Shakespeare's use of the {device} deepens the tragedy.",
        "Kafka's world renders the bureaucratic {emotion} of modernity.",
        "The novel weaves together {a} and {b} into one narrative.",
    ],
    "current_events": [
        "The startup raised ${n}M to build a {tool} for {domain}.",
        "Regulators are considering rules for AI models over {n} parameters.",
        "A new climate agreement targets {n}% emissions reduction by 2030.",
        "Cybersecurity teams warned of a supply-chain attack this week.",
    ],
}

_FILLERS = {
    "year": ["1789", "1848", "1914", "1969", "2001", "2023"],
    "place": ["Paris", "Berlin", "Rome", "Beijing", "Delhi"],
    "ruler": ["Augustus", "Charlemagne", "Ashoka", "Elizabeth I"],
    "n": ["10", "50", "200", "1000"],
    "route": ["Silk Road", "Mediterranean", "Atlantic"],
    "metric": ["latency", "yield", "reaction time", "growth rate"],
    "particle": ["muon", "electron", "gluon", "neutrino"],
    "topic": ["gravity", "evolution", "quantum entanglement"],
    "a": ["being", "form"],
    "b": ["becoming", "matter"],
    "thinker": ["Sartre", "Kant", "Nietzsche"],
    "verb": ["think", "measure"],
    "thing": ["memory", "madness", "grace"],
    "work": ["the Iliad", "Hamlet", "Ulysses"],
    "device": ["soliloquy", "double plot"],
    "emotion": ["dread", "confusion"],
    "tool": ["copilot", "vector database", "search engine"],
    "domain": ["healthcare", "logistics", "education"],
}


def _fill(t: str) -> str:
    out = t
    for k, opts in _FILLERS.items():
        key = "{" + k + "}"
        if key in out:
            out = out.replace(key, _RNG.choice(opts))
    return out


def topic_dataset(n_per_class: int = 200) -> pd.DataFrame:
    rows = []
    for topic, templates in _TOPIC_TEMPLATES.items():
        for _ in range(n_per_class):
            rows.append({"text": _fill(_RNG.choice(templates)), "label": topic})
    return pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)


# ------------------------------------------------------------------
# Agreement regression
# ------------------------------------------------------------------

def agreement_dataset(n: int = 800) -> pd.DataFrame:
    """A single turn + numeric [0..1] 'agrees with prior turn' score.

    We build the label from lexical cues so the regression has real
    signal.
    """
    rows = []
    agree_words = {"agree", "indeed", "yes", "confirmed", "supports"}
    disagree_words = {"disagree", "however", "but", "wrong", "misconception"}

    df_stance = stance_dataset(n_per_class=n // 3)
    for _, r in df_stance.iterrows():
        text = r["text"].lower()
        tokens = text.split()
        a_hits = sum(1 for t in tokens if t.strip(",.") in agree_words)
        d_hits = sum(1 for t in tokens if t.strip(",.") in disagree_words)
        score = 0.5 + 0.15 * a_hits - 0.15 * d_hits
        score = max(0.0, min(1.0, score))
        rows.append({"text": r["text"], "target": round(score, 3)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# Debate-outcome dataset for the neural net
# ------------------------------------------------------------------

def debate_outcome_dataset(n: int = 400) -> pd.DataFrame:
    """Aggregated features per debate + label = consensus_score bucket.

    Features are pretended to come from a completed debate:
    - avg agreement of each persona
    - std across personas
    - turns count
    Labels: 'high' / 'medium' / 'low' consensus.
    """
    rows = []
    for _ in range(n):
        avgs = [_RNG.uniform(0.2, 0.9) for _ in range(5)]
        turns = _RNG.randint(4, 12)
        std = pd.Series(avgs).std()
        mean = pd.Series(avgs).mean()
        consensus = max(0.0, min(1.0, mean - 0.4 * std))
        label = "high" if consensus >= 0.7 else ("medium" if consensus >= 0.45 else "low")
        rows.append({
            "avg_historian": avgs[0],
            "avg_scientist": avgs[1],
            "avg_poet": avgs[2],
            "avg_skeptic": avgs[3],
            "avg_child": avgs[4],
            "turns": turns,
            "std_across": std,
            "mean_across": mean,
            "label": label,
        })
    return pd.DataFrame(rows)
