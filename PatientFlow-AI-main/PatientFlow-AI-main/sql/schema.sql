-- PatientFlow AI - MySQL schema (fallback / reference).
-- The FastAPI app auto-creates these via SQLAlchemy on startup; this file
-- is provided for anyone who wants to provision the schema manually.

CREATE DATABASE IF NOT EXISTS patientflow
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE patientflow;

-- ============================ reference / auth ============================
CREATE TABLE IF NOT EXISTS clinics (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120) NOT NULL UNIQUE,
    city       VARCHAR(80)  NOT NULL,
    phone      VARCHAR(32)  NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(64)  NOT NULL UNIQUE,
    full_name     VARCHAR(120) NOT NULL,
    role          VARCHAR(16)  NOT NULL DEFAULT 'staff',
    password_hash VARCHAR(255) NOT NULL,
    is_active     TINYINT(1)   NOT NULL DEFAULT 1,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS doctors (
    id                VARCHAR(64)  NOT NULL PRIMARY KEY,
    specialty         VARCHAR(64)  NOT NULL,
    mean_service_min  FLOAT        NOT NULL,
    clinic_id         INT          NULL,
    INDEX ix_doc_clinic (clinic_id),
    CONSTRAINT fk_doc_clinic FOREIGN KEY (clinic_id) REFERENCES clinics(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS appointment_types (
    id             VARCHAR(32) NOT NULL PRIMARY KEY,
    no_show_base   FLOAT       NOT NULL,
    default_price  FLOAT       NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- ============================ operational =================================
CREATE TABLE IF NOT EXISTS patients (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(120) NOT NULL,
    age             INT          NOT NULL,
    sex             CHAR(1)      NOT NULL,
    email           VARCHAR(120) NULL,
    phone           VARCHAR(32)  NULL,
    has_insurance   TINYINT(1)   NOT NULL DEFAULT 1,
    prior_visits    INT          NOT NULL DEFAULT 0,
    prior_no_shows  INT          NOT NULL DEFAULT 0,
    sms_reminder    TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_patient_name (full_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS appointments (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    patient_id           INT          NOT NULL,
    doctor_id            VARCHAR(64)  NOT NULL,
    appointment_type_id  VARCHAR(32)  NOT NULL,
    appointment_time     DATETIME     NOT NULL,
    lead_time_days       INT          NOT NULL DEFAULT 0,
    status               VARCHAR(16)  NOT NULL DEFAULT 'scheduled',
    notes                TEXT         NULL,
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_appt_patient (patient_id),
    INDEX ix_appt_doctor  (doctor_id),
    INDEX ix_appt_time    (appointment_time),
    INDEX ix_appt_status  (status),
    CONSTRAINT fk_appt_patient FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    CONSTRAINT fk_appt_doctor  FOREIGN KEY (doctor_id)  REFERENCES doctors(id),
    CONSTRAINT fk_appt_type    FOREIGN KEY (appointment_type_id) REFERENCES appointment_types(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS visit_notes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id  INT           NOT NULL UNIQUE,
    chief_complaint VARCHAR(255)  NOT NULL,
    diagnosis       VARCHAR(255)  NULL,
    prescription    TEXT          NULL,
    follow_up_days  INT           NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_note_appt FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS invoices (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id  INT       NOT NULL UNIQUE,
    amount          FLOAT     NOT NULL,
    currency        CHAR(3)   NOT NULL DEFAULT 'INR',
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    issued_at       DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at         DATETIME  NULL,
    INDEX ix_inv_status (status),
    CONSTRAINT fk_inv_appt FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================ ML + audit ==================================
CREATE TABLE IF NOT EXISTS predictions (
    id                     INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id         INT NULL,
    patient_id             INT NULL,
    payload_json           JSON        NOT NULL,
    cancellation_prob      FLOAT       NOT NULL,
    cancellation_threshold FLOAT       NOT NULL,
    cancellation_flag      TINYINT(1)  NOT NULL,
    wait_p10               FLOAT       NOT NULL,
    wait_p50               FLOAT       NOT NULL,
    wait_p90               FLOAT       NOT NULL,
    interpretation         VARCHAR(255) NOT NULL,
    created_at             DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_pred_appt    (appointment_id),
    INDEX ix_pred_patient (patient_id),
    CONSTRAINT fk_pred_appt    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    CONSTRAINT fk_pred_patient FOREIGN KEY (patient_id)     REFERENCES patients(id)     ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recommendation_runs (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    patient_id     INT NULL,
    payload_json   JSON     NOT NULL,
    horizon_hours  INT      NOT NULL,
    step_minutes   INT      NOT NULL,
    top_k          INT      NOT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_run_patient (patient_id),
    CONSTRAINT fk_run_patient FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recommended_slots (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    run_id            INT          NOT NULL,
    `rank`            INT          NOT NULL,
    doctor_id         VARCHAR(64)  NOT NULL,
    appointment_time  DATETIME     NOT NULL,
    cancellation_prob FLOAT        NOT NULL,
    wait_p10          FLOAT        NOT NULL,
    wait_p50          FLOAT        NOT NULL,
    wait_p90          FLOAT        NOT NULL,
    score             FLOAT        NOT NULL,
    rationale         VARCHAR(255) NOT NULL,
    INDEX ix_slot_run (run_id),
    CONSTRAINT fk_slot_run FOREIGN KEY (run_id) REFERENCES recommendation_runs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

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
