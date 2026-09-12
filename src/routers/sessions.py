from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from uuid import UUID

from src.db.database import get_db
from src.db.models import Session as SessionModel, Message
from src.schemas import SessionResponse, SessionDetail, MessageResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
def create_session(db: DBSession = Depends(get_db)):
    """Create a new chat session."""
    session = SessionModel()
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(
        id=session.id,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("", response_model=list[SessionResponse])
def list_sessions(db: DBSession = Depends(get_db)):
    """List all sessions, most recent first."""
    sessions = db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()
    return [
        SessionResponse(id=s.id, created_at=s.created_at, updated_at=s.updated_at)
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: UUID, db: DBSession = Depends(get_db)):
    """Get session details and message history."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at)
        .all()
    )

    return SessionDetail(
        id=session.id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                provider=m.provider,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/{session_id}")
def delete_session(session_id: UUID, db: DBSession = Depends(get_db)):
    """Delete a session and all associated messages/artifacts."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"success": True}
