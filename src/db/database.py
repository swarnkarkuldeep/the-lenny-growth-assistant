from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    # LLM generation requests can leave a pooled connection idle for minutes
    # (Ollama essay/artifact generation can take up to ~3 minutes). Docker's
    # networking silently drops long-idle TCP connections, which otherwise
    # surfaces as an inexplicable-looking error much later on an unrelated
    # query using the stale connection. pool_pre_ping does a cheap `SELECT 1`
    # before handing out a pooled connection and transparently reconnects if
    # it's dead, rather than failing the request on it.
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
