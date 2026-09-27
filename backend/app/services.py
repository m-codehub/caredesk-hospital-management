from __future__ import annotations

from datetime import datetime


def get_health():
    services = {
        "database": "healthy",
        "api": "healthy",
    }
    status = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"
    return status, services


def login_user(payload):
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        return {"error": {"code": "INVALID_CREDENTIALS", "message": "Email and password are required."}}, 401

    user = {
        "id": "1",
        "name": "Dr. Patel",
        "email": email,
        "role": "doctor",
    }
    return {"user": user, "token": "demo-token", "role": user["role"]}, 200


def get_patients():
    return [
        {
            "id": 1,
            "name": "Aisha Rahman",
            "doctor": "Dr. Patel",
            "lastVisit": "2026-09-26",
            "status": "Active",
            "dob": "1988-04-12",
            "phone": "+971 55 123 4567",
            "insurance": "Aster",
        },
        {
            "id": 2,
            "name": "Daniel Brooks",
            "doctor": "Dr. Singh",
            "lastVisit": "2026-09-25",
            "status": "Follow-up",
            "dob": "1992-06-18",
            "phone": "+971 50 987 6543",
            "insurance": "Daman",
        },
        {
            "id": 3,
            "name": "Noor Hassan",
            "doctor": "Dr. Carter",
            "lastVisit": "2026-09-24",
            "status": "Critical",
            "dob": "1979-11-03",
            "phone": "+971 56 503 1101",
            "insurance": "MedNet",
        },
    ]


def create_patient(payload):
    required = ["name", "dob", "phone", "insurance"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return {"error": {"code": "VALIDATION_ERROR", "message": "Missing required fields.", "details": missing}}, 400

    patient = {
        "id": 101,
        "name": payload["name"],
        "dob": payload["dob"],
        "phone": payload["phone"],
        "insurance": payload["insurance"],
        "doctor": "Dr. Patel",
        "lastVisit": datetime.utcnow().strftime("%Y-%m-%d"),
        "status": "New",
    }
    return {"patient": patient}, 201


def get_appointments():
    return [
        {"id": 1, "patient": "Leah Gomez", "doctor": "Dr. Patel", "time": "09:30 AM", "status": "Confirmed"},
        {"id": 2, "patient": "Sam Ali", "doctor": "Dr. Singh", "time": "11:00 AM", "status": "Pending"},
        {"id": 3, "patient": "Nadia Saleh", "doctor": "Dr. Carter", "time": "01:15 PM", "status": "Checked in"},
    ]


def create_appointment(payload):
    required = ["patientId", "doctorId", "date", "reason"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return {"error": {"code": "VALIDATION_ERROR", "message": "Missing required appointment fields.", "details": missing}}, 400

    appointment = {
        "id": 205,
        "patientId": payload["patientId"],
        "doctorId": payload["doctorId"],
        "date": payload["date"],
        "reason": payload["reason"],
        "status": "Scheduled",
    }
    return {"appointment": appointment}, 201


def get_medical_records(patient_id):
    if patient_id not in {"1", "2", "3"}:
        return {"error": {"code": "NOT_FOUND", "message": "Patient not found."}}, 404
    return {
        "records": [
            {"date": "2026-09-26", "type": "Consultation", "summary": "Follow-up for ongoing care."},
            {"date": "2026-09-15", "type": "Prescription", "summary": "Medication renewed."},
        ]
    }, 200


def get_billing():
    return [
        {"id": "INV-1001", "patient": "Aisha Rahman", "amount": 640, "status": "Paid"},
        {"id": "INV-1002", "patient": "Daniel Brooks", "amount": 290, "status": "Pending"},
    ]


def get_reports():
    return [
        {"id": "lab-1", "title": "CBC Summary", "status": "Normal"},
        {"id": "lab-2", "title": "Cardiology Review", "status": "Critical"},
    ]
