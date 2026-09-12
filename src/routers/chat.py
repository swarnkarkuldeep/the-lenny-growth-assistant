import logging
import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from src.db.database import get_db
from src.db.models import Session as SessionModel, Message
from src.schemas import QAResponse, Citation
from src.services.llm import get_llm_provider
from src.services.retrieval import get_retrieval_service

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(r"\[(.*?),\s*(.*?),\s*(\d{2}:\d{2}:\d{2})\]")
NO_SUPPORT_PHRASES = ("don't have information", "not in the knowledge base")


class ChatRequest(BaseModel):
    session_id: UUID
    message: str
    provider: str = "cloud"


class ChatResponseBody(BaseModel):
    message_id: UUID
    response: QAResponse
    created_at: str


def extract_citations_from_response(response_text: str) -> list[Citation]:
    """Extract [Speaker, Episode, timestamp] citations from response text."""
    citations = []
    seen = set()
    for speaker, episode, timestamp in CITATION_PATTERN.findall(response_text):
        key = (speaker.strip(), episode.strip(), timestamp.strip())
        if key not in seen:
            citations.append(
                Citation(
                    episode=episode.strip(),
                    guest="Unknown",
                    speaker=speaker.strip(),
                    timestamp=timestamp.strip(),
                    video_url=None,
                )
            )
            seen.add(key)
    return citations


def validate_response_citations(response_text: str) -> bool:
    """A response is compliant if it cites a source or explicitly says it can't answer."""
    has_citations = "[" in response_text and "]" in response_text
    has_no_support = any(phrase in response_text.lower() for phrase in NO_SUPPORT_PHRASES)
    return has_citations or has_no_support


@router.post("", response_model=ChatResponseBody)
async def chat(request: ChatRequest, db: DBSession = Depends(get_db)):
    """Submit a message and get a grounded response."""

    session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.provider not in ("cloud", "local"):
        raise HTTPException(status_code=422, detail="provider must be 'cloud' or 'local'")

    user_message = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()

    try:
        retrieval_service = get_retrieval_service(db)
        chunks = retrieval_service.retrieve(request.message)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        raise HTTPException(status_code=503, detail="Retrieval service unavailable") from e

    if not chunks:
        qa_response = QAResponse(
            response_text=(
                "I don't have information on this topic in the knowledge base. "
                "Try a different question."
            ),
            provider=request.provider,
            retrieved_chunks=[],
            citations=[],
            validation_passed=True,
        )
    else:
        try:
            llm_provider = get_llm_provider(request.provider)
            response_text = llm_provider.generate_qa_response(request.message, chunks)
        except ValueError as e:
            logger.error(f"Provider configuration error: {e}")
            raise HTTPException(status_code=400, detail=str(e)) from e
        except RuntimeError as e:
            logger.error(f"Provider error: {e}")
            raise HTTPException(status_code=503, detail=str(e)) from e

        citations = extract_citations_from_response(response_text)
        validation_passed = validate_response_citations(response_text)

        qa_response = QAResponse(
            response_text=response_text,
            provider=request.provider,
            retrieved_chunks=chunks,
            citations=citations,
            validation_passed=validation_passed,
        )

    assistant_message = Message(
        session_id=request.session_id,
        role="assistant",
        content=qa_response.response_text,
        provider=request.provider,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponseBody(
        message_id=assistant_message.id,
        response=qa_response,
        created_at=assistant_message.created_at.isoformat(),
    )
