"""
Churn probability segmentation.
Uses simple logistic regression on tenure, MRR, usage; segments customers by risk.
"""

import pandas as pd
import numpy as np
from pathlib import Path

try:
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, roc_auc_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive tenure (months), log_mrr, and other common churn predictors."""
    out = df.copy()
    if "start_date" in out.columns:
        out["start_date"] = pd.to_datetime(out["start_date"])
        ref = out["start_date"].max() or pd.Timestamp.now()
        out["tenure_months"] = ((ref - out["start_date"]).dt.days / 30).clip(0)
    if "mrr" in out.columns:
        out["log_mrr"] = np.log1p(out["mrr"])
    return out


def train_churn_model(
    X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42
):
    """Train logistic regression and return model, scaler, metrics."""
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn is required. pip install scikit-learn")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    model = LogisticRegression(max_iter=1000, random_state=random_state)
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]
    print(classification_report(y_test, y_pred, target_names=["Retained", "Churned"]))
    print("ROC AUC:", round(roc_auc_score(y_test, y_prob), 4))
    return model, scaler


def segment_by_risk(
    df: pd.DataFrame, proba: np.ndarray, bins: list = [0, 0.2, 0.5, 0.8, 1.0]
) -> pd.DataFrame:
    """Add churn_prob and risk_segment (Low / Medium / High / Critical)."""
    out = df.copy()
    out["churn_prob"] = proba
    out["risk_segment"] = pd.cut(proba, bins=bins, labels=["Low", "Medium", "High", "Critical"])
    return out


if __name__ == "__main__":
    if not HAS_SKLEARN:
        print("Install scikit-learn to run churn model.")
    else:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        path = data_dir / "subscriptions.csv"
        if path.exists():
            df = pd.read_csv(path)
            df = prepare_features(df)
            feature_cols = [c for c in ["tenure_months", "log_mrr", "mrr"] if c in df.columns]
            if "churned" not in df.columns and "end_date" in df.columns:
                df["churned"] = df["end_date"].notna().astype(int)
            if "churned" in df.columns and feature_cols:
                X = df[feature_cols].fillna(0)
                y = df["churned"]
                model, scaler = train_churn_model(X, y)
                proba = model.predict_proba(scaler.transform(X))[:, 1]
                df = segment_by_risk(df, proba)
                print(df[["customer_id", "churn_prob", "risk_segment"]].head(10))
