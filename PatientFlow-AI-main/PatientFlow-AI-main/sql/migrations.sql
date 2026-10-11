-- ============================================================================
--  PatientFlow AI - MIGRATIONS
-- ============================================================================
--  Simple, hand-written forward migrations for teams that don't want to bring
--  in Alembic / Flyway. Each block is idempotent (uses IF NOT EXISTS or checks
--  information_schema) so re-running is safe.
--
--  Numbering: mYYYYMMDD_short_name  ->  each is a logical migration.
-- ============================================================================

USE patientflow;

-- ----------------------------------------------------------------------------
-- m20260101_create_migration_tracking
-- Bootstraps a tiny migration_log table so re-runs are auditable.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS migration_log (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    migration    VARCHAR(120) NOT NULL UNIQUE,
    applied_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note         VARCHAR(255) NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- m20260115_add_patient_contact_fields
-- Adds email + phone to patients (idempotent via information_schema check).
-- ----------------------------------------------------------------------------
SET @has_email := (
    SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name   = 'patients'
       AND column_name  = 'email');
SET @sql := IF(@has_email = 0,
    'ALTER TABLE patients ADD COLUMN email VARCHAR(120) NULL AFTER sex',
    'SELECT ''email column already present'' AS note');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_phone := (
    SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name   = 'patients'
       AND column_name  = 'phone');
SET @sql := IF(@has_phone = 0,
    'ALTER TABLE patients ADD COLUMN phone VARCHAR(32) NULL AFTER email',
    'SELECT ''phone column already present'' AS note');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

INSERT IGNORE INTO migration_log (migration, note)
VALUES ('m20260115_add_patient_contact_fields', 'email + phone on patients');

-- ----------------------------------------------------------------------------
-- m20260201_add_appointment_type_default_price
-- Adds default_price column to appointment_types.
-- ----------------------------------------------------------------------------
SET @has_price := (
    SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name   = 'appointment_types'
       AND column_name  = 'default_price');
SET @sql := IF(@has_price = 0,
    'ALTER TABLE appointment_types ADD COLUMN default_price FLOAT NOT NULL DEFAULT 0',
    'SELECT ''default_price already present'' AS note');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill sensible defaults if this column was just added
UPDATE appointment_types SET default_price = 500  WHERE id = 'consultation' AND default_price = 0;
UPDATE appointment_types SET default_price = 300  WHERE id = 'follow_up'    AND default_price = 0;
UPDATE appointment_types SET default_price = 1500 WHERE id = 'diagnostic'   AND default_price = 0;
UPDATE appointment_types SET default_price = 800  WHERE id = 'vaccination'  AND default_price = 0;
UPDATE appointment_types SET default_price = 2500 WHERE id = 'emergency'    AND default_price = 0;

INSERT IGNORE INTO migration_log (migration, note)
VALUES ('m20260201_add_appointment_type_default_price', 'pricing on appointment_types');

-- ----------------------------------------------------------------------------
-- m20260215_add_doctor_clinic_fk
-- Adds clinic_id + FK to doctors.
-- ----------------------------------------------------------------------------
SET @has_clinic := (
    SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND table_name   = 'doctors'
       AND column_name  = 'clinic_id');
SET @sql := IF(@has_clinic = 0,
    'ALTER TABLE doctors
       ADD COLUMN clinic_id INT NULL,
       ADD INDEX ix_doc_clinic (clinic_id),
       ADD CONSTRAINT fk_doc_clinic FOREIGN KEY (clinic_id)
           REFERENCES clinics(id) ON DELETE SET NULL',
    'SELECT ''doctors.clinic_id already present'' AS note');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

INSERT IGNORE INTO migration_log (migration, note)
VALUES ('m20260215_add_doctor_clinic_fk', 'link doctors -> clinics');

-- ----------------------------------------------------------------------------
-- m20260301_add_appointment_indexes
-- Adds two helpful indexes for common query patterns.
-- ----------------------------------------------------------------------------
SET @has_status_idx := (
    SELECT COUNT(*) FROM information_schema.statistics
     WHERE table_schema = DATABASE()
       AND table_name   = 'appointments'
       AND index_name   = 'ix_appt_status');
SET @sql := IF(@has_status_idx = 0,
    'ALTER TABLE appointments ADD INDEX ix_appt_status (status)',
    'SELECT ''ix_appt_status already exists'' AS note');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_patient_name_idx := (
    SELECT COUNT(*) FROM information_schema.statistics
     WHERE table_schema = DATABASE()
       AND table_name   = 'patients'
       AND index_name   = 'ix_patient_name');
SET @sql := IF(@has_patient_name_idx = 0,
    'ALTER TABLE patients ADD INDEX ix_patient_name (full_name)',
    'SELECT ''ix_patient_name already exists'' AS note');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

INSERT IGNORE INTO migration_log (migration, note)
VALUES ('m20260301_add_appointment_indexes', 'status + patient name indexes');

-- ----------------------------------------------------------------------------
-- m20260315_add_audit_log
-- Adds the audit_log table if missing (older installs pre-dated it).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    entity     VARCHAR(32)  NOT NULL,
    entity_id  VARCHAR(64)  NOT NULL,
    action     VARCHAR(16)  NOT NULL,
    diff_json  JSON         NULL,
    actor      VARCHAR(64)  NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_audit_entity (entity, entity_id),
    INDEX ix_audit_time   (created_at)
) ENGINE=InnoDB;

INSERT IGNORE INTO migration_log (migration, note)
VALUES ('m20260315_add_audit_log', 'audit_log table');

-- ----------------------------------------------------------------------------
-- Report installed migrations
-- ----------------------------------------------------------------------------
SELECT migration, applied_at, note FROM migration_log ORDER BY id;
