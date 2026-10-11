"""
Train cancellation classifier and quantile wait-time regressor.

Models:
    1. Cancellation classifier
       - LogisticRegression baseline (interpretable, sanity check).
       - XGBoost classifier (main model).
       - Isotonic calibration (CalibratedClassifierCV) on a held-out fold.
       - Metrics: ROC-AUC, PR-AUC, Brier score, log-loss, F1@0.5.

    2. Wait-time quantile regressor (only on attended appointments)
       - Three LightGBM models trained with quantile loss for P10/P50/P90.
       - Metrics: pinball loss per quantile, MAE on P50, empirical coverage of
         the [P10, P90] interval (should be ~80%).

Train/test split is TEMPORAL: we sort by appointment_time and use the last
20% as test, simulating the deployment scenario.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, brier_score_loss, f1_score, log_loss,
    mean_absolute_error, mean_squared_error, roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from features import (
    CLASSIFIER_FEATURES_CATEGORICAL,
    CLASSIFIER_FEATURES_NUMERIC,
    REGRESSOR_FEATURES_CATEGORICAL,
    REGRESSOR_FEATURES_NUMERIC,
    EncoderState,
    build_feature_frames,
    fit_encoders,
)


DATA_PATH = Path("ml/data/appointments.parquet")
MODELS_DIR = Path("ml/models")
REPORTS_DIR = Path("ml/reports")


# ----------------------------- Helpers ----------------------------------------

def temporal_split(df: pd.DataFrame, test_frac: float = 0.20) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("appointment_time").reset_index(drop=True)
    cut = int(len(df) * (1 - test_frac))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, q: float) -> float:
    diff = y_true - y_pred
    return float(np.maximum(q * diff, (q - 1) * diff).mean())


def build_preprocessor(
    numeric: list[str], categorical: list[str]
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             categorical),
        ],
        remainder="drop",
    )


# ---------------------- Cancellation classifier -------------------------------

def train_classifier(
    df_train: pd.DataFrame, df_test: pd.DataFrame
) -> tuple[Pipeline, dict]:
    feats = CLASSIFIER_FEATURES_NUMERIC + CLASSIFIER_FEATURES_CATEGORICAL
    X_tr = df_train[feats]
    y_tr = df_train["cancelled"].to_numpy()
    X_te = df_test[feats]
    y_te = df_test["cancelled"].to_numpy()

    pre = build_preprocessor(
        CLASSIFIER_FEATURES_NUMERIC, CLASSIFIER_FEATURES_CATEGORICAL
    )

    # Baseline: logistic regression
    base_pipe = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(max_iter=400, C=1.0, n_jobs=-1)),
    ])
    base_pipe.fit(X_tr, y_tr)
    p_base = base_pipe.predict_proba(X_te)[:, 1]
    base_metrics = _classification_metrics(y_te, p_base)

    # Main: XGBoost (no scale_pos_weight; we calibrate instead and tune threshold)
    xgb_pipe = Pipeline([
        ("pre", build_preprocessor(
            CLASSIFIER_FEATURES_NUMERIC, CLASSIFIER_FEATURES_CATEGORICAL)),
        ("clf", XGBClassifier(
            n_estimators=600, max_depth=5, learning_rate=0.04,
            subsample=0.9, colsample_bytree=0.9,
            min_child_weight=8, reg_lambda=1.0, gamma=0.1,
            eval_metric="logloss", n_jobs=-1, random_state=42,
            tree_method="hist",
        )),
    ])
    xgb_pipe.fit(X_tr, y_tr)

    # Calibrate XGBoost probabilities with isotonic on a held-out CV
    calibrator = CalibratedClassifierCV(
        estimator=xgb_pipe, method="isotonic", cv=3,
    )
    calibrator.fit(X_tr, y_tr)
    p_cal = calibrator.predict_proba(X_te)[:, 1]

    # Find threshold maximizing F1 on validation tail of training data
    from sklearn.metrics import precision_recall_curve
    p_tr_cal = calibrator.predict_proba(X_tr)[:, 1]
    prec, rec, thr = precision_recall_curve(y_tr, p_tr_cal)
    f1s = 2 * prec * rec / (prec + rec + 1e-9)
    best_idx = int(np.nanargmax(f1s[:-1])) if len(f1s) > 1 else 0
    best_thr = float(thr[best_idx]) if len(thr) > best_idx else 0.5

    xgb_metrics = _classification_metrics(y_te, p_cal, threshold=best_thr)
    xgb_metrics["chosen_threshold"] = best_thr

    metrics = {
        "logreg_baseline": base_metrics,
        "xgb_calibrated":  xgb_metrics,
    }
    return calibrator, metrics, best_thr


def _classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "roc_auc":    float(roc_auc_score(y_true, y_prob)),
        "pr_auc":     float(average_precision_score(y_true, y_prob)),
        "log_loss":   float(log_loss(y_true, np.clip(y_prob, 1e-6, 1 - 1e-6))),
        "brier":      float(brier_score_loss(y_true, y_prob)),
        "f1":         float(f1_score(y_true, y_pred)),
        "threshold":  float(threshold),
        "positive_rate": float(y_true.mean()),
    }


# ---------------------- Quantile wait-time regressor --------------------------

def train_regressor(
    df_train: pd.DataFrame, df_test: pd.DataFrame
) -> tuple[dict[str, lgb.LGBMRegressor], dict, ColumnTransformer]:
    # Train only on attended (non-cancelled) appointments with valid wait time
    tr = df_train[df_train["cancelled"] == 0].copy()
    te = df_test[df_test["cancelled"] == 0].copy()

    feats = REGRESSOR_FEATURES_NUMERIC + REGRESSOR_FEATURES_CATEGORICAL

    # We use OneHot for categoricals -> dense matrix LightGBM consumes.
    # Fit ONE preprocessor on train, reuse for test and at inference.
    pre = build_preprocessor(
        REGRESSOR_FEATURES_NUMERIC, REGRESSOR_FEATURES_CATEGORICAL
    )
    X_tr = pre.fit_transform(tr[feats])
    X_te = pre.transform(te[feats])
    y_tr = tr["wait_minutes"].to_numpy()
    y_te = te["wait_minutes"].to_numpy()

    quantiles = [0.10, 0.50, 0.90]
    models: dict[str, lgb.LGBMRegressor] = {}
    test_preds: dict[str, np.ndarray] = {}
    for q in quantiles:
        model = lgb.LGBMRegressor(
            objective="quantile", alpha=q,
            n_estimators=600, learning_rate=0.05,
            num_leaves=63, max_depth=-1,
            min_child_samples=20, subsample=0.85,
            colsample_bytree=0.85, random_state=42,
            verbose=-1,
        )
        model.fit(X_tr, y_tr)
        models[f"p{int(q*100):02d}"] = model
        test_preds[f"p{int(q*100):02d}"] = model.predict(X_te)

    # Metrics
    metrics: dict = {
        "n_train": int(len(tr)),
        "n_test":  int(len(te)),
        "pinball_p10": pinball_loss(y_te, test_preds["p10"], 0.10),
        "pinball_p50": pinball_loss(y_te, test_preds["p50"], 0.50),
        "pinball_p90": pinball_loss(y_te, test_preds["p90"], 0.90),
        "mae_p50":     float(mean_absolute_error(y_te, test_preds["p50"])),
        "rmse_p50":    float(np.sqrt(mean_squared_error(y_te, test_preds["p50"]))),
        "coverage_80pct_interval": float(
            ((y_te >= test_preds["p10"]) & (y_te <= test_preds["p90"])).mean()
        ),
    }
    return models, metrics, pre


# --------------------------------- Main ---------------------------------------

def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    raw = pd.read_parquet(DATA_PATH)
    print(f"  {len(raw):,} rows total")

    print("Temporal train/test split (80/20 by appointment_time)...")
    train_raw, test_raw = temporal_split(raw, test_frac=0.20)
    print(f"  train: {len(train_raw):,}   test: {len(test_raw):,}")

    print("Fitting target encoders on training fold...")
    enc = fit_encoders(train_raw)

    print("Building feature frames (with queue-state for regressor)...")
    train_df = build_feature_frames(train_raw, enc, include_queue=True)
    test_df  = build_feature_frames(test_raw,  enc, include_queue=True)

    print("\n=== Training cancellation classifier ===")
    classifier, clf_metrics, best_thr = train_classifier(train_df, test_df)
    print(json.dumps(clf_metrics, indent=2))

    print("\n=== Training quantile wait-time regressor ===")
    regressors, reg_metrics, reg_pre = train_regressor(train_df, test_df)
    print(json.dumps(reg_metrics, indent=2))

    # ---- Persist artifacts ----
    joblib.dump(classifier, MODELS_DIR / "classifier.joblib")
    joblib.dump(reg_pre, MODELS_DIR / "regressor_preprocessor.joblib")
    for q, m in regressors.items():
        joblib.dump(m, MODELS_DIR / f"regressor_{q}.joblib")
    with open(MODELS_DIR / "encoder_state.json", "w") as f:
        json.dump(enc.to_dict(), f, indent=2)
    with open(MODELS_DIR / "classifier_threshold.json", "w") as f:
        json.dump({"threshold": best_thr}, f)

    full_metrics = {"classifier": clf_metrics, "regressor": reg_metrics}
    with open(REPORTS_DIR / "metrics.json", "w") as f:
        json.dump(full_metrics, f, indent=2)

    print("\nArtifacts saved to ml/models/, metrics to ml/reports/metrics.json")


if __name__ == "__main__":
    main()
