from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_create_job():
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

def test_input_validation():
    response = client.post("/jobs", json={
        "event_name": "Workshop",
        "date": "2026-10-08",
        "recipients": [{"name": "A", "email": "not-an-email"}]
    })
    assert response.status_code == 422

def test_job_status():
    response = client.post("/jobs", json={
        "event_name": "Test",
        "date": "2026-10-08",
        "recipients": [{"name": "Kumar", "email": "kumar@example.com"}]
    })
    job_id = response.json()["job_id"]
    status = client.get(f"/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
