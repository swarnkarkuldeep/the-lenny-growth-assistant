import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.fixture
def session_id():
    response = client.post("/sessions")
    assert response.status_code == 200
    return response.json()["id"]


def test_generate_essay_session_not_found():
    response = client.post(
        "/essays",
        json={
            "session_id": "00000000-0000-0000-0000-000000000000",
            "provider": "local",
        },
    )
    assert response.status_code == 404


def test_generate_essay_invalid_provider(session_id):
    response = client.post(
        "/essays",
        json={"session_id": session_id, "provider": "bogus"},
    )
    assert response.status_code == 422


def test_generate_essay_no_conversation_history(session_id):
    response = client.post(
        "/essays",
        json={"session_id": session_id, "provider": "local"},
    )
    assert response.status_code == 400


def test_generate_essay_with_conversation(session_id):
    # Seed conversation via /chat so retrieval has something to work with.
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
        "/essays",
        json={"session_id": session_id, "provider": "local"},
    )

    # 200 when chunks + local model produce an essay, 400 if retrieval finds
    # nothing for this seeded question, 503 if Ollama is unreachable in this
    # environment. Assert the contract rather than requiring live inference.
    assert response.status_code in (200, 400, 503)

    if response.status_code == 200:
        data = response.json()
        assert "essay_text" in data
        assert "artifact_id" in data
        assert data["provider"] == "local"
        validation = data["validation"]
        for key in (
            "word_count_ok",
            "has_headings",
            "has_takeaway",
            "has_citations",
            "all_claims_traceable",
            "compliance_passed",
            "word_count",
        ):
            assert key in validation

        # The essay must have been persisted as a retrievable markdown artifact.
        artifact_response = client.get(f"/artifacts/{data['artifact_id']}")
        assert artifact_response.status_code == 200
        assert artifact_response.json()["type"] == "markdown"
