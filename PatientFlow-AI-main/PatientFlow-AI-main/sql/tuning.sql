-- ============================================================================
--  PatientFlow AI - PERFORMANCE TUNING GUIDE (in-SQL)
-- ============================================================================
--  A living checklist of index recommendations, EXPLAIN targets, and query
--  refactors that keep the database fast as it grows. Every recommendation
--  is written as a runnable SQL block so you can execute (or skip) each one
--  independently.
-- ============================================================================

USE patientflow;

-- ----------------------------------------------------------------------------
-- 1. Composite indexes for the most common access patterns
-- ----------------------------------------------------------------------------
-- (a) doctor + time range: "who is on doctor D's schedule this week?"
CREATE INDEX IF NOT EXISTS ix_appt_doctor_time
    ON appointments (doctor_id, appointment_time);

-- (b) patient + status: "show me this patient's completed history"
CREATE INDEX IF NOT EXISTS ix_appt_patient_status
    ON appointments (patient_id, status);

-- (c) invoices - unpaid past due
CREATE INDEX IF NOT EXISTS ix_inv_status_issued
    ON invoices (status, issued_at);

-- (d) predictions - filtering per appointment ordered by newest
CREATE INDEX IF NOT EXISTS ix_pred_appt_time
    ON predictions (appointment_id, created_at);


-- ----------------------------------------------------------------------------
-- 2. Recommended EXPLAIN targets
-- ----------------------------------------------------------------------------
-- Run EXPLAIN FORMAT=JSON on each of these to confirm we're using the indexes
-- above, and that no query is doing a full table scan on appointments.

EXPLAIN
SELECT * FROM v_appointment_full
WHERE appointment_time BETWEEN NOW() AND NOW() + INTERVAL 7 DAY;

EXPLAIN
SELECT * FROM appointments
WHERE doctor_id = 'D001_GenPrac_Sharma'
  AND appointment_time >= NOW()
ORDER BY appointment_time
LIMIT 20;

EXPLAIN
SELECT * FROM appointments
WHERE patient_id = 1 AND status = 'completed'
ORDER BY appointment_time DESC
LIMIT 20;

EXPLAIN
SELECT * FROM invoices
WHERE status = 'pending' AND issued_at < NOW() - INTERVAL 30 DAY;


-- ----------------------------------------------------------------------------
-- 3. Materialised summary tables (roll-ups for hot dashboards)
-- ----------------------------------------------------------------------------
-- The /stats endpoint hits base tables directly, which is fine at small scale.
-- Once you cross ~1M appointments, consider materialising a daily roll-up:
CREATE TABLE IF NOT EXISTS stats_daily (
    stat_date       DATE       NOT NULL PRIMARY KEY,
    appointments    INT        NOT NULL DEFAULT 0,
    completed       INT        NOT NULL DEFAULT 0,
    cancelled       INT        NOT NULL DEFAULT 0,
    no_show         INT        NOT NULL DEFAULT 0,
    revenue_paid    FLOAT      NOT NULL DEFAULT 0,
    revenue_pending FLOAT      NOT NULL DEFAULT 0,
    refreshed_at    DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Refresh procedure (call from a nightly EVENT or cron).
DELIMITER $$
DROP PROCEDURE IF EXISTS sp_refresh_stats_daily $$
CREATE PROCEDURE sp_refresh_stats_daily(IN p_from DATE, IN p_to DATE)
BEGIN
    DECLARE v_day DATE;
    SET v_day = p_from;

    WHILE v_day <= p_to DO
        REPLACE INTO stats_daily
            (stat_date, appointments, completed, cancelled, no_show,
             revenue_paid, revenue_pending, refreshed_at)
        SELECT
            v_day,
            COUNT(*),
            SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END),
            SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END),
            SUM(CASE WHEN a.status = 'no_show'   THEN 1 ELSE 0 END),
            COALESCE(SUM(CASE WHEN inv.status = 'paid'    THEN inv.amount END), 0),
            COALESCE(SUM(CASE WHEN inv.status = 'pending' THEN inv.amount END), 0),
            NOW()
        FROM appointments a
        LEFT JOIN invoices inv ON inv.appointment_id = a.id
        WHERE DATE(a.appointment_time) = v_day;

        SET v_day = v_day + INTERVAL 1 DAY;
    END WHILE;
END $$
DELIMITER ;

-- Example schedule: nightly rebuild of the last 7 days.
-- CREATE EVENT IF NOT EXISTS evt_refresh_stats_daily
--   ON SCHEDULE EVERY 1 DAY STARTS (TIMESTAMP(CURRENT_DATE) + INTERVAL 2 HOUR)
--   DO CALL sp_refresh_stats_daily(CURRENT_DATE - INTERVAL 7 DAY, CURRENT_DATE);


-- ----------------------------------------------------------------------------
-- 4. Partition strategy for very large predictions table
-- ----------------------------------------------------------------------------
-- Once `predictions` grows past ~10M rows, range-partition by created_at.
-- (Requires dropping any FKs that reference predictions.id first.)
--
-- ALTER TABLE predictions
--   PARTITION BY RANGE (TO_DAYS(created_at)) (
--     PARTITION p_hist   VALUES LESS THAN (TO_DAYS('2025-01-01')),
--     PARTITION p_2025q1 VALUES LESS THAN (TO_DAYS('2025-04-01')),
--     PARTITION p_2025q2 VALUES LESS THAN (TO_DAYS('2025-07-01')),
--     PARTITION p_2025q3 VALUES LESS THAN (TO_DAYS('2025-10-01')),
--     PARTITION p_2025q4 VALUES LESS THAN (TO_DAYS('2026-01-01')),
--     PARTITION p_future VALUES LESS THAN MAXVALUE
--   );


-- ----------------------------------------------------------------------------
-- 5. Slow-query hygiene
-- ----------------------------------------------------------------------------
-- Enable the slow query log in my.cnf:
--     slow_query_log = 1
--     long_query_time = 0.5
--     log_queries_not_using_indexes = 1
-- Then periodically inspect:
--     mysqldumpslow -s t -t 20 /var/lib/mysql/slow.log
-- Anything hitting appointments or predictions without one of the indexes
-- listed in section 1 is a candidate for review.


-- ----------------------------------------------------------------------------
-- 6. Storage settings we assume
-- ----------------------------------------------------------------------------
-- All base tables use ENGINE=InnoDB with row_format=DYNAMIC (MySQL 8 default).
-- Character set is utf8mb4 (4-byte UTF-8), collation utf8mb4_unicode_ci.
-- This gives us:
--   * transactional integrity via InnoDB
--   * emoji / non-BMP support in text fields (visit notes, prescriptions)
--   * case-insensitive but accent-aware search on names
