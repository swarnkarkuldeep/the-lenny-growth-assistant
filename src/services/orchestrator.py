import logging
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session as DBSession

from src.db.models import Message

logger = logging.getLogger(__name__)


class Orchestrator:
    """Routes requests to appropriate skills based on user intent."""

    @staticmethod
    def detect_skill(message: str) -> str:
        """Detect which skill to invoke based on user message."""
        msg_lower = message.lower()

        if "/essay" in msg_lower or "generate essay" in msg_lower or "ship 30" in msg_lower:
            return "essay"
        elif "/artifact" in msg_lower or "generate artifact" in msg_lower:
            return "artifact"
        else:
            return "answer"

    @staticmethod
    def get_conversation_context(db: DBSession, session_id: UUID, limit: int = 10) -> List[Message]:
        """Get the most recent conversation history for context."""
        messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at)
            .all()
        )
        return messages[-limit:]


def get_orchestrator() -> Orchestrator:
    return Orchestrator()
