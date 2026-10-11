-- ============================================================================
--  PatientFlow AI - SEED DATA (pure SQL)
-- ============================================================================
--  Idempotent seed script. Run this after schema.sql if you want to populate
--  the database from a plain MySQL client instead of relying on the API's
--  Python-side seeder. Uses INSERT ... ON DUPLICATE KEY UPDATE so it can be
--  re-run safely.
--
--  What it seeds:
--   * 3 clinics
--   * 2 users (admin / reception)   -- passwords hashed with SHA-256
--   * 5 appointment types           -- with default prices in INR
--   * 6 doctors                     -- across specialties, mapped to clinics
--   * 12 patients                   -- mixed demographics + priors
--   * 24 appointments               -- spread across past + future
--   * Visit notes + invoices for completed visits
-- ============================================================================

USE patientflow;

-- ---------------------------------------------------------------------------
-- clinics
-- ---------------------------------------------------------------------------
INSERT INTO clinics (id, name, city, phone) VALUES
    (1, 'Central Health Clinic',     'Bengaluru', '+91-80-1234-5678'),
    (2, 'Northside Medical Center',  'Delhi',     '+91-11-2345-6789'),
    (3, 'Harbor Family Practice',    'Mumbai',    '+91-22-3456-7890')
ON DUPLICATE KEY UPDATE
    city  = VALUES(city),
    phone = VALUES(phone);

-- ---------------------------------------------------------------------------
-- users  (passwords: admin/admin, reception/reception  - sha256 hashes)
-- ---------------------------------------------------------------------------
INSERT INTO users (username, full_name, role, password_hash, is_active) VALUES
    ('admin',     'System Admin',
     'admin',
     '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
     1),
    ('reception', 'Front Desk',
     'staff',
     'f76efdbf8bffdbe6c1d5f9294cffb69ec3d13d99e5b2d876a5c6f04d5c34a5c1',
     1)
ON DUPLICATE KEY UPDATE
    full_name = VALUES(full_name),
    role      = VALUES(role);

-- ---------------------------------------------------------------------------
-- appointment_types
-- ---------------------------------------------------------------------------
INSERT INTO appointment_types (id, no_show_base, default_price) VALUES
    ('consultation',  0.12,  500),
    ('follow_up',     0.15,  300),
    ('diagnostic',    0.10, 1500),
    ('vaccination',   0.08,  800),
    ('emergency',     0.05, 2500)
ON DUPLICATE KEY UPDATE
    no_show_base  = VALUES(no_show_base),
    default_price = VALUES(default_price);

-- ---------------------------------------------------------------------------
-- doctors
-- ---------------------------------------------------------------------------
INSERT INTO doctors (id, specialty, mean_service_min, clinic_id) VALUES
    ('D001_GenPrac_Sharma',    'General Practice',  15.0, 1),
    ('D002_Pediatrics_Iyer',   'Pediatrics',        18.0, 2),
    ('D003_Cardiology_Rao',    'Cardiology',        22.0, 3),
    ('D004_Orthopedics_Khan',  'Orthopedics',       20.0, 1),
    ('D005_Dermatology_Nair',  'Dermatology',       12.0, 2),
    ('D006_GenPrac_Menon',     'General Practice',  15.0, 3)
ON DUPLICATE KEY UPDATE
    specialty        = VALUES(specialty),
    mean_service_min = VALUES(mean_service_min),
    clinic_id        = VALUES(clinic_id);

-- ---------------------------------------------------------------------------
-- patients
-- ---------------------------------------------------------------------------
INSERT INTO patients
    (id, full_name, age, sex, email, phone,
     has_insurance, prior_visits, prior_no_shows, sms_reminder)
VALUES
    (1,  'Aarav Sharma',     34, 'M', 'aarav.sharma@example.com',   '+91-9812340001', 1, 4, 0, 1),
    (2,  'Priya Iyer',       29, 'F', 'priya.iyer@example.com',     '+91-9812340002', 1, 2, 1, 1),
    (3,  'Rohan Mehta',      52, 'M', 'rohan.mehta@example.com',    '+91-9812340003', 0, 8, 2, 0),
    (4,  'Sanya Kapoor',     41, 'F', 'sanya.kapoor@example.com',   '+91-9812340004', 1, 6, 0, 1),
    (5,  'Devansh Rao',       8, 'M', 'devansh.rao@example.com',    '+91-9812340005', 1, 3, 0, 1),
    (6,  'Meera Nair',       67, 'F', 'meera.nair@example.com',     '+91-9812340006', 1,12, 3, 0),
    (7,  'Kabir Singh',      23, 'M', 'kabir.singh@example.com',    '+91-9812340007', 0, 1, 1, 1),
    (8,  'Anaya Gupta',      45, 'F', 'anaya.gupta@example.com',    '+91-9812340008', 1, 5, 0, 1),
    (9,  'Vikram Reddy',     36, 'M', 'vikram.reddy@example.com',   '+91-9812340009', 1, 3, 1, 1),
    (10, 'Isha Chatterjee',  19, 'F', 'isha.chatterjee@example.com','+91-9812340010', 1, 0, 0, 1),
    (11, 'Karthik Menon',    58, 'M', 'karthik.menon@example.com',  '+91-9812340011', 0, 7, 2, 0),
    (12, 'Neha Bhatia',      31, 'F', 'neha.bhatia@example.com',    '+91-9812340012', 1, 2, 0, 1)
ON DUPLICATE KEY UPDATE
    full_name       = VALUES(full_name),
    age             = VALUES(age),
    sex             = VALUES(sex),
    email           = VALUES(email),
    phone           = VALUES(phone),
    has_insurance   = VALUES(has_insurance),
    prior_visits    = VALUES(prior_visits),
    prior_no_shows  = VALUES(prior_no_shows),
    sms_reminder    = VALUES(sms_reminder);

-- ---------------------------------------------------------------------------
-- appointments
-- Mix of past (completed / cancelled / no_show) and future (scheduled).
-- Times are expressed relative to NOW() so the seed stays meaningful.
-- ---------------------------------------------------------------------------
INSERT INTO appointments
    (id, patient_id, doctor_id, appointment_type_id,
     appointment_time, lead_time_days, status, notes)
VALUES
    -- past completed
    (101,  1, 'D001_GenPrac_Sharma',   'consultation', NOW() - INTERVAL 21 DAY, 3, 'completed', NULL),
    (102,  2, 'D002_Pediatrics_Iyer',  'follow_up',    NOW() - INTERVAL 18 DAY, 5, 'completed', NULL),
    (103,  3, 'D003_Cardiology_Rao',   'diagnostic',   NOW() - INTERVAL 16 DAY, 7, 'completed', NULL),
    (104,  4, 'D004_Orthopedics_Khan', 'consultation', NOW() - INTERVAL 14 DAY, 2, 'completed', NULL),
    (105,  5, 'D005_Dermatology_Nair', 'follow_up',    NOW() - INTERVAL 12 DAY, 3, 'completed', NULL),
    (106,  8, 'D006_GenPrac_Menon',    'consultation', NOW() - INTERVAL 10 DAY, 1, 'completed', NULL),
    (107,  9, 'D001_GenPrac_Sharma',   'vaccination',  NOW() - INTERVAL  9 DAY, 6, 'completed', NULL),
    (108, 12, 'D002_Pediatrics_Iyer',  'consultation', NOW() - INTERVAL  8 DAY, 2, 'completed', NULL),
    -- past cancelled
    (109,  6, 'D003_Cardiology_Rao',   'follow_up',    NOW() - INTERVAL 20 DAY, 4, 'cancelled', NULL),
    (110,  7, 'D005_Dermatology_Nair', 'consultation', NOW() - INTERVAL 15 DAY, 3, 'cancelled', NULL),
    -- past no_show
    (111,  3, 'D001_GenPrac_Sharma',   'follow_up',    NOW() - INTERVAL 25 DAY, 5, 'no_show',   NULL),
    (112, 11, 'D006_GenPrac_Menon',    'consultation', NOW() - INTERVAL 22 DAY, 2, 'no_show',   NULL),
    (113,  6, 'D003_Cardiology_Rao',   'diagnostic',   NOW() - INTERVAL 11 DAY, 3, 'no_show',   NULL),
    -- future scheduled
    (114,  1, 'D001_GenPrac_Sharma',   'consultation', NOW() + INTERVAL  2 DAY, 2, 'scheduled', NULL),
    (115,  2, 'D002_Pediatrics_Iyer',  'follow_up',    NOW() + INTERVAL  3 DAY, 3, 'scheduled', NULL),
    (116,  4, 'D004_Orthopedics_Khan', 'consultation', NOW() + INTERVAL  4 DAY, 4, 'scheduled', NULL),
    (117,  5, 'D002_Pediatrics_Iyer',  'vaccination',  NOW() + INTERVAL  5 DAY, 5, 'scheduled', NULL),
    (118,  8, 'D005_Dermatology_Nair', 'follow_up',    NOW() + INTERVAL  6 DAY, 6, 'scheduled', NULL),
    (119, 10, 'D001_GenPrac_Sharma',   'consultation', NOW() + INTERVAL  7 DAY, 7, 'scheduled', NULL),
    (120, 11, 'D003_Cardiology_Rao',   'diagnostic',   NOW() + INTERVAL  8 DAY, 8, 'scheduled', NULL),
    (121, 12, 'D006_GenPrac_Menon',    'consultation', NOW() + INTERVAL  9 DAY, 9, 'scheduled', NULL),
    (122,  9, 'D004_Orthopedics_Khan', 'follow_up',    NOW() + INTERVAL 10 DAY,10, 'scheduled', NULL),
    (123,  3, 'D001_GenPrac_Sharma',   'consultation', NOW() + INTERVAL 11 DAY, 3, 'scheduled', NULL),
    (124,  6, 'D003_Cardiology_Rao',   'emergency',    NOW() + INTERVAL  1 DAY, 0, 'scheduled', NULL)
ON DUPLICATE KEY UPDATE
    status = VALUES(status);

-- ---------------------------------------------------------------------------
-- visit_notes for completed appointments
-- ---------------------------------------------------------------------------
INSERT INTO visit_notes
    (appointment_id, chief_complaint, diagnosis, prescription, follow_up_days)
VALUES
    (101, 'fever',    'viral fever',    'paracetamol 500mg x5d',      7),
    (102, 'checkup',  'stable',         'rest + fluids',              NULL),
    (103, 'chest tightness', 'stable angina',
                     'atenolol 25mg x30d + follow-up ECG',            30),
    (104, 'back pain','muscle strain',  'ibuprofen 400mg x5d',        14),
    (105, 'rash',     'contact dermatitis',
                     'hydrocortisone cream',                          14),
    (106, 'follow-up','healthy',        NULL,                         NULL),
    (107, 'vaccine',  'immunization complete', NULL,                  NULL),
    (108, 'cough',    'URI',            'salbutamol syrup',           7)
ON DUPLICATE KEY UPDATE
    chief_complaint = VALUES(chief_complaint),
    diagnosis       = VALUES(diagnosis);

-- ---------------------------------------------------------------------------
-- invoices
-- Completed visits get 'paid' invoices, upcoming scheduled ones get 'pending'.
-- ---------------------------------------------------------------------------
INSERT INTO invoices
    (appointment_id, amount, currency, status, issued_at, paid_at)
VALUES
    (101,  500, 'INR', 'paid',    NOW() - INTERVAL 21 DAY, NOW() - INTERVAL 21 DAY),
    (102,  300, 'INR', 'paid',    NOW() - INTERVAL 18 DAY, NOW() - INTERVAL 18 DAY),
    (103, 1500, 'INR', 'paid',    NOW() - INTERVAL 16 DAY, NOW() - INTERVAL 16 DAY),
    (104,  500, 'INR', 'paid',    NOW() - INTERVAL 14 DAY, NOW() - INTERVAL 14 DAY),
    (105,  300, 'INR', 'paid',    NOW() - INTERVAL 12 DAY, NOW() - INTERVAL 12 DAY),
    (106,  500, 'INR', 'paid',    NOW() - INTERVAL 10 DAY, NOW() - INTERVAL 10 DAY),
    (107,  800, 'INR', 'paid',    NOW() - INTERVAL  9 DAY, NOW() - INTERVAL  9 DAY),
    (108,  500, 'INR', 'paid',    NOW() - INTERVAL  8 DAY, NOW() - INTERVAL  8 DAY),
    -- upcoming (pending)
    (114,  500, 'INR', 'pending', NOW(), NULL),
    (115,  300, 'INR', 'pending', NOW(), NULL),
    (116,  500, 'INR', 'pending', NOW(), NULL),
    (117,  800, 'INR', 'pending', NOW(), NULL),
    (118,  300, 'INR', 'pending', NOW(), NULL),
    (119,  500, 'INR', 'pending', NOW(), NULL),
    (120, 1500, 'INR', 'pending', NOW(), NULL),
    (121,  500, 'INR', 'pending', NOW(), NULL),
    (122,  300, 'INR', 'pending', NOW(), NULL),
    (123,  500, 'INR', 'pending', NOW(), NULL),
    (124, 2500, 'INR', 'pending', NOW(), NULL)
ON DUPLICATE KEY UPDATE
    amount = VALUES(amount),
    status = VALUES(status);
