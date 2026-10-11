-- PatientFlow AI - example analytics queries.
-- These mirror what /stats returns, and can be run directly in the MySQL CLI
-- or any DB IDE (MySQL Workbench, DBeaver, etc).

USE patientflow;

-- ---------------------------------------------------------------------------
-- 1. Overview KPIs
-- ---------------------------------------------------------------------------
SELECT
    (SELECT COUNT(*) FROM patients)     AS patients,
    (SELECT COUNT(*) FROM appointments) AS appointments,
    (SELECT COUNT(*) FROM doctors)      AS doctors,
    (SELECT COUNT(*) FROM invoices)     AS invoices,
    (SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status = 'paid')    AS revenue_paid,
    (SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status = 'pending') AS revenue_pending;

-- ---------------------------------------------------------------------------
-- 2. Appointments by status
-- ---------------------------------------------------------------------------
SELECT status, COUNT(*) AS n
FROM appointments
GROUP BY status
ORDER BY n DESC;

-- ---------------------------------------------------------------------------
-- 3. Load per doctor (with completed / cancelled / no-show breakdown)
-- ---------------------------------------------------------------------------
SELECT
    d.id                                                            AS doctor_id,
    d.specialty,
    COUNT(a.id)                                                     AS total,
    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END)         AS completed,
    SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END)         AS cancelled,
    SUM(CASE WHEN a.status = 'no_show'   THEN 1 ELSE 0 END)         AS no_show
FROM doctors d
LEFT JOIN appointments a ON a.doctor_id = d.id
GROUP BY d.id, d.specialty
ORDER BY total DESC;

-- ---------------------------------------------------------------------------
-- 4. Revenue by appointment type
-- ---------------------------------------------------------------------------
SELECT
    at.id                              AS appointment_type,
    COUNT(i.id)                        AS invoices,
    COALESCE(SUM(i.amount), 0)         AS total_amount
FROM appointment_types at
LEFT JOIN appointments a ON a.appointment_type_id = at.id
LEFT JOIN invoices     i ON i.appointment_id      = a.id
GROUP BY at.id
ORDER BY total_amount DESC;

-- ---------------------------------------------------------------------------
-- 5. Top 5 no-show patients (observed, not the priors column)
-- ---------------------------------------------------------------------------
SELECT
    p.id, p.full_name, COUNT(*) AS observed_no_shows
FROM patients p
JOIN appointments a ON a.patient_id = p.id
WHERE a.status = 'no_show'
GROUP BY p.id, p.full_name
ORDER BY observed_no_shows DESC
LIMIT 5;

-- ---------------------------------------------------------------------------
-- 6. Model calibration: predicted vs observed cancellation rate, bucketed
-- ---------------------------------------------------------------------------
SELECT
    FLOOR(cancellation_prob * 10) / 10 AS prob_bucket,
    COUNT(*)                           AS predictions,
    AVG(cancellation_prob)             AS mean_predicted,
    AVG(CASE WHEN cancellation_flag THEN 1.0 ELSE 0.0 END) AS pct_flagged
FROM predictions
GROUP BY prob_bucket
ORDER BY prob_bucket;

-- ---------------------------------------------------------------------------
-- 7. Recent audit trail
-- ---------------------------------------------------------------------------
SELECT created_at, actor, action, entity, entity_id
FROM audit_log
ORDER BY created_at DESC
LIMIT 20;

-- ---------------------------------------------------------------------------
-- 8. Full patient timeline (appointments + notes + invoices) for one patient
-- ---------------------------------------------------------------------------
SELECT
    a.id                    AS appointment_id,
    a.appointment_time,
    a.doctor_id,
    a.appointment_type_id,
    a.status,
    vn.chief_complaint,
    vn.diagnosis,
    i.amount,
    i.status                AS invoice_status
FROM appointments a
LEFT JOIN visit_notes vn ON vn.appointment_id = a.id
LEFT JOIN invoices    i  ON i.appointment_id  = a.id
WHERE a.patient_id = 1                       -- <-- change patient id here
ORDER BY a.appointment_time DESC;
