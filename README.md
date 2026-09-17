# The Lenny Growth Assistant

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/db-PostgreSQL%20%2B%20pgvector-336791)](https://github.com/pgvector/pgvector)
[![Tests](https://img.shields.io/badge/tests-89%20passing-brightgreen)](tests/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

A locally-deployable AI assistant that turns [Lenny's Podcast transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) into a reliable internal knowledge tool: grounded Q&A with inline citations, Ship 30 for 30–style essay generation, and a safe in-app artifact viewer — running entirely offline on Ollama, or against Google Gemini when a cloud key is available.

Built for the Forward Deployed Engineer take-home assessment (see `task.md`, gitignored — it's the confidential assignment brief). This README is the operational entry point; `PRD.md` covers the discovery brief (user, problem, success metric, assumptions, scope, risks), `docs/architecture.md` the system design, and `docs/design.md` the UI/UX rationale.

---

## Contents

- [Why this exists](#why-this-exists)
- [Quick Start](#quick-start)
- [What you'll see](#what-youll-see)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Artifact Safety Model](#artifact-safety-model)
- [Known Limitations](#known-limitations)
- [Repository Layout](#repository-layout)
- [Demo Video](#demo-video)
- [License](#license)

---

## Why this exists

> A product and growth team wants to turn 400+ episodes of Lenny's Podcast into a reliable internal assistant — one their team can trust for grounded answers and publishable drafts, without needing to understand prompts, models, or infrastructure.

The core design bet: **grounding beats fluency**. Every answer either cites a real `[Speaker, Episode, timestamp]` from a retrieved transcript chunk, or explicitly says it doesn't know — never a confident, unsupported guess. That constraint shapes almost every engineering decision in this repo, from the retrieval threshold to the essay validator to the artifact sanitizer.

Built end-to-end using **Claude Code** (Anthropic's agentic coding CLI, powered by the Claude Agent SDK) as the development agent — designing and implementing the retrieval pipeline, LLM provider abstraction, orchestration/routing logic, essay and artifact generation, and the frontend, phase by phase with tests at each step. Session transcripts are in `agent-transcripts/`. This is distinct from the *running application's* request routing, which does not call Claude Code or the Agent SDK at runtime — see [Known Limitations](#known-limitations).

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM (Postgres + Ollama + a 3B local model)
- Python 3.10+ and Node 18+ (only needed for local dev outside Docker, or to run the test suite from the host)
- A Google Gemini API key (optional — only required for the "Cloud" provider; the app is fully usable with Ollama alone)

### One-command setup

```bash
# 1. Clone the repository
git clone https://github.com/swarnkarkuldeep/the-lenny-growth-assistant.git
cd the-lenny-growth-assistant

# 2. Configure environment
cp .env.example .env
# Edit .env: set GEMINI_API_KEY if you want the Cloud provider (optional — skip for local-only)

# 3. Start every service
docker-compose up -d

# 4. Pull the local models into the Ollama container (first run only, ~2-3GB download)
docker exec -it $(docker ps -qf "name=ollama") ollama pull llama3.2:3b
docker exec -it $(docker ps -qf "name=ollama") ollama pull nomic-embed-text

# 5. Clone and ingest Lenny's Podcast transcripts (first run only)
git clone https://github.com/ChatPRD/lennys-podcast-transcripts.git
python scripts/ingest_transcripts.py

# 6. Open the app
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Health check | http://localhost:8000/health |

> **Port note:** Postgres is exposed on host port **5433**, not the default 5432. This project deliberately avoids 5432 because it's the standard port for a native PostgreSQL install, and colliding with one silently routes your queries to the wrong database with a confusing "password authentication failed" error. Inside Docker, services still talk to each other over the internal `postgres:5432` address — only the host-facing mapping changed.

### Verify it's alive

```bash
curl http://localhost:8000/health
# {"status":"ok","postgres":"connected","ollama":"connected","gemini_api_key":"missing"|"configured"}
```

If `postgres` or `ollama` don't say `connected`, see [Troubleshooting](#troubleshooting) before going further.

---

## What you'll see

- **Chat interface** with a Cloud/Local provider switch, message history, and inline citations to episode/speaker/timestamp
- **Generate Essay** action that produces a Ship 30/30-style draft grounded in the conversation
- **Artifact viewer** rendering the generated Markdown/HTML safely alongside the chat
- **Session sidebar** to create, switch between, and delete conversations

The frontend's visual identity is a vinyl/cassette-inspired dark record-sleeve board — sessions read as a tracklist, chat as a deck, citations as stamped cue-point chips, and generated essays as a paper sleeve insert. Full rationale in `docs/design.md`.

---

## Architecture Overview

### Backend (FastAPI)

| Endpoint | Purpose |
|---|---|
| `GET /health` | Postgres / Ollama / Gemini-key status |
| `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}` | Session CRUD |
| `POST /chat` | Retrieve context, generate a grounded answer, persist both turns |
| `POST /essays` | Generate + validate a Ship 30/30 essay from the session's conversation, persisted as a markdown artifact |
| `POST /artifacts`, `GET /artifacts/{id}` | Generate or fetch a Markdown/HTML artifact (HTML is sanitized server-side) |
| `POST /retrieve` | Debug endpoint: run retrieval directly for a query |

Full request/response contracts, DB schema, and the ingestion/retrieval/generation flow are documented in `docs/architecture.md`.

### Request flow: asking a question

```
User question ("What is product-market fit?", provider: "local")
  │
  ▼
POST /chat ─── embed query (Ollama nomic-embed-text)
  │             │
  │             ▼
  │        pgvector cosine search → top-5 chunks ≥ similarity threshold
  │             │
  ▼             ▼
  Selected LLM provider generates an answer grounded in those chunks
  │
  ▼
validate_response_citations() ─── cites a real chunk, or admits it doesn't know?
  │
  ▼
Persist both turns → return { response_text, citations, retrieved_chunks, validation_passed }
```

### Database (PostgreSQL + pgvector)

`sessions`, `messages`, `transcript_chunks`, `chunk_embeddings` (768-dim vectors), `artifacts`. Schema lives in `src/db/migrations/001_init.sql` and is applied automatically on first container start.

### Knowledge base

- **Source:** [Lenny's Podcast transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) (cloned separately, not vendored into this repo — see step 5 of Quick Start)
- **Chunking:** `src/services/chunker.py` splits by speaker turn, preserving timestamps and `[inaudible]` markers; long turns are split with token overlap
- **Embedding:** Ollama + `nomic-embed-text` (768-dim)
- **Retrieval:** `src/services/retrieval.py` — cosine similarity via pgvector, top-k (default 5) above a similarity threshold (default 0.5), both configurable via env vars
- **Refresh:** re-run `python scripts/ingest_transcripts.py` (it clears and rebuilds `transcript_chunks`/`chunk_embeddings`); there is no live/incremental refresh in v1

### LLM providers

Selected per-request via the `provider` field (`"cloud"` or `"local"`) — **no silent fallback**: if the selected provider is unavailable, the request fails with a clear error rather than switching providers.

| | Cloud (Gemini) | Local (Ollama) — mandatory for the demo |
|---|---|---|
| Model | `gemini-flash-latest` | `llama3.2:3b` |
| Requires | `GEMINI_API_KEY` | Nothing (fully offline) |
| Typical answer latency | a few seconds | 10–30s on a laptop CPU |
| Typical essay latency | well under a minute | 1–3 minutes |
| Citation format reliability | Follows the prompted `[Speaker, Episode, timestamp]` format reliably | Grounds correctly but paraphrases/reformats citations — see [Known Limitations](#known-limitations) |

### Frontend (React + Vite)

Two-pane layout: chat (with provider switch, citations, session sidebar) beside an artifact viewer. Markdown renders via `react-markdown` (no raw HTML execution); HTML artifacts are sanitized twice — once server-side with `bleach` before persistence, and again client-side with `DOMPurify` before `dangerouslySetInnerHTML` — see [Artifact Safety Model](#artifact-safety-model). Design rationale, states, and accessibility notes are in `docs/design.md`.

---

## Configuration

### Environment variables (`.env`, see `.env.example`)

**Optional (cloud generation only):**
- `GEMINI_API_KEY` — Google Generative Language API key (starts with `AIzaSy...`, from [Google AI Studio](https://aistudio.google.com/apikey)). Leave blank to run Ollama-only.

**Have sensible defaults, override if needed:**
- `DATABASE_URL` — defaults to the host-mapped Docker Postgres (`localhost:5433`, see the port note above)
- `DB_PASSWORD` — Postgres password (default: `password`; only meaningful for local dev, never used for a real deployment)
- `OLLAMA_BASE_URL` — default `http://localhost:11434` on host, `http://ollama:11434` inside Docker
- `RETRIEVAL_TOP_K` — chunks retrieved per query (default: 5)
- `SIMILARITY_THRESHOLD` — pgvector cosine-similarity cutoff (default: 0.5)
- `LOG_LEVEL` — default `INFO`

No secrets are committed — verified with `git log --all -- .env` (empty history). `.env` is git-ignored; `.env.example` ships only placeholder/default values.

### Running in different modes

```bash
# Local-only (no API key, fully offline)
docker-compose up -d
# select "Local" in the UI provider switch

# Cloud + Local both available
# set GEMINI_API_KEY in .env, then:
docker-compose up -d

# Dev with hot reload, outside Docker
uvicorn src.main:app --reload --port 8000          # backend
cd frontend && npm install && npm run dev           # frontend
```

---

## Usage

1. **Create or select a session** in the sidebar.
2. **Ask a question**, e.g. "What do successful PMs do to reduce churn?" Pick Cloud or Local before sending.
3. **Read the answer** — every claim either cites `[Speaker, Episode, timestamp]` or the assistant explicitly says it doesn't have the information, rather than guessing.
4. **Generate an essay** from the conversation — validated against word count (1,100–1,400), heading structure, a takeaway, citations, and claim traceability before being saved as a markdown artifact.
5. **Generate an artifact** (Markdown or HTML) — rendered in the artifact viewer beside the chat.

---

## Testing

### Automated tests

```bash
# Full suite (89 tests)
pytest tests/ -v

# A specific area
pytest tests/test_retrieval.py -v
pytest tests/test_artifact_safety.py -v      # XSS / sanitization
pytest tests/test_integration.py -v          # end-to-end workflow

# With coverage
pytest tests/ --cov=src
```

Requires the Docker stack running (`docker-compose up -d`) so tests can reach Postgres/Ollama on the host-mapped ports. Tests involving the Cloud provider skip automatically when `GEMINI_API_KEY` is unset, and skip (not fail) on a Gemini free-tier quota exhaustion — an expected operational condition, not a defect. Tests involving live local-model inference tolerate `503` (provider unreachable) so the suite stays meaningful on a machine without Ollama pulled/running, rather than requiring live inference to pass.

**Current state:** 89 tests — 88 pass, 1 skips when the Gemini daily free-tier quota is exhausted (expected under repeated testing).

**Coverage by concern:**
- **Retrieval** — semantic search quality, similarity ordering, threshold filtering (`test_retrieval.py`)
- **Ingestion** — chunking, embeddings, required metadata (`test_ingestion.py`)
- **LLM providers** — Gemini and Ollama response generation (`test_llm_gemini.py`, `test_llm_ollama.py`)
- **API contracts** — sessions, chat, essays, artifacts (`test_chat_api.py`, `test_essays_api.py`, `test_artifacts_api.py`)
- **Source attribution** — every grounded response must cite or explicitly admit it can't answer (`test_chat_api.py::test_validate_response_citations`)
- **Essay compliance** — word count, headings, takeaway, citations, claim traceability (`test_essay.py`)
- **Artifact safety (XSS)** — script tags, event handlers, iframes, `javascript:`/`data:` URLs, disallowed tags (`test_artifact_safety.py`)
- **End-to-end** — session → chat → essay → artifact → cleanup (`test_integration.py`)
- **Infrastructure** — Docker/config/model scaffolding exists as expected (`test_infrastructure.py`)

### Manual testing

A step-by-step manual QA script for the frontend (startup, sessions, Q&A, essay generation, artifact safety, responsive/accessibility) is in `docs/manual-test-plan.md`.

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/sessions
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<uuid>", "message": "What is product-market fit?", "provider": "local"}'
curl -X POST http://localhost:8000/essays \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<uuid>", "provider": "local"}'
```

---

## Troubleshooting

### `password authentication failed for user "postgres"` when running pytest from the host

**Cause:** something else on your machine (commonly a native PostgreSQL install) is already listening on port 5432, so host-side connections never reach the Docker container even though `docker exec ... psql` works fine (it connects internally, bypassing the port).

**Fix:** this repo already maps Postgres to host port **5433** for exactly this reason (`docker-compose.yml`, `.env`/`.env.test`). If you changed it back to 5432 and hit this, check `netstat -ano | findstr 5432` (Windows) / `lsof -i :5432` (macOS/Linux) for a conflicting process before assuming the container is broken.

### `API key not valid` from Gemini

**Symptom:** `google.api_core.exceptions.InvalidArgument: 400 API key not valid`

**Before concluding the key itself is bad, rule out environment shadowing:** `pydantic-settings` gives real OS/shell environment variables precedence over `.env` file values. If your shell (or a global Windows/macOS environment variable set by some other tool) already has a `GEMINI_API_KEY` defined, it silently overrides whatever is in `.env` — check with `echo $GEMINI_API_KEY` (bash) / `echo $env:GEMINI_API_KEY` (PowerShell) / `[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")` (persistent Windows var) before assuming `.env` is being read at all. This exact scenario happened during development (see `IMPLEMENTATION_LOG.md`, Phase 7, defect 4) — a stray persistent env var, unrelated to this project, was shadowing a perfectly valid key.

If the key genuinely is invalid: get one from [Google AI Studio](https://aistudio.google.com/apikey) and update `GEMINI_API_KEY` in `.env`, or skip Cloud entirely and use Local (Ollama) only.

### `429 RESOURCE_EXHAUSTED` from Gemini

**Symptom:** `quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"`

**Cause:** the Gemini free tier caps daily requests per project/model (as low as ~20/day at the time of writing). This is expected under repeated testing, not a bug — `tests/test_llm_gemini.py` skips (rather than fails) when it detects this specific error. Wait for the daily quota reset, or switch to Local (Ollama) for uninterrupted testing.

### `Ollama unreachable at http://localhost:11434`

```bash
docker ps | grep ollama                       # is it running?
curl http://localhost:11434/api/tags          # does it respond?
docker exec -it $(docker ps -qf "name=ollama") ollama pull llama3.2:3b   # model present?
docker-compose restart ollama
```

Note: the Ollama container's own Docker healthcheck may show `unhealthy` because the image doesn't ship `curl`, even though the service itself responds fine — check with `curl` from the host as above rather than trusting `docker ps` status alone.

### "I don't have information on this topic" for everything

```bash
# 1. Confirm chunks were ingested
docker exec -it $(docker ps -qf "name=postgres") psql -U postgres -d lenny_assistant -c "SELECT COUNT(*) FROM transcript_chunks;"
# 2. If 0, re-run ingestion
python scripts/ingest_transcripts.py
# 3. Sanity-check retrieval directly
curl -X POST "http://localhost:8000/retrieve?query=product+strategy"
```

### Essay/artifact generation is slow or times out on Local

Expected — a 3B model on CPU is materially slower than a cloud model. Switch to Cloud for faster generation, or expect 1–3 minutes locally.

### `docker-compose up` fails or containers keep restarting

```bash
docker-compose logs postgres    # check for port/volume conflicts
docker-compose logs fastapi     # check for missing env vars, DB connection errors
docker-compose down && docker-compose up -d   # clean restart
```

---

## Artifact Safety Model

Generated HTML is treated as untrusted input end-to-end:

1. **Server-side (`src/routers/artifacts.py`):** `bleach.clean()` strips everything outside a fixed whitelist — `h1–h6, p, ul, ol, li, strong, em, a, blockquote, code, pre` — and the only attribute allowed anywhere is `href` on `<a>`. `<script>`, `<iframe>`, `<object>`/`<embed>`, `<svg>`, `<style>`, `<img>`, event-handler attributes (`onclick`, `onerror`, `onload`, ...), and `javascript:`/`data:` URI schemes are all removed before the artifact is ever persisted.
2. **Client-side (`frontend`):** the sanitized HTML is run through `DOMPurify` again before `dangerouslySetInnerHTML`, as defense in depth against any gap in the server-side whitelist.
3. **Markdown** artifacts never touch either sanitizer — they render via `react-markdown`, which builds safe React elements directly and never executes raw HTML.

See `tests/test_artifact_safety.py` for the exhaustive payload coverage (script tags in various cases, event handlers, `<iframe>`/`<object>`/`<embed>`/`<svg>`, `javascript:`/`data:` hrefs, and confirmation that the whitelist itself excludes every dangerous tag).

---

## Known Limitations

- **At runtime, request routing is a hand-rolled Orchestrator, not a live Agent SDK / Pi Coding Agent integration.** `src/services/orchestrator.py` routes by keyword detection (`/essay`, `/artifact`) rather than through either named agent framework, and endpoints (`/chat`, `/essays`, `/artifacts`) call retrieval and LLM services directly. Claude Code (built on the Claude Agent SDK) was the *development* agent that designed and built this system — it is not part of the deployed application's request path. This was a scope decision to prioritize a working, well-tested RAG pipeline within the assessment timeline; the skill boundaries and routing logic are the same shape a runtime agent-SDK integration would have, just hand-rolled rather than framework-mediated. See `PRD.md` (Assumption 7) for the full record.
- **Local-model attribution is evidence-based, not format-based, and still heuristic.** `validate_response_citations` (`src/routers/chat.py`) accepts either a `[Speaker, Episode, timestamp]` citation, an explicit "I don't have this" admission (regex patterns, since Gemini uses the prompt's exact wording but the 3B local model paraphrases it unpredictably), or — because the local model often grounds its answer correctly but cites it in prose (`"According to Grenier... (Grenier, "Episode", timestamp: 00:00:00)"`) instead of brackets — a real retrieved chunk's speaker name plus a timestamp appearing anywhere in the response. Even with this, `validation_passed` is not 100% reliable on any *single* live call against the local model (a 3B model at temperature 0.7 occasionally hedges or skips citing altogether, even for a clearly answerable question) — treat it as a useful per-response signal, not a guarantee, for the Local provider specifically. The underlying logic is covered by deterministic unit tests against real captured phrasings (`tests/test_chat_api.py`); see `IMPLEMENTATION_LOG.md` for the full investigation. The structured `citations` list returned to the frontend still only recognizes bracket-style output, so a prose citation passes attribution but won't render as a clickable citation chip.
- **Static knowledge base.** No live/incremental transcript refresh; re-run `scripts/ingest_transcripts.py` to pick up new episodes (it rebuilds the chunk/embedding tables from scratch).
- **Single implicit user, no auth.** Out of scope for v1 per `PRD.md`.
- **Simplified claim traceability.** The essay validator checks that citations reference a speaker present in the retrieved chunks, not full semantic entailment of every sentence.

See `PRD.md` for the complete list of assumptions, scope cuts, and risk trade-offs.

---

## Repository Layout

```
src/                       FastAPI app: routers, services (retrieval/llm/essay/orchestrator), db models
scripts/                   Transcript ingestion
frontend/                  React + Vite app
tests/                     pytest suite, 89 tests (see Testing above)
docs/architecture.md       System design, DB schema, API contracts, security model
docs/design.md             UI/UX principles, states, accessibility
docs/manual-test-plan.md   Manual QA script for the frontend
agent-transcripts/         Coding-agent session logs, redacted of secrets before commit
PRD.md                     Discovery brief, requirements, acceptance criteria
IMPLEMENTATION_LOG.md      Real development history: decisions, defects found and fixed, limitations
LICENSE                    MIT
```

---

## Demo Video

2–3 minute walkthrough covering the problem, the product, a live Local (Ollama) demo, and one technical trade-off: (https://youtu.be/NgcW0OCvVjM)

---

## License

[MIT](LICENSE) — see the LICENSE file for the full text.

---

## Contributors

Built for the Forward Deployed Engineer take-home assessment.
