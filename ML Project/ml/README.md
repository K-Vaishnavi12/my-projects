# `ml/` - Machine-Learning Pipeline

The ML core of **PatientFlow AI**. Owns data generation, feature engineering, training, evaluation, and inference.

## What this component does

Produces **two trained models** and the artifacts the API needs to serve them:

1. **Cancellation classifier** - calibrated XGBoost predicting probability that a patient will no-show.
2. **Wait-time quantile regressor** - three LightGBM models (P10 / P50 / P90) trained with quantile loss to give a calibrated uncertainty band on wait time.

Plus a **counterfactual slot recommender** (`inference.py`) that combines both models into a single decision score for ranking `(doctor, time)` candidates.

## Tech stack

| Layer | Tools |
|---|---|
| Language | Python 3.11 |
| Data | NumPy 1.26, pandas 2.2, PyArrow 16 |
| ML | scikit-learn 1.4, XGBoost 2.0, LightGBM 4.3 |
| Calibration | `sklearn.calibration.CalibratedClassifierCV` (isotonic, 3-fold) |
| Explainability | SHAP 0.45 (`TreeExplainer`) |
| Plots | matplotlib 3.8, seaborn 0.13 |
| Persistence | joblib 1.4 |
| Notebook | Jupyter, nbformat, nbconvert |

All pinned in the root-level `requirements.txt`.

## Folder layout

```
ml/
  src/
    generate_data.py     Synthetic data generator with documented causal structure
    features.py          Feature engineering (cyclical encoding, target encoding,
                         queue-state features, leakage-free fit/transform)
    train.py             Trains classifier + 3 quantile regressors,
                         calibrates probabilities, tunes threshold on PR curve
    evaluate.py          ROC/PR, calibration diagram, confusion matrix,
                         quantile coverage, residuals, EDA, SHAP plots
    inference.py         Loads artifacts; predict_cancellation /
                         predict_wait / recommend_slots
  scripts/
    build_notebook.py    Programmatically constructs the storytelling notebook
  notebooks/
    PatientFlow_AI.ipynb  29-cell narrative; executed end-to-end with outputs
  data/
    appointments.parquet  Generated dataset (80,000 rows)
    appointments.csv      Same dataset in CSV for non-Python consumers
  models/
    classifier.joblib              Calibrated XGBoost classifier
    classifier_threshold.json      F1-optimal decision threshold from PR curve
    regressor_p10.joblib           LightGBM, quantile=0.10
    regressor_p50.joblib           LightGBM, quantile=0.50 (median)
    regressor_p90.joblib           LightGBM, quantile=0.90
    regressor_preprocessor.joblib  Fitted ColumnTransformer (one-hot + scaler)
    encoder_state.json             Doctor-level target-encoding stats
                                   (fit on training fold ONLY)
  reports/
    metrics.json         All test-set metrics (consumed by /metadata API endpoint)
    figures/             9 PNGs: ROC/PR, calibration, confusion, quantile
                         coverage, residuals, EDA seasonality, EDA wait
                         distribution, SHAP classifier, SHAP regressor
```

## Held-out test results (20% temporal split, 80,000 rows)

| Component | Metric | Value |
|---|---|---|
| LogReg baseline | ROC-AUC | 0.695 |
| **XGBoost (calibrated)** | **ROC-AUC** | **0.683** |
| XGBoost (calibrated) | PR-AUC vs 0.152 base | 0.279 (1.84x lift) |
| XGBoost (calibrated) | Brier score | 0.123 |
| XGBoost (calibrated) | F1 at threshold 0.177 | 0.339 |
| **Quantile regressor** | **MAE on P50** | **9.11 min** |
| Quantile regressor | RMSE on P50 | 17.67 min |
| Quantile regressor | Pinball P10 / P50 / P90 | 1.33 / 4.55 / 3.00 |
| **Quantile regressor** | **Empirical [P10, P90] coverage** | **79.8%** (target 80%) |

## How to execute (from project root)

### 1. Activate Python environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 2. Run the full pipeline

Each step writes its outputs and is independently re-runnable:

```powershell
# Step 1: Generate the dataset (~5 sec, writes ml/data/)
.\.venv\Scripts\python ml\src\generate_data.py --n 80000

# Step 2: Train both models (~30-60 sec, writes ml/models/ and ml/reports/metrics.json)
.\.venv\Scripts\python ml\src\train.py

# Step 3: Generate evaluation plots and SHAP (~20-40 sec, writes ml/reports/figures/)
.\.venv\Scripts\python ml\src\evaluate.py

# Step 4: Build the notebook (writes ml/notebooks/PatientFlow_AI.ipynb)
.\.venv\Scripts\python ml\scripts\build_notebook.py

# Step 5: Execute the notebook end-to-end (writes outputs into the notebook)
.\.venv\Scripts\python -m jupyter nbconvert --to notebook --execute `
    ml\notebooks\PatientFlow_AI.ipynb --output PatientFlow_AI.ipynb `
    --ExecutePreprocessor.timeout=300
```

### 3. Use the trained models from Python

```python
from datetime import datetime
import sys
sys.path.insert(0, "ml/src")
from inference import PatientFlowModel, default_candidate_times

model = PatientFlowModel()  # loads ml/models/* on construction

patient = dict(
    doctor_id="D001_GenPrac_Sharma",
    appointment_type="consultation",
    age=41, sex="F", has_insurance=True,
    lead_time_days=3, prior_no_shows=0, prior_visits=4,
    sms_reminder=True,
    appointment_time=datetime(2025, 7, 14, 10, 0),
)

print("cancel prob:", model.predict_cancellation(patient))
print("wait quantiles:", model.predict_wait(patient).to_dict())

recs = model.recommend_slots(
    patient,
    candidate_times=default_candidate_times(datetime(2025, 7, 14, 9, 0), 48, 60),
    candidate_doctors=["D001_GenPrac_Sharma", "D002_GenPrac_Iyer"],
    top_k=5,
)
for r in recs:
    print(r.appointment_time, r.doctor_id, r.expected_wait.p50, r.score)
```

## Key design choices

- **Temporal split**, not random. Sort by `appointment_time` and use the last 20% as test - this simulates the real deployment scenario.
- **Target encoders fit on training fold only** (`fit_encoders` returns an `EncoderState` consumed by both the test set and inference - no leakage).
- **Isotonic calibration** wraps the XGBoost classifier so the output probabilities are usable as decision inputs, not just rankings.
- **Threshold tuned on the PR curve** instead of left at 0.5 (which is wrong for a 15% positive class).
- **Quantile loss**, not MSE, for wait time. The empirical coverage of [P10, P90] is reported as the calibration check.
- **Quantile crossing fix**: at inference we sort to enforce `P10 <= P50 <= P90`.

## Common things to change

| You want to | Edit |
|---|---|
| Use a different dataset size or seed | `ml/src/generate_data.py` (`--n`, `--seed`) or call `generate(GenConfig(...))` directly |
| Add a new feature | Append to `CLASSIFIER_FEATURES_*` / `REGRESSOR_FEATURES_*` and the `add_*` builders in `ml/src/features.py` |
| Swap LightGBM for CatBoost | Edit `train_regressor` in `ml/src/train.py`; the inference code uses joblib so any sklearn-compatible regressor works |
| Change the recommender's lambdas | `uncertainty_penalty` and `rush_penalty` kwargs on `PatientFlowModel.recommend_slots` |
| Use a real dataset | Replace `pd.read_parquet(DATA_PATH)` in `train.py` and ensure column names match |

## Honest limitations

- Data is synthetic. Numbers reflect model quality, not deployable absolute accuracy.
- Quantile models are independent; in real deployments use a constrained quantile network or conformal prediction for stronger guarantees.
- Recommender weights are heuristic; in production they should be tuned by A/B testing operational outcomes.
