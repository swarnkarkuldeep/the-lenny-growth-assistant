import logging
import json
import requests
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.db.models import TranscriptChunk, ChunkEmbedding
from src.config import settings
from src.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class RetrievalService:
    """Semantic search over transcript chunks using pgvector."""

    def __init__(self, db: Session):
        self.db = db

    def embed_query(self, query: str) -> List[float]:
        """Get embedding for user query using Ollama."""
        try:
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/embed",
                json={"model": "nomic-embed-text", "input": query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]
        except Exception as e:
            logger.error(f"Embedding query error: {e}")
            raise

    def retrieve(self, query: str, top_k: int = None) -> List[RetrievedChunk]:
        """
        Retrieve top-k most similar chunks using pgvector semantic search.
        Returns chunks ordered by cosine similarity.
        """
        if top_k is None:
            top_k = settings.RETRIEVAL_TOP_K

        try:
            # Get query embedding
            embedding = self.embed_query(query)

            # Convert embedding to pgvector format
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

            # Semantic similarity search using pgvector cosine distance operator (<=>)
            results = self.db.execute(
                text("""
                    SELECT
                        tc.id,
                        tc.episode_title,
                        tc.guest_name,
                        tc.speaker_name,
                        tc.timestamp,
                        tc.content,
                        tc.video_url,
                        1 - (ce.embedding <=> :embedding::vector) as similarity
                    FROM chunk_embeddings ce
                    JOIN transcript_chunks tc ON ce.chunk_id = tc.id
                    WHERE 1 - (ce.embedding <=> :embedding::vector) > :threshold
                    ORDER BY similarity DESC
                    LIMIT :top_k
                """),
                {
                    "embedding": embedding_str,
                    "threshold": settings.SIMILARITY_THRESHOLD,
                    "top_k": top_k
                }
            ).fetchall()

            chunks = []
            for row in results:
                chunk = RetrievedChunk(
                    chunk_id=row[0],
                    episode_title=row[1],
                    guest_name=row[2],
                    speaker_name=row[3],
                    timestamp=row[4],
                    content=row[5],
                    video_url=row[6],
                    similarity_score=float(row[7])
                )
                chunks.append(chunk)

            logger.info(f"Retrieved {len(chunks)} chunks for query: {query[:50]}...")
            return chunks

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            raise


def get_retrieval_service(db: Session) -> RetrievalService:
    return RetrievalService(db)
