-- ============================================================================
--  PatientFlow AI - STORED PROCEDURES
-- ============================================================================
--  Encapsulates common multi-step operations that would otherwise require
--  several round-trips from the application. All procedures do their own
--  input validation and raise SIGNAL SQLSTATE '45000' on business-rule
--  violations so the API layer can surface a clean error message.
-- ============================================================================

USE patientflow;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- sp_book_appointment
-- Books a new appointment, auto-generates a pending invoice at the
-- appointment-type default price, and returns the new appointment id.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_book_appointment $$
CREATE PROCEDURE sp_book_appointment(
    IN  p_patient_id            INT,
    IN  p_doctor_id             VARCHAR(64),
    IN  p_appointment_type_id   VARCHAR(32),
    IN  p_appointment_time      DATETIME,
    IN  p_lead_time_days        INT,
    IN  p_notes                 TEXT,
    OUT p_new_appointment_id    INT
)
BEGIN
    DECLARE v_price       FLOAT;
    DECLARE v_exists      INT;

    -- ---- validation --------------------------------------------------------
    SELECT COUNT(*) INTO v_exists FROM patients WHERE id = p_patient_id;
    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'sp_book_appointment: unknown patient_id';
    END IF;

    SELECT COUNT(*) INTO v_exists FROM doctors WHERE id = p_doctor_id;
    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'sp_book_appointment: unknown doctor_id';
    END IF;

    SELECT default_price INTO v_price
      FROM appointment_types WHERE id = p_appointment_type_id;
    IF v_price IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'sp_book_appointment: unknown appointment_type_id';
    END IF;

    IF p_appointment_time <= NOW() THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'sp_book_appointment: appointment_time must be in the future';
    END IF;

    -- Optional: prevent double-booking the same doctor at the exact same time.
    SELECT COUNT(*) INTO v_exists
      FROM appointments
     WHERE doctor_id = p_doctor_id
       AND appointment_time = p_appointment_time
       AND status IN ('scheduled', 'completed');
    IF v_exists > 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'sp_book_appointment: doctor already booked at this time';
    END IF;

    -- ---- insert ------------------------------------------------------------
    INSERT INTO appointments
        (patient_id, doctor_id, appointment_type_id, appointment_time,
         lead_time_days, status, notes, created_at)
    VALUES
        (p_patient_id, p_doctor_id, p_appointment_type_id, p_appointment_time,
         COALESCE(p_lead_time_days, DATEDIFF(p_appointment_time, NOW())),
         'scheduled', p_notes, NOW());

    SET p_new_appointment_id = LAST_INSERT_ID();

    INSERT INTO invoices
        (appointment_id, amount, currency, status, issued_at)
    VALUES
        (p_new_appointment_id, v_price, 'INR', 'pending', NOW());

    INSERT INTO audit_log (entity, entity_id, action, diff_json, actor, created_at)
    VALUES ('appointment', CAST(p_new_appointment_id AS CHAR),
            'create',
            JSON_OBJECT(
              'patient_id', p_patient_id,
              'doctor_id',  p_doctor_id,
              'via',        'sp_book_appointment'),
            'system', NOW());
END $$

-- ----------------------------------------------------------------------------
-- sp_cancel_appointment
-- Cancels an appointment, voids any pending invoice, refunds any paid invoice.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_cancel_appointment $$
CREATE PROCEDURE sp_cancel_appointment(
    IN p_appointment_id INT,
    IN p_reason         VARCHAR(255)
)
BEGIN
    DECLARE v_status VARCHAR(16);

    SELECT status INTO v_status FROM appointments WHERE id = p_appointment_id;
    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'sp_cancel_appointment: appointment not found';
    END IF;
    IF v_status IN ('cancelled', 'no_show') THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'sp_cancel_appointment: already cancelled/no_show';
    END IF;

    UPDATE appointments
       SET status = 'cancelled',
           notes  = CONCAT(COALESCE(notes, ''),
                           IF(notes IS NULL OR notes = '', '', ' | '),
                           'cancelled: ',
                           COALESCE(p_reason, 'no reason given'))
     WHERE id = p_appointment_id;

    UPDATE invoices
       SET status = 'void'
     WHERE appointment_id = p_appointment_id
       AND status = 'pending';

    UPDATE invoices
       SET status  = 'refunded'
     WHERE appointment_id = p_appointment_id
       AND status = 'paid';

    INSERT INTO audit_log (entity, entity_id, action, diff_json, actor, created_at)
    VALUES ('appointment', CAST(p_appointment_id AS CHAR),
            'update',
            JSON_OBJECT('status', 'cancelled', 'reason', p_reason),
            'system', NOW());
END $$

-- ----------------------------------------------------------------------------
-- sp_mark_no_show
-- Marks a past scheduled appointment as no_show and bumps the patient's prior
-- counter so future model calls see the updated feature.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_mark_no_show $$
CREATE PROCEDURE sp_mark_no_show(IN p_appointment_id INT)
BEGIN
    DECLARE v_patient_id INT;
    DECLARE v_status     VARCHAR(16);
    DECLARE v_time       DATETIME;

    SELECT status, patient_id, appointment_time
      INTO v_status, v_patient_id, v_time
      FROM appointments WHERE id = p_appointment_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'sp_mark_no_show: not found';
    END IF;
    IF v_status <> 'scheduled' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'sp_mark_no_show: only scheduled visits';
    END IF;
    IF v_time > NOW() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'sp_mark_no_show: appointment not past yet';
    END IF;

    UPDATE appointments SET status = 'no_show' WHERE id = p_appointment_id;
    UPDATE patients SET prior_no_shows = prior_no_shows + 1 WHERE id = v_patient_id;
    UPDATE invoices SET status = 'void' WHERE appointment_id = p_appointment_id AND status = 'pending';

    INSERT INTO audit_log (entity, entity_id, action, diff_json, actor, created_at)
    VALUES ('appointment', CAST(p_appointment_id AS CHAR),
            'update',
            JSON_OBJECT('status', 'no_show'),
            'system', NOW());
END $$

-- ----------------------------------------------------------------------------
-- sp_complete_visit
-- Marks a scheduled appointment complete, upserts a visit note, and marks the
-- invoice paid at the given amount (or the default_price if not supplied).
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_complete_visit $$
CREATE PROCEDURE sp_complete_visit(
    IN p_appointment_id  INT,
    IN p_chief_complaint VARCHAR(255),
    IN p_diagnosis       VARCHAR(255),
    IN p_prescription    TEXT,
    IN p_follow_up_days  INT,
    IN p_amount_override FLOAT
)
BEGIN
    DECLARE v_status  VARCHAR(16);
    DECLARE v_type_id VARCHAR(32);
    DECLARE v_price   FLOAT;
    DECLARE v_amount  FLOAT;

    SELECT status, appointment_type_id
      INTO v_status, v_type_id
      FROM appointments WHERE id = p_appointment_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'sp_complete_visit: not found';
    END IF;
    IF v_status = 'completed' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'sp_complete_visit: already completed';
    END IF;

    SELECT default_price INTO v_price FROM appointment_types WHERE id = v_type_id;
    SET v_amount = COALESCE(p_amount_override, v_price, 0);

    UPDATE appointments SET status = 'completed' WHERE id = p_appointment_id;

    INSERT INTO visit_notes
        (appointment_id, chief_complaint, diagnosis, prescription, follow_up_days, created_at)
    VALUES
        (p_appointment_id, p_chief_complaint, p_diagnosis, p_prescription, p_follow_up_days, NOW())
    ON DUPLICATE KEY UPDATE
        chief_complaint = VALUES(chief_complaint),
        diagnosis       = VALUES(diagnosis),
        prescription    = VALUES(prescription),
        follow_up_days  = VALUES(follow_up_days);

    INSERT INTO invoices
        (appointment_id, amount, currency, status, issued_at, paid_at)
    VALUES
        (p_appointment_id, v_amount, 'INR', 'paid', NOW(), NOW())
    ON DUPLICATE KEY UPDATE
        status  = 'paid',
        amount  = VALUES(amount),
        paid_at = NOW();

    INSERT INTO audit_log (entity, entity_id, action, diff_json, actor, created_at)
    VALUES ('appointment', CAST(p_appointment_id AS CHAR),
            'update',
            JSON_OBJECT('status', 'completed', 'amount', v_amount),
            'system', NOW());
END $$

-- ----------------------------------------------------------------------------
-- sp_refresh_patient_priors
-- Recomputes prior_visits + prior_no_shows for one patient from the observed
-- appointment history. Useful as a nightly maintenance job.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_refresh_patient_priors $$
CREATE PROCEDURE sp_refresh_patient_priors(IN p_patient_id INT)
BEGIN
    UPDATE patients p
    SET p.prior_visits = (
            SELECT COUNT(*)
              FROM appointments a
             WHERE a.patient_id = p.id
               AND a.status = 'completed'
        ),
        p.prior_no_shows = (
            SELECT COUNT(*)
              FROM appointments a
             WHERE a.patient_id = p.id
               AND a.status = 'no_show'
        )
    WHERE p.id = p_patient_id;
END $$

-- ----------------------------------------------------------------------------
-- sp_refresh_all_priors
-- Same as above but for every patient. Safe as a nightly cron.
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_refresh_all_priors $$
CREATE PROCEDURE sp_refresh_all_priors()
BEGIN
    UPDATE patients p
       LEFT JOIN (
           SELECT patient_id,
                  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS visits,
                  SUM(CASE WHEN status = 'no_show'   THEN 1 ELSE 0 END) AS no_shows
             FROM appointments
            GROUP BY patient_id
       ) agg ON agg.patient_id = p.id
    SET p.prior_visits   = COALESCE(agg.visits, 0),
        p.prior_no_shows = COALESCE(agg.no_shows, 0);
END $$

DELIMITER ;
