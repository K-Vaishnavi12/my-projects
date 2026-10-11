"""
Inference layer for PatientFlow AI.

Loads trained artifacts and exposes:
    - PatientFlowModel.predict_cancellation(...)  -> calibrated probability
    - PatientFlowModel.predict_wait(...)          -> dict {p10, p50, p90}
    - PatientFlowModel.recommend_slots(...)       -> ranked candidate slots

The recommender is a counterfactual scoring layer on top of the trained
models: for each candidate slot it builds a feature row, asks both models
for predictions, and computes a composite score:

    score = expected_wait_p50 * (1 - cancel_prob)
            + UNCERTAINTY_PENALTY * (p90 - p10)
            + RUSH_PENALTY * is_monday_morning_indicator

Lower score = better slot. We also expose the top-K with their full
predicted distributions so the UI can show uncertainty bands.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from features import (
    CLASSIFIER_FEATURES_CATEGORICAL, CLASSIFIER_FEATURES_NUMERIC,
    REGRESSOR_FEATURES_CATEGORICAL, REGRESSOR_FEATURES_NUMERIC,
    EncoderState, build_feature_frames,
)


MODELS_DIR = Path("ml/models")


@dataclass
class WaitPrediction:
    p10: float
    p50: float
    p90: float

    def to_dict(self) -> dict:
        return {"p10": self.p10, "p50": self.p50, "p90": self.p90}


@dataclass
class SlotRecommendation:
    appointment_time: datetime
    doctor_id: str
    expected_wait: WaitPrediction
    cancellation_prob: float
    score: float                    # lower is better
    rationale: str

    def to_dict(self) -> dict:
        return {
            "appointment_time": self.appointment_time.isoformat(),
            "doctor_id": self.doctor_id,
            "expected_wait": self.expected_wait.to_dict(),
            "cancellation_prob": self.cancellation_prob,
            "score": self.score,
            "rationale": self.rationale,
        }


class PatientFlowModel:
    """Single entry point that bundles classifier + quantile regressors."""

    def __init__(self, models_dir: Path = MODELS_DIR) -> None:
        self.classifier = joblib.load(models_dir / "classifier.joblib")
        self.threshold = json.loads(
            (models_dir / "classifier_threshold.json").read_text()
        )["threshold"]
        self.reg_pre = joblib.load(models_dir / "regressor_preprocessor.joblib")
        self.reg = {
            "p10": joblib.load(models_dir / "regressor_p10.joblib"),
            "p50": joblib.load(models_dir / "regressor_p50.joblib"),
            "p90": joblib.load(models_dir / "regressor_p90.joblib"),
        }
        self.enc = EncoderState.from_dict(json.loads(
            (models_dir / "encoder_state.json").read_text()
        ))

    # ------------------------------------------------------------------
    # Single-row inference
    # ------------------------------------------------------------------
    def _build_row(self, raw: dict) -> pd.DataFrame:
        df = pd.DataFrame([raw])
        # We need a placeholder cancelled/wait column so feature builder works
        if "cancelled" not in df:
            df["cancelled"] = 0
        if "wait_minutes" not in df:
            df["wait_minutes"] = np.nan
        if "appointment_id" not in df:
            df["appointment_id"] = "QUERY-0001"
        return build_feature_frames(df, self.enc, include_queue=False)

    def _build_batch(self, rows: list[dict], queue_context: pd.DataFrame | None) -> pd.DataFrame:
        df = pd.DataFrame(rows)
        df["cancelled"] = 0
        df["wait_minutes"] = np.nan
        if "appointment_id" not in df:
            df["appointment_id"] = [f"Q{i:05d}" for i in range(len(df))]

        if queue_context is not None and len(queue_context) > 0:
            # Concatenate so queue-state features see the existing schedule
            ctx = queue_context.copy()
            for col in ["cancelled", "wait_minutes"]:
                if col not in ctx:
                    ctx[col] = np.nan
            if "appointment_id" not in ctx:
                ctx["appointment_id"] = [f"CTX{i:05d}" for i in range(len(ctx))]
            combo = pd.concat([ctx, df], ignore_index=True)
            built = build_feature_frames(combo, self.enc, include_queue=True)
            return built.tail(len(df)).reset_index(drop=True)
        return build_feature_frames(df, self.enc, include_queue=True)

    def predict_cancellation(self, raw: dict) -> float:
        row = self._build_row(raw)
        feats = CLASSIFIER_FEATURES_NUMERIC + CLASSIFIER_FEATURES_CATEGORICAL
        prob = float(self.classifier.predict_proba(row[feats])[0, 1])
        return prob

    def predict_wait(
        self, raw: dict, queue_context: pd.DataFrame | None = None
    ) -> WaitPrediction:
        feats = REGRESSOR_FEATURES_NUMERIC + REGRESSOR_FEATURES_CATEGORICAL
        df = self._build_batch([raw], queue_context)
        X = self.reg_pre.transform(df[feats])
        p10 = float(self.reg["p10"].predict(X)[0])
        p50 = float(self.reg["p50"].predict(X)[0])
        p90 = float(self.reg["p90"].predict(X)[0])
        # Enforce monotonicity p10 <= p50 <= p90 (rare quantile-crossing fix)
        p10 = min(p10, p50)
        p90 = max(p90, p50)
        return WaitPrediction(p10=max(p10, 0.0), p50=max(p50, 0.0), p90=max(p90, 0.0))

    # ------------------------------------------------------------------
    # Slot recommender
    # ------------------------------------------------------------------
    def recommend_slots(
        self,
        patient: dict,
        candidate_times: Iterable[datetime],
        candidate_doctors: list[str] | None = None,
        queue_context: pd.DataFrame | None = None,
        top_k: int = 5,
        uncertainty_penalty: float = 0.25,
        rush_penalty: float = 5.0,
    ) -> list[SlotRecommendation]:
        """For each (doctor, time) candidate, score the slot and rank."""
        candidates = []
        candidate_doctors = candidate_doctors or [patient.get("doctor_id")]
        for t in candidate_times:
            for doc in candidate_doctors:
                cand = dict(patient)
                cand["appointment_time"] = pd.Timestamp(t)
                cand["doctor_id"] = doc
                candidates.append(cand)

        feats_clf = CLASSIFIER_FEATURES_NUMERIC + CLASSIFIER_FEATURES_CATEGORICAL
        feats_reg = REGRESSOR_FEATURES_NUMERIC + REGRESSOR_FEATURES_CATEGORICAL

        df_built = self._build_batch(candidates, queue_context)
        cancel_probs = self.classifier.predict_proba(df_built[feats_clf])[:, 1]
        Xreg = self.reg_pre.transform(df_built[feats_reg])
        p10s = self.reg["p10"].predict(Xreg)
        p50s = self.reg["p50"].predict(Xreg)
        p90s = self.reg["p90"].predict(Xreg)

        recs: list[SlotRecommendation] = []
        for i, cand in enumerate(candidates):
            p10, p50, p90 = float(p10s[i]), float(p50s[i]), float(p90s[i])
            p10 = min(p10, p50)
            p90 = max(p90, p50)
            cancel = float(cancel_probs[i])
            ts = pd.Timestamp(cand["appointment_time"])
            is_monday_morning = (ts.dayofweek == 0 and ts.hour < 11)
            score = (
                p50 * (1.0 - cancel)
                + uncertainty_penalty * (p90 - p10)
                + (rush_penalty if is_monday_morning else 0.0)
            )
            rationale = self._explain(p50, p90 - p10, cancel, is_monday_morning)
            recs.append(SlotRecommendation(
                appointment_time=ts.to_pydatetime(),
                doctor_id=cand["doctor_id"],
                expected_wait=WaitPrediction(max(p10, 0), max(p50, 0), max(p90, 0)),
                cancellation_prob=cancel,
                score=float(score),
                rationale=rationale,
            ))

        recs.sort(key=lambda r: r.score)
        return recs[:top_k]

    @staticmethod
    def _explain(p50: float, spread: float, cancel: float, is_rush: bool) -> str:
        bits = []
        if p50 < 8:
            bits.append("low expected wait")
        elif p50 < 20:
            bits.append("moderate expected wait")
        else:
            bits.append("long expected wait")
        if spread < 12:
            bits.append("tight uncertainty band")
        elif spread > 30:
            bits.append("highly variable - consider risk")
        if cancel > 0.30:
            bits.append("high no-show risk for this profile")
        if is_rush:
            bits.append("Monday-morning rush penalty applied")
        return "; ".join(bits)


# ------------------------------ Helpers ---------------------------------------

def default_candidate_times(
    start: datetime, hours_horizon: int = 48, step_minutes: int = 60
) -> list[datetime]:
    """Generate candidate slots inside clinic hours."""
    out = []
    cur = start.replace(minute=0, second=0, microsecond=0)
    end = cur + timedelta(hours=hours_horizon)
    while cur < end:
        if 8 <= cur.hour <= 18 and cur.weekday() != 6:
            out.append(cur)
        cur += timedelta(minutes=step_minutes)
    return out


# --------------------------------- Smoke --------------------------------------

def _smoke() -> None:
    model = PatientFlowModel()
    patient = {
        "doctor_id": "D001_GenPrac_Sharma",
        "appointment_type": "consultation",
        "age": 41,
        "sex": "F",
        "has_insurance": True,
        "lead_time_days": 3,
        "prior_no_shows": 0,
        "prior_visits": 4,
        "sms_reminder": True,
        "appointment_time": datetime(2025, 7, 14, 10, 0),
    }
    print("Cancellation prob:", model.predict_cancellation(patient))
    w = model.predict_wait(patient)
    print(f"Wait: P10={w.p10:.1f}  P50={w.p50:.1f}  P90={w.p90:.1f}")

    recs = model.recommend_slots(
        patient,
        candidate_times=default_candidate_times(datetime(2025, 7, 14, 9, 0), 48, 60),
        candidate_doctors=[
            "D001_GenPrac_Sharma", "D002_GenPrac_Iyer",
        ],
        top_k=5,
    )
    print("\nTop-5 slot recommendations:")
    for r in recs:
        print(f"  {r.appointment_time}  {r.doctor_id}  "
              f"P50={r.expected_wait.p50:.1f}  cancel={r.cancellation_prob:.2%}  "
              f"score={r.score:.2f}  -- {r.rationale}")


if __name__ == "__main__":
    _smoke()
