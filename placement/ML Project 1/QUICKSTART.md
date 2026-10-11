# Symposium - Quick Start

Follow these steps IN ORDER. Every step is idempotent (safe to re-run).

---

## 0. Prerequisites

- Python 3.11 (older 3.10 also works)
- ~2 GB free disk (sentence-transformer model + FAISS + data)
- A [Google AI Studio API key](https://aistudio.google.com/apikey) (free)
- A [MongoDB Atlas free M0 cluster](https://www.mongodb.com/cloud/atlas/register)
  (or run local Mongo via `docker compose up -d mongo`)

Optional for the cloud demo:
- AWS account with S3 + EC2 access
- Docker Desktop

---

## 1. Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Configure

```powershell
copy .env.example .env
notepad .env       # fill in GEMINI_API_KEY and MONGODB_URI
```

## 3. Run the ETL

```powershell
python scripts\run_etl.py --topics history science philosophy literature current_events
```

Downloads ~50 Wikipedia articles, cleans them, chunks them, embeds them (locally with MiniLM), scores each chunk against every persona, then loads facts + dims into SQLite AND persona-scoped collections in MongoDB.

**First run takes ~2-5 minutes** depending on network + CPU.

## 4. Train the ML models

```powershell
python scripts\train_models.py
```

Trains SVM + Naive Bayes + Ridge + Logistic + KNN + K-Means + PCA + Keras MLP.
Writes `data/models/*.joblib`, `*.keras`, and `metrics.json`.

## 5. Launch the app

```powershell
streamlit run app\Home.py
```

Open http://localhost:8501 and:
1. Go to **Live Debate**
2. Ask: *"Is progress in AI ultimately good for humanity?"*
3. Watch the five personas argue, then read the moderator's verdict.

## 6. (Optional) Explore Power BI

```powershell
python scripts\export_csv.py
```

Open the CSVs in `data\exports\` with Power BI Desktop and follow `powerbi\README.md`.

## 7. (Optional) Run all tests

```powershell
pytest tests -v
```

---

## Everything via the task runner

```powershell
.\tasks.ps1 install    # step 1
.\tasks.ps1 etl        # step 3
.\tasks.ps1 train      # step 4
.\tasks.ps1 app        # step 5
.\tasks.ps1 export     # step 6
.\tasks.ps1 test       # step 7
.\tasks.ps1 help       # show all
```

---

## Troubleshooting

**"GEMINI_API_KEY missing - OFFLINE stub mode"**
The app still works with placeholder text so you can demo the plumbing. Add your key to `.env` for real answers.

**MongoDB $vectorSearch fails**
The store automatically falls back to a client-side cosine loop. Slow but functional. Fix by:
- Waiting for the Atlas Search index to finish building (~2 min after first upload)
- Or set `USE_LOCAL_VECTOR_STORE=true` in `.env` and run `python scripts\build_faiss.py`

**Streamlit page shows "Data warehouse isn't populated yet"**
Run step 3 first.

**Tensorflow slow on first import**
Normal — TF loads a lot on first use. Second run is fast.
