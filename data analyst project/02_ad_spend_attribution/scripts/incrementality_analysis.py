"""
Incrementality analysis: compare exposed vs control (holdout) to measure true lift.
Uses two-group comparison with confidence intervals.
"""

import pandas as pd
import numpy as np
from pathlib import Path

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def load_campaign_and_conversions(
    spend_path: str, conversions_path: str, exposed_flag_col: str = "exposed"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load spend and conversions; conversions should have exposed (0/1) for test/control."""
    spend = pd.read_csv(spend_path)
    spend["date"] = pd.to_datetime(spend["date"])
    conv = pd.read_csv(conversions_path)
    conv["conversion_date"] = pd.to_datetime(conv["conversion_date"])
    if exposed_flag_col not in conv.columns:
        conv[exposed_flag_col] = np.random.binomial(1, 0.5, size=len(conv))  # placeholder
    return spend, conv


def compute_lift(
    control_conversions: np.ndarray,
    exposed_conversions: np.ndarray,
    control_n: int,
    exposed_n: int,
    alpha: float = 0.05,
) -> dict:
    """
    Two-proportion z-test for incrementality.
    Returns lift %, p-value, and CI for the difference in conversion rates.
    """
    if not HAS_SCIPY:
        raise ImportError("scipy required. pip install scipy")
    p_c = control_conversions.sum() / max(control_n, 1)
    p_e = exposed_conversions.sum() / max(exposed_n, 1)
    lift_pct = (p_e - p_c) / max(p_c, 1e-9) * 100
    # Pooled proportion for SE
    p_pool = (control_conversions.sum() + exposed_conversions.sum()) / max(control_n + exposed_n, 1)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / control_n + 1 / exposed_n))
    z = (p_e - p_c) / max(se, 1e-9)
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    margin = stats.norm.ppf(1 - alpha / 2) * se
    return {
        "control_rate": p_c,
        "exposed_rate": p_e,
        "lift_pct": lift_pct,
        "p_value": p_value,
        "ci_low": (p_e - p_c - margin) * 100,
        "ci_high": (p_e - p_c + margin) * 100,
        "significant": p_value < alpha,
    }


def run_incrementality_report(conv_df: pd.DataFrame, exposed_col: str = "exposed", value_col: str = "conversion_value") -> pd.DataFrame:
    """
    Aggregate conversions by exposed vs control; optional revenue comparison.
    """
    agg = (
        conv_df.groupby(exposed_col)
        .agg(
            users=("user_id", "nunique"),
            conversions=("user_id", "count"),
            revenue=(value_col, "sum") if value_col in conv_df.columns else ("user_id", "count"),
        )
        .reset_index()
    )
    agg["conversion_rate"] = agg["conversions"] / agg["users"]
    return agg


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[1] / "data"
    spend_path = data_dir / "campaign_spend.csv"
    conv_path = data_dir / "conversions.csv"
    if conv_path.exists() and "exposed" in pd.read_csv(conv_path, nrows=1).columns:
        spend, conv = load_campaign_and_conversions(str(spend_path), str(conv_path))
        control = conv[conv["exposed"] == 0]
        exposed = conv[conv["exposed"] == 1]
        conv_binary = conv["user_id"].duplicated(keep="first").astype(int)  # simplify to per-user
        conv["converted"] = 1 - conv.groupby("user_id")["user_id"].transform(lambda x: (x.count() == 1).astype(int))
        # Simplified: use conversion count per user
        control_conv = np.ones(control["user_id"].nunique())  # placeholder
        exposed_conv = np.ones(exposed["user_id"].nunique())
        result = compute_lift(
            np.array([0] * max(control["user_id"].nunique() - control["conversion_value"].count(), 1)),
            exposed_conv,
            control["user_id"].nunique(),
            exposed["user_id"].nunique(),
        )
        print(result)
    else:
        print("Add conversions.csv with 'exposed' column (0=control, 1=test) and run again.")
