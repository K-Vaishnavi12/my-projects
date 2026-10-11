-- ============================================================
-- 01_schema.sql : star-schema DDL for the Symposium DWH
-- ============================================================
-- Reference:
--   * Kimball star schema (fact tables in the middle, dims around)
--   * OLAP-oriented (write-once, read-many, aggregate-friendly)
--   * All PK/FK constraints are declared so the diagram is complete
--     even though SQLite enforces FKs only when PRAGMA is ON.
-- ============================================================

-- ---------- Dimension: topic ----------
CREATE TABLE IF NOT EXISTS dim_topic (
    topic_key       TEXT PRIMARY KEY,        -- 'history', 'science', ...
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Dimension: persona ----------
CREATE TABLE IF NOT EXISTS dim_persona (
    persona_key     TEXT PRIMARY KEY,        -- 'historian', 'scientist', ...
    name            TEXT NOT NULL,
    tagline         TEXT,
    color           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Dimension: document (source article) ----------
CREATE TABLE IF NOT EXISTS dim_document (
    doc_id          TEXT PRIMARY KEY,        -- stable_id('wiki', title)
    title           TEXT NOT NULL,
    url             TEXT,
    topic_key       TEXT NOT NULL,
    summary         TEXT,
    extracted_at    TEXT,
    loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_key) REFERENCES dim_topic(topic_key)
);
CREATE INDEX IF NOT EXISTS ix_doc_topic ON dim_document(topic_key);

-- ---------- Fact: chunk (grain = one chunk per row) ----------
CREATE TABLE IF NOT EXISTS fact_chunk (
    chunk_id            TEXT PRIMARY KEY,
    doc_id              TEXT NOT NULL,
    position            INTEGER NOT NULL,
    char_len            INTEGER NOT NULL,
    year_count          INTEGER NOT NULL DEFAULT 0,
    date_density        REAL NOT NULL,
    evidence_density    REAL NOT NULL,
    narrative_density   REAL NOT NULL,
    counter_density     REAL NOT NULL,
    reading_ease        REAL NOT NULL,
    avg_word_len        REAL NOT NULL,
    score_historian     REAL NOT NULL,
    score_scientist     REAL NOT NULL,
    score_poet          REAL NOT NULL,
    score_skeptic       REAL NOT NULL,
    score_child         REAL NOT NULL,
    loaded_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES dim_document(doc_id)
);
CREATE INDEX IF NOT EXISTS ix_chunk_doc  ON fact_chunk(doc_id);
CREATE INDEX IF NOT EXISTS ix_chunk_hist ON fact_chunk(score_historian);
CREATE INDEX IF NOT EXISTS ix_chunk_sci  ON fact_chunk(score_scientist);
CREATE INDEX IF NOT EXISTS ix_chunk_poet ON fact_chunk(score_poet);
CREATE INDEX IF NOT EXISTS ix_chunk_skep ON fact_chunk(score_skeptic);
CREATE INDEX IF NOT EXISTS ix_chunk_chld ON fact_chunk(score_child);

-- ---------- Fact: query (one row per debate the user runs) ----------
CREATE TABLE IF NOT EXISTS fact_query (
    query_id            TEXT PRIMARY KEY,
    question            TEXT NOT NULL,
    topic_key           TEXT,
    started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at            TIMESTAMP,
    consensus_score     REAL,
    moderator_summary   TEXT,
    FOREIGN KEY (topic_key) REFERENCES dim_topic(topic_key)
);
CREATE INDEX IF NOT EXISTS ix_query_topic ON fact_query(topic_key);

-- ---------- Fact: turn (one row per agent utterance) ----------
CREATE TABLE IF NOT EXISTS fact_turn (
    turn_id             TEXT PRIMARY KEY,
    query_id            TEXT NOT NULL,
    persona_key         TEXT NOT NULL,
    turn_index          INTEGER NOT NULL,
    content             TEXT NOT NULL,
    tokens              INTEGER,
    stance_label        TEXT,        -- 'agree' / 'disagree' / 'neutral'
    stance_score        REAL,        -- SVM confidence [0,1]
    agreement_score     REAL,        -- regression output [0,1]
    latency_ms          INTEGER,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES fact_query(query_id),
    FOREIGN KEY (persona_key) REFERENCES dim_persona(persona_key)
);
CREATE INDEX IF NOT EXISTS ix_turn_query   ON fact_turn(query_id);
CREATE INDEX IF NOT EXISTS ix_turn_persona ON fact_turn(persona_key);

-- ---------- Fact: retrieval (which chunks each turn used) ----------
CREATE TABLE IF NOT EXISTS fact_retrieval (
    turn_id     TEXT NOT NULL,
    chunk_id    TEXT NOT NULL,
    rank        INTEGER NOT NULL,
    similarity  REAL NOT NULL,
    PRIMARY KEY (turn_id, chunk_id),
    FOREIGN KEY (turn_id) REFERENCES fact_turn(turn_id),
    FOREIGN KEY (chunk_id) REFERENCES fact_chunk(chunk_id)
);
CREATE INDEX IF NOT EXISTS ix_ret_chunk ON fact_retrieval(chunk_id);

-- ============================================================
-- Metadata table (Data-Warehouse "metadata layer")
-- ============================================================
CREATE TABLE IF NOT EXISTS meta_pipeline_run (
    run_id      TEXT PRIMARY KEY,
    started_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at    TIMESTAMP,
    status      TEXT NOT NULL DEFAULT 'RUNNING',
    stats_json  TEXT
);
