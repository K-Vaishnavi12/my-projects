# PatientFlow AI

**A SQL-first outpatient clinic management system, with an ML layer on top for cancellation-risk and wait-time forecasting.**

Around 60% of this project is the SQL / data layer (12 normalized MySQL tables, full CRUD, analytics, audit trail); the remaining 40% is an XGBoost + LightGBM inference pipeline exposed through the same FastAPI service.

---

## What it does

- **Manages clinic operations in SQL**: patients, doctors, clinics, appointments, visit notes, invoices, users - all with proper foreign keys, indexes and referential integrity.
- **Logs every mutation** to an `audit_log` table (create / update / delete for every entity).
- **Computes analytics in the database** via `GROUP BY` queries (revenue by type, doctor load, top no-show patients, appointment status distribution) - served through a `/stats` endpoint.
- **Predicts cancellation risk + wait time quantiles** from calibrated XGBoost + LightGBM models, and **persists every prediction and recommendation** to `predictions`, `recommendation_runs` and `recommended_slots` tables so you can build a longitudinal model-vs-reality dataset.

---

## SQL schema (12 tables)

```
                   +----------+          +--------------------+
                   | clinics  |          | appointment_types  |
                   +----+-----+          +---------+----------+
                        |                          |
                        v                          v
+---------+      +------+------+          +--------+---------+
|  users  |      |   doctors   |<---+     |                  |
+---------+      +------+------+    |     |                  |
                        |           |     |                  |
                        v           |     v                  |
+----------+       +----+-------+   |  +--+-----------+      |
| patients +------>|            +---+->| appointments +------+
+----+-----+       |            |      +----+---------+      |
     |             +------------+           |                |
     |                                      +--> visit_notes |
     |                                      +--> invoices    |
     |                                      +--> predictions <---+
     |                                                            \
     +---> recommendation_runs ---> recommended_slots               \
                                                                     \
                                     audit_log  (every mutation) ----+
```

| Group | Table | Purpose |
|---|---|---|
| Reference / auth | `clinics` | Clinic locations |
|  | `users` | Staff accounts (SHA-256 hashed passwords, role: admin/doctor/staff) |
|  | `doctors` | Clinicians (FK -> `clinics`) |
|  | `appointment_types` | Service catalog with default prices |
| Operational | `patients` | Patient records (name, contact, insurance, priors) |
|  | `appointments` | Scheduled visits (FK -> patient / doctor / type) |
|  | `visit_notes` | 1:1 with appointment - complaint, diagnosis, prescription |
|  | `invoices` | 1:1 with appointment - amount, currency, status |
| ML / audit | `predictions` | Every `/predict` call, full JSON payload + outputs |
|  | `recommendation_runs` | One row per `/recommend` call |
|  | `recommended_slots` | Child rows of `recommendation_runs` |
|  | `audit_log` | Every create/update/delete on every entity |

Full DDL is in [`sql/schema.sql`](sql/schema.sql). The complete SQL toolkit shipped with the project:

| File | Contents |
|---|---|
| `sql/schema.sql` | Full DDL for all 12 tables, indexes, foreign keys |
| `sql/seed.sql` | Idempotent pure-SQL seed (clinics, users, patients, appointments, notes, invoices) |
| `sql/views.sql` | 9 reusable views: `v_patient_directory`, `v_appointment_full`, `v_doctor_kpi`, `v_revenue_daily`, `v_revenue_by_specialty`, `v_no_show_risk_watch`, `v_prediction_calibration`, `v_audit_recent`, `v_clinic_snapshot` |
| `sql/procedures.sql` | Stored procedures: `sp_book_appointment`, `sp_cancel_appointment`, `sp_mark_no_show`, `sp_complete_visit`, `sp_refresh_patient_priors`, `sp_refresh_all_priors` |
| `sql/triggers.sql` | Server-side invariants: auto-derive lead time, keep patient counters in sync, stamp `paid_at`, refuse deletion of patients with prediction history |
| `sql/reports.sql` | 17 reporting queries covering daily ops, weekly/monthly analytics, model-vs-reality calibration, cohort retention, data-quality checks |
| `sql/analytics.sql` | 8 example `GROUP BY` queries mirroring the `/stats` endpoint |
| `sql/migrations.sql` | Idempotent forward migrations with a `migration_log` tracking table |
| `sql/tuning.sql` | Performance guide: composite indexes, EXPLAIN targets, materialised roll-ups, partition strategy |

---

## API surface

```
Reference
  GET    /doctors
  GET    /appointment-types
  GET    /clinics
  POST   /clinics
  DELETE /clinics/{id}

Users
  GET    /users
  POST   /users
  DELETE /users/{id}

Patients (CRUD)
  GET    /patients        (?q=... for name search)
  POST   /patients
  GET    /patients/{id}
  PATCH  /patients/{id}
  DELETE /patients/{id}

Appointments (CRUD)
  GET    /appointments    (?patient_id / ?doctor_id / ?status_)
  POST   /appointments
  GET    /appointments/{id}
  PATCH  /appointments/{id}
  DELETE /appointments/{id}

Clinical / billing
  GET    /visit-notes     (?appointment_id)
  POST   /visit-notes
  DELETE /visit-notes/{id}
  GET    /invoices        (?status_ / ?appointment_id)
  POST   /invoices
  PATCH  /invoices/{id}

Analytics (SQL GROUP BY)
  GET    /stats

ML
  POST   /predict         (persists to `predictions`)
  POST   /recommend       (persists to `recommendation_runs` + `recommended_slots`)
  GET    /predictions

Meta
  GET    /health          (api + db liveness)
  GET    /metadata
```

Full interactive Swagger UI at `/docs` once the server is running.

---

## Quick start

### 1. MySQL

Install MySQL / MariaDB locally (or run it in Docker), then copy `.env.example` -> `.env` and set your credentials:

```
PATIENTFLOW_DB_HOST=127.0.0.1
PATIENTFLOW_DB_PORT=3306
PATIENTFLOW_DB_USER=root
PATIENTFLOW_DB_PASSWORD=yourpassword
PATIENTFLOW_DB_NAME=patientflow
```

The API will auto-`CREATE DATABASE IF NOT EXISTS`, create all 12 tables, and seed:
- 3 clinics, 2 users (`admin/admin`, `reception/reception`)
- doctors + appointment types from the ML feature contract
- 8 sample patients + ~50 appointments (mixed past/future + statuses)
- visit notes + invoices for the completed ones

### 2. Python + backend

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend

```powershell
npm install
npm run dev
```

Opens at `http://localhost:5173`. Nav has four sections:
- **Patients** - CRUD table + modal form
- **Appointments** - CRUD + one-click "run + persist prediction"
- **Stats** - live SQL-driven analytics dashboard
- **Predict** - ad-hoc prediction / slot-recommendation playground

---

## ML layer (the other 40%)

The ML pipeline lives under `ml/src/`:

- `generate_data.py` - synthetic outpatient dataset (~80k rows) with known causal structure
- `features.py` - feature engineering + `EncoderState` (target encoding fit on train fold only)
- `train.py` - trains an XGBoost cancellation classifier (isotonic-calibrated, F1-tuned threshold) + three LightGBM quantile regressors (P10/P50/P90) for wait time
- `evaluate.py` - ROC/PR/calibration metrics, SHAP explainability
- `inference.py` - `PatientFlowModel` class loaded by the FastAPI service at startup

Held-out test metrics (temporally split, 20% test fold) are stored in `ml/reports/metrics.json` and served through `/metadata`:

| Model | Metric | Value |
|---|---|---|
| XGBoost (calibrated) | ROC-AUC | 0.683 |
| XGBoost (calibrated) | PR-AUC | 0.279 (vs 0.152 base rate) |
| XGBoost (calibrated) | Brier | 0.123 |
| Wait regressor (P50) | MAE | 9.11 min |
| Wait regressor | Empirical [P10, P90] coverage | 79.8% (target 80%) |

To retrain from scratch:

```powershell
.\.venv\Scripts\python ml\src\generate_data.py --n 80000
.\.venv\Scripts\python ml\src\train.py
.\.venv\Scripts\python ml\src\evaluate.py
```

---

## Project layout

```
api/                         SQL + REST backend
  main.py                    FastAPI composition
  db.py                      SQLAlchemy engine + session + .env loader
  models.py                  12 ORM models
  schemas.py                 Pydantic request/response schemas
  seed.py                    DB init + reference + sample seed
  audit.py                   audit_log helper
  routers/
    reference.py             /doctors, /appointment-types, /clinics
    users.py                 /users
    patients.py              /patients CRUD
    appointments.py          /appointments CRUD
    visit_notes.py           /visit-notes
    invoices.py              /invoices
    stats.py                 /stats (SQL analytics)
    ml.py                    /predict, /recommend, /predictions

sql/
  schema.sql                 Full DDL (fallback / reference)
  analytics.sql              Example GROUP BY queries

ml/                          ML training + inference
  src/{generate_data,features,train,evaluate,inference}.py
  models/                    Trained artifacts (joblib) - regenerated locally
  reports/metrics.json       Held-out test metrics served via /metadata

src/                         React + TS frontend
  App.tsx                    Router + top nav
  api.ts, types.ts           Typed fetch layer
  pages/
    PatientsPage.tsx
    AppointmentsPage.tsx
    StatsPage.tsx            SQL analytics dashboard
    PredictPage.tsx          ad-hoc predict / recommend
  components/                (form, cards, prediction, recommendation list)

requirements.txt             Python deps
package.json                 Frontend deps
.env.example                 DB connection template
```

---

## Design notes

- **SQL as source of truth.** Doctors and appointment types are seeded from the ML feature constants on first startup, but the DB is authoritative from then on - the API queries `doctors` / `appointment_types` on every `/metadata` call.
- **Every mutation is auditable.** `audit_log` receives an entry with a JSON diff on every create/update/delete, keyed by `(entity, entity_id)`.
- **Analytics in-database.** `/stats` is a single request that fans out several `GROUP BY` queries; the frontend renders them as KPI cards + tables. No aggregation happens in application code.
- **ML predictions are persisted.** Every `/predict` and `/recommend` call writes to SQL by default (`persist=true`), so you can build a real-vs-predicted dataset over time and audit model behavior in production.
- **Referential integrity.** `ON DELETE CASCADE` on appointments -> patients (deleting a patient removes their appointments, notes, invoices, predictions); `ON DELETE SET NULL` where a soft break is safer (e.g. patient_id on prediction runs).
