---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Symposium - Multi-Agent Debating RAG'
footer: 'Cognizant AI/ML/DS Course - 1 Credit Project'
style: |
  section { font-family: 'Helvetica', 'Arial', sans-serif; }
  h1 { color: #2c3e50; }
  h2 { color: #34495e; }
  .persona { display: inline-block; padding: 4px 12px; border-radius: 16px; margin: 4px; }
---

<!-- _class: lead -->

# Symposium
## A Multi-Agent Debating RAG

Five AI personas walk into a room.
They read the same corpus but retrieve different pieces of it.
They argue. A moderator scores the debate.
**You watch it happen live.**

---

## The problem with most RAG projects

- "Chat with your PDF" - single retriever, single voice
- The AI is a mirror, not a **council**
- Reviewers see nothing that couldn't be built in an afternoon
- No unified home for the full AI/ML/DS syllabus

**Symposium** solves all four in one product.

---

## Three structural innovations

1. **Multi-agent, per-persona retrieval**
   Every chunk is scored against 5 personas at ETL time and lands in that persona's OWN Mongo collection.

2. **Moderator agent scores the debate**
   Consensus + winner computed by our own SVM + regression models — not a black box.

3. **Every turn is warehoused**
   Star-schema DWH means analysts can slice: *"which persona wins on ethics? which hallucinates on history?"*

---

## The five personas

<div class="persona" style="background:#8B451322;color:#8B4513;">The Historian</div>
<div class="persona" style="background:#1E90FF22;color:#1E90FF;">The Scientist</div>
<div class="persona" style="background:#B0306022;color:#B03060;">The Poet</div>
<div class="persona" style="background:#556B2F22;color:#556B2F;">The Skeptic</div>
<div class="persona" style="background:#FFB34722;color:#FFB347;">The Child</div>

Each persona:
- Owns a lexicon-driven retrieval bias
- Has a hand-crafted system prompt with voice + guardrails
- Retrieves from ITS OWN Mongo collection at query time

---

## Architecture

```
Wikipedia -> RAW (JSON lake) -> STAGING (clean) -> SERVING (SQL + NoSQL)
                                                       |
                                                       v
                                             Persona Agents + Moderator
                                                       |
                                                       v
                                       Streamlit UI + Power BI dashboards
```

**Polyglot persistence:** SQLite for facts + dims, MongoDB for vectors.
Every debate writes to BOTH stores.

---

## ETL - full lakehouse pattern

- **Extract**: Wikipedia API (5 topic buckets, ~50 articles).
- **Transform**:
  - Data-quality rules (length, alphanumeric ratio, boilerplate strip)
  - Regex-based reference cleanup
  - Feature extraction (date density, evidence density, ...)
  - Persona affinity scoring (5 scores per chunk)
  - Sentence-boundary chunking with overlap
  - Sentence-transformer embedding (MiniLM, 384-dim)
- **Load**: MongoDB (6 collections + vector index) + SQLite star schema

Every stage is a pure function -> maps 1:1 onto Airflow operators.

---

## Star-schema DWH (SQLite)

```
              dim_topic
                  |
              dim_document                  dim_persona
                  |                              |
                  +--> fact_chunk                |
                                                 |
              fact_query <---- fact_turn <-------+
                                    |
                                    v
                              fact_retrieval  ------> fact_chunk
```

**Views**: `v_persona_activity`, `v_topic_debate_stats`, `v_debate_evidence_trail`, `v_chunk_persona_leaderboard` (uses WINDOW functions).
**Triggers**: audit log + range-check guardrails.

---

## NoSQL: MongoDB Atlas Vector Search

- 6 collections: `chunks_all` + one per persona
- Native `$vectorSearch` on cosine similarity
- Flexible schema: `persona_scores` is a nested object
  (would require 5 columns + an ALTER TABLE in SQL)
- Horizontal scale via Atlas sharding

**Rule of thumb**:
- SQL for aggregation / joins / audit
- NoSQL for vectors + flexible metadata

---

## Machine Learning - every syllabus algorithm

| Algorithm | Purpose | Framework |
|---|---|---|
| **Linear + Logistic Regression** | Agreement scoring | scikit-learn |
| **SVM (Linear + Calibrated)** | Stance classification | scikit-learn |
| **Multinomial Naive Bayes** | Topic routing | scikit-learn |
| **K-Nearest Neighbours** | Similar past turns | scikit-learn |
| **K-Means + PCA** | Argument space visualization | scikit-learn |
| **Neural Network (Keras MLP)** | Consensus tier prediction | TensorFlow |

Reproducible: run `python scripts/train_models.py` — trains all six in ~30s.

---

## Multi-agent orchestration

```
question
  |
  v
Naive Bayes topic router
  |
  v
+-- for each round -----------------------+
|   for each persona in order:            |
|     retrieve from persona's Mongo coll  |
|     build prompt (system + evidence)    |
|     Gemini generates turn               |
|     SVM classifies stance               |
|     regressor scores agreement          |
|     write turn to SQL DWH               |
+------------------------------------------+
  |
  v
Moderator synthesises -> consensus + winner + summary
```

---

## Prompt engineering

**Three styles built into the Prompt Lab page:**

- **Zero-shot**: "Answer this question in 3-5 sentences."
- **Few-shot**: prepend 2 hand-crafted Q/A examples.
- **Chain-of-thought**: force `<thinking>...</thinking>` before answer.

**Anti-hallucination guardrails** (baked into every persona prompt):

1. Only use retrieved evidence
2. Cite with [E1], [E2] tags
3. Never invent URLs / stats / dates
4. Refuse hate speech / medical / legal advice
5. Stay in persona voice

---

## Live demo checkpoints

1. **Home** - meet the personas.
2. **Live Debate** - "Is progress in AI ultimately good for humanity?"
   Watch each persona stream their turn.
3. **Analytics** - persona airtime, topic consensus, rolling averages.
4. **Corpus** - which chunks the Skeptic claims.
5. **ML Playground** - live SVM prediction, PCA scatter, NN scoring.
6. **Prompt Lab** - the same question through 3 prompting styles.

---

## Cloud footprint (AWS)

| Layer | Service |
|---|---|
| Compute | EC2 (Docker) |
| Storage | S3 (raw data lake) |
| Vector DB | MongoDB Atlas (free tier) |
| DWH (prod) | RDS PostgreSQL |
| Logs | CloudWatch |
| DNS/HTTPS | Route 53 + ACM |

`bash deploy_ec2.sh` = one-shot install + first-run ETL + train.
Total cost ~$0-32/month at demo scale.

---

## Advanced Python showcase

Every syllabus "Python Advanced" topic used *in production code*, not toy examples:

- **Iterators + generators**: chunker streams chunks lazily
- **Decorators + closures**: `@retry`, `@timed` in `symposium/utils`
- **Comprehensions + map/filter/reduce**: python_showcase.py
- **Regex**: cleaner + persona classifier
- **Enum + dataclasses**: `Turn`, `Persona`, `Confidence`
- **Serialization**: `write_json`, `write_pickle`
- **Partial functions**: `functools.partial(round, ndigits=2)`

Run: `python -m symposium.utils.python_showcase`

---

## What this project proves

- I can **design** a star-schema DWH
- I can **write** production-grade SQL with views + triggers + windows
- I know **when** to reach for NoSQL vs SQL
- I can **build** a full ETL pipeline with DQ rules
- I understand **every** classical ML algorithm in the syllabus
- I can **deploy** with Docker + AWS
- I can **prompt-engineer** to reduce hallucinations
- I can **integrate** an LLM into a real product

All in one codebase, ~2500 lines, one weekend.

---

<!-- _class: lead -->

# Thank you!

**Symposium** — five AI personas debate your question.

Repo: `github.com/YOUR_USER/symposium`
Demo: `http://<ec2-host>:8501`

Questions?
