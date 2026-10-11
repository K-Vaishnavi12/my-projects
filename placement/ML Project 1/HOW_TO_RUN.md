# Symposium - How to Run (verified end-to-end)

Every command below has been executed successfully on Windows 11 +
Python 3.11.9. Follow **in order**.

---

## 0. Prerequisites

- **Python 3.11** (3.10 also works, 3.12+ is untested)
- Windows PowerShell (native)
- ~5 GB free disk (deps + sentence-transformer model + tensorflow)
- Internet connection (for Wikipedia + Gemini)

**Two free accounts** (5 min setup):

1. **Google Gemini API key** — https://aistudio.google.com/apikey  ->  "Create API key"  ->  copy it
2. **MongoDB Atlas free M0 cluster** — https://www.mongodb.com/cloud/atlas/register
   - Create free cluster
   - Database Access -> Add user (remember the password)
   - Network Access -> Add IP -> "Allow access from anywhere"
   - Cluster -> Connect -> Drivers -> Python -> copy the connection string
   - Replace `<password>` in the string with your actual password

If you skip Gemini, the app runs in **stub mode** (placeholder responses).
If you skip Atlas, use `USE_LOCAL_VECTOR_STORE=true` + local Mongo via Docker.

---

## Step 1: Create the virtual env

```powershell
python -m venv .venv
```

## Step 2: Install everything (one command)

```powershell
.\tasks.ps1 install
```

This installs pip -> torch (CPU) -> sentence-transformers -> tensorflow -> everything else.
**Takes ~10 minutes on first run** (~3 GB download).

*Manual equivalent if `tasks.ps1` blocked by execution policy:*

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

*If PowerShell blocks the script:* run once
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and confirm.

## Step 3: Create your `.env`

```powershell
copy .env.example .env
notepad .env
```

Fill in these two lines (leave the rest alone):

```
GEMINI_API_KEY=paste_your_key_here
MONGODB_URI=paste_your_atlas_uri_here
```

## Step 4: Verify with tests

```powershell
.\tasks.ps1 test
```

Expected: **`20 passed`**. If you see failures, stop and fix them first.

## Step 5: Train the ML models (~30 seconds)

```powershell
.\tasks.ps1 train
```

Trains all 6 models (SVM, Naive Bayes, Ridge+Logistic, KNN, K-Means+PCA, Keras neural net) on synthetic labeled data. Writes `data/models/*.joblib` + `neural_debate_scorer.keras`.

## Step 6: Run the ETL to load Wikipedia into MongoDB + SQLite

```powershell
.\tasks.ps1 etl
```

Fetches ~50 Wikipedia articles across 5 topics, cleans them, chunks them, embeds them locally with MiniLM, scores each chunk against every persona, and loads into MongoDB (per-persona collections) + SQLite (star schema).

**Takes ~5 minutes on first run** (Wikipedia rate-limits gentle scraping).

Progress bars will show what's happening. If you just want to test the UI without waiting, ETL is optional — the ML Playground page works without it.

## Step 7: Launch the app

```powershell
.\tasks.ps1 app
```

A browser opens at http://localhost:8501.

You should see:

- **Home** — the five personas, live status cards.
- **Live Debate** — type a question, watch personas argue.
- **Analytics** — charts from the SQL DWH.
- **Corpus** — top chunks per persona.
- **ML Playground** — try SVM / Naive Bayes / regression / KNN / K-Means / neural net live.
- **Prompt Lab** — see zero-shot vs few-shot vs chain-of-thought side by side.
- **About** — syllabus coverage matrix.

---

## Suggested first debate

On the **Live Debate** page, try:

> *"Is progress in artificial intelligence ultimately good for humanity?"*

Set topic = `current_events`, rounds = 1. Watch each persona stream their turn (they retrieve DIFFERENT chunks even though the corpus is the same), then read the moderator's verdict with consensus score.

---

## Optional extras

### Export CSVs for Power BI

```powershell
.\tasks.ps1 export
```

Writes `data/exports/*.csv`. Open Power BI Desktop, "Get data -> Text/CSV",
follow `powerbi/README.md` for the star-schema mapping + DAX measures.

### Run one debate on the CLI (no browser)

```powershell
.\.venv\Scripts\python.exe scripts\run_debate.py "Should robots have rights?" --rounds 1
```

### See the advanced-Python showcase

```powershell
.\.venv\Scripts\python.exe -m symposium.utils.python_showcase
```

### Docker deployment

```powershell
docker compose up -d --build
```

App at http://localhost:8501 with a local Mongo container.

### AWS EC2 deployment

Follow `docs/DEPLOYMENT.md` — one-shot script provided.

---

## Common issues

**"cannot be loaded because running scripts is disabled"**
Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` -> `Y`.

**MongoDB "Could not connect" / IP whitelist error**
Atlas -> Network Access -> Add `0.0.0.0/0` (dev only).

**MongoDB "$vectorSearch not found"**
The store falls back to client-side cosine automatically. To use the fast path, wait ~2 min after first ETL run for the Atlas Search index to build. Check "Search" tab on your cluster.

**Streamlit "Data warehouse isn't populated yet"**
Run `.\tasks.ps1 etl` first.

**"GEMINI_API_KEY missing - OFFLINE stub mode"**
UI still works, but persona responses are placeholders. Fix by adding your key to `.env`.

**Tensorflow slow on first import**
Normal — TF pre-warms on first use. Second run is instant.

**Slow first ML training**
`sentence-transformers` downloads MiniLM (~90 MB) on first use. Cached afterwards.

---

## Quick reference (`.\tasks.ps1 <task>`)

| Task | What it does |
|---|---|
| `install` | pip + torch (CPU) + requirements.txt |
| `test` | Run all 20 pytest cases |
| `train` | Train all 6 ML models |
| `etl` | Wikipedia -> MongoDB + SQLite |
| `app` | Launch Streamlit UI |
| `debate` | Run one debate on CLI |
| `export` | Dump DWH to CSVs for Power BI |
| `faiss` | Build local FAISS snapshot from Mongo (offline mode) |
| `docker-up` | docker compose up |
| `docker-down` | docker compose down |
| `showcase` | Run Python-advanced showcase |
| `clean` | Wipe data folders |
| `help` | Show all tasks |
