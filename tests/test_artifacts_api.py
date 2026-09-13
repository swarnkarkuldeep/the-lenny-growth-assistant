import pytest
from fastapi.testclient import TestClient

from src.db.database import SessionLocal
from src.db.models import Artifact
from src.main import app

client = TestClient(app)


@pytest.fixture
def session_id():
    response = client.post("/sessions")
    assert response.status_code == 200
    return response.json()["id"]


def test_get_artifact_not_found():
    response = client.get("/artifacts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_artifact_sanitizes_html(session_id):
    """A stored HTML artifact with a script tag must come back stripped."""
    db = SessionLocal()
    try:
        malicious_html = (
            "<h2>Findings</h2><script>alert('xss')</script>"
            "<p onclick=\"alert('xss')\">Click me</p>"
            "<iframe src='javascript:alert(1)'></iframe>"
        )
        artifact = Artifact(session_id=session_id, type="html", content=malicious_html)
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        artifact_id = str(artifact.id)
    finally:
        db.close()

    response = client.get(f"/artifacts/{artifact_id}")
    assert response.status_code == 200
    content = response.json()["content"]

    assert "<script" not in content
    assert "onclick" not in content
    assert "<iframe" not in content
    assert "<h2>Findings</h2>" in content


def test_get_artifact_markdown_passthrough(session_id):
    """Markdown artifacts are returned as-is (no HTML sanitization applied)."""
    db = SessionLocal()
    try:
        md_content = "## Heading\n\nSome **bold** text with a [citation, Ep, 00:01:00]."
        artifact = Artifact(session_id=session_id, type="markdown", content=md_content)
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        artifact_id = str(artifact.id)
    finally:
        db.close()

    response = client.get(f"/artifacts/{artifact_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "markdown"
    assert data["content"] == md_content


def test_generate_artifact_session_not_found():
    response = client.post(
        "/artifacts",
        json={
            "session_id": "00000000-0000-0000-0000-000000000000",
            "type": "markdown",
            "provider": "local",
        },
    )
    assert response.status_code == 404


def test_generate_artifact_invalid_type(session_id):
    response = client.post(
        "/artifacts",
        json={"session_id": session_id, "type": "pdf", "provider": "local"},
    )
    assert response.status_code == 422


def test_generate_artifact_no_conversation_history(session_id):
    response = client.post(
        "/artifacts",
        json={"session_id": session_id, "type": "markdown", "provider": "local"},
    )
    assert response.status_code == 400


def test_generate_html_artifact_is_sanitized_end_to_end(session_id):
    """Full pipeline: chat to seed context, then request an HTML artifact and
    confirm whatever comes back (real or degraded) is safe to render."""
    chat_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "What is product market fit?",
            "provider": "local",
        },
    )
    assert chat_response.status_code == 200

    response = client.post(
        "/artifacts",
        json={"session_id": session_id, "type": "html", "provider": "local"},
    )

    assert response.status_code in (200, 400, 503)

    if response.status_code == 200:
        data = response.json()
        assert data["type"] == "html"
        assert "<script" not in data["content"]
        assert "onclick" not in data["content"]
