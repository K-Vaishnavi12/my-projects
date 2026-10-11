"""Legal/regulatory text classifier dataset.

Builds a synthetic but realistic 4-class corpus (compliance / regulatory /
litigation / governance) from templates. Stored as CSV in
``ml_data_dir/legal/legal_corpus.csv`` and merged with anything found in
``data/legal/legal.json`` (real records) when available.
"""
from __future__ import annotations
import random
from pathlib import Path
from typing import Tuple

import pandas as pd

from src.ml.config import LEGAL_LABEL2ID, LEGAL_ID2LABEL, ml_data_dir
from src.config import get_settings


def _csv_path() -> Path:
    p = ml_data_dir() / "legal"
    p.mkdir(parents=True, exist_ok=True)
    return p / "legal_corpus.csv"


# ── Templates per class (rich enough to fight overfitting) ─────────
_TEMPLATES = {
    "compliance": [
        "MCA21 annual return for {entity} is due on {date}; ensure form MGT-7 filing.",
        "Statutory audit report for {entity} must be filed before {date}.",
        "GST monthly return GSTR-3B due for {entity} by {date}.",
        "Form DPT-3 deposit return pending for {entity}; deadline {date}.",
        "ROC compliance: form AOC-4 financial statements due {date} for {entity}.",
        "Income tax audit under section 44AB pending for {entity}.",
        "Director KYC (DIR-3 KYC) renewal pending for board members of {entity}.",
        "Company secretary certificate must be attached with annual return of {entity}.",
        "TDS quarterly return for {entity} due by {date}.",
        "Compliance certificate from practising CS pending for {entity}.",
        "PF and ESI monthly contribution remittance due for {entity}.",
        "{entity} must file form CSR-2 detailing CSR spend before {date}.",
    ],
    "regulatory": [
        "SEBI revised the framework for related-party transactions effective {date}.",
        "RBI issued a circular tightening capital adequacy norms for NBFCs.",
        "Ministry of Corporate Affairs notified an amendment to the Companies Act.",
        "SEBI introduced new disclosure requirements for listed entities from {date}.",
        "IRDAI updated solvency margin guidelines applicable to insurers.",
        "MCA notified amendments to the Companies (Audit and Auditors) Rules.",
        "SEBI proposed mandatory ESG disclosures for the top 1000 listed companies.",
        "RBI revised priority sector lending targets for scheduled banks.",
        "CCI released revised thresholds for combination notification under section 5.",
        "SEBI tightened insider trading rules with stricter pre-clearance norms.",
        "SEBI norms on minimum public shareholding revised for newly listed firms.",
        "Income tax department issued circular clarifying TDS on virtual digital assets.",
    ],
    "litigation": [
        "{entity} filed a writ petition challenging the SEBI penalty order.",
        "The NCLT admitted a corporate insolvency resolution process against {entity}.",
        "Supreme Court upheld the SEBI order penalising {entity} for non-disclosure.",
        "{entity} faces a class action suit alleging mis-statements in the prospectus.",
        "Income tax tribunal dismissed the appeal filed by {entity}.",
        "High Court stayed the SEBI debarment order against the promoter of {entity}.",
        "An arbitration tribunal awarded damages against {entity} in a contract dispute.",
        "{entity} settled the consumer protection case before the NCDRC.",
        "Enforcement Directorate issued a show-cause notice to {entity} under PMLA.",
        "{entity} filed an appeal before SAT against the SEBI adjudication order.",
        "NCLAT remanded the matter back to NCLT for fresh adjudication on {entity}.",
        "Bombay High Court issued notice to {entity} in a public interest litigation.",
    ],
    "governance": [
        "Board of {entity} approved appointment of an additional independent director.",
        "{entity} reconstituted its audit committee in line with SEBI LODR requirements.",
        "AGM of {entity} scheduled on {date}; notice circulated to shareholders.",
        "Board meeting of {entity} approved the unaudited quarterly results.",
        "{entity} disclosed a related-party transaction approved by audit committee.",
        "Nomination and remuneration committee of {entity} reviewed senior management pay.",
        "Whistleblower mechanism reviewed and reaffirmed by the board of {entity}.",
        "{entity} announced succession plan for the position of managing director.",
        "Risk management committee of {entity} adopted a new enterprise risk framework.",
        "Stakeholders relationship committee of {entity} addressed shareholder grievances.",
        "CSR committee of {entity} approved budget for sustainability initiatives.",
        "{entity} board approved code of conduct for prevention of insider trading.",
    ],
}

_ENTITIES = [
    "Acme Industries", "Globex Pharma", "Initech Ltd", "Cyberdyn Systems",
    "Omnicorp Ltd", "TechFlow Pvt Ltd", "GreenEnergy Solutions",
    "HealthBridge Ltd", "Reliance Industries", "Tata Consultancy",
    "Infosys Ltd", "HDFC Bank", "Larsen & Toubro", "Bharti Airtel",
]
_DATES = [
    "2025-03-31", "2025-04-15", "2025-05-30", "2025-06-30", "2025-07-31",
    "2025-09-30", "2025-10-15", "2025-11-30", "2026-01-15", "2026-03-31",
]


def _generate_synthetic(rows_per_class: int = 120, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    records: list[dict] = []
    for cls, templates in _TEMPLATES.items():
        for _ in range(rows_per_class):
            tmpl = rng.choice(templates)
            text = tmpl.format(entity=rng.choice(_ENTITIES), date=rng.choice(_DATES))
            records.append({"text": text, "label_id": LEGAL_LABEL2ID[cls], "label": cls})
    rng.shuffle(records)
    return pd.DataFrame(records)


def _merge_real_records(df: pd.DataFrame) -> pd.DataFrame:
    """Pull anything we already have in data/legal/legal.json so the model
    sees the user's real data alongside synthetic templates.
    """
    settings = get_settings()
    real_path = Path(settings.legal_data_path) / "legal.json"
    if not real_path.exists():
        return df
    try:
        import json
        with open(real_path, encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        return df
    extras: list[dict] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        title = (it.get("title") or "").strip()
        body = (it.get("summary") or "").strip()
        text = (title + ". " + body).strip(". ").strip()
        cls = (it.get("type") or "").lower()
        if not text or cls not in LEGAL_LABEL2ID:
            continue
        extras.append({"text": text, "label_id": LEGAL_LABEL2ID[cls], "label": cls})
    if not extras:
        return df
    return pd.concat([df, pd.DataFrame(extras)], ignore_index=True)


def load_legal_dataset(force_regenerate: bool = False) -> pd.DataFrame:
    csv_path = _csv_path()
    if csv_path.exists() and not force_regenerate:
        df = pd.read_csv(csv_path)
        if not df.empty:
            return df
    df = _generate_synthetic()
    df = _merge_real_records(df)
    df.to_csv(csv_path, index=False)
    return df


def train_test_split_legal(df: pd.DataFrame, test_size: float = 0.2,
                            seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
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
    df = load_legal_dataset(force_regenerate=True)
    print(df["label"].value_counts())
    print("rows:", len(df))
