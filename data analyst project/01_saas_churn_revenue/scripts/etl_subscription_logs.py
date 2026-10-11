"""
ETL for SaaS subscription logs.
Loads/generates subscription and customer data; outputs clean tables for cohort and churn.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def generate_sample_subscriptions(
    n_customers: int = 5000,
    start: str = "2022-01-01",
    end: str = "2024-12-31",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate simulated subscription logs for cohort/churn analysis."""
    np.random.seed(seed)
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    subs = []
    for i in range(1, n_customers + 1):
        sub_start = start_dt + (end_dt - start_dt) * np.random.random()
        tenure_months = np.random.exponential(12)
        sub_end = sub_start + pd.DateOffset(months=tenure_months)
        if sub_end > end_dt:
            sub_end = pd.NaT
            status = "active"
        else:
            status = "churned"
        mrr = np.random.choice([29, 49, 99, 199, 499], p=[0.3, 0.35, 0.2, 0.1, 0.05])
        subs.append({
            "subscription_id": i,
            "customer_id": i,
            "plan_id": np.random.choice(["basic", "pro", "enterprise"], p=[0.5, 0.35, 0.15]),
            "mrr": mrr,
            "start_date": sub_start.date(),
            "end_date": sub_end.date() if pd.notna(sub_end) else None,
            "status": status,
        })
    return pd.DataFrame(subs)


def generate_sample_customers(subscriptions: pd.DataFrame) -> pd.DataFrame:
    """Derive customer table from subscriptions (signup = first start_date)."""
    first = subscriptions.groupby("customer_id")["start_date"].min().reset_index()
    first.columns = ["customer_id", "signup_date"]
    first["segment"] = np.random.choice(["SMB", "Mid-Market", "Enterprise"], size=len(first), p=[0.6, 0.3, 0.1])
    first["region"] = np.random.choice(["NA", "EMEA", "APAC"], size=len(first), p=[0.5, 0.3, 0.2])
    return first


def run_etl(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load or generate subscription + customer data; return clean DataFrames.
    """
    sub_path = data_dir / "subscriptions.csv"
    cust_path = data_dir / "customers.csv"
    if sub_path.exists():
        subs = pd.read_csv(sub_path)
        subs["start_date"] = pd.to_datetime(subs["start_date"])
        subs["end_date"] = pd.to_datetime(subs["end_date"], errors="coerce")
    else:
        subs = generate_sample_subscriptions()
        subs.to_csv(data_dir / "subscriptions.csv", index=False)
    if cust_path.exists():
        customers = pd.read_csv(cust_path)
        customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    else:
        customers = generate_sample_customers(subs)
        customers.to_csv(data_dir / "customers.csv", index=False)
    return subs, customers


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    subs, customers = run_etl(data_dir)
    print("Subscriptions:", subs.shape)
    print("Customers:", customers.shape)
    print(subs.head())
