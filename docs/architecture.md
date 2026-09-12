# Architecture: The Lenny Growth Assistant

## Overview

The Lenny Growth Assistant is a locally-deployable, AI-powered conversational system that answers product and growth questions grounded in Lenny's Podcast transcripts. The system ingests transcripts, retrieves relevant context via semantic search, generates grounded responses and essays using a configurable LLM (cloud or local), and renders artifacts safely in the UI.

**Architecture pattern:** Modular, synchronous request/response pipeline with pluggable LLM providers.

---

## System Components

### 1. Ingestion Service

**Purpose:** Load, chunk, and embed Lenny's Podcast transcripts into a searchable knowledge base.

**Input:** Raw transcripts from [github.com/ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)

**Process:**
1. Clone/fetch the transcript repository
2. Parse YAML frontmatter and transcript content from each `episodes/{guest-name}/transcript.md` file
3. **Chunk strategy:** Split transcripts by speaker turn (each speaker's continuous dialogue is one chunk). If a speaker turn exceeds 2,000 tokens, split it into fixed 2,000-token windows with 200-token overlap.
4. **Timestamp inheritance:** Each chunk inherits the timestamp of the speaker turn where it begins. Chunks preserve [inaudible] markers and transcription artifacts as-is; do not error or sanitize them.
5. Embed each chunk using Ollama + nomic-embed-text
6. Store chunks and embeddings in Postgres (`transcript_chunks` and `chunk_embeddings` tables)

**Output:** Searchable, embedded transcript chunks in Postgres

**Script:** `scripts/ingest_transcripts.py`
- Not part of FastAPI startup
- Can be re-run to refresh KB (currently static for v1)

---

### 2. Retrieval Service

**Purpose:** Retrieve relevant transcript chunks for a given query.

**Input:** User query text (string)

**Process:**
1. Embed query using Ollama + nomic-embed-text (same model as ingestion)
2. Perform vector similarity search against `chunk_embeddings` table using Postgres pgvector
3. Retrieve top 5 results (configurable via `RETRIEVAL_TOP_K` env var)
4. Filter out results below similarity threshold (0.5 by default)
5. Return chunks with metadata (episode, guest, speaker, timestamp, similarity score)

**Output:** List of `RetrievedChunk` objects:
```python
class RetrievedChunk(BaseModel):
    chunk_id: str
    episode_title: str
    guest_name: str
    speaker_name: str
    timestamp: str  # HH:MM:SS
    content: str
    similarity_score: float
    video_url: str  # from frontmatter
```

**Implementation:** `src/services/retrieval.py`

---

### 3. LLM Provider Abstraction

**Purpose:** Unified interface for cloud and local LLM generation.

**Providers:**
- **Cloud:** Google Gemini API (gemini-1.5-flash or later)
- **Local:** Ollama + llama3.2:3b

**Interface:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: list[RetrievedChunk]) -> str:
        """Generate response given prompt and retrieved context."""
        pass

class ClaudeProvider(LLMProvider):
    """Calls Anthropic Claude API."""
    pass

class OllamaProvider(LLMProvider):
    """Calls local Ollama instance."""
    pass
```

**Provider Selection:** Per-message via query parameter (`?provider=cloud` or `?provider=local`); defaults to `cloud`

**Error Handling:** If selected provider fails, return provider-specific error:
- Gemini: "Gemini API error: [reason]" (rate limit, auth, timeout, etc.)
- Ollama: "Ollama unreachable at localhost:11434" or "Ollama inference error: [reason]"
- No fallback; user must manually retry with different provider

**Implementation:** `src/services/llm.py`

---

### 4. Agent Orchestrator

**Purpose:** Route requests to the appropriate skill/tool based on user intent.

**Skills:**
1. **Answer Question** — Retrieve context, generate grounded Q&A response
2. **Write Essay** — Generate a Ship 30 for 30–style essay based on conversation context
3. **Generate Artifact** — Generate Markdown or HTML based on conversation

**Routing Logic:**
- If user message contains `/essay` or clicks "Generate Essay" button → **Write Essay**
- If user message contains `/artifact` or clicks "Generate Artifact" → **Generate Artifact**
- Otherwise → **Answer Question**

**Implementation:** `src/services/orchestrator.py`

---

### 5. Question Answering Skill

**Purpose:** Retrieve context and generate grounded responses.

**Input:** User question (string), session context (prior messages)

**Process:**
1. Retrieve top-5 relevant chunks using Retrieval Service
2. Construct prompt with retrieved chunks and conversation context
3. Call selected LLM provider to generate response
4. Extract citations from response (episode names, speaker names, timestamps)
5. Validate: response must cite sources OR explicitly state "I don't have information on this topic"
6. Return response with metadata (provider, chunks used, citations)

**Output:**
```python
class QAResponse(BaseModel):
    response_text: str
    provider: str  # "cloud" or "local"
    retrieved_chunks: list[RetrievedChunk]
    citations: list[Citation]  # extracted from response
    validation_passed: bool  # source attribution >= 95%
```

**Implementation:** `src/skills/qa.py`

---

### 6. Ship 30/30 Essay Skill

**Purpose:** Generate a publish-ready essay grounded in knowledge base.

**Input:** Research context (prior Q&A turns, user request)

**Process:**
1. Synthesize conversation context into essay prompt
2. Retrieve additional chunks if needed to enrich essay
3. Call selected LLM provider with Ship 30/30 prompt (see below)
4. Validate essay structure (word count, headings, takeaway, citations, claims traceable)
5. Return essay with validation metadata

**Ship 30/30 Prompt Requirements:**
- ~1,250 words (1,100–1,400 range)
- Strong hook (first paragraph grabs attention)
- Clear narrative arc (3–4 main sections)
- Skimmable formatting (h2 subheadings, bullet points, bold emphasis on key terms)
- One specific, actionable takeaway
- All claims grounded in retrieved chunks with inline citations
- Conversational, human tone (not robotic)

**Output:**
```python
class EssayResponse(BaseModel):
    essay_text: str  # Markdown
    provider: str
    word_count: int
    validation: EssayValidation
        word_count_ok: bool
        has_headings: bool
        has_takeaway: bool
        has_citations: bool
        all_claims_traceable: bool
        compliance_passed: bool  # 100%
```

**Implementation:** `src/skills/essay.py`

---

### 7. Artifact Generator

**Purpose:** Generate HTML or Markdown artifacts based on conversation.

**Input:** Conversation context, artifact type request (`markdown` or `html`), optional prompt override

**Process:**
1. Summarize conversation
2. Call LLM to generate artifact (HTML/Markdown)
3. If HTML: sanitize before returning
4. Return artifact with metadata

**Sanitization (HTML only):**
- Use DOMPurify library (Node.js or Python binding)
- Allowed tags: h1, h2, h3, h4, h5, h6, p, ul, ol, li, strong, em, a, blockquote, code, pre
- Allowed attributes: href (on `<a>` only)
- Strip: script, iframe, onclick, on* attributes, style with dangerous CSS

**Output:**
```python
class Artifact(BaseModel):
    artifact_id: str
    type: str  # "markdown" or "html"
    content: str  # sanitized for HTML
    created_at: datetime
```

**Implementation:** `src/skills/artifact_generator.py`

---

## Database Schema

### `sessions` table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb  -- future: user_id, tags, etc.
);
```

### `messages` table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,  -- "user" or "assistant"
    content TEXT NOT NULL,
    provider TEXT,  -- "cloud" or "local", NULL for user messages
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### `transcript_chunks` table
```sql
CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    episode_title TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    speaker_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,  -- HH:MM:SS
    video_url TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### `chunk_embeddings` table
```sql
CREATE TABLE chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES transcript_chunks(id) ON DELETE CASCADE,
    embedding vector(384),  -- nomic-embed-text produces 384-dim vectors
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunk_embeddings_vector ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### `artifacts` table
```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    type TEXT NOT NULL,  -- "markdown" or "html"
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## API Endpoints

### Session Management

**POST /sessions**
- Create a new session
- Request: `{}`
- Response: `{ session_id: UUID, created_at: ISO8601 }`

**GET /sessions**
- List all sessions
- Request: (none)
- Response: `{ sessions: [{ id: UUID, created_at: ISO8601, updated_at: ISO8601 }] }`

**GET /sessions/{session_id}**
- Get session details and message history
- Request: (none)
- Response: `{ id: UUID, created_at: ISO8601, messages: [{ id: UUID, role: string, content: string, created_at: ISO8601 }] }`

**DELETE /sessions/{session_id}**
- Delete a session
- Request: (none)
- Response: `{ success: true }`

### Chat

**POST /chat**
- Submit a message and get a response
- Request:
  ```json
  {
    "session_id": "UUID",
    "message": "What is product-market fit?",
    "provider": "cloud",  // optional, defaults to "cloud"
    "skill": "answer"  // optional: "answer", "essay", "artifact"; defaults to auto-detect
  }
  ```
- Response:
  ```json
  {
    "message_id": "UUID",
    "response": {
      "text": "...",
      "provider": "cloud",
      "citations": [
        {
          "episode": "Brian Chesky: ...",
          "guest": "Brian Chesky",
          "speaker": "Brian Chesky",
          "timestamp": "00:12:34",
          "video_url": "https://..."
        }
      ],
      "validation": { "passed": true, "reason": "citations present" }
    },
    "created_at": "ISO8601"
  }
  ```

**Error Response:**
```json
{
  "error": "claude_api_error",
  "message": "Claude API rate limited. Try again in 30 seconds.",
  "provider": "cloud"
}
```

### Artifacts

**POST /artifacts**
- Generate an artifact (HTML/Markdown)
- Request:
  ```json
  {
    "session_id": "UUID",
    "type": "markdown",  // or "html"
    "provider": "cloud"
  }
  ```
- Response:
  ```json
  {
    "artifact_id": "UUID",
    "type": "markdown",
    "content": "...",
    "created_at": "ISO8601"
  }
  ```

### Health

**GET /health**
- Check system health
- Request: (none)
- Response:
  ```json
  {
    "status": "ok",
    "postgres": "connected",
    "ollama": "connected",
    "claude_api_key": "configured"
  }
  ```

---

## Deployment Topology

### Services (Docker Compose)

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: lenny_assistant
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  ollama:
    image: ollama/ollama:latest
    environment:
      OLLAMA_HOST: 0.0.0.0:11434
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  fastapi:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/lenny_assistant
      OLLAMA_BASE_URL: http://ollama:11434
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    depends_on:
      - postgres
      - ollama
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on:
      - fastapi
    ports:
      - "5173:5173"
```

### Environment Variables

**Required:**
- `GEMINI_API_KEY` — Google Gemini API key
- `DATABASE_URL` — Postgres connection string

**Optional:**
- `OLLAMA_BASE_URL` — Ollama endpoint (default: http://localhost:11434)
- `RETRIEVAL_TOP_K` — Number of chunks to retrieve (default: 5)
- `SIMILARITY_THRESHOLD` — Vector search threshold (default: 0.5)
- `LOG_LEVEL` — Logging level (default: INFO)

---

## Artifact Rendering Security Model

### HTML Artifact Rendering

**Frontend approach:**
1. Sanitize all user-generated HTML using DOMPurify before rendering
2. Whitelist allowed HTML tags and attributes:
   - **Tags:** h1–h6, p, ul, ol, li, strong, em, a, blockquote, code, pre
   - **Attributes:** href (on `<a>` only)
3. Strip all other tags and attributes (script, iframe, onclick, style, etc.)
4. Render sanitized HTML via `dangerouslySetInnerHTML` **only after sanitization**

**Why this works:**
- DOMPurify is battle-tested for XSS prevention
- Whitelist approach (strip by default, allow specific tags) is more secure than blacklist
- No user input reaches the DOM without sanitization
- Timestamps and citations are safe (plain text, no HTML generation)

**Testing:**
- Automated test: inject malicious HTML (script tags, event handlers, iframes) and verify they're stripped
- Example malicious inputs:
  ```html
  <script>alert('xss')</script>
  <img src=x onerror="alert('xss')">
  <a href="javascript:alert('xss')">click</a>
  <iframe src="evil.com"></iframe>
  ```
  All should be sanitized before rendering.

### Markdown Artifact Rendering

**Frontend approach:**
1. Parse Markdown using `react-markdown` library
2. Configure to render only safe tags (same whitelist as HTML)
3. Never use `dangerouslySetInnerHTML` for Markdown

**Why this works:**
- `react-markdown` builds real DOM, not HTML strings
- Built-in sanitization via allowed tags configuration
- No XSS surface

---

## Error Handling & Observability

### Structured Logging

All critical operations log to stdout as JSON:
```json
{
  "timestamp": "2026-09-13T03:15:00Z",
  "level": "INFO",
  "service": "retrieval",
  "action": "retrieve_chunks",
  "query": "product-market fit",
  "top_k": 5,
  "results_returned": 3,
  "similarity_scores": [0.87, 0.84, 0.72],
  "duration_ms": 142
}
```

### Failure Scenarios

**Missing retrieval results:**
- Log: "retrieval_no_results"
- Response: "I don't have information on this topic in the knowledge base."

**LLM provider timeout:**
- Log: "llm_timeout" with provider name and duration
- Response: Provider-specific error message

**Artifact rendering injection attempt:**
- Log: "artifact_sanitization" with number of tags/attributes removed
- Response: Safe, sanitized artifact rendered

---

## Future Work (Out of v1 Scope)

- **Real-time transcript sync:** Webhook-based ingestion when new episodes are published
- **Multi-user auth:** Per-user session isolation, account management
- **Fine-tuned local models:** Better quality answers without requiring Claude
- **Export/import:** Save conversations as PDFs or markdown
- **Observability dashboard:** Metrics on retrieval quality, LLM performance, user feedback

---
