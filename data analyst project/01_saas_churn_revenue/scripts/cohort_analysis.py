"""
Cohort retention analysis for SaaS subscriptions.
Computes retention by signup cohort and period (month/quarter).
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_subscription_data(path: str) -> pd.DataFrame:
    """Load subscription log with at least: customer_id, start_date, end_date, mrr, status."""
    df = pd.read_csv(path)
    df["start_date"] = pd.to_datetime(df["start_date"])
    if "end_date" in df.columns:
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    return df


def assign_cohort(df: pd.DataFrame, date_col: str = "start_date") -> pd.DataFrame:
    """Assign cohort month (first period) per customer."""
    out = df.copy()
    out["cohort_month"] = out.groupby("customer_id")[date_col].transform("min").dt.to_period("M")
    return out


def compute_retention_matrix(
    df: pd.DataFrame,
    period_col: str = "period_month",
    value_col: str = "retention_pct",
) -> pd.DataFrame:
    """
    Build cohort x period retention matrix.
    Expects columns: customer_id, cohort_month, period_month, and optionally active (0/1).
    """
    agg = (
        df.groupby(["cohort_month", period_col])
        .agg(
            customers=("customer_id", "nunique"),
            active=("active", "sum") if "active" in df.columns else ("customer_id", "count"),
        )
        .reset_index()
    )
    if "active" not in agg.columns:
        agg["active"] = agg["customers"]
    cohort_sizes = df.groupby("cohort_month")["customer_id"].nunique()
    agg["cohort_size"] = agg["cohort_month"].map(cohort_sizes)
    agg[value_col] = (agg["active"] / agg["cohort_size"] * 100).round(2)
    return agg


def pivot_retention(agg: pd.DataFrame, value_col: str = "retention_pct") -> pd.DataFrame:
    """Pivot to cohort (rows) x period (columns) for heatmap."""
    return agg.pivot(index="cohort_month", columns="period_month", values=value_col)


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[1] / "data"
    sub_path = data_dir / "subscriptions.csv"
    if not sub_path.exists():
        print("Place subscriptions.csv in 01_saas_churn_revenue/data/ or use generate_sample_data.py")
    else:
        df = load_subscription_data(str(sub_path))
        df = assign_cohort(df)
        df["period_month"] = df["start_date"].dt.to_period("M")
        df["active"] = 1  # customize for churn flag if needed
        retention_agg = compute_retention_matrix(df)
        matrix = pivot_retention(retention_agg)
        print(matrix.head(10))
