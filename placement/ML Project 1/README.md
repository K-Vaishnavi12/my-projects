# Symposium: A Multi-Agent Debating RAG

> Five AI personas walk into a room. They read the same corpus but retrieve different pieces of it. They argue. A moderator scores the debate. You watch it happen live.

**Symposium** is an end-to-end Data + AI project built for the Cognizant 1-credit **AI / ML / DS** course. It covers every topic in the syllabus (Data Warehouse, SQL, NoSQL, ETL, Cloud, Advanced Python, ML, Deep Learning, Prompt Engineering, Generative AI, AI-Assisted Development) inside one coherent product.

---

## About the Project

### The Problem
Most RAG (Retrieval-Augmented Generation) projects today are variants of *"chat with your PDF"* — a single AI reads a document and answers questions about it. The AI acts as a mirror, giving you one perspective. This is boring, unoriginal, and misses the real strength of modern LLMs.

### The Idea
What if, instead of ONE AI answering your question, **five different personalities** each read the same knowledge base but retrieve DIFFERENT parts of it based on their worldview, and then **debate live** in front of you? A moderator then scores the debate using machine learning models trained on the fly.

That's **Symposium**. It's like asking a panel of experts instead of one generalist:

- The **Historian** anchors every claim to a date, a precedent, or a prior thinker
- The **Scientist** demands mechanism, evidence, and quantification
- The **Poet** weaves the same facts into metaphor and narrative
- The **Skeptic** hunts for counter-examples and hidden assumptions
- The **Child** cuts through jargon with disarmingly simple questions

Each persona has its own **private slice of the corpus** (built during ETL by scoring every text chunk against a persona-specific retrieval bias), its own **system prompt** enforcing voice + guardrails, and its own **vector search index** in MongoDB.

### How It Works (End-to-End Flow)

```
1. USER asks: "Was the Industrial Revolution good for humanity?"
             │
             ▼
2. NAIVE BAYES model routes the question to a topic bucket (e.g. "history")
             │
             ▼
3. FIVE PERSONA AGENTS run in parallel:
       Each one:
         a. Retrieves top-K chunks from ITS OWN MongoDB collection
         b. Builds a prompt with persona voice + evidence + anti-hallucination guardrails
         c. Calls Groq (Llama-3.3-70B) to generate a 3-6 sentence turn
         d. SVM classifies the turn as agree/disagree/neutral
         e. Ridge regressor scores how agreeing it sounds
         f. Writes the turn to a SQL star-schema DWH
             │
             ▼
4. MODERATOR AGENT reads the full transcript, synthesizes a summary,
   picks a "winner", and outputs a consensus score
             │
             ▼
5. Everything is stored so you can slice debates later in Power BI:
   "Which persona wins most on ethics? Which one hallucinates most on 20th-century history?"
```

### The Innovation (What Makes This Unique)

Symposium is structurally different from every other student RAG project in three ways:

1. **Multi-agent per-persona retrieval.** The corpus is *classified into persona-specific sub-corpora during ETL*. Same query → 5 different retrieved chunk sets → 5 genuinely different perspectives. This isn't 5 clones with different temperatures.

2. **A moderator agent scores the debate.** Consensus, stance, and agreement are quantified turn-by-turn using our OWN trained ML models (SVM + Naive Bayes + Ridge regression). It's not a black-box "trust the LLM" — you can see the numbers.

3. **Every turn is warehoused in a star schema.** Debates aren't ephemeral. Every question, every persona turn, every retrieved chunk is a row in SQLite. That means you can slice: *"which persona has the highest disagreement rate on philosophy questions in Q3 2026?"* — the kind of analytics a real product needs.

### Tech Stack

| Layer | Tech |
|---|---|
| **LLM** | Groq (Llama-3.3-70B) — fast + free tier, with Gemini fallback |
| **Embeddings** | sentence-transformers MiniLM (384-dim, runs locally) |
| **Vector DB** | MongoDB Atlas Vector Search (per-persona collections) |
| **SQL DWH** | SQLite with a Kimball star schema (dims + facts + views + triggers) |
| **ETL** | Custom Python pipeline (Wikipedia → Mongo + SQLite) |
| **ML** | scikit-learn (SVM, Naive Bayes, Ridge, Logistic, KNN, K-Means, PCA) + TensorFlow/Keras (neural network) |
| **Web UI** | Streamlit multi-page app |
| **BI** | Power BI (with pre-built DAX measures + CSV export pipeline) |
| **Deployment** | Docker + AWS EC2 (deploy script included) |
| **AI-assisted dev** | Built with OpenCode CLI + Claude Opus 4.7 |

### What You Can Actually Do With It

Open the Streamlit UI and navigate six pages:

1. **Home** — meet the five personas, see corpus stats
2. **Live Debate** — ask a question, watch personas argue in real time with live SVM/regression scores on each turn
3. **Analytics** — bar charts showing which persona wins most, topic-level consensus, rolling averages (SQL window functions in action)
4. **Corpus Explorer** — see WHICH chunks each persona has "claimed" as its evidence pool (proves the per-persona retrieval works)
5. **ML Playground** — try live predictions with the SVM stance classifier, Naive Bayes topic router, Ridge regressor, KNN, K-Means + PCA scatter, and Keras neural net
6. **Prompt Lab** — same question through three prompting styles (zero-shot, few-shot, chain-of-thought) side-by-side

### Business / Real-World Angle

- **Education**: give students five perspectives on any topic to build critical thinking
- **Research**: use the Skeptic + Scientist personas to stress-test claims before citing them
- **Content generation**: the Poet persona for narrative, the Historian for context, the Child for accessible explanations — combined by the moderator
- **Reducing hallucinations**: five grounded voices with retrieval + a moderator that flags disagreement is more trustworthy than one unsupported LLM answer

---

## What makes it unique

Most RAG projects are "chat with your PDF." Symposium is different in three structural ways:

1. **Multi-agent, per-persona retrieval.** The corpus is *classified into persona-specific sub-corpora* during ETL. When you ask a question, five agents (Historian, Scientist, Poet, Skeptic, Child) each retrieve **only from their own worldview** and answer in their own voice.
2. **A moderator agent scores the debate.** Consensus, novelty, and evidence-grounding are quantified turn-by-turn using our own ML models (SVM stance classifier, regression on agreement, K-Means on argument clusters).
3. **Every turn is logged to a star-schema DWH** so you can slice the debate later in SQL or Power BI: "which persona wins on ethics questions? which persona hallucinates most on 20th-century history?"

---

## Architecture at a glance

```
                   +---------------------+
                   |  Wikipedia (extract)|
                   +----------+----------+
                              |
                              v
+-----------+     +----------------------+     +---------------------+
| Raw JSON  | --> |  Transform (persona  | --> | MongoDB Atlas       |
| (S3/local)|     |  classify + chunk    |     | (per-persona chunks |
+-----------+     |  + embed + enrich)   |     |  + vector index)    |
                  +----------+-----------+     +----------+----------+
                             |                            |
                             v                            v
                  +----------------------+     +---------------------+
                  |  SQLite Star DWH     |     | Persona Agents (5)  |
                  |  (dims + facts)      |<----| Moderator (Groq LLM)|
                  +----------+-----------+     +----------+----------+
                             |                            |
                             v                            v
                  +----------------------+     +---------------------+
                  | Power BI Dashboard   |     | Streamlit Live UI   |
                  +----------------------+     +---------------------+
```

Full detail: see `docs/ARCHITECTURE.md`.

---

## Syllabus coverage matrix

| Syllabus Topic | Where it lives in this project |
|---|---|
| **DWH concepts (OLTP vs OLAP, ETL, Data Marts, Metadata)** | `symposium/dwh/`, `docs/ARCHITECTURE.md` |
| **Data Lakehouse** | `data/raw` (lake) + `data/processed` (curated) + DWH layer |
| **ETL (extract, transform, load; joins, filters, aggregations)** | `symposium/etl/` (Airflow-style DAG in `scripts/run_etl.py`) |
| **ETL tools awareness** | `docs/ARCHITECTURE.md` (comparison table + why we chose custom Python) |
| **SQL (DQL, DDL, DML, joins, subqueries, window functions, optimization)** | `symposium/dwh/sql/*.sql` |
| **SQL Advanced (stored procedures, triggers, views, functions)** | `symposium/dwh/sql/03_views_triggers_procs.sql` |
| **NoSQL fundamentals & comparison** | `symposium/vectorstore/` + `docs/NOSQL_VS_SQL.md` |
| **Power BI** | `powerbi/` folder with CSV exports + DAX guide + `.pbix` instructions |
| **Python (beginner + advanced)** | Whole codebase; `symposium/utils/python_showcase.py` is the guided tour |
| **Cloud (AWS)** | `deployment/aws/` + `Dockerfile` + `docs/DEPLOYMENT.md` |
| **Python DS libs (NumPy, Pandas, Matplotlib, Scikit-Learn)** | `symposium/ml/` + `notebooks/` |
| **AI fundamentals, ML types, regression, classification** | `symposium/ml/` (linear reg, logistic reg, SVM, KNN, Naive Bayes) |
| **Unsupervised (K-Means, PCA)** | `symposium/ml/clustering.py` |
| **Neural Networks / TensorFlow** | `symposium/ml/neural_debate_scorer.py` |
| **Prompt Engineering (zero/few-shot, mindset, hallucinations)** | `symposium/prompts/` + `app/pages/5_Prompt_Lab.py` |
| **Generative AI / LLMs** | `symposium/agents/` (Groq / Gemini) |
| **AI-Assisted Development** | `docs/COPILOT_WORKFLOW.md` |

---

## Quick start

```powershell
# 1. Clone & install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\tasks.ps1 install

# 2. Configure
copy .env.example .env
# then edit .env and fill in GROQ_API_KEY and MONGODB_URI

# 3. Run the full pipeline (extract -> transform -> load -> train ML)
.\tasks.ps1 etl
.\tasks.ps1 train

# 4. Launch the UI
.\tasks.ps1 app
```

Then open http://localhost:8501 and try a debate.

Full step-by-step guide with troubleshooting: see `HOW_TO_RUN.md`.

---

## Repo layout

```
symposium/           # Core library
  config/            # Pydantic settings, persona registry
  etl/               # Extract, transform, load (Wikipedia -> Mongo + SQLite)
  dwh/               # Star schema DDL, DML, views, triggers, stored procedures
  vectorstore/       # MongoDB Atlas Vector Search helpers
  ml/                # SVM, regression, K-Means, PCA, KNN, Naive Bayes, NN
  agents/            # Persona agents, moderator, orchestrator
  prompts/           # Zero/few-shot templates, chain-of-thought, guardrails
  utils/             # Advanced Python showcase (decorators, generators, ...)
app/                 # Streamlit multi-page app
scripts/             # Runnable entry points
notebooks/           # EDA + model exploration
data/                # raw / staging / processed / models / exports (gitignored)
powerbi/             # CSV exports + DAX guide
deployment/          # Docker + AWS deploy scripts
docs/                # Architecture, syllabus map, slides, screenshots
tests/               # Pytest suite
```

---

## The 5 personas

| Persona | Retrieval bias | Prompt personality |
|---|---|---|
| **Historian** | Prefers dated events, causes, precedents | Cautious, cites eras, "as X taught us..." |
| **Scientist** | Prefers evidence, mechanisms, papers | Empirical, quantifies, demands data |
| **Poet** | Prefers narratives, metaphors, feelings | Metaphorical, emotive, holistic |
| **Skeptic** | Prefers counter-examples, edge cases | Adversarial, plays devil's advocate |
| **Child** | Prefers simple, foundational chunks | Naive, asks "but why?", cuts through jargon |

The moderator agent (also an LLM) reads all five responses, assigns a stance vector (via our SVM), scores agreement (via our regressor), and produces a synthesized answer.

---

## Project Stats

- **88 files** across 15 directories
- **60 Python modules** (~5,000 lines of production code)
- **4 SQL scripts** (star schema + views + triggers + reference queries)
- **10 documentation files** (README, architecture, deployment, syllabus coverage, slides)
- **20/20 unit tests** passing
- **6 trained ML models** (SVM, Naive Bayes, Ridge, Logistic, KNN, K-Means+PCA, Keras neural net)
- **6,380 chunks** indexed across 6 MongoDB collections during ETL
- **5 topic buckets** (history, science, philosophy, literature, current events)

---

## License

MIT. Built for education.
