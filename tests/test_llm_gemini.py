import pytest

from src.config import settings
from src.db.database import SessionLocal
from src.db.models import TranscriptChunk
from src.schemas import RetrievedChunk
from src.services.llm import get_llm_provider


@pytest.mark.skipif(not settings.GEMINI_API_KEY, reason="GEMINI_API_KEY not configured")
def test_gemini_qa_response():
    """Test Gemini Q&A generation."""
    db = SessionLocal()

    chunk = db.query(TranscriptChunk).first()
    assert chunk is not None, "No chunks in DB"

    retrieved_chunk = RetrievedChunk(
        chunk_id=chunk.id,
        episode_title=chunk.episode_title,
        guest_name=chunk.guest_name,
        speaker_name=chunk.speaker_name,
        timestamp=chunk.timestamp,
        content=chunk.content,
        video_url=chunk.video_url,
        similarity_score=1.0,
    )

    provider = get_llm_provider("cloud")
    response = provider.generate_qa_response("What is product strategy?", [retrieved_chunk])

    assert response
    assert len(response) > 10

    db.close()


def test_get_llm_provider_cloud_raises_without_key(monkeypatch):
    """Verify missing GEMINI_API_KEY raises a clear error."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_llm_provider("cloud")
