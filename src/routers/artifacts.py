import logging
from uuid import UUID

import bleach
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from src.db.database import get_db
from src.db.models import Artifact
from src.db.models import Message
from src.db.models import Session as SessionModel
from src.services.llm import get_llm_provider
from src.services.retrieval import get_retrieval_service

router = APIRouter(prefix="/artifacts", tags=["artifacts"])
logger = logging.getLogger(__name__)

ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "ul", "ol", "li", "strong", "em", "a", "blockquote", "code", "pre",
]
ALLOWED_ATTRIBUTES = {"a": ["href"]}


class ArtifactRequest(BaseModel):
    session_id: UUID
    type: str = "markdown"  # "markdown" or "html"
    provider: str = "cloud"


class ArtifactResponse(BaseModel):
    artifact_id: UUID
    type: str
    content: str
    created_at: str


def sanitize_if_html(artifact_type: str, content: str) -> str:
    """Strip disallowed tags/attributes from HTML artifacts. Markdown passes through untouched."""
    if artifact_type != "html":
        return content
    return bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


@router.post("", response_model=ArtifactResponse)
async def generate_artifact(request: ArtifactRequest, db: DBSession = Depends(get_db)):
    """Generate a Markdown or HTML artifact grounded in the current conversation."""

    if request.type not in ("markdown", "html"):
        raise HTTPException(status_code=422, detail="type must be 'markdown' or 'html'")

    if request.provider not in ("cloud", "local"):
        raise HTTPException(status_code=422, detail="provider must be 'cloud' or 'local'")

    session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == request.session_id)
        .order_by(Message.created_at)
        .all()[-10:]
    )
    if not messages:
        raise HTTPException(status_code=400, detail="No conversation history for artifact generation")

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
            detail="No relevant transcript material found for this conversation; cannot generate a grounded artifact.",
        )

    try:
        llm_provider = get_llm_provider(request.provider)
        content = llm_provider.generate_artifact(messages, chunks, request.type)
    except ValueError as e:
        logger.error(f"Provider configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error(f"Provider error: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e

    sanitized_content = sanitize_if_html(request.type, content)

    artifact = Artifact(
        session_id=request.session_id,
        type=request.type,
        content=sanitized_content,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return ArtifactResponse(
        artifact_id=artifact.id,
        type=artifact.type,
        content=artifact.content,
        created_at=artifact.created_at.isoformat(),
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: UUID, db: DBSession = Depends(get_db)):
    """Retrieve a previously generated artifact, sanitizing HTML on the way out."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    sanitized_content = sanitize_if_html(artifact.type, artifact.content)

    return ArtifactResponse(
        artifact_id=artifact.id,
        type=artifact.type,
        content=sanitized_content,
        created_at=artifact.created_at.isoformat(),
    )
