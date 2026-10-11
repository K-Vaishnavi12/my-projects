"""
Feature engineering pipeline for PatientFlow AI.

Two feature sets:
    - X_clf: features available BEFORE the appointment, used for predicting
      cancellation/no-show. No leakage from queue state.
    - X_reg: features available AT CHECK-IN (queue is observable), used for
      predicting wait time. Includes queue-state features.

Key engineered features:
    - Cyclical encoding for hour-of-day and day-of-week (sin/cos pairs).
    - Doctor-level target encoding for service speed.
    - Lead-time bucketing (short/medium/long).
    - Patient reliability score = prior_visits / (1 + prior_no_shows).
    - Queue-load features (only for the regressor, computed leak-free).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


# ----------------------------- Feature constants ------------------------------

CLASSIFIER_FEATURES_NUMERIC = [
    "age", "lead_time_days", "prior_no_shows", "prior_visits",
    "patient_reliability", "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    "is_monday_morning", "is_weekend", "is_lunch_hour",
    "doctor_mean_service", "doctor_no_show_rate",
]
CLASSIFIER_FEATURES_CATEGORICAL = [
    "doctor_id", "appointment_type", "sex",
    "lead_time_bucket", "has_insurance", "sms_reminder",
]

REGRESSOR_FEATURES_NUMERIC = CLASSIFIER_FEATURES_NUMERIC + [
    "queue_length_60min", "queue_load_minutes", "doctor_busyness_today",
]
REGRESSOR_FEATURES_CATEGORICAL = CLASSIFIER_FEATURES_CATEGORICAL


# ------------------------------- Helpers --------------------------------------

def _cyclical(values: np.ndarray, period: int) -> tuple[np.ndarray, np.ndarray]:
    rad = 2.0 * np.pi * values / period
    return np.sin(rad), np.cos(rad)


def _bucket_lead_time(days: pd.Series) -> pd.Series:
    return pd.cut(
        days, bins=[-1, 1, 7, 30, 1000],
        labels=["same_day", "short", "medium", "long"],
    ).astype(str)


# --------------------------- Encoder fit/transform ----------------------------

@dataclass
class EncoderState:
    """Statistics learned only from the training fold (no leakage)."""
    doctor_mean_service: dict[str, float]
    doctor_no_show_rate: dict[str, float]
    global_service: float
    global_no_show: float

    def to_dict(self) -> dict:
        return {
            "doctor_mean_service": self.doctor_mean_service,
            "doctor_no_show_rate": self.doctor_no_show_rate,
            "global_service": self.global_service,
            "global_no_show": self.global_no_show,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EncoderState":
        return cls(
            doctor_mean_service=d["doctor_mean_service"],
            doctor_no_show_rate=d["doctor_no_show_rate"],
            global_service=d["global_service"],
            global_no_show=d["global_no_show"],
        )


def fit_encoders(df_train: pd.DataFrame) -> EncoderState:
    """Fit target-encodings on the training data only."""
    attended = df_train[df_train["cancelled"] == 0]
    doc_serv = attended.groupby("doctor_id")["wait_minutes"].mean().to_dict()
    doc_ns = df_train.groupby("doctor_id")["cancelled"].mean().to_dict()
    return EncoderState(
        doctor_mean_service=doc_serv,
        doctor_no_show_rate=doc_ns,
        global_service=float(attended["wait_minutes"].mean()),
        global_no_show=float(df_train["cancelled"].mean()),
    )


# ------------------------------ Main transform --------------------------------

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ts = pd.to_datetime(df["appointment_time"])
    df["appointment_time"] = ts
    df["hour"] = ts.dt.hour
    df["dow"] = ts.dt.dayofweek
    df["date"] = ts.dt.date
    hs, hc = _cyclical(df["hour"].to_numpy(), 24)
    ds, dc = _cyclical(df["dow"].to_numpy(), 7)
    df["hour_sin"], df["hour_cos"] = hs, hc
    df["dow_sin"], df["dow_cos"] = ds, dc
    df["is_monday_morning"] = ((df["dow"] == 0) & (df["hour"] < 11)).astype(int)
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["is_lunch_hour"] = ((df["hour"] >= 12) & (df["hour"] <= 13)).astype(int)
    df["lead_time_bucket"] = _bucket_lead_time(df["lead_time_days"])
    df["patient_reliability"] = (
        df["prior_visits"].astype(float) / (1.0 + df["prior_no_shows"].astype(float))
    )
    return df


def add_target_encoded(df: pd.DataFrame, enc: EncoderState) -> pd.DataFrame:
    df = df.copy()
    df["doctor_mean_service"] = (
        df["doctor_id"].map(enc.doctor_mean_service).fillna(enc.global_service)
    )
    df["doctor_no_show_rate"] = (
        df["doctor_id"].map(enc.doctor_no_show_rate).fillna(enc.global_no_show)
    )
    return df


def add_queue_state_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute queue-state features for the wait-time regressor.

    For every appointment, we look at:
        - queue_length_60min: number of OTHER same-doctor appointments scheduled
          within +/- 60 minutes.
        - queue_load_minutes: sum of expected service times for non-cancelled
          appointments earlier the same day on the same doctor (cumulative load).
        - doctor_busyness_today: total appointments that doctor has today.

    These features only use data observable at check-in (no future leakage of
    actual wait times).
    """
    df = df.copy().sort_values(["doctor_id", "appointment_time"]).reset_index(drop=True)

    # doctor_busyness_today = count of appointments same doctor + same date
    df["doctor_busyness_today"] = df.groupby(
        ["doctor_id", "date"]
    )["appointment_id"].transform("count").astype(int)

    # Queue length within +/- 60 minutes for same doctor
    queue_len = np.zeros(len(df), dtype=int)
    queue_load = np.zeros(len(df), dtype=float)

    # Average expected service time per type x doctor (rough proxy)
    type_service_proxy = {
        "consultation": 14.0, "follow_up": 9.0, "diagnostic": 20.0,
        "vaccination": 6.0, "emergency": 18.0,
    }
    df["_serv_proxy"] = df["appointment_type"].map(type_service_proxy)

    for _, group in df.groupby("doctor_id", sort=False):
        idx = group.index.to_numpy()
        times = group["appointment_time"].to_numpy()
        serv = group["_serv_proxy"].to_numpy()
        date_arr = group["date"].to_numpy()

        for i, t in enumerate(times):
            window_start = t - np.timedelta64(60, "m")
            window_end = t + np.timedelta64(60, "m")
            in_window = (times >= window_start) & (times <= window_end)
            in_window[i] = False
            queue_len[idx[i]] = in_window.sum()

            same_day_earlier = (date_arr == date_arr[i]) & (times < t)
            queue_load[idx[i]] = serv[same_day_earlier].sum()

    df["queue_length_60min"] = queue_len
    df["queue_load_minutes"] = queue_load
    df = df.drop(columns=["_serv_proxy"])
    return df


def build_feature_frames(
    df: pd.DataFrame,
    enc: EncoderState,
    *,
    include_queue: bool,
) -> pd.DataFrame:
    df = add_time_features(df)
    df = add_target_encoded(df, enc)
    if include_queue:
        df = add_queue_state_features(df)
    return df


# ---------------------------------- CLI ---------------------------------------

def _smoke_test() -> None:
    """Quick check that we can run the pipeline on a small slice."""
    df = pd.read_parquet("ml/data/appointments.parquet").head(2000)
    enc = fit_encoders(df)
    out = build_feature_frames(df, enc, include_queue=True)
    print("Output columns:", list(out.columns))
    print("Shape:", out.shape)
    print(out[["doctor_id", "queue_length_60min", "queue_load_minutes",
               "doctor_busyness_today", "doctor_mean_service",
               "doctor_no_show_rate"]].head())


if __name__ == "__main__":
    _smoke_test()
