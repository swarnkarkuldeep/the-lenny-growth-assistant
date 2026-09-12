from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    episode_title: str
    guest_name: str
    speaker_name: str
    timestamp: str
    content: str
    video_url: Optional[str] = None
    similarity_score: float


class Citation(BaseModel):
    episode: str
    guest: str
    speaker: str
    timestamp: str
    video_url: Optional[str] = None


class QAResponse(BaseModel):
    response_text: str
    provider: str
    retrieved_chunks: List[RetrievedChunk]
    citations: List[Citation]
    validation_passed: bool


class SessionCreate(BaseModel):
    pass


class SessionResponse(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    provider: Optional[str] = None
    created_at: datetime


class SessionDetail(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]
