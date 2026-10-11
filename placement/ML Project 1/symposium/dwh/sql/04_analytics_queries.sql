-- ============================================================
-- 04_analytics_queries.sql : reference query library
-- ============================================================
-- NOT executed by the loader. These are the "canonical" analytical
-- queries used in the Streamlit dashboard + Power BI. Kept as a
-- .sql file so a reviewer / SME can grade the SQL directly.
-- ============================================================

-- ------------------------------------------------------------
-- Q1. Basic DQL: recent debates
-- ------------------------------------------------------------
SELECT  query_id, question, topic_key, consensus_score, started_at
FROM    fact_query
ORDER   BY started_at DESC
LIMIT   20;

-- ------------------------------------------------------------
-- Q2. Filtering + ordering
-- ------------------------------------------------------------
SELECT  persona_key, COUNT(*) AS turns
FROM    fact_turn
WHERE   stance_label = 'disagree'
GROUP   BY persona_key
ORDER   BY turns DESC;

-- ------------------------------------------------------------
-- Q3. Grouping + aggregation + HAVING
-- ------------------------------------------------------------
SELECT  d.topic_key,
        COUNT(c.chunk_id)                    AS chunks,
        AVG(c.evidence_density)              AS avg_evidence,
        AVG(c.narrative_density)             AS avg_narrative
FROM    fact_chunk c
JOIN    dim_document d USING (doc_id)
GROUP   BY d.topic_key
HAVING  chunks >= 5
ORDER   BY avg_evidence DESC;

-- ------------------------------------------------------------
-- Q4. JOIN + Subquery: which persona wins the most debates?
-- (Winner = highest avg agreement_score in that query)
-- ------------------------------------------------------------
WITH per_query AS (
    SELECT  query_id,
            persona_key,
            AVG(agreement_score) AS avg_agree
    FROM    fact_turn
    WHERE   agreement_score IS NOT NULL
    GROUP   BY query_id, persona_key
),
ranked AS (
    SELECT  query_id, persona_key, avg_agree,
            RANK() OVER (PARTITION BY query_id ORDER BY avg_agree DESC) AS rk
    FROM    per_query
)
SELECT  persona_key, COUNT(*) AS wins
FROM    ranked
WHERE   rk = 1
GROUP   BY persona_key
ORDER   BY wins DESC;

-- ------------------------------------------------------------
-- Q5. Window function: rolling 5-debate avg consensus per topic
-- ------------------------------------------------------------
SELECT  topic_key,
        query_id,
        started_at,
        consensus_score,
        AVG(consensus_score) OVER (
            PARTITION BY topic_key
            ORDER BY started_at
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS rolling5_avg
FROM    fact_query
WHERE   consensus_score IS NOT NULL
ORDER   BY topic_key, started_at;

-- ------------------------------------------------------------
-- Q6. Optimisation demo: EXPLAIN QUERY PLAN
-- ------------------------------------------------------------
EXPLAIN QUERY PLAN
SELECT  d.title, AVG(c.evidence_density)
FROM    fact_chunk c
JOIN    dim_document d ON d.doc_id = c.doc_id
WHERE   d.topic_key = 'science'
GROUP   BY d.title
ORDER   BY 2 DESC;

-- ------------------------------------------------------------
-- Q7. Automation hint: refresh the CSV exports for Power BI
-- (executed from Python's Warehouse.export_all_csv())
-- ------------------------------------------------------------
-- .mode csv
-- .headers on
-- .output data/exports/dim_persona.csv
-- SELECT * FROM dim_persona;
-- .output data/exports/fact_turn.csv
-- SELECT * FROM fact_turn;
