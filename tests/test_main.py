"""Comprehensive unit tests for the cloud-native FastAPI microservice."""

import pytest
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import app, app_state


@pytest.fixture
def client():
    """Create a TestClient with application lifespan active."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verify GET / returns service identity, environment, and 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["status"] == "running"
    assert "environment" in data
    assert "version" in data


def test_healthz_liveness_endpoint(client):
    """Verify GET /healthz returns 200 OK with alive status."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_ready_endpoint_success(client):
    """Verify GET /ready returns 200 OK when service is initialized."""
    app_state["is_ready"] = True
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_endpoint_not_ready(client):
    """Verify GET /ready returns 503 Service Unavailable when is_ready is False."""
    try:
        app_state["is_ready"] = False
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "not_ready"}
    finally:
        # Restore ready state for subsequent tests
        app_state["is_ready"] = True


def test_metrics_endpoint(client):
    """Verify GET /metrics returns 200 OK and Prometheus metrics format."""
    # Trigger a request to populate instrumented metrics
    client.get("/")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    assert len(response.text) > 0


def test_configuration_environment_override(monkeypatch):
    """Verify 12-factor configuration loads correctly from environment variables."""
    monkeypatch.setenv("PORT", "9090")
    monkeypatch.setenv("SERVICE_NAME", "custom-service")
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()
    assert settings.PORT == 9090
    assert settings.SERVICE_NAME == "custom-service"
    assert settings.ENVIRONMENT == "staging"
    assert settings.LOG_LEVEL == "DEBUG"
