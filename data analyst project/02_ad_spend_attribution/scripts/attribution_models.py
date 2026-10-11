"""
Multi-touch attribution: linear, time-decay, position-based (U-shaped).
Assigns credit to each touchpoint in a conversion path.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_touchpoints(path: str) -> pd.DataFrame:
    """Expects: user_id, touch_date, channel, touch_order, conversion_id."""
    df = pd.read_csv(path)
    df["touch_date"] = pd.to_datetime(df["touch_date"])
    return df


def linear_attribution(touchpoints: pd.DataFrame) -> pd.DataFrame:
    """Credit = 1 / num_touches per conversion path."""
    paths = touchpoints.groupby("conversion_id").agg(
        touches=("channel", "count"),
        channels=("channel", list),
    ).reset_index()
    paths["credit_per_touch"] = 1.0 / paths["touches"]
    out = touchpoints.merge(
        paths[["conversion_id", "credit_per_touch", "touches"]],
        on="conversion_id",
        how="left",
    )
    out["attribution_credit"] = out["credit_per_touch"]
    return out


def time_decay_attribution(touchpoints: pd.DataFrame, half_life_days: float = 7.0) -> pd.DataFrame:
    """Credit proportional to recency; more weight to touches closer to conversion."""
    conv_date = touchpoints.groupby("conversion_id")["touch_date"].transform("max")
    touchpoints = touchpoints.copy()
    touchpoints["days_to_conv"] = (conv_date - touchpoints["touch_date"]).dt.total_seconds() / 86400
    touchpoints["weight"] = np.exp(-0.693 * touchpoints["days_to_conv"] / half_life_days)
    total = touchpoints.groupby("conversion_id")["weight"].transform("sum")
    touchpoints["attribution_credit"] = touchpoints["weight"] / total
    return touchpoints


def position_based_attribution(touchpoints: pd.DataFrame, first_last_share: float = 0.4) -> pd.DataFrame:
    """U-shaped: first and last touch share 40% each (default), rest split among middle."""
    tp = touchpoints.sort_values(["conversion_id", "touch_order"])
    tp["position"] = tp.groupby("conversion_id").cumcount() + 1
    tp["total_touches"] = tp.groupby("conversion_id")["channel"].transform("count")
    share_middle = 1.0 - 2 * first_last_share
    def credit(row):
        n = row["total_touches"]
        if n <= 2:
            return 1.0 / n
        if row["position"] == 1 or row["position"] == n:
            return first_last_share
        return share_middle / (n - 2)
    tp["attribution_credit"] = tp.apply(credit, axis=1)
    return tp


def channel_summary(attributed: pd.DataFrame) -> pd.DataFrame:
    """Sum attribution credit by channel."""
    return (
        attributed.groupby("channel")
        .agg(
            attributed_conversions=("attribution_credit", "sum"),
            touch_count=("channel", "count"),
        )
        .reset_index()
    )


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[1] / "data"
    path = data_dir / "touchpoints.csv"
    if path.exists():
        tp = load_touchpoints(str(path))
        linear = linear_attribution(tp)
        print("Linear attribution by channel:")
        print(channel_summary(linear))
        decay = time_decay_attribution(tp)
        print("Time-decay attribution by channel:")
        print(channel_summary(decay))
    else:
        print("Place touchpoints.csv in 02_ad_spend_attribution/data/ or run generate_sample_campaign_data.py")
