"""
Generate sample campaign spend, conversions, and touchpoints for attribution demos.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def generate_campaign_spend(
    start: str = "2024-01-01",
    end: str = "2024-06-30",
    channels: list = None,
    seed: int = 42,
) -> pd.DataFrame:
    if channels is None:
        channels = ["google_paid", "meta", "linkedin", "organic", "email"]
    np.random.seed(seed)
    dates = pd.date_range(start=start, end=end, freq="D")
    rows = []
    for d in dates:
        for ch in channels:
            spend = np.random.lognormal(3, 1.5)
            rows.append({
                "date": d.date(),
                "channel": ch,
                "spend": round(spend, 2),
                "impressions": int(np.random.lognormal(10, 1)),
                "clicks": int(np.random.poisson(100)),
            })
    return pd.DataFrame(rows)


def generate_conversions_and_touchpoints(
    n_conversions: int = 2000,
    start: str = "2024-01-01",
    end: str = "2024-06-30",
    channels: list = None,
    seed: int = 43,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if channels is None:
        channels = ["google_paid", "meta", "linkedin", "organic", "email"]
    np.random.seed(seed)
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    conversions = []
    touchpoints = []
    for i in range(1, n_conversions + 1):
        conv_date = start_dt + (end_dt - start_dt) * np.random.random()
        num_touches = np.random.choice([1, 2, 3, 4, 5], p=[0.2, 0.35, 0.25, 0.15, 0.05])
        path_channels = np.random.choice(channels, size=num_touches, replace=True)
        path_channels = list(dict.fromkeys(path_channels))  # simple dedup order
        if len(path_channels) < num_touches:
            path_channels += list(np.random.choice(channels, size=num_touches - len(path_channels)))
        path_channels = path_channels[:num_touches]
        conversions.append({
            "conversion_id": i,
            "user_id": 10000 + i,
            "conversion_date": conv_date.date(),
            "conversion_value": round(np.random.lognormal(5, 1), 2),
            "conversion_type": np.random.choice(["signup", "trial", "paid"], p=[0.5, 0.3, 0.2]),
            "exposed": np.random.binomial(1, 0.5),
        })
        for ord, ch in enumerate(path_channels, 1):
            touch_date = conv_date - timedelta(days=np.random.exponential(5))
            touchpoints.append({
                "user_id": 10000 + i,
                "touch_date": touch_date.date(),
                "channel": ch,
                "touch_order": ord,
                "conversion_id": i,
            })
    return pd.DataFrame(conversions), pd.DataFrame(touchpoints)


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    spend = generate_campaign_spend()
    conv, tp = generate_conversions_and_touchpoints()
    spend.to_csv(data_dir / "campaign_spend.csv", index=False)
    conv.to_csv(data_dir / "conversions.csv", index=False)
    tp.to_csv(data_dir / "touchpoints.csv", index=False)
    print("Generated:", data_dir / "campaign_spend.csv", data_dir / "conversions.csv", data_dir / "touchpoints.csv")
