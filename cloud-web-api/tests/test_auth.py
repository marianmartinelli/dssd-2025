import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "local"}


def test_login_with_valid_credentials():
    """Test login with valid demo credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@example.org", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "wrong@example.org", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_with_invalid_email_format():
    """Test login with invalid email format."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "not-an-email", "password": "admin123"}
    )
    assert response.status_code == 422


def test_login_with_short_password():
    """Test login with password too short."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@example.org", "password": "123"}
    )
    assert response.status_code == 422


def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token."""
    response = client.post("/api/v1/projects", json={})
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token():
    """Test accessing protected endpoint with invalid token."""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.post("/api/v1/projects", json={}, headers=headers)
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token():
    """Test accessing protected endpoint with valid token."""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@example.org", "password": "admin123"}
    )
    token = login_response.json()["access_token"]
    
    # Try to access protected endpoint (will fail due to missing Bonita, but auth should work)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/projects",
        json={
            "projectName": "Test Project",
            "projectDescription": "A test project description that is long enough to pass validation.",
            "projectCategory": "Test",
            "requestingOrganization": "Test ONG",
            "contactEmail": "test@example.org",
            "estimatedBudget": 1000,
            "currency": "USD",
            "startDate": "2025-01-01",
            "endDate": "2025-12-31",
            "priorityLevel": "medium",
            "workPlanStages": [
                {
                    "stageName": "Test Stage",
                    "stageStart": "2025-01-01",
                    "stageEnd": "2025-01-15",
                    "supportType": "financial",
                    "description": "Test stage description"
                }
            ]
        },
        headers=headers
    )
    # Should not be 401 (auth should work), but may be 502 (Bonita connection issue)
    assert response.status_code != 401
