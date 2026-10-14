import pytest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db
import app.services as services

# Test database setup (in-memory SQLite isolated from production)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Isolate database and generated PDF files for each test."""
    Base.metadata.create_all(bind=test_engine)
    
    # Point GENERATED_DIR to a temporary folder
    test_generated_dir = tmp_path / "test_generated"
    test_generated_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(services, "GENERATED_DIR", test_generated_dir)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bulk Certificate Generator API is running"}

def test_create_job(client):
    response = client.post("/jobs", json={
        "event_name": "Python Workshop",
        "date": "2026-10-08",
        "recipients": [
            {"name": "Rahul", "email": "rahul@example.com"},
            {"name": "Priya", "email": "priya@example.com"}
        ]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0
    assert data["status"] == "completed"
    assert len(data["certificates"]) == 2
    assert data["certificates"][0]["recipient_name"] == "Rahul"
    assert data["certificates"][0]["status"] == "success"
    assert data["certificates"][0]["download_url"] is not None

def test_input_validation(client):
    # Invalid email
    response = client.post("/jobs", json={
        "event_name": "Workshop",
        "date": "2026-10-08",
        "recipients": [{"name": "A", "email": "not-an-email"}]
    })
    assert response.status_code == 422

    # Whitespace only name
    response = client.post("/jobs", json={
        "event_name": "Workshop",
        "date": "2026-10-08",
        "recipients": [{"name": "   ", "email": "valid@example.com"}]
    })
    assert response.status_code == 422

    # Empty recipients list
    response = client.post("/jobs", json={
        "event_name": "Workshop",
        "date": "2026-10-08",
        "recipients": []
    })
    assert response.status_code == 422

def test_job_status(client):
    response = client.post("/jobs", json={
        "event_name": "Test",
        "date": "2026-10-08",
        "recipients": [{"name": "Kumar", "email": "kumar@example.com"}]
    })
    job_id = response.json()["job_id"]
    status = client.get(f"/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    assert status.json()["successful"] == 1

def test_job_not_found(client):
    response = client.get("/jobs/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

def test_get_certificate_pdf(client):
    create_resp = client.post("/jobs", json={
        "event_name": "Webinar",
        "date": "2026-10-08",
        "recipients": [{"name": "Ananya", "email": "ananya@example.com"}]
    })
    cert_id = create_resp.json()["certificates"][0]["id"]
    
    cert_resp = client.get(f"/certificates/{cert_id}")
    assert cert_resp.status_code == 200
    assert cert_resp.headers["content-type"] == "application/pdf"
    assert cert_resp.content.startswith(b"%PDF")

def test_certificate_not_found(client):
    response = client.get("/certificates/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate not found"

def test_certificate_status(client):
    create_resp = client.post("/jobs", json={
        "event_name": "Hackathon",
        "date": "2026-10-08",
        "recipients": [{"name": "Kiran", "email": "kiran@example.com"}]
    })
    cert_id = create_resp.json()["certificates"][0]["id"]

    status_resp = client.get(f"/certificates/{cert_id}/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["id"] == cert_id
    assert data["recipient_name"] == "Kiran"
    assert data["status"] == "success"
    assert data["download_url"] == f"/certificates/{cert_id}"

def test_get_job_certificates(client):
    create_resp = client.post("/jobs", json={
        "event_name": "AI Summit",
        "date": "2026-10-08",
        "recipients": [
            {"name": "Dev", "email": "dev@example.com"},
            {"name": "Sneha", "email": "sneha@example.com"}
        ]
    })
    job_id = create_resp.json()["job_id"]

    list_resp = client.get(f"/jobs/{job_id}/certificates")
    assert list_resp.status_code == 200
    certs = list_resp.json()
    assert len(certs) == 2
    assert certs[0]["recipient_name"] == "Dev"
    assert certs[1]["recipient_name"] == "Sneha"

def test_partial_failure_isolation(client):
    """Test that a failure for one recipient does not stop processing for others."""
    original_generate = services.generate_certificate

    def mock_generate(event_name, event_date, recipient_name, certificate_id):
        if recipient_name == "FailingUser":
            raise RuntimeError("Simulated PDF generation error")
        return original_generate(event_name, event_date, recipient_name, certificate_id)

    with patch("app.main.generate_certificate", side_effect=mock_generate):
        response = client.post("/jobs", json={
            "event_name": "Resilience Test",
            "date": "2026-10-08",
            "recipients": [
                {"name": "FailingUser", "email": "fail@example.com"},
                {"name": "SuccessUser", "email": "success@example.com"}
            ]
        })
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 2
        assert data["successful"] == 1
        assert data["failed"] == 1
        assert data["status"] == "completed"

        failed_cert = next(c for c in data["certificates"] if c["recipient_name"] == "FailingUser")
        assert failed_cert["status"] == "failed"
        assert "Simulated PDF generation error" in failed_cert["error"]
        assert failed_cert["download_url"] is None

        success_cert = next(c for c in data["certificates"] if c["recipient_name"] == "SuccessUser")
        assert success_cert["status"] == "success"
        assert success_cert["download_url"] is not None

def test_certificate_file_missing_on_disk(client):
    """Test that missing PDF on disk returns 404 instead of unhandled 500 error."""
    create_resp = client.post("/jobs", json={
        "event_name": "Deletion Test",
        "date": "2026-10-08",
        "recipients": [{"name": "Test User", "email": "test@example.com"}]
    })
    cert_id = create_resp.json()["certificates"][0]["id"]
    
    # Intentionally delete the generated file from disk
    file_path = services.GENERATED_DIR / f"certificate_{cert_id}.pdf"
    if file_path.exists():
        file_path.unlink()

    resp = client.get(f"/certificates/{cert_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Certificate file not found on disk"

