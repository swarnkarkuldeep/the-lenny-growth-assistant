from src.db.database import SessionLocal
from src.db.models import TranscriptChunk
from src.schemas import RetrievedChunk
from src.services.llm import get_llm_provider


def test_ollama_qa_response():
    """Test Ollama Q&A generation."""
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

    provider = get_llm_provider("local")
    response = provider.generate_qa_response("What is product strategy?", [retrieved_chunk])

    assert response
    assert len(response) > 10

    db.close()
