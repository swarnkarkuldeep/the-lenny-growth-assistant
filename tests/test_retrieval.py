import pytest
from src.db.database import SessionLocal
from src.services.retrieval import RetrievalService


def test_retrieve_returns_chunks():
    """Verify retrieval returns chunks for a query."""
    db = SessionLocal()
    service = RetrievalService(db)

    try:
        chunks = service.retrieve("product market fit", top_k=5)

        assert len(chunks) > 0, "Retrieval returned no chunks"
        assert len(chunks) <= 5, "Retrieval returned more than top_k"

        for chunk in chunks:
            assert chunk.episode_title
            assert chunk.speaker_name
            assert chunk.timestamp
            assert chunk.similarity_score > 0
    finally:
        db.close()


def test_retrieve_similarity_order():
    """Verify chunks are ordered by similarity."""
    db = SessionLocal()
    service = RetrievalService(db)

    try:
        chunks = service.retrieve("pricing strategy", top_k=10)

        if len(chunks) > 1:
            similarities = [c.similarity_score for c in chunks]
            assert similarities == sorted(similarities, reverse=True), "Chunks not ordered by similarity"
    finally:
        db.close()


def test_retrieve_respects_threshold():
    """Verify only chunks above threshold are returned."""
    db = SessionLocal()
    service = RetrievalService(db)

    try:
        chunks = service.retrieve("asdf qwerty zxcv gibberish xyz", top_k=10)

        # Should return few or no results for gibberish
        for chunk in chunks:
            assert chunk.similarity_score >= 0.5, f"Chunk similarity {chunk.similarity_score} below threshold"
    finally:
        db.close()


def test_retrieve_with_different_queries():
    """Verify retrieval works with different query types."""
    db = SessionLocal()
    service = RetrievalService(db)

    try:
        queries = [
            "product strategy",
            "user retention",
            "metrics",
            "go-to-market"
        ]

        for query in queries:
            chunks = service.retrieve(query, top_k=3)
            # Just verify no errors occur
            assert isinstance(chunks, list)
    finally:
        db.close()
