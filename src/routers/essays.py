import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from src.db.database import get_db
from src.db.models import Artifact, Message
from src.db.models import Session as SessionModel
from src.services.essay import EssayValidator
from src.services.llm import get_llm_provider
from src.services.retrieval import get_retrieval_service

router = APIRouter(prefix="/essays", tags=["essays"])
logger = logging.getLogger(__name__)


class EssayRequest(BaseModel):
    session_id: UUID
    provider: str = "cloud"


class EssayValidation(BaseModel):
    word_count_ok: bool
    has_headings: bool
    has_takeaway: bool
    has_citations: bool
    all_claims_traceable: bool
    compliance_passed: bool
    word_count: int


class EssayResponse(BaseModel):
    essay_text: str
    provider: str
    validation: EssayValidation
    artifact_id: UUID


@router.post("", response_model=EssayResponse)
async def generate_essay(request: EssayRequest, db: DBSession = Depends(get_db)):
    """Generate a Ship 30/30-style essay from conversation context."""

    session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.provider not in ("cloud", "local"):
        raise HTTPException(status_code=422, detail="provider must be 'cloud' or 'local'")

    messages = (
        db.query(Message)
        .filter(Message.session_id == request.session_id)
        .order_by(Message.created_at)
        .all()[-10:]
    )

    if not messages:
        raise HTTPException(status_code=400, detail="No conversation history for essay generation")

    try:
        retrieval_service = get_retrieval_service(db)
        user_messages = [m.content for m in messages if m.role == "user"]
        combined_query = " ".join(user_messages)
        chunks = retrieval_service.retrieve(combined_query, top_k=10)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        raise HTTPException(status_code=503, detail="Retrieval service unavailable") from e

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No relevant transcript material found for this conversation; cannot generate a grounded essay.",
        )

    try:
        llm_provider = get_llm_provider(request.provider)
        essay_text = llm_provider.generate_essay(messages, chunks)
    except ValueError as e:
        logger.error(f"Provider configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error(f"Provider error: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e

    validation = EssayValidator.validate(essay_text, chunks)

    artifact = Artifact(
        session_id=request.session_id,
        type="markdown",
        content=essay_text,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return EssayResponse(
        essay_text=essay_text,
        provider=request.provider,
        validation=EssayValidation(**validation),
        artifact_id=artifact.id,
    )
