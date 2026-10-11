-- ============================================================================
--  PatientFlow AI - REPORTING QUERIES
-- ============================================================================
--  Standard operational reports run by clinic administrators. Each query is
--  documented with its business purpose and can be scheduled (via cron / a BI
--  tool / MySQL EVENT) or run ad-hoc.
-- ============================================================================

USE patientflow;

-- ============================================================================
-- SECTION 1 - Daily operations
-- ============================================================================

-- R01. Today's appointment schedule, ordered by doctor and time.
SELECT
    a.appointment_time,
    d.id                    AS doctor,
    d.specialty,
    p.full_name             AS patient,
    a.appointment_type_id   AS type,
    a.status,
    inv.status              AS invoice_status,
    a.notes
FROM appointments a
JOIN doctors  d  ON d.id = a.doctor_id
JOIN patients p  ON p.id = a.patient_id
LEFT JOIN invoices inv ON inv.appointment_id = a.id
WHERE DATE(a.appointment_time) = CURDATE()
ORDER BY d.id, a.appointment_time;

-- R02. Doctor utilisation today (booked minutes / working minutes assumed 480).
SELECT
    d.id                                                     AS doctor,
    d.specialty,
    COUNT(a.id)                                              AS booked_visits,
    SUM(d.mean_service_min)                                  AS booked_minutes,
    ROUND(SUM(d.mean_service_min) / 480.0, 3)                AS utilisation_ratio
FROM doctors d
LEFT JOIN appointments a
       ON a.doctor_id = d.id
      AND DATE(a.appointment_time) = CURDATE()
      AND a.status IN ('scheduled', 'completed')
GROUP BY d.id, d.specialty
ORDER BY utilisation_ratio DESC;

-- R03. Front-desk work queue: high-risk upcoming visits (uses the view).
SELECT * FROM v_no_show_risk_watch
ORDER BY appointment_time;

-- R04. Overdue pending invoices (issued more than 30 days ago and unpaid).
SELECT
    i.id           AS invoice_id,
    i.amount,
    i.issued_at,
    p.full_name    AS patient,
    p.phone,
    a.appointment_time,
    a.status       AS appt_status
FROM invoices i
JOIN appointments a ON a.id = i.appointment_id
JOIN patients     p ON p.id = a.patient_id
WHERE i.status  = 'pending'
  AND i.issued_at < NOW() - INTERVAL 30 DAY
ORDER BY i.issued_at;


-- ============================================================================
-- SECTION 2 - Weekly / monthly analytics
-- ============================================================================

-- R05. Weekly appointment volume for the last 12 weeks.
SELECT
    YEARWEEK(a.appointment_time, 1)                        AS iso_yearweek,
    MIN(DATE(a.appointment_time))                          AS week_start,
    COUNT(*)                                               AS appointments,
    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
    SUM(CASE WHEN a.status = 'no_show'   THEN 1 ELSE 0 END) AS no_show
FROM appointments a
WHERE a.appointment_time >= NOW() - INTERVAL 12 WEEK
GROUP BY YEARWEEK(a.appointment_time, 1)
ORDER BY iso_yearweek;

-- R06. Monthly revenue trend (paid invoices, last 12 months).
SELECT
    DATE_FORMAT(inv.paid_at, '%Y-%m')             AS month,
    COUNT(*)                                       AS paid_invoices,
    SUM(inv.amount)                                AS revenue,
    ROUND(AVG(inv.amount), 2)                      AS avg_ticket
FROM invoices inv
WHERE inv.status = 'paid'
  AND inv.paid_at >= NOW() - INTERVAL 12 MONTH
GROUP BY DATE_FORMAT(inv.paid_at, '%Y-%m')
ORDER BY month;

-- R07. Specialty performance: completion + revenue by specialty.
SELECT
    d.specialty,
    COUNT(a.id)                                          AS appointments,
    ROUND(AVG(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END), 4)
                                                         AS completion_rate,
    SUM(CASE WHEN inv.status = 'paid' THEN inv.amount ELSE 0 END)
                                                         AS revenue_paid
FROM doctors d
LEFT JOIN appointments a  ON a.doctor_id = d.id
LEFT JOIN invoices     inv ON inv.appointment_id = a.id
GROUP BY d.specialty
ORDER BY revenue_paid DESC;

-- R08. Which appointment types drive the most no-shows (rate + volume)?
SELECT
    a.appointment_type_id,
    COUNT(*)                                                     AS total,
    SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END)        AS no_shows,
    ROUND(
        SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*),
        4)                                                       AS no_show_rate
FROM appointments a
WHERE a.status IN ('completed', 'cancelled', 'no_show')
GROUP BY a.appointment_type_id
ORDER BY no_show_rate DESC;


-- ============================================================================
-- SECTION 3 - Model-vs-reality (drift & calibration)
-- ============================================================================

-- R09. Calibration bucket view.
SELECT * FROM v_prediction_calibration ORDER BY prob_bucket;

-- R10. For each doctor, average predicted cancellation prob vs observed rate.
SELECT
    a.doctor_id,
    COUNT(*)                                             AS predictions,
    ROUND(AVG(pr.cancellation_prob), 4)                  AS mean_predicted,
    ROUND(AVG(CASE
        WHEN a.status IN ('cancelled', 'no_show') THEN 1.0
        WHEN a.status = 'completed'               THEN 0.0
    END), 4)                                             AS observed_rate,
    ROUND(AVG(pr.cancellation_prob) - AVG(CASE
        WHEN a.status IN ('cancelled', 'no_show') THEN 1.0
        WHEN a.status = 'completed'               THEN 0.0
    END), 4)                                             AS bias
FROM predictions pr
JOIN appointments a ON a.id = pr.appointment_id
WHERE a.status IN ('completed', 'cancelled', 'no_show')
GROUP BY a.doctor_id
ORDER BY ABS(
    AVG(pr.cancellation_prob) - AVG(CASE
        WHEN a.status IN ('cancelled', 'no_show') THEN 1.0
        WHEN a.status = 'completed'               THEN 0.0
    END)
) DESC;

-- R11. Wait-time prediction accuracy (needs actual_wait_min column, placeholder).
-- SELECT AVG(ABS(pr.wait_p50 - a.actual_wait_min)) AS mae_p50 ...


-- ============================================================================
-- SECTION 4 - Cohort & retention
-- ============================================================================

-- R12. Patient cohorts: month of first appointment vs retention 30/60/90 days.
WITH first_visit AS (
    SELECT patient_id, MIN(appointment_time) AS first_at
      FROM appointments
     WHERE status = 'completed'
     GROUP BY patient_id
)
SELECT
    DATE_FORMAT(fv.first_at, '%Y-%m')                       AS cohort_month,
    COUNT(*)                                                AS cohort_size,
    SUM(CASE WHEN a.appointment_time BETWEEN fv.first_at
                 AND fv.first_at + INTERVAL 30 DAY
             THEN 1 ELSE 0 END)                             AS retained_30d,
    SUM(CASE WHEN a.appointment_time BETWEEN fv.first_at
                 AND fv.first_at + INTERVAL 60 DAY
             THEN 1 ELSE 0 END)                             AS retained_60d,
    SUM(CASE WHEN a.appointment_time BETWEEN fv.first_at
                 AND fv.first_at + INTERVAL 90 DAY
             THEN 1 ELSE 0 END)                             AS retained_90d
FROM first_visit fv
LEFT JOIN appointments a
       ON a.patient_id = fv.patient_id
      AND a.status = 'completed'
      AND a.appointment_time > fv.first_at
GROUP BY DATE_FORMAT(fv.first_at, '%Y-%m')
ORDER BY cohort_month;

-- R13. Insurance vs cash: revenue split by insurance status.
SELECT
    p.has_insurance,
    COUNT(*)                                               AS appointments,
    ROUND(AVG(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END), 4)
                                                           AS no_show_rate,
    SUM(CASE WHEN inv.status = 'paid' THEN inv.amount ELSE 0 END)
                                                           AS revenue_paid
FROM patients      p
JOIN appointments  a   ON a.patient_id      = p.id
LEFT JOIN invoices inv ON inv.appointment_id = a.id
GROUP BY p.has_insurance;

-- R14. Age-band demand: which specialties do different age groups use?
SELECT
    CASE
        WHEN p.age < 18                        THEN '00-17'
        WHEN p.age BETWEEN 18 AND 34           THEN '18-34'
        WHEN p.age BETWEEN 35 AND 54           THEN '35-54'
        WHEN p.age BETWEEN 55 AND 74           THEN '55-74'
        ELSE                                        '75+'
    END                                        AS age_band,
    d.specialty,
    COUNT(*)                                   AS visits
FROM appointments a
JOIN patients p ON p.id = a.patient_id
JOIN doctors  d ON d.id = a.doctor_id
GROUP BY age_band, d.specialty
ORDER BY age_band, visits DESC;


-- ============================================================================
-- SECTION 5 - Data quality
-- ============================================================================

-- R15. Orphaned invoices (invoice status = 'paid' but appointment is cancelled).
SELECT
    i.id AS invoice_id, i.amount, i.status AS invoice_status,
    a.id AS appointment_id, a.status AS appointment_status
FROM invoices     i
JOIN appointments a ON a.id = i.appointment_id
WHERE i.status = 'paid'
  AND a.status IN ('cancelled', 'no_show');

-- R16. Patients with inconsistent priors (observed history != stored counters).
SELECT
    p.id, p.full_name,
    p.prior_visits    AS stored_visits,
    COALESCE(agg.visits, 0)   AS observed_visits,
    p.prior_no_shows  AS stored_no_shows,
    COALESCE(agg.no_shows, 0) AS observed_no_shows
FROM patients p
LEFT JOIN (
    SELECT patient_id,
           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS visits,
           SUM(CASE WHEN status = 'no_show'   THEN 1 ELSE 0 END) AS no_shows
      FROM appointments GROUP BY patient_id
) agg ON agg.patient_id = p.id
WHERE p.prior_visits   <> COALESCE(agg.visits, 0)
   OR p.prior_no_shows <> COALESCE(agg.no_shows, 0);

-- R17. Missing visit notes on completed appointments.
SELECT a.id AS appointment_id, a.appointment_time, a.doctor_id, a.patient_id
FROM appointments a
LEFT JOIN visit_notes vn ON vn.appointment_id = a.id
WHERE a.status = 'completed'
  AND vn.id IS NULL;
