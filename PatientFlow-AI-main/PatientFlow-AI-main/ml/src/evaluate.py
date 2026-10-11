"""
Generate evaluation plots and SHAP explanations.

Outputs (saved to ml/reports/figures/):
    - cancel_roc_pr.png         : ROC and PR curves for both classifiers
    - cancel_calibration.png    : Reliability diagram (calibration curve)
    - cancel_confusion.png      : Confusion matrix at chosen threshold
    - reg_quantile_calib.png    : Predicted vs actual coverage by decile
    - reg_residuals.png         : Residual scatter for P50
    - eda_*.png                 : EDA plots (cancellation rate by hour/day, etc.)
    - shap_classifier.png       : SHAP summary plot for the cancellation model
    - shap_regressor_p50.png    : SHAP summary plot for the median wait model
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay, confusion_matrix,
    precision_recall_curve, roc_curve,
)

from features import (
    CLASSIFIER_FEATURES_CATEGORICAL, CLASSIFIER_FEATURES_NUMERIC,
    REGRESSOR_FEATURES_CATEGORICAL, REGRESSOR_FEATURES_NUMERIC,
    EncoderState, build_feature_frames, fit_encoders,
)
from train import temporal_split

DATA_PATH = Path("ml/data/appointments.parquet")
MODELS_DIR = Path("ml/models")
FIG_DIR = Path("ml/reports/figures")

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 150


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # --- Load data + artifacts ---
    raw = pd.read_parquet(DATA_PATH)
    train_raw, test_raw = temporal_split(raw, 0.20)
    enc = EncoderState.from_dict(json.loads(
        (MODELS_DIR / "encoder_state.json").read_text()
    ))
    train_df = build_feature_frames(train_raw, enc, include_queue=True)
    test_df = build_feature_frames(test_raw, enc, include_queue=True)

    classifier = joblib.load(MODELS_DIR / "classifier.joblib")
    threshold = json.loads(
        (MODELS_DIR / "classifier_threshold.json").read_text()
    )["threshold"]
    reg_pre = joblib.load(MODELS_DIR / "regressor_preprocessor.joblib")
    reg_p10 = joblib.load(MODELS_DIR / "regressor_p10.joblib")
    reg_p50 = joblib.load(MODELS_DIR / "regressor_p50.joblib")
    reg_p90 = joblib.load(MODELS_DIR / "regressor_p90.joblib")

    feats_clf = CLASSIFIER_FEATURES_NUMERIC + CLASSIFIER_FEATURES_CATEGORICAL
    feats_reg = REGRESSOR_FEATURES_NUMERIC + REGRESSOR_FEATURES_CATEGORICAL

    X_clf_test = test_df[feats_clf]
    y_clf_test = test_df["cancelled"].to_numpy()
    p_cal = classifier.predict_proba(X_clf_test)[:, 1]

    attended = test_df[test_df["cancelled"] == 0].copy()
    X_reg_test = reg_pre.transform(attended[feats_reg])
    y_reg_test = attended["wait_minutes"].to_numpy()
    pred_p10 = reg_p10.predict(X_reg_test)
    pred_p50 = reg_p50.predict(X_reg_test)
    pred_p90 = reg_p90.predict(X_reg_test)

    # ============================================================
    # 1) Classifier ROC and PR curves
    # ============================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    fpr, tpr, _ = roc_curve(y_clf_test, p_cal)
    axes[0].plot(fpr, tpr, label=f"XGB (calibrated)", lw=2)
    axes[0].plot([0, 1], [0, 1], "--", color="grey", label="Random")
    axes[0].set_xlabel("False Positive Rate")
    axes[0].set_ylabel("True Positive Rate")
    axes[0].set_title("ROC Curve - Cancellation Classifier")
    axes[0].legend(loc="lower right")

    prec, rec, _ = precision_recall_curve(y_clf_test, p_cal)
    axes[1].plot(rec, prec, lw=2, color="C2")
    axes[1].axhline(y_clf_test.mean(), ls="--", color="grey",
                    label=f"Base rate = {y_clf_test.mean():.3f}")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision-Recall Curve")
    axes[1].legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "cancel_roc_pr.png")
    plt.close(fig)

    # ============================================================
    # 2) Calibration / reliability diagram
    # ============================================================
    fig, ax = plt.subplots(figsize=(7, 7))
    prob_true, prob_pred = calibration_curve(y_clf_test, p_cal, n_bins=12, strategy="quantile")
    ax.plot([0, 1], [0, 1], "--", color="grey", label="Perfectly calibrated")
    ax.plot(prob_pred, prob_true, "o-", lw=2, color="C3", label="XGB (isotonic)")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Empirical fraction of cancellations")
    ax.set_title("Calibration (Reliability) Diagram")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "cancel_calibration.png")
    plt.close(fig)

    # ============================================================
    # 3) Confusion matrix at chosen threshold
    # ============================================================
    y_pred = (p_cal >= threshold).astype(int)
    cm = confusion_matrix(y_clf_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5.5))
    ConfusionMatrixDisplay(cm, display_labels=["Show", "Cancel"]).plot(
        ax=ax, cmap="Blues", colorbar=False
    )
    ax.set_title(f"Confusion Matrix (threshold = {threshold:.3f})")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "cancel_confusion.png")
    plt.close(fig)

    # ============================================================
    # 4) Quantile coverage by decile of predicted P50
    # ============================================================
    deciles = pd.qcut(pred_p50, 10, labels=False, duplicates="drop")
    cov = []
    centers = []
    for d in range(deciles.max() + 1):
        m = deciles == d
        if m.sum() > 0:
            covered = ((y_reg_test[m] >= pred_p10[m]) & (y_reg_test[m] <= pred_p90[m])).mean()
            cov.append(covered)
            centers.append(pred_p50[m].mean())
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(centers, cov, "o-", lw=2)
    ax.axhline(0.80, ls="--", color="grey", label="Target coverage = 0.80")
    ax.set_xlabel("Mean predicted P50 wait (min)")
    ax.set_ylabel("Empirical coverage of [P10, P90]")
    ax.set_title("Quantile Interval Coverage by Predicted-Wait Decile")
    ax.set_ylim(0.5, 1.0)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "reg_quantile_calib.png")
    plt.close(fig)

    # ============================================================
    # 5) Residuals (P50)
    # ============================================================
    residuals = y_reg_test - pred_p50
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    axes[0].scatter(pred_p50, residuals, alpha=0.15, s=8)
    axes[0].axhline(0, color="red", lw=1)
    axes[0].set_xlabel("Predicted P50 wait (min)")
    axes[0].set_ylabel("Residual (actual - predicted)")
    axes[0].set_title("P50 Residuals vs Prediction")

    axes[1].hist(residuals, bins=60, color="C0", edgecolor="white")
    axes[1].axvline(0, color="red")
    axes[1].set_xlabel("Residual (min)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Residual Distribution")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "reg_residuals.png")
    plt.close(fig)

    # ============================================================
    # 6) EDA: cancellation rate by hour and weekday
    # ============================================================
    eda = train_df.copy()
    eda["weekday_name"] = eda["appointment_time"].dt.day_name()
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    by_hour = eda.groupby("hour")["cancelled"].mean()
    axes[0].bar(by_hour.index, by_hour.values, color="C0")
    axes[0].set_xlabel("Hour of day")
    axes[0].set_ylabel("Cancellation rate")
    axes[0].set_title("Cancellation Rate by Hour")

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    by_dow = eda.groupby("weekday_name")["cancelled"].mean().reindex(order)
    axes[1].bar(by_dow.index, by_dow.values, color="C2")
    axes[1].set_ylabel("Cancellation rate")
    axes[1].set_title("Cancellation Rate by Weekday")
    axes[1].tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_cancellation_seasonality.png")
    plt.close(fig)

    # Wait-time distribution + by appointment type
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    axes[0].hist(eda.loc[eda["cancelled"] == 0, "wait_minutes"], bins=60,
                 color="C3", edgecolor="white")
    axes[0].set_xlabel("Wait time (min)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Wait-Time Distribution (attended)")
    axes[0].set_yscale("log")

    sns.boxplot(
        data=eda[eda["cancelled"] == 0],
        x="appointment_type", y="wait_minutes",
        ax=axes[1], showfliers=False,
    )
    axes[1].set_title("Wait Time by Appointment Type")
    axes[1].tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_wait_distribution.png")
    plt.close(fig)

    # ============================================================
    # 7) SHAP - regressor P50 (LightGBM TreeExplainer is fast)
    # ============================================================
    print("Computing SHAP for regressor P50...")
    sample_idx = np.random.RandomState(0).choice(
        X_reg_test.shape[0], size=min(2000, X_reg_test.shape[0]), replace=False
    )
    X_reg_sample = X_reg_test[sample_idx]
    feature_names_reg = reg_pre.get_feature_names_out()
    explainer_reg = shap.TreeExplainer(reg_p50)
    shap_vals_reg = explainer_reg.shap_values(X_reg_sample)
    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_vals_reg, X_reg_sample, feature_names=feature_names_reg,
        show=False, max_display=15,
    )
    plt.tight_layout()
    plt.savefig(FIG_DIR / "shap_regressor_p50.png", bbox_inches="tight")
    plt.close()

    # ============================================================
    # 8) SHAP - classifier (use base XGB inside the calibrator)
    # ============================================================
    print("Computing SHAP for cancellation classifier...")
    base_pipe = classifier.calibrated_classifiers_[0].estimator
    pre_clf = base_pipe.named_steps["pre"]
    base_xgb = base_pipe.named_steps["clf"]
    X_clf_t = pre_clf.transform(X_clf_test.iloc[sample_idx[:1500]])
    feat_names_clf = pre_clf.get_feature_names_out()
    explainer_clf = shap.TreeExplainer(base_xgb)
    shap_vals_clf = explainer_clf.shap_values(X_clf_t)
    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_vals_clf, X_clf_t, feature_names=feat_names_clf,
        show=False, max_display=15,
    )
    plt.tight_layout()
    plt.savefig(FIG_DIR / "shap_classifier.png", bbox_inches="tight")
    plt.close()

    print(f"All figures saved under {FIG_DIR}/")
    for f in sorted(FIG_DIR.glob("*.png")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
