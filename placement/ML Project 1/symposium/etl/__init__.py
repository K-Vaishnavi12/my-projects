"""ETL package.

Layered on the classic **Extract -> Transform -> Load** pattern, with
sub-packages named exactly that way so the folder structure teaches
itself:

- ``extract``   - pull Wikipedia articles for the requested topics
- ``transform`` - clean, classify per persona, chunk, embed
- ``load``      - write to MongoDB (facts) and SQLite (dims + facts)

Orchestration lives in :func:`run_pipeline`, invoked by
``scripts/run_etl.py`` (or a real Airflow DAG in production).

Note: submodules are NOT eagerly imported so lightweight imports
(e.g. the persona classifier) work without installing every heavy
dependency (tensorflow, wikipedia-api, sentence-transformers).
Import ``symposium.etl.pipeline`` explicitly when you need the
orchestrator.
"""
