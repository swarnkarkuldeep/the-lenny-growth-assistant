from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.routers.chat import validate_response_citations
from src.schemas import RetrievedChunk

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


@pytest.mark.parametrize(
    "response_text,expected",
    [
        ("I don't have information on this topic in the knowledge base.", True),
        ("Sorry, that's not in the knowledge base.", True),
        (
            "I don't see any relevant information in the retrieved chunks "
            "about the user's question. The chunks appear to be unrelated to the topic.",
            True,
        ),
        (
            "I'm happy to help, but I have to say that your question is a bit... "
            "unconventional. Unfortunately, I don't have any information on "
            '"asdf" in the retrieved chunks.',
            True,
        ),
        (
            "Product-market fit is [Lenny Rachitsky, Episode X, 00:01:00] "
            "the degree to which a product satisfies market demand.",
            True,
        ),
        ("Product-market fit is when your product satisfies the market.", False),
    ],
)
def test_validate_response_citations(response_text, expected):
    """Source attribution guardrail: a response must either cite a source
    or explicitly admit it can't answer, in wording either provider actually
    produces (Gemini follows the prompt's exact phrase; local Ollama paraphrases)."""
    assert validate_response_citations(response_text) is expected


def _chunk(speaker="Grenier", episode="When to invest in new acquisition channels"):
    return RetrievedChunk(
        chunk_id=uuid4(),
        episode_title=episode,
        guest_name="Adam Grenier",
        speaker_name=speaker,
        timestamp="00:00:00",
        content="...",
        video_url=None,
        similarity_score=0.7,
    )


def test_validate_response_citations_accepts_prose_style_citation():
    """The local model often grounds its answer correctly but writes the
    citation as prose/parentheses instead of the prompted bracket format,
    e.g. '(Grenier, "Episode Title", timestamp: 00:00:00)' - this must still
    count as attributed, since the model DID reference real retrieved evidence."""
    text = (
        "According to Adam Grenier, product market fit is a crucial concept "
        '(Grenier, "When to invest in new acquisition channels", timestamp: 00:00:00).'
    )
    assert validate_response_citations(text, [_chunk()]) is True


def test_validate_response_citations_rejects_untethered_mention():
    """A timestamp or speaker name appearing without the other - or without
    a real retrieved chunk backing it - must not be treated as a citation."""
    assert validate_response_citations("Product market fit is important.", [_chunk()]) is False
    assert validate_response_citations("Grenier has a lot of experience.", [_chunk()]) is False
    assert validate_response_citations("Something happened at 00:00:00.", [_chunk()]) is False
    assert validate_response_citations("According to Grenier at 00:00:00.", []) is False
