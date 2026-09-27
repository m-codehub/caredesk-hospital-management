import tempfile
import unittest
from pathlib import Path

from app import create_app
from database.db import connect, initialize_database


class HospitalAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "hospital.db"
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "DATABASE": str(database_path)})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def login(self, username, password):
        page = self.client.get("/login")
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        return self.client.post("/login", data={
            "username": username, "password": password, "csrf_token": csrf_token,
        }, follow_redirects=True)

    def test_login_redirects_to_role_dashboard(self):
        response = self.login("admin", "admin123")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hospital overview", response.data)

    def test_patient_cannot_open_staff_management(self):
        self.login("patient", "patient123")
        response = self.client.get("/module/staff")
        self.assertEqual(response.status_code, 403)

    def test_patient_sees_only_their_appointments(self):
        self.login("patient", "patient123")
        response = self.client.get("/module/appointments")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Jamie Morgan", response.data)
        self.assertNotIn(b"Alex Rivera", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.json, {"status": "ok"})

    def test_every_module_has_sample_data_and_seeding_is_idempotent(self):
        tables = (
            "departments", "doctors", "staff", "patients", "appointments",
            "medical_records", "prescriptions", "bills", "beds",
        )
        with connect(self.app.config["DATABASE"]) as connection:
            counts_before = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in tables
            }
        self.assertTrue(all(count > 0 for count in counts_before.values()), counts_before)

        initialize_database(self.app.config["DATABASE"])

        with connect(self.app.config["DATABASE"]) as connection:
            counts_after = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in tables
            }
        self.assertEqual(counts_after, counts_before)

    def test_admin_can_open_all_management_modules(self):
        self.login("admin", "admin123")
        for module_key in (
            "patients", "doctors", "staff", "departments", "appointments",
            "medical_records", "prescriptions", "billing", "beds",
        ):
            with self.subTest(module=module_key):
                self.assertEqual(self.client.get(f"/module/{module_key}").status_code, 200)
        self.assertEqual(self.client.get("/reports").status_code, 200)

    def test_patient_cannot_create_medical_records(self):
        self.login("patient", "patient123")
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = self.client.post("/module/medical_records", data={"csrf_token": csrf_token})
        self.assertEqual(response.status_code, 403)

    def test_patient_can_book_appointment_for_self(self):
        self.login("patient", "patient123")
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = self.client.post("/module/appointments", data={
            "csrf_token": csrf_token,
            "patient_id": "2",
            "doctor_id": "1",
            "visit_date": "2099-01-01",
            "visit_time": "09:30",
            "reason": "Patient booking test",
            "status": "Completed",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with connect(self.app.config["DATABASE"]) as connection:
            saved = connection.execute(
                "SELECT patient_id, status FROM appointments WHERE reason = 'Patient booking test'"
            ).fetchone()
        self.assertEqual(saved["patient_id"], 1)
        self.assertEqual(saved["status"], "Scheduled")

    def test_patient_can_pay_only_their_own_bill(self):
        self.login("patient", "patient123")
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        with connect(self.app.config["DATABASE"]) as connection:
            connection.execute(
                "INSERT INTO bills(patient_id, amount, due_date) VALUES (2, 30, '2099-01-01')"
            )
        response = self.client.post("/module/billing/1/pay", data={"csrf_token": csrf_token})
        self.assertEqual(response.status_code, 302)
        response = self.client.post("/module/billing/2/pay", data={"csrf_token": csrf_token})
        self.assertEqual(response.status_code, 404)
        with connect(self.app.config["DATABASE"]) as connection:
            status = connection.execute("SELECT status FROM bills WHERE id = 1").fetchone()["status"]
        self.assertEqual(status, "Paid")

    def test_reception_cannot_edit_doctors_or_departments(self):
        self.login("reception", "reception123")
        for module_key in ("doctors", "departments"):
            with self.subTest(module=module_key):
                response = self.client.get(f"/module/{module_key}")
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(b"Add ", response.data)
                with self.client.session_transaction() as session:
                    csrf_token = session["csrf_token"]
                response = self.client.post(f"/module/{module_key}", data={"csrf_token": csrf_token})
                self.assertEqual(response.status_code, 403)

    def test_admin_cannot_add_prescriptions(self):
        self.login("admin", "admin123")
        response = self.client.get("/module/prescriptions")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Add prescriptions record", response.data)
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = self.client.post("/module/prescriptions", data={"csrf_token": csrf_token})
        self.assertEqual(response.status_code, 403)

    def test_admin_can_edit_department(self):
        self.login("admin", "admin123")
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = self.client.post("/module/departments/1/edit", data={
            "csrf_token": csrf_token,
            "name": "Cardiology Updated",
            "location": "West Wing",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with connect(self.app.config["DATABASE"]) as connection:
            department = connection.execute("SELECT name, location FROM departments WHERE id = 1").fetchone()
        self.assertEqual((department["name"], department["location"]), ("Cardiology Updated", "West Wing"))

    def test_reception_cannot_open_doctor_or_department_edit_pages(self):
        self.login("reception", "reception123")
        for module_key, record_id in (("doctors", 1), ("departments", 1)):
            with self.subTest(module=module_key):
                response = self.client.get(f"/module/{module_key}/{record_id}/edit")
                self.assertEqual(response.status_code, 403)

    def test_doctor_cannot_register_patients(self):
        self.login("doctor", "doctor123")
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = self.client.post("/module/patients", data={"csrf_token": csrf_token})
        self.assertEqual(response.status_code, 403)

    def test_doctor_cannot_create_appointment_for_another_doctor(self):
        self.login("doctor", "doctor123")
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = self.client.post("/module/appointments", data={
            "csrf_token": csrf_token,
            "patient_id": "1",
            "doctor_id": "2",
            "visit_date": "2099-01-01",
            "visit_time": "09:00",
            "reason": "Ownership test",
            "status": "Scheduled",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with connect(self.app.config["DATABASE"]) as connection:
            saved = connection.execute(
                "SELECT doctor_id FROM appointments WHERE reason = 'Ownership test'"
            ).fetchone()
        self.assertEqual(saved["doctor_id"], 1)


if __name__ == "__main__":
    unittest.main()