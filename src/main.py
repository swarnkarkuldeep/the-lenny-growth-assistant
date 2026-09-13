import logging
import requests
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from src.config import settings
from src.db.database import get_db
from src.routers import artifacts, chat, essays, sessions
from src.services.retrieval import get_retrieval_service

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lenny Growth Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(essays.router)
app.include_router(artifacts.router)

@app.get("/health")
async def health_check():
    """Check system health: database, Ollama, Gemini API key."""
    health = {
        "status": "ok",
        "postgres": "unknown",
        "ollama": "unknown",
        "gemini_api_key": "configured" if settings.GEMINI_API_KEY else "missing"
    }

    # Check Postgres
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        health["postgres"] = "connected"
    except Exception as e:
        health["postgres"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check Ollama
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            health["ollama"] = "connected"
        else:
            health["ollama"] = f"error: HTTP {response.status_code}"
            health["status"] = "degraded"
    except Exception as e:
        health["ollama"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Lenny Growth Assistant API"}


@app.post("/retrieve")
async def test_retrieve(query: str, db: DBSession = Depends(get_db)):
    """Test endpoint: retrieve chunks for a query."""
    service = get_retrieval_service(db)
    chunks = service.retrieve(query, top_k=5)
    return {
        "query": query,
        "chunks": chunks,
        "count": len(chunks)
    }
