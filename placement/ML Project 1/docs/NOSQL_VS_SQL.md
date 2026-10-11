# SQL vs NoSQL in Symposium

The syllabus asks you to *compare* SQL and NoSQL. Symposium is a
rare project where BOTH are essential and their strengths are visible
side by side. Here's the honest scorecard.

## Where SQL wins (SQLite DWH)

- **Complex joins** across `fact_turn`, `fact_query`, `fact_retrieval`, `dim_document`, `dim_persona` for the "evidence trail" view.
- **Aggregation + window functions** for the "rolling consensus by topic" chart.
- **Referential integrity** — you can't have a `fact_retrieval` row pointing at a non-existent chunk (FK on).
- **Triggers** for audit + validation (see `03_views_triggers.sql`).
- **Ad-hoc analytics** — a data analyst opens SQLite Studio and writes SQL against the same schema Power BI already knows.
- **Small, portable** — a single file, no server.

## Where NoSQL wins (MongoDB)

- **Vector search** — first-class `$vectorSearch` operator with a KNN index. No relational database ships this.
- **Flexible schema** — chunk documents carry a dict of persona affinity scores and per-chunk metadata that changes as we add or remove personas. Adding a new persona doesn't require an `ALTER TABLE` migration.
- **Horizontal scale** — sharding across chunk collections is trivial with Atlas.
- **Per-collection filtering** — each persona has its own collection so the vector index is naturally scoped; no `WHERE` clause needed.
- **Rich nested fields** — `persona_scores` is a nested object, painful to model as SQL columns; trivial in Mongo.

## Where they meet

Every debate produces facts in BOTH stores:

- **SQL (facts + dims)**: `fact_turn`, `fact_retrieval` — how a debate unfolded, who spoke when, what evidence they used.
- **NoSQL (facts + semantic content)**: the chunks themselves plus their embeddings.

This is a modern **polyglot persistence** pattern: use the right database for the right job. The trade-off is operational complexity — you now run two systems. In this project we mitigate that by:

- centralising all writes in one Python module per store (`SqliteLoader`, `MongoLoader`)
- deterministic chunk IDs (`stable_id`) so a Mongo `chunk_id` always resolves to a SQL row and vice versa.

## Rule of thumb (adopt for real projects)

| Question you'll ask | Use |
|---|---|
| "How many turns did the Skeptic take last month, grouped by topic?" | **SQL** |
| "Find the 5 chunks most semantically similar to this new question." | **NoSQL / vector** |
| "What are the top-5 disagreement bursts across all debates?" | **SQL** window functions |
| "Give me the full text + metadata of chunk X." | **NoSQL** (nested docs are cheap) |
| "Enforce that every retrieval points at a valid chunk." | **SQL** FKs |
| "Add a 6th persona tomorrow." | **NoSQL** flexibility (add collection); regenerate the SQL score column via ALTER TABLE |
