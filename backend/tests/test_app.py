from app import create_app


def test_health_endpoint():
    app = create_app()
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] in {"healthy", "degraded"}


def test_login_endpoint():
    app = create_app()
    client = app.test_client()
    response = client.post(
        "/api/auth/login",
        json={"email": "doctor@example.com", "password": "secret"},
    )
    assert response.status_code == 200
    assert response.json["role"] == "doctor"


def test_patients_endpoint():
    app = create_app()
    client = app.test_client()
    response = client.get("/api/patients")
    assert response.status_code == 200
    assert len(response.json["patients"]) >= 1
