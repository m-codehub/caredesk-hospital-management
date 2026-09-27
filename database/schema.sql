PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    location TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 130),
    gender TEXT NOT NULL,
    phone TEXT NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    phone TEXT NOT NULL,
    department_id INTEGER REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'doctor', 'receptionist', 'patient')),
    patient_id INTEGER UNIQUE REFERENCES patients(id),
    doctor_id INTEGER UNIQUE REFERENCES doctors(id)
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    visit_date TEXT NOT NULL,
    visit_time TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Scheduled'
);

CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    record_date TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    medication TEXT NOT NULL,
    dosage TEXT NOT NULL,
    instructions TEXT NOT NULL DEFAULT '',
    prescribed_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    amount REAL NOT NULL CHECK (amount >= 0),
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS beds (
    id INTEGER PRIMARY KEY,
    bed_number TEXT NOT NULL UNIQUE,
    ward TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Available',
    patient_id INTEGER REFERENCES patients(id)
);

CREATE TABLE IF NOT EXISTS demo_seed_markers (
    name TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_records_patient ON medical_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_bills_patient ON bills(patient_id);