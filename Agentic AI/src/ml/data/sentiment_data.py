"""Sentiment dataset loader.

Primary source: HuggingFace ``financial_phrasebank`` (Malo et al., 2014) —
4,840 sentences from financial news labelled negative/neutral/positive.
Falls back to a curated synthetic seed set so training & tests still work
without internet.
"""
from __future__ import annotations
import random
from pathlib import Path
from typing import Tuple

import pandas as pd

from src.ml.config import SENTIMENT_LABEL2ID, ml_data_dir


def _csv_path() -> Path:
    p = ml_data_dir() / "sentiment"
    p.mkdir(parents=True, exist_ok=True)
    return p / "financial_phrasebank.csv"


# ── Synthetic seed set — used when HF datasets unreachable ──────────
_SYNTHETIC: list[tuple[str, str]] = [
    # ── positive ─────────────────────────────────────────────────
    ("Quarterly profit jumped 28%, beating analyst expectations.", "positive"),
    ("The company announced a record dividend after strong earnings.", "positive"),
    ("Revenue surged on robust demand across core markets.", "positive"),
    ("Shares rallied 5% as the firm raised full-year guidance.", "positive"),
    ("Order book grew sharply, signalling a healthy pipeline.", "positive"),
    ("The merger is expected to be highly accretive to earnings.", "positive"),
    ("Margins expanded thanks to disciplined cost management.", "positive"),
    ("The board approved a buyback worth two billion rupees.", "positive"),
    ("Free cash flow doubled compared to the prior quarter.", "positive"),
    ("Investors cheered the upbeat outlook and stronger margins.", "positive"),
    ("Operating profit hit an all-time high this quarter.", "positive"),
    ("The launch of the new product line exceeded sales targets.", "positive"),
    ("Net income rose sharply, lifting the share price.", "positive"),
    ("The firm secured a major government contract worth crores.", "positive"),
    ("Customer growth accelerated, beating internal forecasts.", "positive"),
    # ── negative ─────────────────────────────────────────────────
    ("The company missed earnings estimates and lowered guidance.", "negative"),
    ("Shares slumped 7% after weak quarterly results.", "negative"),
    ("Profit fell sharply due to rising input costs.", "negative"),
    ("The regulator imposed a hefty fine on the bank.", "negative"),
    ("Loan defaults rose, pressuring asset quality.", "negative"),
    ("The CEO resigned amid allegations of accounting fraud.", "negative"),
    ("Demand contracted, dragging revenue lower.", "negative"),
    ("The board cut the dividend after a disappointing year.", "negative"),
    ("Operating losses widened in the consumer segment.", "negative"),
    ("Regulatory action could materially impact future earnings.", "negative"),
    ("The company warned of softer demand in the next quarter.", "negative"),
    ("A data breach exposed millions of customer records.", "negative"),
    ("Margins compressed under intense price competition.", "negative"),
    ("The credit rating was downgraded over rising leverage.", "negative"),
    ("Auditors flagged material weaknesses in internal controls.", "negative"),
    # ── neutral ──────────────────────────────────────────────────
    ("The company filed its annual return with the registrar.", "neutral"),
    ("Trading volumes were broadly in line with the prior session.", "neutral"),
    ("Quarterly results are scheduled for release on Friday.", "neutral"),
    ("The board meeting is set for the end of the month.", "neutral"),
    ("Markets traded in a narrow range through the session.", "neutral"),
    ("The firm appointed a new chief financial officer.", "neutral"),
    ("Headline indices closed flat for the day.", "neutral"),
    ("The annual general meeting will be held on June 14.", "neutral"),
    ("Disclosures were made in line with SEBI requirements.", "neutral"),
    ("Brokerages maintained their existing recommendations.", "neutral"),
    ("The board reviewed compliance with statutory norms.", "neutral"),
    ("Regulatory filings noted a routine change of address.", "neutral"),
    ("Trading was suspended briefly due to a technical glitch.", "neutral"),
    ("The exchange clarified its position on disclosure timelines.", "neutral"),
    ("The company published its sustainability report on its website.", "neutral"),
]


def _augment_synthetic(records: list[tuple[str, str]], factor: int = 8) -> list[tuple[str, str]]:
    """Light augmentation: shuffle, slight phrasing tweaks. Keeps things
    workable when only the small synthetic set is available.
    """
    out: list[tuple[str, str]] = []
    rng = random.Random(42)
    for _ in range(factor):
        for text, label in records:
            variants = [
                text,
                text.replace(".", " today."),
                "Reuters: " + text,
                "ANALYSIS — " + text,
            ]
            out.append((rng.choice(variants), label))
    rng.shuffle(out)
    return out


# ── Public API ──────────────────────────────────────────────────────
def fetch_financial_phrasebank() -> pd.DataFrame | None:
    """Try to fetch FPB via HuggingFace ``datasets``; return None on failure."""
    try:
        from datasets import load_dataset
    except ImportError:
        return None
    try:
        # ``sentences_75agree`` = subset where 75%+ annotators agreed
        ds = load_dataset("financial_phrasebank", "sentences_75agree",
                          split="train", trust_remote_code=True)
        df = pd.DataFrame({
            "text": [r["sentence"] for r in ds],
            # FPB uses 0=negative, 1=neutral, 2=positive in label_text
            "label": [r["label"] for r in ds],
        })
        # FPB ordering: 0=negative, 1=neutral, 2=positive (matches our id space
        # because our config uses negative<neutral<positive too).
        return df
    except Exception as e:
        print(f"[sentiment_data] HF datasets unavailable ({e}); using synthetic")
        return None


def load_sentiment_dataset(force_synthetic: bool = False) -> pd.DataFrame:
    """Return DataFrame[text, label_id, label] cached as CSV after first call."""
    csv_path = _csv_path()
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if not df.empty:
            return df

    df: pd.DataFrame | None = None if force_synthetic else fetch_financial_phrasebank()
    if df is None or df.empty:
        records = _augment_synthetic(_SYNTHETIC, factor=8)
        df = pd.DataFrame({
            "text": [t for t, _ in records],
            "label": [SENTIMENT_LABEL2ID[l] for _, l in records],
        })

    # Normalise column names + add label string
    from src.ml.config import SENTIMENT_ID2LABEL
    df = df.rename(columns={"label": "label_id"} if "label_id" not in df.columns else {})
    if "label_id" not in df.columns:
        df["label_id"] = df["label"]
        df = df.drop(columns=["label"], errors="ignore")
    df["label"] = df["label_id"].map(SENTIMENT_ID2LABEL)
    df = df.dropna(subset=["text", "label_id"]).reset_index(drop=True)
    df.to_csv(csv_path, index=False)
    return df


def train_test_split_text(df: pd.DataFrame, test_size: float = 0.2,
                          seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Stratified shuffle split — class balance preserved in both folds."""
    rng = random.Random(seed)
    train_rows, test_rows = [], []
    for label_id, sub in df.groupby("label_id"):
        rows = sub.sample(frac=1.0, random_state=seed).to_dict("records")
        n_test = max(1, int(len(rows) * test_size))
        test_rows.extend(rows[:n_test])
        train_rows.extend(rows[n_test:])
    rng.shuffle(train_rows); rng.shuffle(test_rows)
    return pd.DataFrame(train_rows), pd.DataFrame(test_rows)


if __name__ == "__main__":
    df = load_sentiment_dataset()
    print(df.head())
    print("class balance:", df["label"].value_counts().to_dict())
    print("rows:", len(df))
