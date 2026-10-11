"""
Synthetic data generator for PatientFlow AI.

Generates realistic patient appointment data with KNOWN ground-truth structure
so we can verify our ML models recover the signal.

Causal structure encoded:
    - Doctor base service time (mean, variance) varies by doctor.
    - Appointment type changes mean service time multiplicatively.
    - Day-of-week and hour-of-day seasonality (Monday morning rush, lunch dip).
    - Patient age affects no-show probability (older = less likely to skip).
    - Lead time (days between booking and appointment) increases no-show prob.
    - Prior no-show count is the strongest predictor of future no-shows.
    - Queue position at arrival drives most of the wait-time variance.
    - Heteroscedastic noise: variance grows with queue length (realistic).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


# ----------------------------- Configuration ----------------------------------

DOCTORS = {
    "D001_GenPrac_Sharma":   {"mean_service_min": 12.0, "sigma": 3.5, "specialty": "general"},
    "D002_GenPrac_Iyer":     {"mean_service_min": 14.0, "sigma": 4.0, "specialty": "general"},
    "D003_Cardio_Banerjee":  {"mean_service_min": 22.0, "sigma": 6.0, "specialty": "cardiology"},
    "D004_Pediatric_Khan":   {"mean_service_min": 16.0, "sigma": 4.5, "specialty": "pediatrics"},
    "D005_Derma_Roy":        {"mean_service_min": 10.0, "sigma": 2.5, "specialty": "dermatology"},
    "D006_Ortho_Mehta":      {"mean_service_min": 18.0, "sigma": 5.0, "specialty": "orthopedics"},
}

APPT_TYPES = {
    "consultation":   {"service_mult": 1.00, "no_show_base": 0.18},
    "follow_up":      {"service_mult": 0.70, "no_show_base": 0.10},
    "diagnostic":     {"service_mult": 1.40, "no_show_base": 0.08},
    "vaccination":    {"service_mult": 0.45, "no_show_base": 0.22},
    "emergency":      {"service_mult": 1.30, "no_show_base": 0.02},
}

# Hour-of-day load multiplier (24-hour). Index = hour. Approximates a clinic
# day with morning rush, lunch dip, and afternoon spike.
HOURLY_LOAD = np.array([
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3,   # 0-7
    0.9, 1.4, 1.6, 1.5, 1.0, 0.8, 1.2, 1.5,   # 8-15
    1.7, 1.3, 0.9, 0.5, 0.2, 0.0, 0.0, 0.0,   # 16-23
])

# Weekday multiplier: Mon=0..Sun=6. Saturday is half-day, Sunday closed.
WEEKDAY_LOAD = np.array([1.20, 1.00, 1.05, 1.00, 1.10, 0.55, 0.0])


# ------------------------------- Generator ------------------------------------

@dataclass
class GenConfig:
    n_samples: int = 80_000
    start_date: str = "2024-01-01"
    end_date: str = "2025-06-30"
    seed: int = 42


def _sample_age(rng: np.random.Generator, n: int) -> np.ndarray:
    """Mixture of three age groups roughly matching outpatient distribution."""
    comp = rng.choice(3, size=n, p=[0.25, 0.55, 0.20])
    age = np.empty(n)
    age[comp == 0] = rng.normal(8,  4,  size=(comp == 0).sum())   # children
    age[comp == 1] = rng.normal(38, 12, size=(comp == 1).sum())   # adults
    age[comp == 2] = rng.normal(67, 8,  size=(comp == 2).sum())   # seniors
    return np.clip(age, 0, 95).round().astype(int)


def generate(cfg: GenConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)

    # ---- Sample appointment time grid ----
    date_range = pd.date_range(cfg.start_date, cfg.end_date, freq="h")
    # Filter to clinic open hours and non-Sunday days
    valid_mask = (
        (date_range.hour >= 8) & (date_range.hour <= 19) &
        (date_range.dayofweek != 6)
    )
    valid_slots = date_range[valid_mask]

    # Weight slot probability by hourly+weekday load
    hour_w = HOURLY_LOAD[valid_slots.hour.to_numpy()]
    wday_w = WEEKDAY_LOAD[valid_slots.dayofweek.to_numpy()]
    slot_weights = hour_w * wday_w
    slot_weights = slot_weights / slot_weights.sum()

    chosen_slot_idx = rng.choice(
        len(valid_slots), size=cfg.n_samples, replace=True, p=slot_weights
    )
    appt_time = valid_slots[chosen_slot_idx].to_numpy()

    # Add minute jitter within the hour
    minute_offsets = rng.integers(0, 60, size=cfg.n_samples)
    appt_time = appt_time + minute_offsets.astype("timedelta64[m]")

    # ---- Patient demographics ----
    age = _sample_age(rng, cfg.n_samples)
    sex = rng.choice(["M", "F", "O"], size=cfg.n_samples, p=[0.48, 0.50, 0.02])
    has_insurance = rng.random(cfg.n_samples) < 0.72

    # ---- Booking metadata ----
    lead_time_days = np.clip(
        rng.exponential(scale=4.5, size=cfg.n_samples).astype(int), 0, 60
    )
    prior_no_shows = rng.poisson(lam=0.4, size=cfg.n_samples)
    prior_visits = rng.poisson(lam=3.5, size=cfg.n_samples)
    sms_reminder = rng.random(cfg.n_samples) < 0.65

    # ---- Doctor + appointment type ----
    doc_ids = list(DOCTORS.keys())
    doctor_id = rng.choice(doc_ids, size=cfg.n_samples)
    appt_type = rng.choice(
        list(APPT_TYPES.keys()), size=cfg.n_samples,
        p=[0.45, 0.25, 0.10, 0.15, 0.05],
    )

    df = pd.DataFrame({
        "appointment_id": [f"A{i:07d}" for i in range(cfg.n_samples)],
        "appointment_time": appt_time,
        "doctor_id": doctor_id,
        "appointment_type": appt_type,
        "age": age,
        "sex": sex,
        "has_insurance": has_insurance,
        "lead_time_days": lead_time_days,
        "prior_no_shows": prior_no_shows,
        "prior_visits": prior_visits,
        "sms_reminder": sms_reminder,
    })

    # Sort by doctor + time so we can compute queue state
    df = df.sort_values(["doctor_id", "appointment_time"]).reset_index(drop=True)

    # ============================================================
    # CANCELLATION / NO-SHOW PROBABILITY (KNOWN GROUND TRUTH)
    # ============================================================
    # logit(p) = base + age_effect + lead_effect + history_effect
    #            + sms_effect + insurance_effect + type_base
    base_logit = np.array([np.log(APPT_TYPES[t]["no_show_base"] /
                                  (1 - APPT_TYPES[t]["no_show_base"]))
                           for t in df["appointment_type"]])

    age_effect = -0.015 * (df["age"].to_numpy() - 35)            # older -> lower
    lead_effect = 0.04 * df["lead_time_days"].to_numpy()         # longer -> higher
    history_effect = 0.55 * df["prior_no_shows"].to_numpy()      # strong predictor
    sms_effect = -0.45 * df["sms_reminder"].to_numpy()
    ins_effect = -0.25 * df["has_insurance"].to_numpy()

    weekday = df["appointment_time"].dt.dayofweek.to_numpy()
    monday_morning = (
        (weekday == 0) & (df["appointment_time"].dt.hour.to_numpy() < 11)
    ).astype(float) * 0.30  # Monday morning chaos -> slightly higher no-show

    logit = (base_logit + age_effect + lead_effect + history_effect
             + sms_effect + ins_effect + monday_morning)
    no_show_prob = 1.0 / (1.0 + np.exp(-logit))
    no_show_prob = np.clip(no_show_prob, 0.005, 0.85)
    cancelled = (rng.random(cfg.n_samples) < no_show_prob).astype(int)
    df["cancelled"] = cancelled

    # ============================================================
    # WAIT TIME (only meaningful for non-cancelled appointments)
    # Driven by queue load + doctor speed + type difficulty + heteroscedastic noise
    # ============================================================
    wait_minutes = np.full(cfg.n_samples, np.nan)

    for doc_id, group in df.groupby("doctor_id", sort=False):
        idx = group.index.to_numpy()
        params = DOCTORS[doc_id]
        mean_serv = params["mean_service_min"]
        sigma_serv = params["sigma"]

        # Per-appointment service time (truncated normal, only for shows)
        attended_mask = group["cancelled"].to_numpy() == 0
        type_mults = group["appointment_type"].map(
            lambda t: APPT_TYPES[t]["service_mult"]
        ).to_numpy()
        service_time = np.clip(
            rng.normal(mean_serv * type_mults, sigma_serv), 3.0, 90.0
        )
        # If patient cancelled, that slot empties out (service_time effectively 0)
        effective_service = np.where(attended_mask, service_time, 0.0)

        # Build queue: cumulative running delay relative to scheduled time.
        # We approximate "wait time at arrival" as max(0, sum of previous
        # overruns within a sliding window of the same hour bucket).
        times = group["appointment_time"].to_numpy()
        # Convert to minutes since first appointment for this doctor
        t_min = (times - times[0]).astype("timedelta64[m]").astype(float)

        running_end = 0.0
        wait = np.zeros(len(group))
        for i in range(len(group)):
            scheduled = t_min[i]
            if running_end > scheduled:
                wait[i] = running_end - scheduled
            else:
                wait[i] = 0.0
                running_end = scheduled
            running_end += effective_service[i]
            # Heteroscedastic noise: bigger queues = more variance
            wait[i] += rng.normal(0, 1.0 + 0.15 * wait[i])

        wait = np.clip(wait, 0.0, 240.0)

        # Cancelled patients have NaN wait (they didn't experience it)
        wait[~attended_mask] = np.nan
        wait_minutes[idx] = wait

    df["wait_minutes"] = wait_minutes

    # Final shuffle for randomness in train/test splits later
    df = df.sample(frac=1.0, random_state=cfg.seed).reset_index(drop=True)
    return df


# ---------------------------------- CLI ---------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=80_000)
    parser.add_argument("--out", type=str, default="ml/data/appointments.parquet")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = GenConfig(n_samples=args.n, seed=args.seed)
    df = generate(cfg)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    csv_path = out.with_suffix(".csv")
    df.to_csv(csv_path, index=False)

    print(f"Generated {len(df):,} rows")
    print(f"  parquet -> {out}")
    print(f"  csv     -> {csv_path}")
    print(f"\nClass balance (cancelled): {df['cancelled'].mean():.4f}")
    print(f"Wait time stats (attended only):")
    print(df.loc[df['cancelled'] == 0, 'wait_minutes'].describe().round(2))


if __name__ == "__main__":
    main()
