-- ============================================================================
--  PatientFlow AI - TRIGGERS
-- ============================================================================
--  Server-side invariants that would otherwise have to be enforced by every
--  application talking to the database.
-- ============================================================================

USE patientflow;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- trg_appointments_bi
-- BEFORE INSERT: auto-derive lead_time_days if the caller left it at 0,
-- and reject appointments scheduled in the far past (> 1 day ago) for the
-- "scheduled" status.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_appointments_bi $$
CREATE TRIGGER trg_appointments_bi
BEFORE INSERT ON appointments
FOR EACH ROW
BEGIN
    IF NEW.lead_time_days IS NULL OR NEW.lead_time_days = 0 THEN
        SET NEW.lead_time_days = GREATEST(DATEDIFF(NEW.appointment_time, NOW()), 0);
    END IF;

    IF NEW.status = 'scheduled'
       AND NEW.appointment_time < (NOW() - INTERVAL 1 DAY) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'appointment: cannot schedule more than 1 day in the past';
    END IF;

    IF NEW.status NOT IN ('scheduled', 'completed', 'cancelled', 'no_show') THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'appointment: invalid status';
    END IF;
END $$

-- ----------------------------------------------------------------------------
-- trg_appointments_au
-- AFTER UPDATE: keep patient counters in sync with observed history.
-- - Transitioning to 'completed'   -> increment prior_visits
-- - Transitioning to 'no_show'     -> increment prior_no_shows
-- - Reverting away from 'completed'/'no_show' -> decrement accordingly
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_appointments_au $$
CREATE TRIGGER trg_appointments_au
AFTER UPDATE ON appointments
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        -- new status counters
        IF NEW.status = 'completed' THEN
            UPDATE patients SET prior_visits = prior_visits + 1 WHERE id = NEW.patient_id;
        ELSEIF NEW.status = 'no_show' THEN
            UPDATE patients SET prior_no_shows = prior_no_shows + 1 WHERE id = NEW.patient_id;
        END IF;

        -- rollback counters when transitioning out
        IF OLD.status = 'completed' AND NEW.status <> 'completed' THEN
            UPDATE patients
               SET prior_visits = GREATEST(prior_visits - 1, 0)
             WHERE id = OLD.patient_id;
        END IF;
        IF OLD.status = 'no_show' AND NEW.status <> 'no_show' THEN
            UPDATE patients
               SET prior_no_shows = GREATEST(prior_no_shows - 1, 0)
             WHERE id = OLD.patient_id;
        END IF;
    END IF;
END $$

-- ----------------------------------------------------------------------------
-- trg_invoices_bu
-- BEFORE UPDATE: stamp paid_at automatically when status transitions to 'paid'.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_invoices_bu $$
CREATE TRIGGER trg_invoices_bu
BEFORE UPDATE ON invoices
FOR EACH ROW
BEGIN
    IF NEW.status = 'paid' AND OLD.status <> 'paid' AND NEW.paid_at IS NULL THEN
        SET NEW.paid_at = NOW();
    END IF;
    IF NEW.status <> 'paid' AND OLD.status = 'paid' THEN
        SET NEW.paid_at = NULL;
    END IF;
END $$

-- ----------------------------------------------------------------------------
-- trg_patients_bd
-- BEFORE DELETE: refuse to delete a patient that has any predictions logged;
-- forces the caller to soft-delete instead. Prevents accidental orphaning of
-- longitudinal ML data.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_patients_bd $$
CREATE TRIGGER trg_patients_bd
BEFORE DELETE ON patients
FOR EACH ROW
BEGIN
    DECLARE v_pred_count INT;
    SELECT COUNT(*) INTO v_pred_count FROM predictions WHERE patient_id = OLD.id;
    IF v_pred_count > 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'patient has prediction history; delete predictions first or soft-delete';
    END IF;
END $$

DELIMITER ;
