-- ============================================================
-- 03_views_triggers.sql : SQL Advanced concepts in action
-- ============================================================
-- The syllabus mentions Views, Triggers, Stored Procedures, and
-- Functions. SQLite supports Views + Triggers natively; stored
-- procedures are provided as *Python callables* in
-- symposium/dwh/warehouse.py (see class Warehouse) - a common
-- lightweight-DB pattern.
-- ============================================================

-- ------------------------------------------------------------
-- VIEW 1: v_persona_activity
-- Roll-up of how much airtime each persona gets across debates.
-- Uses aggregation, GROUP BY, and a JOIN to the persona dim.
-- ------------------------------------------------------------
DROP VIEW IF EXISTS v_persona_activity;
CREATE VIEW v_persona_activity AS
SELECT  p.persona_key,
        p.name AS persona_name,
        COUNT(t.turn_id)                          AS total_turns,
        COALESCE(AVG(t.stance_score), 0)          AS avg_stance_score,
        COALESCE(AVG(t.agreement_score), 0)       AS avg_agreement_score,
        COALESCE(AVG(t.latency_ms), 0)            AS avg_latency_ms
FROM    dim_persona p
LEFT    JOIN fact_turn t ON t.persona_key = p.persona_key
GROUP   BY p.persona_key, p.name;

-- ------------------------------------------------------------
-- VIEW 2: v_topic_debate_stats
-- Debates + turns per topic; how divisive each topic is.
-- ------------------------------------------------------------
DROP VIEW IF EXISTS v_topic_debate_stats;
CREATE VIEW v_topic_debate_stats AS
SELECT  q.topic_key,
        COUNT(DISTINCT q.query_id)                AS debates,
        COUNT(t.turn_id)                          AS turns,
        AVG(q.consensus_score)                    AS avg_consensus,
        MIN(q.consensus_score)                    AS min_consensus,
        MAX(q.consensus_score)                    AS max_consensus
FROM    fact_query q
LEFT    JOIN fact_turn t ON t.query_id = q.query_id
GROUP   BY q.topic_key;

-- ------------------------------------------------------------
-- VIEW 3: v_chunk_persona_leaderboard
-- Uses a WINDOW FUNCTION (syllabus topic) to rank chunks
-- inside each persona's claimed pool by affinity score.
-- ------------------------------------------------------------
DROP VIEW IF EXISTS v_chunk_persona_leaderboard;
CREATE VIEW v_chunk_persona_leaderboard AS
SELECT  c.chunk_id,
        d.title            AS doc_title,
        d.topic_key,
        'historian' AS persona_key,
        c.score_historian  AS affinity,
        RANK() OVER (PARTITION BY d.topic_key ORDER BY c.score_historian DESC) AS topic_rank
FROM    fact_chunk c JOIN dim_document d USING (doc_id)
UNION ALL
SELECT  c.chunk_id, d.title, d.topic_key, 'scientist',
        c.score_scientist,
        RANK() OVER (PARTITION BY d.topic_key ORDER BY c.score_scientist DESC)
FROM    fact_chunk c JOIN dim_document d USING (doc_id)
UNION ALL
SELECT  c.chunk_id, d.title, d.topic_key, 'poet',
        c.score_poet,
        RANK() OVER (PARTITION BY d.topic_key ORDER BY c.score_poet DESC)
FROM    fact_chunk c JOIN dim_document d USING (doc_id)
UNION ALL
SELECT  c.chunk_id, d.title, d.topic_key, 'skeptic',
        c.score_skeptic,
        RANK() OVER (PARTITION BY d.topic_key ORDER BY c.score_skeptic DESC)
FROM    fact_chunk c JOIN dim_document d USING (doc_id)
UNION ALL
SELECT  c.chunk_id, d.title, d.topic_key, 'child',
        c.score_child,
        RANK() OVER (PARTITION BY d.topic_key ORDER BY c.score_child DESC)
FROM    fact_chunk c JOIN dim_document d USING (doc_id);

-- ------------------------------------------------------------
-- VIEW 4: v_debate_evidence_trail
-- Denormalised report joining turns -> retrievals -> chunks -> docs
-- for the "trace" tab in the UI.
-- ------------------------------------------------------------
DROP VIEW IF EXISTS v_debate_evidence_trail;
CREATE VIEW v_debate_evidence_trail AS
SELECT  q.query_id,
        q.question,
        t.turn_id,
        t.persona_key,
        t.turn_index,
        r.rank        AS evidence_rank,
        r.similarity,
        c.chunk_id,
        d.title       AS source_title,
        d.url         AS source_url,
        d.topic_key
FROM    fact_query q
JOIN    fact_turn t          ON t.query_id = q.query_id
JOIN    fact_retrieval r     ON r.turn_id  = t.turn_id
JOIN    fact_chunk c         ON c.chunk_id = r.chunk_id
JOIN    dim_document d       ON d.doc_id   = c.doc_id;

-- ============================================================
-- TRIGGERS (auto-maintain aggregates + audit)
-- ============================================================

-- Audit table populated by triggers below.
CREATE TABLE IF NOT EXISTS audit_turn_log (
    audit_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    turn_id      TEXT NOT NULL,
    action       TEXT NOT NULL,
    ts           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TRIGGER IF EXISTS trg_turn_after_insert;
CREATE TRIGGER trg_turn_after_insert
AFTER INSERT ON fact_turn
BEGIN
    INSERT INTO audit_turn_log(turn_id, action) VALUES (NEW.turn_id, 'INSERT');
END;

DROP TRIGGER IF EXISTS trg_turn_after_update;
CREATE TRIGGER trg_turn_after_update
AFTER UPDATE ON fact_turn
BEGIN
    INSERT INTO audit_turn_log(turn_id, action) VALUES (NEW.turn_id, 'UPDATE');
END;

-- ------------------------------------------------------------
-- Cascading integrity guard trigger.
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_query_score_bounds;
CREATE TRIGGER trg_query_score_bounds
BEFORE UPDATE OF consensus_score ON fact_query
FOR EACH ROW
WHEN NEW.consensus_score IS NOT NULL
     AND (NEW.consensus_score < 0.0 OR NEW.consensus_score > 1.0)
BEGIN
    SELECT RAISE(ABORT, 'consensus_score must be within [0,1]');
END;
