import sqlite3
from contextlib import contextmanager
from pathlib import Path

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT / "database" / "hospital.db"


@contextmanager
def connect(db_path=DEFAULT_DB_PATH):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path=DEFAULT_DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as connection:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        connection.executescript(schema)
        if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            connection.executemany(
                "INSERT OR IGNORE INTO departments(name, location) VALUES (?, ?)",
                [("Cardiology", "North Wing"), ("General Medicine", "Main Building"),
                 ("Neurology", "East Wing"), ("Pediatrics", "South Wing")],
            )
            department_ids = {
                row["name"]: row["id"]
                for row in connection.execute("SELECT id, name FROM departments")
            }
            connection.executemany(
                "INSERT INTO doctors(name, specialty, phone, department_id) VALUES (?, ?, ?, ?)",
                [("Dr. Taylor Green", "Cardiology", "555-0201", department_ids["Cardiology"]),
                 ("Dr. Morgan Lee", "General Medicine", "555-0202", department_ids["General Medicine"])],
            )
            connection.executemany(
                "INSERT INTO patients(name, age, gender, phone, department_id) VALUES (?, ?, ?, ?, ?)",
                [("Jamie Morgan", 34, "Female", "555-0101", department_ids["Cardiology"]),
                 ("Alex Rivera", 52, "Male", "555-0102", department_ids["General Medicine"])],
            )
            connection.execute(
                "INSERT INTO staff(name, role, phone) VALUES (?, ?, ?)",
                ("Jordan Kim", "Receptionist", "555-0301"),
            )
            demo_users = [
                ("admin", "admin123", "admin", None, None),
                ("doctor", "doctor123", "doctor", None, 1),
                ("reception", "reception123", "receptionist", None, None),
                ("patient", "patient123", "patient", 1, None),
            ]
            connection.executemany(
                "INSERT INTO users(username, password_hash, role, patient_id, doctor_id) VALUES (?, ?, ?, ?, ?)",
                [(username, generate_password_hash(password), role, patient_id, doctor_id)
                 for username, password, role, patient_id, doctor_id in demo_users],
            )
            connection.executemany(
                "INSERT INTO appointments(patient_id, doctor_id, visit_date, visit_time, reason, status) "
                "VALUES (?, ?, date('now', '+1 day'), '10:30', ?, 'Scheduled')",
                [(1, 1, "Cardiology follow-up"), (2, 2, "Annual check-up")],
            )
            connection.execute(
                "INSERT INTO beds(bed_number, ward, status) VALUES ('A-101', 'North Wing', 'Available')"
            )
            connection.execute(
                "INSERT INTO bills(patient_id, amount, due_date, status) "
                "VALUES (1, 45.00, date('now', '+14 days'), 'Pending')"
            )

        seed_demo_records(connection)


def seed_demo_records(connection):
    marker = "sample-records-v1"
    if connection.execute("SELECT 1 FROM demo_seed_markers WHERE name = ?", (marker,)).fetchone():
        return

    connection.executemany(
        "INSERT OR IGNORE INTO departments(name, location) VALUES (?, ?)",
        [("Cardiology", "North Wing"), ("General Medicine", "Main Building"),
         ("Neurology", "East Wing"), ("Pediatrics", "South Wing")],
    )
    department_ids = {
        row["name"]: row["id"]
        for row in connection.execute("SELECT id, name FROM departments")
    }
    new_doctors = [
        ("Dr. Casey Nguyen", "Pediatrics", "555-0203", department_ids["Pediatrics"]),
        ("Dr. Avery Chen", "Neurology", "555-0204", department_ids["Neurology"]),
    ]
    connection.executemany(
        "INSERT INTO doctors(name, specialty, phone, department_id) VALUES (?, ?, ?, ?)", new_doctors
    )
    doctor_ids = {
        row["name"]: row["id"]
        for row in connection.execute(
            "SELECT id, name FROM doctors WHERE name IN ('Dr. Casey Nguyen', 'Dr. Avery Chen')"
        )
    }
    new_patients = [
        ("Morgan Chen", 27, "Female", "555-0103", department_ids["Pediatrics"]),
        ("Riley Brooks", 41, "Other", "555-0104", department_ids["Neurology"]),
        ("Drew Parker", 63, "Male", "555-0105", department_ids["General Medicine"]),
    ]
    connection.executemany(
        "INSERT INTO patients(name, age, gender, phone, department_id) VALUES (?, ?, ?, ?, ?)",
        new_patients,
    )
    patient_ids = {
        row["name"]: row["id"]
        for row in connection.execute(
            "SELECT id, name FROM patients WHERE name IN ('Morgan Chen', 'Riley Brooks', 'Drew Parker')"
        )
    }
    connection.executemany(
        "INSERT INTO users(username, password_hash, role, patient_id, doctor_id) VALUES (?, ?, ?, ?, ?)",
        [
            ("doctor2", generate_password_hash("doctor2123"), "doctor", None, doctor_ids["Dr. Casey Nguyen"]),
            ("doctor3", generate_password_hash("doctor3123"), "doctor", None, doctor_ids["Dr. Avery Chen"]),
            ("patient2", generate_password_hash("patient2123"), "patient", patient_ids["Morgan Chen"], None),
            ("patient3", generate_password_hash("patient3123"), "patient", patient_ids["Riley Brooks"], None),
            ("patient4", generate_password_hash("patient4123"), "patient", patient_ids["Drew Parker"], None),
        ],
    )
    connection.executemany(
        "INSERT INTO staff(name, role, phone) VALUES (?, ?, ?)",
        [("Robin Ellis", "Nurse", "555-0302"), ("Cameron Wells", "Technician", "555-0303")],
    )
    connection.executemany(
        "INSERT INTO appointments(patient_id, doctor_id, visit_date, visit_time, reason, status) "
        "VALUES (?, ?, date('now', ?), ?, ?, ?)",
        [
            (patient_ids["Morgan Chen"], doctor_ids["Dr. Casey Nguyen"], "+2 days", "09:15", "Wellness visit", "Scheduled"),
            (patient_ids["Riley Brooks"], doctor_ids["Dr. Avery Chen"], "+3 days", "13:45", "Neurology review", "Scheduled"),
            (patient_ids["Drew Parker"], 2, "+4 days", "11:00", "Routine check-up", "Checked in"),
        ],
    )
    connection.executemany(
        "INSERT INTO medical_records(patient_id, doctor_id, record_date, diagnosis, notes) "
        "VALUES (?, ?, date('now', '-7 days'), ?, ?)",
        [
            (patient_ids["Morgan Chen"], doctor_ids["Dr. Casey Nguyen"], "Seasonal allergies", "Sample record for classroom use."),
            (patient_ids["Riley Brooks"], doctor_ids["Dr. Avery Chen"], "Routine follow-up", "Fictional sample entry."),
        ],
    )
    connection.executemany(
        "INSERT INTO prescriptions(patient_id, doctor_id, medication, dosage, instructions, prescribed_date) "
        "VALUES (?, ?, ?, ?, ?, date('now', '-3 days'))",
        [
            (patient_ids["Morgan Chen"], doctor_ids["Dr. Casey Nguyen"], "Sample medication A", "10 mg", "Demo only: take as directed."),
            (patient_ids["Riley Brooks"], doctor_ids["Dr. Avery Chen"], "Sample medication B", "5 mg", "Demo only: follow clinician guidance."),
        ],
    )
    connection.executemany(
        "INSERT INTO bills(patient_id, amount, due_date, status) VALUES (?, ?, date('now', ?), ?)",
        [(patient_ids["Morgan Chen"], 125.50, "+14 days", "Pending"),
         (patient_ids["Riley Brooks"], 82.00, "+7 days", "Paid"),
         (patient_ids["Drew Parker"], 210.00, "+21 days", "Pending")],
    )
    connection.executemany(
        "INSERT INTO beds(bed_number, ward, status, patient_id) VALUES (?, ?, ?, ?)",
        [("A-102", "North Wing", "Occupied", patient_ids["Morgan Chen"]),
         ("B-201", "East Wing", "Available", None),
         ("B-202", "East Wing", "Maintenance", None)],
    )
    connection.execute("INSERT INTO demo_seed_markers(name) VALUES (?)", (marker,))