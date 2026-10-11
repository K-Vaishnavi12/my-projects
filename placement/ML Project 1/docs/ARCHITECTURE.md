# Symposium - Architecture

> Multi-agent debating RAG on a lakehouse-style stack.

---

## 1. Bird's-eye view

```
                                    +---------------+
                                    | Wikipedia API |
                                    +-------+-------+
                                            |
                                            v
+---------- RAW LAYER (data lake) -----------------------------+
|  data/raw/{topic}/{slug}.json                                |
|  * Extractor writes verbatim JSON dumps                      |
|  * Idempotent, re-runnable, S3-shippable                     |
+--------------------------------+-----------------------------+
                                 |
                                 v
+---------- STAGING LAYER --------------------------------------+
|  data/staging/{doc_id}.json                                   |
|  * Cleaned text, DQ rules applied, references stripped        |
|  * "Curated" zone in Lakehouse terms                          |
+--------------------------------+------------------------------+
                                 |
                                 v
+---------- SERVING LAYER (OLAP + NoSQL) ------------------------------+
|                                                                      |
|  SQLite Star DWH                        MongoDB Atlas                 |
|  (analytical facts)                     (semantic + vector)           |
|                                                                       |
|  dim_topic ------\        dim_persona          documents              |
|  dim_document ---+> fact_chunk         +--> chunks_all (vector idx)   |
|                  |                     |    chunks_historian          |
|  fact_query --< fact_turn -< fact_retr +    chunks_scientist          |
|                                             chunks_poet               |
|                                             chunks_skeptic            |
|                                             chunks_child              |
+----------------------------------------------------------------------+
                                 |
                                 v
+---------- APPLICATION LAYER ------------------------------------------+
|  Streamlit multi-page app          |   Power BI dashboards             |
|  - Live Debate                     |   - Executive KPIs                |
|  - Analytics                       |   - Persona Insight               |
|  - Corpus                          |   - Evidence Explorer             |
|  - ML Playground                   |   - Corpus Health                 |
|  - Prompt Lab                      |                                   |
|  - About                           |                                   |
+----------------------------------------------------------------------+

  ML models used at runtime:
    SVM stance -> Naive Bayes topic router -> Ridge/Logistic regressor
    K-Means + PCA (offline analysis) -> KNN (similar turns) -> Keras MLP (consensus tier)
```

---

## 2. Layer responsibilities

### Raw (data lake)
- **Purpose**: exact copy of what Wikipedia returned. Never mutated.
- **Format**: JSON per article; folder per topic.
- **Storage**: local disk in dev, S3 in prod (`deployment/aws/upload_raw_to_s3.py`).

### Staging
- **Purpose**: cleaned text ready for chunking.
- **DQ rules**: min length, min alphanumeric ratio, drop navigation sections.
- **Idempotent**: overwrites on re-run so cleanup can be improved without re-extract.

### Serving

**SQLite DWH (OLAP)**

- Kimball star schema with 3 dims + 4 facts + 1 metadata table + views.
- Views implement complex analytics with **JOIN + GROUP BY + WINDOW** functions (see `symposium/dwh/sql/03_views_triggers.sql`).
- Triggers maintain an audit log and enforce range constraints.
- "Stored procedures" are Python callables on `Warehouse` (SQLite doesn't do real SPs; this is the canonical workaround).

**MongoDB (NoSQL + vectors)**

- Six chunk collections: `chunks_all` + one per persona.
- Vector index (Atlas Search) with **cosine similarity** on the 384-dim MiniLM embedding.
- Rich per-chunk metadata (persona scores, topic, doc_url) so retrieval can be filtered without joining.

### Application

- **Streamlit**: interactive debate runner + dashboards + ML playground.
- **Power BI**: exec-facing dashboards built on CSV exports.

---

## 3. ETL orchestration

```
extract_topics()  ->  clean_stream()  ->  stage_to_disk()  ->
  chunk_article()  ->  embed()  ->
    load(mongo)  &  load(sqlite)  ->  ensure_vector_index()
```

Each stage is a pure function; the orchestrator (`symposium/etl/pipeline.py`) simply composes them. Swap-in for a real Airflow DAG is trivial: turn each stage into an operator.

**Why not use a heavyweight tool?**

| Tool                | Fit for this project | Why we chose otherwise |
|---|---|---|
| Apache Airflow      | Yes                 | Overkill for 1-credit demo; requires scheduler + web server |
| AWS Glue            | Yes (on AWS)        | Requires an AWS account with billing; not portable          |
| Azure Data Factory  | Yes (on Azure)      | Same as Glue but Azure                                      |
| SSIS / Talend       | GUI-oriented        | We wanted git-friendly, code-only pipelines                 |
| **Custom Python**   | Ideal for a demo    | Fully reproducible, no infra, still teaches every concept   |

Once we outgrow the demo, `pipeline.run_pipeline()` maps 1-to-1 onto an Airflow DAG (each function -> `PythonOperator`).

---

## 4. Multi-agent orchestration

```
User question
    |
    v
Naive-Bayes topic router
    |
    v
For each round:
    For each persona in order:
        - Retrieve top-K chunks from THIS PERSONA'S Mongo collection
        - Build persona prompt (system + prior turns + evidence + guardrails)
        - LLM (Gemini) generates a 3-6 sentence turn
        - SVM classifies stance
        - Ridge regressor scores agreement
        - Recorder writes fact_turn + fact_retrieval to SQL
    end
end
    |
    v
Moderator LLM synthesises transcript -> consensus_score + winner + summary
    |
    v
Recorder writes back to fact_query
```

Everything is streamable: `Symposium.run(..., on_turn=fn)` fires the callback per turn so the Streamlit UI paints as agents speak.

---

## 5. OLTP vs OLAP

We fake an OLTP surface for turn writes (small, row-at-a-time INSERTs), then use OLAP-style views for analytics. In production you'd:

- keep OLTP writes on the SQLite (fast enough at this scale, or swap for Postgres)
- ELT into a real DWH (BigQuery / Snowflake / Redshift) via a nightly job
- point Power BI at the DWH, not the OLTP DB

---

## 6. Metadata

`meta_pipeline_run` (Section 1 above) stores every ETL run's start/end + stats JSON. This is the "metadata layer" from the DWH syllabus in miniature. Extending it to a full lineage tool (OpenLineage / Marquez) is straightforward.

---

## 7. Cloud footprint

| Component | Local dev | AWS prod |
|---|---|---|
| Raw data | disk | S3 |
| DWH | SQLite file | RDS PostgreSQL |
| Vector store | Mongo Atlas free | Mongo Atlas M10 |
| App | `streamlit run` | Docker on EC2 (see `docs/DEPLOYMENT.md`) |
| Embeddings | local MiniLM | same, packaged in image |
| LLM | Gemini API | Gemini API |
| Auth | none | Cognito in front of ALB |

The `Dockerfile` + `deploy_ec2.sh` script deploy the app in one shot.
