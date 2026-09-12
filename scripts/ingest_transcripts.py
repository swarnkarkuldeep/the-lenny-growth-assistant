import os
import sys
import json
import logging
from pathlib import Path
from typing import List
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import settings
from src.db.database import SessionLocal
from src.db.models import TranscriptChunk, ChunkEmbedding
from src.services.chunker import chunk_episode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """Get embedding from Ollama."""
    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/embed",
            json={"model": "nomic-embed-text", "input": text},
            timeout=60
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise


def ingest_transcripts():
    """Load all transcripts from lennys-podcast-transcripts repo."""

    transcripts_dir = Path("./lennys-podcast-transcripts/episodes")
    if not transcripts_dir.exists():
        logger.error(f"Transcripts directory not found: {transcripts_dir}")
        logger.info("Please clone the repo: git clone https://github.com/ChatPRD/lennys-podcast-transcripts.git")
        return

    db = SessionLocal()

    try:
        # Clear existing data
        db.query(ChunkEmbedding).delete()
        db.query(TranscriptChunk).delete()
        db.commit()
        logger.info("Cleared existing chunks and embeddings")

        chunk_count = 0
        episode_count = 0
        error_count = 0

        episode_dirs = sorted([d for d in transcripts_dir.iterdir() if d.is_dir()])
        total_dirs = len(episode_dirs)

        for idx, episode_dir in enumerate(episode_dirs, 1):
            transcript_file = episode_dir / "transcript.md"
            if not transcript_file.exists():
                logger.warning(f"[{idx}/{total_dirs}] No transcript.md in {episode_dir.name}")
                continue

            logger.info(f"[{idx}/{total_dirs}] Processing {episode_dir.name}...")

            try:
                content = transcript_file.read_text(encoding='utf-8')
                chunks = chunk_episode(content)

                for chunk_data in chunks:
                    db_chunk = TranscriptChunk(**chunk_data)
                    db.add(db_chunk)
                    db.flush()

                    # Get embedding
                    embedding = get_embedding(chunk_data['content'])

                    # Store embedding as JSON string
                    db_embedding = ChunkEmbedding(
                        chunk_id=db_chunk.id,
                        embedding=json.dumps(embedding)
                    )
                    db.add(db_embedding)

                    chunk_count += 1

                db.commit()
                episode_count += 1
                logger.info(f"  ✓ {len(chunks)} chunks created")

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing {episode_dir.name}: {e}")
                db.rollback()

        logger.info(f"\n✓ Ingestion complete: {episode_count} episodes, {chunk_count} chunks")
        if error_count > 0:
            logger.warning(f"⚠ {error_count} episodes failed")

    finally:
        db.close()


if __name__ == "__main__":
    ingest_transcripts()
