import pytest
from src.db.database import SessionLocal
from src.db.models import TranscriptChunk, ChunkEmbedding


def test_chunks_loaded():
    """Verify chunks were loaded into database."""
    db = SessionLocal()
    count = db.query(TranscriptChunk).count()
    db.close()
    assert count > 0, "No chunks loaded into database"


def test_embeddings_exist():
    """Verify embeddings were created for chunks."""
    db = SessionLocal()
    embedding_count = db.query(ChunkEmbedding).count()
    chunk_count = db.query(TranscriptChunk).count()
    db.close()
    assert embedding_count == chunk_count, f"Embedding count ({embedding_count}) != chunk count ({chunk_count})"


def test_chunk_has_required_fields():
    """Verify chunks have all required metadata."""
    db = SessionLocal()
    chunk = db.query(TranscriptChunk).first()
    db.close()
    assert chunk is not None, "No chunks in database"
    assert chunk.episode_title
    assert chunk.guest_name
    assert chunk.speaker_name
    assert chunk.timestamp
    assert chunk.content


def test_chunk_embedding_has_vector():
    """Verify embeddings have vector data."""
    db = SessionLocal()
    embedding = db.query(ChunkEmbedding).first()
    db.close()
    if embedding:
        assert embedding.embedding is not None, "Embedding vector is None"
        # Verify it's valid JSON
        import json
        try:
            vec = json.loads(embedding.embedding)
            assert isinstance(vec, list), "Embedding should be a list"
            assert len(vec) > 0, "Embedding should not be empty"
        except json.JSONDecodeError:
            pytest.fail("Embedding is not valid JSON")
