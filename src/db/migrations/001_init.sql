CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    provider TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant'))
);

CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_title TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    speaker_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    video_url TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES transcript_chunks(id) ON DELETE CASCADE,
    embedding TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(chunk_id)
);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_type CHECK (type IN ('markdown', 'html'))
);

CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_artifacts_session ON artifacts(session_id);
CREATE INDEX idx_transcript_chunks_guest ON transcript_chunks(guest_name);
