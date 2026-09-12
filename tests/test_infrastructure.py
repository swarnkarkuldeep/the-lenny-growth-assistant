"""Tests for Phase 1: Infrastructure & Setup"""
import os
import pytest
from pathlib import Path


class TestDockerCompose:
    """Verify Docker Compose configuration."""

    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists."""
        assert Path("docker-compose.yml").exists(), "docker-compose.yml not found"

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        assert Path("Dockerfile").exists(), "Dockerfile not found"

    def test_env_example_exists(self):
        """Test that .env.example exists."""
        assert Path(".env.example").exists(), ".env.example not found"

    def test_docker_compose_has_services(self):
        """Test that docker-compose.yml defines required services."""
        import yaml
        with open("docker-compose.yml") as f:
            compose = yaml.safe_load(f)

        required_services = {"postgres", "ollama", "fastapi", "frontend"}
        assert "services" in compose, "services section not found"
        assert required_services.issubset(compose["services"].keys()), \
            f"Missing services. Got: {set(compose['services'].keys())}"

    def test_postgres_health_check(self):
        """Test that Postgres service has health check."""
        import yaml
        with open("docker-compose.yml") as f:
            compose = yaml.safe_load(f)

        postgres = compose["services"]["postgres"]
        assert "healthcheck" in postgres, "Postgres missing healthcheck"
        assert "test" in postgres["healthcheck"], "Healthcheck missing test"


class TestDatabaseModels:
    """Verify SQLAlchemy models are defined."""

    def test_models_file_exists(self):
        """Test that src/db/models.py exists."""
        assert Path("src/db/models.py").exists(), "src/db/models.py not found"

    def test_models_define_session(self):
        """Test that Session model is defined."""
        from src.db.models import Session
        assert Session is not None
        assert hasattr(Session, '__tablename__')
        assert Session.__tablename__ == "sessions"

    def test_models_define_message(self):
        """Test that Message model is defined."""
        from src.db.models import Message
        assert Message is not None
        assert hasattr(Message, '__tablename__')
        assert Message.__tablename__ == "messages"

    def test_models_define_transcript_chunk(self):
        """Test that TranscriptChunk model is defined."""
        from src.db.models import TranscriptChunk
        assert TranscriptChunk is not None
        assert hasattr(TranscriptChunk, '__tablename__')
        assert TranscriptChunk.__tablename__ == "transcript_chunks"

    def test_models_define_chunk_embedding(self):
        """Test that ChunkEmbedding model is defined."""
        from src.db.models import ChunkEmbedding
        assert ChunkEmbedding is not None
        assert hasattr(ChunkEmbedding, '__tablename__')
        assert ChunkEmbedding.__tablename__ == "chunk_embeddings"

    def test_models_define_artifact(self):
        """Test that Artifact model is defined."""
        from src.db.models import Artifact
        assert Artifact is not None
        assert hasattr(Artifact, '__tablename__')
        assert Artifact.__tablename__ == "artifacts"


class TestRequirements:
    """Verify dependencies are listed."""

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        assert Path("requirements.txt").exists(), "requirements.txt not found"

    def test_requirements_has_fastapi(self):
        """Test that requirements.txt includes FastAPI."""
        with open("requirements.txt") as f:
            content = f.read()
        assert "fastapi" in content.lower(), "fastapi not in requirements.txt"

    def test_requirements_has_sqlalchemy(self):
        """Test that requirements.txt includes SQLAlchemy."""
        with open("requirements.txt") as f:
            content = f.read()
        assert "sqlalchemy" in content.lower(), "sqlalchemy not in requirements.txt"

    def test_requirements_has_psycopg2(self):
        """Test that requirements.txt includes psycopg2."""
        with open("requirements.txt") as f:
            content = f.read()
        assert "psycopg2" in content.lower(), "psycopg2 not in requirements.txt"


class TestConfigModule:
    """Verify configuration module."""

    def test_config_file_exists(self):
        """Test that src/config.py exists."""
        assert Path("src/config.py").exists(), "src/config.py not found"

    def test_settings_class_exists(self):
        """Test that Settings class is defined."""
        from src.config import settings
        assert settings is not None


class TestGitignore:
    """Verify .gitignore is configured."""

    def test_gitignore_exists(self):
        """Test that .gitignore exists."""
        assert Path(".gitignore").exists(), ".gitignore not found"

    def test_gitignore_excludes_env(self):
        """Test that .gitignore excludes .env files."""
        with open(".gitignore") as f:
            content = f.read()
        assert ".env" in content, ".env not in .gitignore"
        assert "__pycache__" in content, "__pycache__ not in .gitignore"
