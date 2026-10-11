-- ============================================================================
--  PatientFlow AI - VIEWS
-- ============================================================================
--  Reusable read-only projections layered on top of the base tables. Views
--  encapsulate common joins and make ad-hoc reporting from any BI tool
--  (Metabase, Superset, MySQL Workbench, Tableau) trivial.
--
--  Naming convention: v_<subject>_<qualifier>
-- ============================================================================

USE patientflow;

-- ----------------------------------------------------------------------------
-- v_patient_directory
-- Flat directory of patients with derived engagement fields.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_patient_directory;
CREATE VIEW v_patient_directory AS
SELECT
    p.id                                                        AS patient_id,
    p.full_name,
    p.age,
    p.sex,
    p.email,
    p.phone,
    p.has_insurance,
    p.sms_reminder,
    p.prior_visits,
    p.prior_no_shows,
    CASE
        WHEN p.prior_visits = 0 THEN NULL
        ELSE ROUND(p.prior_no_shows / p.prior_visits, 4)
    END                                                         AS historical_no_show_rate,
    p.created_at                                                AS registered_at,
    (SELECT MAX(a.appointment_time)
       FROM appointments a
      WHERE a.patient_id = p.id)                                AS last_appointment_time,
    (SELECT COUNT(*)
       FROM appointments a
      WHERE a.patient_id = p.id
        AND a.status = 'scheduled'
        AND a.appointment_time >= NOW())                        AS upcoming_appointments
FROM patients p;

-- ----------------------------------------------------------------------------
-- v_appointment_full
-- Fully denormalized appointment record: joins the entity graph so a single
-- SELECT gets you everything for one row (patient, doctor, clinic, type,
-- optional note, optional invoice, latest prediction).
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_appointment_full;
CREATE VIEW v_appointment_full AS
SELECT
    a.id                        AS appointment_id,
    a.appointment_time,
    a.status,
    a.lead_time_days,
    p.id                        AS patient_id,
    p.full_name                 AS patient_name,
    p.age,
    p.sex,
    p.has_insurance,
    d.id                        AS doctor_id,
    d.specialty,
    d.mean_service_min,
    c.id                        AS clinic_id,
    c.name                      AS clinic_name,
    c.city                      AS clinic_city,
    at.id                       AS appointment_type,
    at.default_price,
    vn.chief_complaint,
    vn.diagnosis,
    vn.follow_up_days,
    inv.amount                  AS invoice_amount,
    inv.currency                AS invoice_currency,
    inv.status                  AS invoice_status,
    latest_pred.cancellation_prob,
    latest_pred.wait_p50,
    a.created_at                AS booked_at
FROM appointments a
JOIN patients          p  ON p.id  = a.patient_id
JOIN doctors           d  ON d.id  = a.doctor_id
LEFT JOIN clinics      c  ON c.id  = d.clinic_id
JOIN appointment_types at ON at.id = a.appointment_type_id
LEFT JOIN visit_notes  vn ON vn.appointment_id = a.id
LEFT JOIN invoices     inv ON inv.appointment_id = a.id
LEFT JOIN (
    SELECT pr.appointment_id,
           pr.cancellation_prob,
           pr.wait_p50,
           ROW_NUMBER() OVER (
             PARTITION BY pr.appointment_id
             ORDER BY pr.created_at DESC
           ) AS rn
    FROM predictions pr
    WHERE pr.appointment_id IS NOT NULL
) latest_pred ON latest_pred.appointment_id = a.id AND latest_pred.rn = 1;

-- ----------------------------------------------------------------------------
-- v_doctor_kpi
-- Per-doctor operational KPIs: total load, completion rate, cancellation rate,
-- and average lead time on scheduled visits.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_doctor_kpi;
CREATE VIEW v_doctor_kpi AS
SELECT
    d.id                                                                    AS doctor_id,
    d.specialty,
    c.name                                                                  AS clinic_name,
    d.mean_service_min,
    COUNT(a.id)                                                             AS appointments_total,
    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END)                 AS appointments_completed,
    SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END)                 AS appointments_cancelled,
    SUM(CASE WHEN a.status = 'no_show'   THEN 1 ELSE 0 END)                 AS appointments_no_show,
    SUM(CASE WHEN a.status = 'scheduled' THEN 1 ELSE 0 END)                 AS appointments_scheduled,
    ROUND(
        SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(a.id), 0),
        4
    )                                                                       AS completion_rate,
    ROUND(
        SUM(CASE WHEN a.status IN ('cancelled', 'no_show') THEN 1 ELSE 0 END)
        / NULLIF(COUNT(a.id), 0),
        4
    )                                                                       AS attrition_rate,
    ROUND(AVG(a.lead_time_days), 2)                                         AS avg_lead_time_days
FROM doctors d
LEFT JOIN clinics      c ON c.id = d.clinic_id
LEFT JOIN appointments a ON a.doctor_id = d.id
GROUP BY d.id, d.specialty, c.name, d.mean_service_min;

-- ----------------------------------------------------------------------------
-- v_revenue_daily
-- Paid + pending invoice revenue rolled up per day of the appointment.
-- Useful as the source for a time-series revenue chart.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_revenue_daily;
CREATE VIEW v_revenue_daily AS
SELECT
    DATE(a.appointment_time)                                       AS day,
    inv.currency,
    COUNT(inv.id)                                                  AS invoices,
    SUM(CASE WHEN inv.status = 'paid'     THEN inv.amount ELSE 0 END) AS revenue_paid,
    SUM(CASE WHEN inv.status = 'pending'  THEN inv.amount ELSE 0 END) AS revenue_pending,
    SUM(CASE WHEN inv.status = 'refunded' THEN inv.amount ELSE 0 END) AS revenue_refunded
FROM invoices inv
JOIN appointments a ON a.id = inv.appointment_id
GROUP BY DATE(a.appointment_time), inv.currency;

-- ----------------------------------------------------------------------------
-- v_revenue_by_specialty
-- Revenue attributable to each specialty (routes via doctor).
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_revenue_by_specialty;
CREATE VIEW v_revenue_by_specialty AS
SELECT
    d.specialty,
    COUNT(inv.id)                                                     AS invoices,
    SUM(CASE WHEN inv.status = 'paid'    THEN inv.amount ELSE 0 END)  AS revenue_paid,
    SUM(CASE WHEN inv.status = 'pending' THEN inv.amount ELSE 0 END)  AS revenue_pending,
    ROUND(AVG(CASE WHEN inv.status = 'paid' THEN inv.amount END), 2)  AS avg_paid_amount
FROM doctors d
LEFT JOIN appointments a  ON a.doctor_id = d.id
LEFT JOIN invoices     inv ON inv.appointment_id = a.id
GROUP BY d.specialty;

-- ----------------------------------------------------------------------------
-- v_no_show_risk_watch
-- Patients with a historically-high no-show rate AND an upcoming appointment.
-- Ideal for a front-desk "call to confirm" work queue.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_no_show_risk_watch;
CREATE VIEW v_no_show_risk_watch AS
SELECT
    p.id                                             AS patient_id,
    p.full_name,
    p.phone,
    a.id                                             AS appointment_id,
    a.appointment_time,
    a.doctor_id,
    a.appointment_type_id,
    p.prior_visits,
    p.prior_no_shows,
    ROUND(p.prior_no_shows / NULLIF(p.prior_visits, 0), 4) AS historical_rate,
    latest_pred.cancellation_prob                     AS model_predicted_prob
FROM patients p
JOIN appointments a ON a.patient_id = p.id
LEFT JOIN (
    SELECT pr.appointment_id,
           pr.cancellation_prob,
           ROW_NUMBER() OVER (
             PARTITION BY pr.appointment_id
             ORDER BY pr.created_at DESC
           ) AS rn
    FROM predictions pr
) latest_pred ON latest_pred.appointment_id = a.id AND latest_pred.rn = 1
WHERE a.status = 'scheduled'
  AND a.appointment_time >= NOW()
  AND a.appointment_time <  NOW() + INTERVAL 7 DAY
  AND (
        (p.prior_visits > 0 AND p.prior_no_shows / p.prior_visits >= 0.20)
     OR latest_pred.cancellation_prob >= 0.30
      );

-- ----------------------------------------------------------------------------
-- v_prediction_calibration
-- Bucketed model calibration: how does predicted probability compare to
-- observed cancellation rate for appointments that already resolved?
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_prediction_calibration;
CREATE VIEW v_prediction_calibration AS
SELECT
    FLOOR(pr.cancellation_prob * 10) / 10                       AS prob_bucket,
    COUNT(*)                                                    AS n_predictions,
    ROUND(AVG(pr.cancellation_prob), 4)                         AS mean_predicted,
    ROUND(AVG(CASE
        WHEN a.status IN ('cancelled', 'no_show') THEN 1.0
        WHEN a.status = 'completed'               THEN 0.0
        ELSE NULL
      END), 4)                                                  AS observed_cancel_rate,
    SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END)     AS observed_cancelled,
    SUM(CASE WHEN a.status = 'no_show'   THEN 1 ELSE 0 END)     AS observed_no_show,
    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END)     AS observed_completed
FROM predictions pr
JOIN appointments a ON a.id = pr.appointment_id
WHERE a.status IN ('cancelled', 'no_show', 'completed')
GROUP BY FLOOR(pr.cancellation_prob * 10) / 10;

-- ----------------------------------------------------------------------------
-- v_audit_recent
-- The last 30 days of mutations with an entity-friendly display.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_audit_recent;
CREATE VIEW v_audit_recent AS
SELECT
    al.id,
    al.created_at,
    al.actor,
    al.action,
    al.entity,
    al.entity_id,
    JSON_EXTRACT(al.diff_json, '$')            AS diff_json
FROM audit_log al
WHERE al.created_at >= NOW() - INTERVAL 30 DAY
ORDER BY al.created_at DESC;

-- ----------------------------------------------------------------------------
-- v_clinic_snapshot
-- One-row-per-clinic overview: doctors, patients seen, upcoming appointments.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_clinic_snapshot;
CREATE VIEW v_clinic_snapshot AS
SELECT
    c.id                                              AS clinic_id,
    c.name                                            AS clinic_name,
    c.city,
    COUNT(DISTINCT d.id)                              AS doctors,
    COUNT(DISTINCT a.patient_id)                      AS distinct_patients,
    COUNT(a.id)                                       AS appointments_total,
    SUM(CASE
          WHEN a.status = 'scheduled'
           AND a.appointment_time >= NOW()
          THEN 1 ELSE 0
        END)                                          AS appointments_upcoming,
    SUM(CASE
          WHEN a.status = 'completed'
          THEN 1 ELSE 0
        END)                                          AS appointments_completed,
    ROUND(
      SUM(CASE WHEN inv.status = 'paid' THEN inv.amount ELSE 0 END),
      2)                                              AS revenue_paid
FROM clinics c
LEFT JOIN doctors      d   ON d.clinic_id  = c.id
LEFT JOIN appointments a   ON a.doctor_id  = d.id
LEFT JOIN invoices     inv ON inv.appointment_id = a.id
GROUP BY c.id, c.name, c.city;
