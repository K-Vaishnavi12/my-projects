# PatientFlow AI

**Multi-task ML for outpatient clinics: cancellation-risk classification + quantile wait-time forecasting + counterfactual slot recommendation.**

This is an end-to-end machine-learning project (data generation -> EDA -> feature engineering -> two coupled supervised models -> probability calibration -> quantile evaluation -> SHAP explainability -> FastAPI service -> React frontend) suitable as a portfolio piece for programs like Amazon ML Summer School.

## What it does

Given a patient profile and a candidate appointment, the system answers three questions:

1. **Will the patient cancel / no-show?** Calibrated probability from an XGBoost classifier with isotonic calibration and threshold tuned on the precision-recall curve.
2. **How long will they wait if they show up?** P10 / P50 / P90 quantiles from three LightGBM models trained with quantile (pinball) loss.
3. **What is the best slot to book them into?** A counterfactual scoring layer combines both models to rank `(doctor, time)` candidates by expected wait, weighted by attendance probability and penalized for uncertainty.

## Held-out test results (20% temporal split, 80,000-row synthetic dataset)

| Model | Metric | Value |
|---|---|---|
| LogReg baseline | ROC-AUC | 0.695 |
| **XGBoost (calibrated)** | **ROC-AUC** | **0.683** |
| XGBoost (calibrated) | PR-AUC | 0.279 (vs 0.152 base rate -> 1.84x lift) |
| XGBoost (calibrated) | Brier | 0.123 |
| XGBoost (calibrated) | F1 (tuned threshold = 0.177) | 0.339 |
| **Wait regressor (P50)** | **MAE** | **9.11 min** |
| Wait regressor (P50) | RMSE | 17.67 min |
| Wait regressor | Pinball P10 | 1.33 |
| Wait regressor | Pinball P50 | 4.55 |
| Wait regressor | Pinball P90 | 3.00 |
| **Wait regressor** | **Empirical [P10, P90] coverage** | **79.8%** (target 80%) |

These are honest, calibrated numbers: deliberately not 0.95-AUC vapor.

## Tech stack

**ML / Data**
- Python 3.11
- NumPy 1.26, pandas 2.2, PyArrow 16 (parquet I/O)
- scikit-learn 1.4 (preprocessing, calibration, metrics, baseline LogReg)
- XGBoost 2.0 (cancellation classifier)
- LightGBM 4.3 (quantile regressors P10/P50/P90)
- SHAP 0.45 (TreeExplainer)
- matplotlib 3.8 + seaborn 0.13 (plots)
- joblib 1.4 (model persistence)
- Jupyter / nbformat / nbconvert (storytelling notebook)

**Backend**
- FastAPI 0.110
- Uvicorn 0.29 (ASGI server)
- Pydantic 2.7 (request/response validation)
- python-dateutil

**Frontend**
- React 18.3
- TypeScript 5.5
- Vite 5.4 (build / dev server)
- Tailwind CSS 3.4 (styling)
- Lucide React (icons)
- Native `fetch` (no axios; thin typed wrapper in `src/api.ts`)

**Tooling**
- ESLint 9 + typescript-eslint
- PostCSS + Autoprefixer

## Project layout

```
project/
  api/main.py                       FastAPI app exposing /predict, /recommend, /metadata
  ml/
    src/
      generate_data.py              Synthetic data generator (causal structure)
      features.py                   Feature engineering pipeline
      train.py                      Trains classifier + 3 quantile regressors
      evaluate.py                   ROC/PR, calibration, SHAP, EDA plots
      inference.py                  Loads artifacts, exposes recommender
    scripts/
      build_notebook.py             Builds + executes the storytelling notebook
    notebooks/
      PatientFlow_AI.ipynb          End-to-end narrative with code + plots
    data/
      appointments.parquet/csv      Generated dataset (80k rows)
    models/
      classifier.joblib             Calibrated XGBoost classifier
      regressor_p10/50/90.joblib    Three LightGBM quantile regressors
      regressor_preprocessor.joblib ColumnTransformer used at inference
      classifier_threshold.json     F1-optimal decision threshold
      encoder_state.json            Target-encoding stats fit on training fold
    reports/
      metrics.json                  All test-set metrics
      figures/                      9 generated PNGs (ROC, PR, calibration,
                                    confusion, quantile coverage, residuals,
                                    EDA, SHAP classifier, SHAP regressor)
  src/                              React + TS frontend that calls the API
    components/
      PatientForm.tsx
      PredictionCard.tsx            Cancel-prob gauge + quantile band
      RecommendationList.tsx        Top-K slot recommendations
      MetricsPanel.tsx              Renders held-out test metrics from API
    api.ts                          Typed fetch wrappers
    types.ts
    App.tsx
  requirements.txt                  Python deps (numpy, sklearn, xgboost,
                                    lightgbm, shap, fastapi, uvicorn, ...)
  package.json                      Frontend deps (React, Vite, Tailwind, Lucide)
```

## How to run from scratch

### 1. Python environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 2. Generate data + train models + build plots + execute notebook

```powershell
.\.venv\Scripts\python ml\src\generate_data.py --n 80000
.\.venv\Scripts\python ml\src\train.py
.\.venv\Scripts\python ml\src\evaluate.py
.\.venv\Scripts\python ml\scripts\build_notebook.py
.\.venv\Scripts\python -m jupyter nbconvert --to notebook --execute `
    ml\notebooks\PatientFlow_AI.ipynb --output PatientFlow_AI.ipynb `
    --ExecutePreprocessor.timeout=300
```

### 3. Start the ML API

```powershell
.\.venv\Scripts\python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open `http://127.0.0.1:8000/docs` for the auto-generated Swagger UI.

### 4. Start the frontend

```powershell
npm install
npm run dev
```

Frontend opens at `http://localhost:5173` and talks to the API at `http://127.0.0.1:8000`.

## API quick reference

```
GET  /health                # liveness probe
GET  /metadata              # doctors, appointment types, model metrics
POST /predict               # one patient -> cancel prob + P10/P50/P90 wait
POST /recommend             # one patient -> top-K slots ranked by score
```

Example `/predict`:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d "{\
  \"doctor_id\": \"D001_GenPrac_Sharma\", \"appointment_type\": \"consultation\", \
  \"appointment_time\": \"2025-07-14T10:00:00\", \"age\": 41, \"sex\": \"F\", \
  \"has_insurance\": true, \"lead_time_days\": 3, \"prior_no_shows\": 0, \
  \"prior_visits\": 4, \"sms_reminder\": true}"
```

## ML design choices, justified

- **Synthetic but principled data.** A handcrafted generator encodes known causal structure (doctor-specific service rates, hour/weekday seasonality, no-show priors). Because we know the ground truth, we can verify that SHAP recovers the right features.
- **Temporal train/test split.** Sorting by `appointment_time` and using the last 20% as test simulates the real deployment scenario and prevents leakage.
- **Target encoding fit only on training fold.** `EncoderState` is computed inside `fit_encoders(train_df)` and reused for test/inference - no leakage.
- **Probability calibration.** XGBoost outputs are isotonic-calibrated via `CalibratedClassifierCV(cv=3)` so the predicted probabilities are usable as decision inputs, not just rankings.
- **Threshold selection on the PR curve.** F1 is maximized along the training PR curve; we deliberately do not use 0.5 on an imbalanced problem.
- **Quantile regression, not point regression.** Wait time is heavy-tailed and heteroscedastic. Quantile loss is the proper scoring rule, and we report empirical coverage of the [P10, P90] interval as a calibration check.
- **Counterfactual recommender.** The score `P50 * (1 - p_cancel) + lambda * (P90 - P10)` weights expected wait by attendance probability and penalizes uncertainty - a small but principled optimization layer on top of ML predictions.

## Limitations (honest)

- Data is synthetic. Absolute accuracy numbers will differ on real clinic data; the relative comparisons (calibration improvement, quantile coverage close to nominal) are what matter.
- Quantile models are independent and can occasionally cross; we sort at inference time to enforce P10 <= P50 <= P90.
- Recommender weights are heuristics, not learned; in production they should be tuned by A/B-testing operational outcomes.

## Natural extensions

- Drop in the public **Brazilian no-show dataset** (~110k real records) for the classifier.
- Replace independent quantile heads with a **single multi-task neural network** sharing a trunk between cancellation logits and quantile outputs.
- Add **conformal prediction** (e.g. via MAPIE) for finite-sample coverage guarantees independent of the model class.
- Replace the rule-based recommender with **constrained ILP** to schedule a *batch* of patients while respecting per-doctor capacity.
