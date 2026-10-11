# Syllabus Coverage Matrix

Direct one-to-one mapping between every line of the course syllabus
and the file(s) in this repo that satisfy it. Reviewers can grade
each row independently.

## Session 1 - DWH + SQL + NoSQL

| Sub-topic | Where it lives |
|---|---|
| Need for BI | `README.md` + `docs/ARCHITECTURE.md` (why we built a DWH) |
| Data Warehouse | `symposium/dwh/` |
| OLTP vs OLAP | `docs/ARCHITECTURE.md#5-oltp-vs-olap` |
| ETL | `symposium/etl/` (extract / transform / load) |
| Data Mart | See "topic-scoped tables" — dim_topic + fact_chunk filtered |
| Metadata | `meta_pipeline_run` table + `01_schema.sql` |
| DWH Architecture | `docs/ARCHITECTURE.md#1-birds-eye-view` |
| Demo creating a DWH | `python scripts/run_etl.py` provisions the star schema |
| Data Lakehouse | `data/raw` (lake) + `data/staging` (curated) + DWH layer |
| Data Lake -> Data Swamp | Explained in `docs/ARCHITECTURE.md` (staging DQ rules) |
| SQL Relational DBs | `symposium/dwh/sql/*.sql` |
| Transactional processing | `fact_turn` inserts during debates |
| Databricks Evolution | Discussed in `docs/ARCHITECTURE.md` (why not Databricks here) |
| Extract data dump | `symposium/etl/extract/wiki_extractor.py` |
| Data format consistency | `symposium/etl/transform/cleaner.py` |
| DQ rules | `cleaner.looks_like_content` + regex rules |
| Truncate & load | Load strategy documented in `ARCHITECTURE.md`; SQL uses UPSERT |
| Load strategies / approach | Bulk upserts in `sqlite_loader.py` + `mongo_loader.py` |
| Transform / Mapping / Enriching | `chunker.py` + `persona_classifier.py` |
| Joins, filter, dedupe | SQL views + Mongo unique indexes on `chunk_id` |
| Aggregation | `04_analytics_queries.sql` |
| Dimension, Facts, EDW, Data Marts | `01_schema.sql` (star schema) |
| Variety of ETL Tools | Comparison table in `ARCHITECTURE.md` |
| SQL DQL / DDL / DML | `01_schema.sql` (DDL) + `02_seed.sql` (DML) + `04_analytics_queries.sql` (DQL) |
| Filtering + sorting | `04_analytics_queries.sql` Q1, Q2 |
| Grouping + aggregation | Q3 |
| Joins + subqueries | Q4 |
| Window functions | Q4 CTE + Q5 |
| SQL optimization | Q6 `EXPLAIN QUERY PLAN` |
| Automation | Q7 + `scripts/export_csv.py` |
| Stored procedures | Python callables on `Warehouse` (SQLite-idiomatic) |
| Triggers | `03_views_triggers.sql` (audit + validation) |
| Views | `v_persona_activity`, `v_topic_debate_stats`, ... |
| Functions | SQLite built-ins + Python "stored procs" |
| NoSQL fundamentals | `symposium/vectorstore/` + `docs/NOSQL_VS_SQL.md` |
| NoSQL vs SQL | `docs/NOSQL_VS_SQL.md` (side-by-side scorecard) |
| Power BI | `powerbi/README.md` + `scripts/export_csv.py` |
| Connecting Data Sources | `powerbi/README.md` #1 |
| Data Modeling | `powerbi/README.md` #2 |
| Calculated Fields | `powerbi/README.md` #3 (DAX measures) |

---

## Session 2 - Python + Cloud

| Sub-topic | Where it lives |
|---|---|
| Variables, operators, functions | Everywhere |
| Libraries, methods, refactoring | `symposium/utils/__init__.py` |
| Enum | `symposium/utils/python_showcase.py` (`Confidence`) |
| Tuples, dicts, sets | `python_showcase.py::comprehensions_demo` |
| Map, filter, reduce | `python_showcase.py::total_words` |
| Class + objects | `Persona`, `Symposium`, `Warehouse`, ... |
| Exceptions | Every I/O path (loader + orchestrator) |
| Overloading | `python_showcase.py::describe` (`functools.singledispatch`) |
| Iterators | `symposium/utils/__init__.py::iter_sentences` |
| Modules + packages | Whole `symposium/` package tree |
| Generators | `iter_sentences`, `chunk_by_sentences`, `rolling_window` |
| List / dict / set comprehensions | `python_showcase.py` |
| Regular expressions | `symposium/etl/transform/cleaner.py`, `persona_classifier.py`, `utils/__init__.py` |
| Serialization | `write_json` / `write_pickle` in `utils/__init__.py` |
| Partial functions | `python_showcase.py::round2` (`functools.partial`) |
| Closures | `symposium/utils/__init__.py::timed` and `retry` |
| Decorators | `@timed`, `@retry`, `@announce`, `@functools.wraps` |
| **Cloud fundamentals** | `docs/DEPLOYMENT.md` |
| Benefits of AWS | `docs/DEPLOYMENT.md` cost section |
| AWS services | `deployment/aws/` + `docs/DEPLOYMENT.md` #services-used |
| Compute / Storage / DB / Networking / Security / Management / Developer tools | Mapping in `docs/DEPLOYMENT.md` |
| Python DS libs (NumPy, Pandas, Matplotlib, sklearn) | `symposium/ml/*` |
| Preprocessing / visualization | `symposium/ml/clustering.py` PCA + `app/pages/4_ML_Playground.py` |
| Python for AI | `symposium/agents/` + `symposium/prompts/` |

---

## Session 3 - AI + ML + Prompt Engineering

| Sub-topic | Where it lives |
|---|---|
| AI + its types | `docs/ARCHITECTURE.md` + `app/pages/6_About.py` |
| AI Roadmap | `docs/ARCHITECTURE.md` (pipeline diagram) |
| ML + its types | `symposium/ml/` (each file's docstring) |
| Linear regression | `symposium/ml/agreement_regressor.py` |
| Classifications in ML | SVM + Naive Bayes + Logistic |
| AI vs ML | `app/pages/6_About.py` |
| Classification vs regression | Both classes side-by-side in `agreement_regressor.py` |
| Supervised | Every ML file (SVM, NB, Ridge, Logistic, NN) |
| Unsupervised | `clustering.py` (K-Means + PCA) |
| Training a model | `scripts/train_models.py` |
| Preparing data | `symposium/ml/datasets.py` |
| K-Nearest Neighbors | `symposium/ml/similar_turn_knn.py` |
| Naive Bayes | `symposium/ml/topic_naive_bayes.py` |
| Logistic Regression | `agreement_regressor.py::AgreementRegressor.clf` |
| Support Vector Machine | `symposium/ml/stance_svm.py` |
| Neural Networks | `symposium/ml/neural_debate_scorer.py` |
| TensorFlow | Same file (Keras Sequential) |
| K-Means Clustering | `symposium/ml/clustering.py` |
| Principal Component Analysis | Same file |
| K-Means + PCA impl | Same file + `app/pages/4_ML_Playground.py` |
| Prompt Engineering intro | `app/pages/5_Prompt_Lab.py` |
| Linguistics / Language Models | `symposium/agents/llm.py` (Gemini) |
| Prompt Engineering Mindset | `symposium/prompts/templates.py` |
| Zero shot + few shot prompts | `5_Prompt_Lab.py` (3 templates) |
| AI hallucinations | `SAFETY_GUARDRAILS` in `prompts/templates.py` |
| Vectors / text embeddings | `symposium/etl/transform/embedder.py` + `vectorstore/` |
| Generative AI use cases | `docs/ARCHITECTURE.md` |
| How LLMs work | `docs/ARCHITECTURE.md` + slides |
| NLP tasks | Debate synthesis, topic routing, stance classification |
| Fine-tuned / proprietary models | Discussion in `docs/COPILOT_WORKFLOW.md` |
| Mixing LLM flavors | Moderator is a different Gemini config from personas (temperature) |
| Data privacy / security | Guardrails in prompts + no PII in corpus |
| AI-Assisted Development | `docs/COPILOT_WORKFLOW.md` |
| CoPilot tools + integration | Same doc |
| VS Code / extensions | Same doc |
| Code completion / features / contexts / conversations | Same doc |
| Development workflow | Same doc |
| Task automation | `scripts/*.py` + PowerShell helper |
