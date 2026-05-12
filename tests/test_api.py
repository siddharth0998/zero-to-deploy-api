from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint_returns_service_status():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Internal API",
        "status": "active",
    }


def test_data_endpoint_returns_expected_payload():
    response = client.get("/data")

    assert response.status_code == 200
    assert response.json() == {
        "items": ["unit_01", "unit_02"],
        "authorized": True,
    }


def test_health_endpoint_reports_environment(monkeypatch):
    monkeypatch.setenv("ENV", "test")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "test",
    }
