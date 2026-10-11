import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["ok", "degraded"]

def test_document_upload_analysis():
    response = client.post(
        "/api/v1/analysis/upload",
        files={"file": ("test_srs.pdf", b"The system SHALL automatically lock user sessions after 15 minutes of inactivity.", "application/pdf")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["total_requirements"] == 3
    assert data["processed_requirements"] == 3
