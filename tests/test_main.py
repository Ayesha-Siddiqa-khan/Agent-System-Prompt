"""Comprehensive unit tests for the cloud-native FastAPI microservice and Agent Studio."""

import pytest
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import app, app_state


@pytest.fixture
def client():
    """Create a TestClient with application lifespan active."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint_html(client):
    """Verify GET / returns 200 OK and HTML content for web browsers."""
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Agent System Prompt Studio" in response.text


def test_root_endpoint_json(client):
    """Verify GET / with format=json returns service identity and environment."""
    response = client.get("/?format=json")
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
    client.get("/")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    assert len(response.text) > 0


def test_api_templates(client):
    """Verify GET /api/templates returns pre-configured battle-tested archetypes."""
    response = client.get("/api/templates")
    assert response.status_code == 200
    templates = response.json()
    assert "devops_architect" in templates
    assert "k8s_troubleshooter" in templates
    assert "security_auditor" in templates
    assert "code_reviewer" in templates


def test_api_generate_prompt(client):
    """Verify POST /api/generate-prompt synthesizes prompts and model payloads."""
    payload = {
        "persona": "devops_architect",
        "task_goal": "Configure automated canary deployments with Flagger and Istio.",
        "constraints": ["No downtime", "Zero static secrets"],
        "output_format": "markdown",
        "temperature": 0.2,
    }
    response = client.post("/api/generate-prompt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "system_prompt" in data
    assert "Flagger and Istio" in data["system_prompt"]
    assert data["token_estimate"] > 0
    assert "anthropic_format" in data
    assert "openai_format" in data


def test_api_validate_prompt(client):
    """Verify POST /api/validate-prompt audits prompts and returns quality scorecard."""
    sample_prompt = (
        "You are an Elite Cloud DevOps Architect. "
        "Strict rules: Never hardcode secrets. Follow zero-trust principles. "
        "Output format: Valid JSON only."
    )
    response = client.post("/api/validate-prompt", json={"prompt": sample_prompt})
    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 80
    assert data["has_role_definition"] is True
    assert data["has_constraints"] is True
    assert data["has_output_spec"] is True


def test_api_cluster_telemetry(client):
    """Verify GET /api/cluster-telemetry returns node and cluster health."""
    response = client.get("/api/cluster-telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert len(data["nodes"]) >= 2
    assert len(data["pods"]) >= 1


def test_hero_graphic_endpoint(client):
    """Verify GET /static/hero_graphic.jpg returns 200 OK and JPEG image data."""
    response = client.get("/static/hero_graphic.jpg")
    assert response.status_code == 200
    assert response.headers.get("content-type") == "image/jpeg"
    assert len(response.content) > 1000



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
