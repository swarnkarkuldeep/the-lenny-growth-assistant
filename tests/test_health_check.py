"""Tests for Milestone 1.2: Health Check & Ollama Setup"""
import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_endpoint_exists(self, client):
        """Test that /health endpoint responds."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Test that /health returns JSON."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)

    def test_health_includes_status(self, client):
        """Test that health response includes status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "degraded"]

    def test_health_checks_postgres(self, client):
        """Test that health checks Postgres."""
        response = client.get("/health")
        data = response.json()
        assert "postgres" in data
        assert isinstance(data["postgres"], str)

    def test_health_checks_ollama(self, client):
        """Test that health checks Ollama."""
        response = client.get("/health")
        data = response.json()
        assert "ollama" in data
        assert isinstance(data["ollama"], str)

    def test_health_checks_gemini_key(self, client):
        """Test that health checks Gemini API key configuration."""
        response = client.get("/health")
        data = response.json()
        assert "gemini_api_key" in data
        assert data["gemini_api_key"] in ["configured", "missing"]


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint_exists(self, client):
        """Test that root endpoint responds."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_json(self, client):
        """Test that root returns JSON."""
        response = client.get("/")
        data = response.json()
        assert isinstance(data, dict)

    def test_root_has_message(self, client):
        """Test that root response has message field."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
