import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.fixture
def session_id():
    response = client.post("/sessions")
    assert response.status_code == 200
    return response.json()["id"]


def test_create_session():
    response = client.post("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "created_at" in data


def test_list_sessions(session_id):
    response = client.get("/sessions")
    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert session_id in ids


def test_get_session_not_found():
    response = client.get("/sessions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_delete_session(session_id):
    response = client.delete(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 404


def test_chat_session_not_found():
    response = client.post(
        "/chat",
        json={
            "session_id": "00000000-0000-0000-0000-000000000000",
            "message": "What is product market fit?",
            "provider": "local",
        },
    )
    assert response.status_code == 404


def test_chat_invalid_provider(session_id):
    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "What is product market fit?",
            "provider": "bogus",
        },
    )
    assert response.status_code == 422


def test_chat_with_local_provider_persists_messages(session_id):
    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "What is product market fit?",
            "provider": "local",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "message_id" in data
    assert data["response"]["provider"] == "local"

    detail = client.get(f"/sessions/{session_id}").json()
    roles = [m["role"] for m in detail["messages"]]
    assert roles == ["user", "assistant"]
