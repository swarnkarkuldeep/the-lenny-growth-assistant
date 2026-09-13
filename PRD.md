# Product Requirements Document: The Lenny Growth Assistant

**Version:** 1.0  
**Status:** Approved for Development  
**Target Deadline:** 2026-09-15 EOD  

---

## 1. User & Problem

### Primary User

**Persona:** Growth or Marketing Manager  
A team member responsible for publishing thoughtful, credible pieces (blog posts, essays, internal memos) on specific product and growth topics. They need authentic practitioner insight, not generic advice or unsupported claims.

### Job-to-Be-Done

Two-step workflow:
1. **Research** — Ask a specific question and receive a grounded answer traceable to one or more episodes and speakers in Lenny's Podcast
2. **Create** — Turn that grounded answer into a publish-ready essay or article they can edit and ship

### Pain Points

- **Information overload:** Lenny's Podcast has 400+ episodes; manually wading through audio or transcripts to find relevant insight takes hours
- **Blank page problem:** Knowing *what* to say (from research) doesn't automatically unlock *how* to say it credibly; structuring research into a polished, ship-ready essay requires significant editing effort
- **Source credibility:** Writing with conviction requires being able to trace advice back to real practitioners, not generic guidance

### Solution

A conversational AI system grounded in Lenny's Podcast transcripts that:
- Answers research questions with specific citations (episode, speaker, timestamp where available)
- Explicitly acknowledges when a question falls outside the knowledge base rather than hallucinating
- Generates structured, publication-ready essays (Ship 30 for 30–style) based on grounded research in a single step
- Renders generated artifacts (Markdown, HTML) natively in the UI so users can evaluate and edit immediately

---

## 2. Success Metrics

### Primary Metric: Source Attribution Rate

**Definition:** Percentage of responses that either cite at least one valid source (episode + speaker) OR explicitly state that the question is not covered in the knowledge base.

**Target:** ≥95%  
**Enforcement:** Automated test suite. Every response is validated; zero tolerance for unsourced claims presented as fact.

**Why this matters:** Hallucination is the system's credibility killer. If the assistant generates plausible-sounding advice without grounding, the user loses trust immediately.

### Secondary Metric 1: Structural Compliance Rate

**Definition:** Percentage of generated essays that meet all Ship 30 for 30 structural requirements *programmatically*:
- Word count 1,100–1,400 words
- At least one heading (h2 or h3)
- Contains an explicit takeaway or key insight
- Contains at least one valid citation (traceable to retrieved chunks)
- Zero claims sourced from chunks not returned by retrieval

**Target:** 100%  
**Enforcement:** Automated test suite (no subjective human judgment).

**Why this matters:** The second pain point is the blank-page problem. If the system can generate essay drafts that *structurally* meet publishing standards, the user can focus on editing voice and examples, not building the article from scratch.

### Secondary Metric 2: Time-to-Actionable-Answer

**Definition:** Wall-clock time from user submission to receipt of a complete, usable response.

**Targets (split by provider):**
- **Cloud (Google Gemini API):** <15 seconds for Q&A answer, <2 minutes for essay generation
- **Local (Ollama + llama3.2:3b):** <30 seconds for Q&A answer, <3 minutes for essay generation

**Enforcement:** Benchmarked and reported honestly in README, even if targets are not met.

**Why this matters:** If latency is excessive, the system becomes unusable, regardless of response quality. Setting provider-specific targets acknowledges that local models are slower and keeps expectations realistic.

---

## 3. Assumptions

### Assumption 1: Single-User, Multiple Sessions, No Auth

- One implicit user (no login, no accounts, no multi-tenant isolation)
- Multiple independent chat sessions supported (each session has its own context and message history)
- No authentication layer; the evaluator runs the system locally and assumes they are the sole user
- **Rationale:** Multi-user auth adds 4–6 hours of development time and touches none of the three graded product tasks. Excluded from v1; documented as out-of-scope.

### Assumption 2: Static Knowledge Base, Local Embeddings

- Transcripts are ingested via a standalone `scripts/ingest_transcripts.py` script, **not** as part of FastAPI startup
- Ingestion loads all 400+ episodes from the Lenny's Podcast transcript repo, chunks them, embeds them using Ollama + nomic-embed-text, and writes to Postgres
- Embeddings are always computed locally via Ollama; no third-party embedding APIs (no OpenAI Embeddings, Cohere, etc.)
- Knowledge base is static for v1; to refresh with newer episodes, re-run the ingestion script manually
- **Rationale:** Keeps the local pipeline fully self-contained. One API key (Gemini, if using cloud generation) instead of two. Decouples ingestion iteration from app development.

### Assumption 3: Strict Provider Mode, Per-Message Selection

- Two generation modes available: "Cloud (Gemini)" or "Local (Ollama)"
- **User selects a generation provider via a dropdown alongside the chat input** (e.g., a small selector showing "Cloud (Gemini)" or "Local (Ollama)"); the selection persists as the default until manually changed
- **Each message can use a different provider** — user can send one message with Cloud, then switch the dropdown and send the next with Local; no session-level lock
- If the selected provider fails (bad API key, rate limit, Ollama unreachable, etc.), the request fails with a **clear, provider-specific error message** (e.g., "Gemini API rate limited" vs. "Ollama unreachable at localhost:11434")
- User can switch providers and resubmit if they want to retry with a different LLM; no silent fallback
- **Retrieval and embeddings always use Ollama (nomic-embed-text), regardless of the selected generation provider**
- **Rationale:** Per-message selection enables side-by-side cloud/local comparison in a single session (supports demo requirement); strict mode makes failures transparent and diagnostically clear.

### Assumption 4: Local-Only Deployment

- The system is deployed and run on the evaluator's local machine using `docker-compose up` or equivalent
- Session data persists to a local PostgreSQL instance
- No cloud hosting (Heroku, Railway, etc.) required for v1
- **Rationale:** 2-day timeline; local demo is sufficient and eliminates infrastructure setup friction.

### Assumption 5: Session Persistence, No Auto-Cleanup

- Sessions and messages persist indefinitely in Postgres
- User can manually delete sessions or reset the database if needed
- No automatic session expiry, archival, or data retention policy
- **Rationale:** Simpler to build; sufficient for a demo where the evaluator controls the data lifecycle.

### Assumption 6: Synchronous Request Handling

- User submits a request (message or "Generate Essay"); the UI shows a spinner while waiting for the response
- **Essay generation is synchronous** — when user clicks "Generate Essay", the backend generates the essay in a single request/response cycle and returns it immediately (not a background job)
- No request queuing, async callbacks, or background jobs for any operation
- If a response (including essay generation) takes 3 minutes, the user waits 3 minutes with a spinner visible
- **Rationale:** Single-user scope eliminates concurrency complexity; sufficient for a demo where the evaluator controls their own patience.

### Assumption 7: Hand-Rolled Orchestration Instead of the Claude Agent SDK or Pi Coding Agent

- The take-home brief names the Anthropic Claude Agent SDK or Pi Coding Agent as the intended agent layer
- This implementation instead uses a small custom `Orchestrator` (`src/services/orchestrator.py`) that routes by keyword detection, with each FastAPI endpoint (`/chat`, `/essays`, `/artifacts`) calling the retrieval and LLM services directly — the same skill boundaries and routing shape an agent-SDK implementation would have, just framework-free
- **Rationale:** given the 2-day timeline, priority went to a correct, well-tested, well-grounded RAG pipeline (retrieval quality, citation validation, essay/artifact compliance) over adopting an additional framework layer on top of it. This is a deliberate, documented scope trade-off, not an oversight — flagged explicitly here per the brief's own request to record assumptions made against an incomplete client spec.
- **Risk accepted:** an evaluator scoring strictly against "must use the named SDK" will see this as a gap; the mitigation is transparency (this entry) plus equivalent behavior (clear skill boundaries, reliable routing, sensible failure handling) delivered without it.

---

## 4. Scope: In v1

✅ **FastAPI backend** with `/chat` (submit message), `/sessions` (list/manage sessions), `/health` endpoints  
✅ **PostgreSQL persistence** of sessions, messages, and metadata (using Supabase or self-hosted)  
✅ **RAG system** using Ollama embeddings (nomic-embed-text) for semantic search over transcript chunks  
✅ **Generation provider toggle** (Cloud: Google Gemini API OR Local: Ollama llama3.2:3b), strict mode, provider-specific error messages  
✅ **Grounded conversational assistant** that answers questions from Lenny's transcripts, cites sources, and explicitly declines out-of-scope questions  
✅ **Ship 30 for 30 content generation skill** — converts grounded research into ~1,250-word essays with hook, narrative, formatting, and takeaway  
✅ **Artifact generation and in-app viewer** — renders Markdown and sanitized HTML natively in the UI (no external redirects, no raw code display)  
✅ **React + Vite frontend** with chat interface, session management, artifact viewer, and provider selection  
✅ **Meaningful automated tests** covering:
- Retrieval quality (relevant chunks returned for test queries)
- Source attribution (100% of responses have valid citations or explicit no-support message)
- Structural compliance of generated essays (word count, headings, takeaway, citation)
- Artifact safety (XSS/injection attempts are sanitized)
✅ **Documentation:**
- README.md: setup, prerequisites, environment variables, local and cloud model configuration, run commands, troubleshooting
- architecture.md: database schema, API contracts, retrieval flow, LLM routing, artifact rendering strategy and security model
- design.md: UI/UX principles, layout, interaction states, accessibility
- PRD (this document)
✅ **Demo video** (2–3 minutes, on-camera): explain problem → show product → demonstrate local Ollama working → discuss one technical trade-off (artifact safety, local model limits, or hallucination mitigation)  
✅ **Agent transcripts folder** with coding logs, failed attempts, and corrections (secrets removed before commit)  

---

## 5. Scope: Out v1 (Explicitly Excluded)

❌ Multi-user authentication (OAuth, SSO, email/password login)  
❌ Per-user data isolation or multi-tenant database schema  
❌ Real-time transcript synchronization or auto-refresh  
❌ Provider fallback or silent switching (strict mode only)  
❌ External observability infrastructure (Datadog, New Relic, etc.); local structured logging to stdout/file only  
❌ Admin dashboard, analytics UI, or usage metrics  
❌ Conversation export/import  
❌ Fine-tuned or custom LLMs  
❌ Audio processing, transcript generation, or speech-to-text  
❌ Multi-language support  
❌ Rate limiting or usage quotas  

**Rationale for scope cuts:** 
- Auth, multi-tenancy, and observability do not affect the three graded product tasks and would consume 4–6+ hours of development
- Real-time sync and fine-tuning are nice-to-have but not core to the problem being solved
- Out-of-scope items are documented as future work in architecture.md (e.g., how refresh would work with webhooks and cron jobs)

---

## 6. User Flows

### Flow 1: Chat and Grounded Q&A

1. User opens the app and sees a chat interface with a **Provider Selector dropdown** (default: "Cloud (Claude)") alongside the message input
2. User types a question (e.g., "What do successful PMs do to reduce user churn?")
3. **User optionally changes the provider selector** before submitting (Cloud vs. Local); if unchanged, uses the default
4. **Backend retrieves relevant transcript chunks** (via semantic search using Ollama embeddings)
5. **LLM generates a grounded response** using the selected provider, citing specific episodes, speaker names, and timestamps
6. **Response is validated:** Contains source citations (episode, speaker, timestamp) OR an explicit "I don't have information on this topic" message
7. User sees response in chat with cited sources (episode name, speaker, timestamp; timestamp should be clickable or copyable to help verify)
8. **User can change the provider selector and ask the same question again** without creating a new session, enabling cloud/local comparison
9. User can ask follow-up questions; context is preserved within the session

### Flow 2: Essay Generation

1. User has asked a grounded question and received an answer with good citations
2. User clicks **"Generate Essay"** button (or types a command like "/essay")
3. **System generates a Ship 30 for 30–style essay** (~1,250 words) based on the conversation context and retrieved chunks
4. **Essay is validated:** Word count, headings, takeaway, citations, claims are all traceable
5. User sees the essay rendered in an **Artifact Viewer** beside the chat (similar to Claude Artifacts)
6. User can:
   - **Read** the essay in the viewer
   - **Copy** the text to their editor
   - **Regenerate** if unsatisfied
   - **Ask follow-ups** in chat to refine specific sections

### Flow 3: Artifact Viewing and Safety

1. User sees a generated Markdown or HTML artifact in the viewer
2. **Markdown artifacts** are parsed using a markdown library (e.g., `react-markdown`) and rendered as safe DOM
3. **HTML artifacts** are sanitized using DOMPurify (whitelist: h1–h6, p, ul, ol, li, strong, em, a, blockquote, code, pre; block: script, iframe, onclick, event handlers, etc.) and rendered via `dangerouslySetInnerHTML` **only after sanitization**
4. User can read, copy, or edit the artifact without XSS risk
5. User can click a **"Download"** button to export the artifact as .md or .html

---

## 7. Acceptance Criteria

### AC1: Grounded Responses
- ✅ Every response either cites a source (episode name, speaker name, timestamp) OR explicitly states "I don't have information on this topic"
- ✅ Cited sources are verifiable: evaluator can locate the episode in the transcript repo and confirm the speaker and timestamp match the retrieved chunk
- ✅ Response attribution rate ≥95% (measured by automated test)

### AC2: Ship 30 for 30 Essays
- ✅ Generated essays are 1,100–1,400 words
- ✅ Every essay has at least one heading and a clear takeaway
- ✅ Every essay cites at least one source from the knowledge base
- ✅ Every claim in the essay is traceable to a retrieved transcript chunk
- ✅ Structural compliance rate = 100% (measured by automated test)

### AC3: Artifact Safety
- ✅ Malicious HTML (script tags, onclick handlers, iframes) is stripped before rendering
- ✅ Allowed tags include: h1–h6, p, ul, ol, li, strong, em, a, blockquote, code, pre
- ✅ No artifacts break the UI or crash the browser
- ✅ Automated test includes injection attempts; all are safely sanitized

### AC4: Provider Selection
- ✅ User can select "Cloud (Gemini)" or "Local (Ollama)" via a dropdown selector alongside the chat input
- ✅ Selection persists as the default until manually changed
- ✅ User can change the provider and resubmit the same question without creating a new session (enables side-by-side cloud/local comparison)
- ✅ If provider fails, error message clearly identifies the failure (not silent fallback)

### AC5: Session Management
- ✅ User can create a new session (fresh context)
- ✅ User can load an existing session (context is restored)
- ✅ User can view a list of past sessions with timestamps

### AC6: Latency
- ✅ Cloud responses: answer <15s, essay <2min
- ✅ Local responses: answer <30s, essay <3min
- ✅ If targets are not met, latency is reported honestly in README

### AC7: Documentation and Handoff
- ✅ README explains setup, run commands, troubleshooting
- ✅ architecture.md documents database schema, API contracts, retrieval flow, artifact rendering strategy
- ✅ design.md explains UI/UX rationale
- ✅ Inline code comments explain non-obvious logic (e.g., why certain chunks are filtered, how citation extraction works)
- ✅ Fresh evaluator can clone, run, and test the system using only the README

---

## 8. Key Risks & Mitigations

### Risk 1: Hallucination (Claims Unsupported by KB)

**Failure Mode:** Assistant generates plausible-sounding advice that isn't actually in any transcript; evaluator doesn't immediately notice and loses trust in the system.

**Mitigations:**
- **Test-driven:** Automated test validates that 100% of responses cite valid sources or explicitly say "not in KB"
- **Retrieval validation:** During development, spot-check 10+ test queries to ensure retrieved chunks actually support the answer
- **Prompt engineering:** LLM receives explicit instructions to refuse out-of-scope questions, always cite sources, and clearly mark any limitations
- **Demo script:** Include at least one question explicitly designed to test graceful "I don't know" behavior (e.g., "How does Lenny recommend hiring for Go expertise?")
- **Metric:** Source attribution rate ≥95% is the primary success metric and is continuously measured

### Risk 2: Artifact Rendering XSS / Code Injection

**Failure Mode:** Generated HTML contains `<script>` tags or `onclick` handlers; evaluator opens the artifact, and malicious code executes in their browser.

**Mitigations:**
- **Sanitization library:** Use DOMPurify with a strict whitelist (h1–h6, p, ul, ol, li, strong, em, a, blockquote, code, pre; block everything else)
- **Rendering pattern:** 
  - Markdown: use `react-markdown` (builds real DOM, never uses `dangerouslySetInnerHTML`)
  - HTML: sanitize with DOMPurify **first**, then render via `dangerouslySetInnerHTML` (this is the safe pattern)
- **Testing:** Automated test suite includes injection attempts (script tags, event handlers, iframes) and verifies they are stripped
- **Documentation:** architecture.md includes a dedicated section: "Artifact Viewer Security Model — What We Permit, Block, and Why"

### Risk 3: Cloud LLM Quality & Latency (Gemini vs. Claude)

**Failure Mode:** Google Gemini generates lower-quality responses than Claude, or API latency exceeds targets.

**Mitigations:**
- **Honest expectations:** README documents Gemini quality/latency targets separately from Claude (if we had used it)
- **Retrieval focus:** Invest in retrieval quality (chunking, embedding) since it impacts all LLMs equally
- **Side-by-side testing:** Demo includes same query answered by both Gemini and local model
- **Transparent documentation:** If Gemini underperforms latency targets, report honestly in README

### Risk 3: Local Model Quality Ceiling (llama3.2:3b)

**Failure Mode:** Ollama model generates poor, unhelpful responses; evaluator tries local mode, gets disappointed, thinks the entire system doesn't work (even though cloud mode is superior).

**Mitigations:**
- **Honest expectations:** README explicitly sets local model performance targets (lower than cloud) and notes known limitations
- **Side-by-side demo:** Demo video shows the same query answered by both cloud and local model, narrated with honest commentary on trade-offs
- **Development focus:** Invest more effort in retrieval quality (chunking, embedding, search) than in LLM tuning; a mediocre LLM + excellent retrieval beats a great LLM + poor retrieval
- **Transparency:** Latency targets are provider-specific and documented; if local model is slower or lower-quality, this is reported, not hidden

### Risk 4: Retrieval Gaps (Sparse KB or Noisy Chunks)

**Failure Mode:** System retrieves irrelevant chunks, misses the right episode entirely, or returns too little context; answers become unhelpful or the system hallucinates to fill gaps.

**Mitigations:**
- **Chunking strategy:** Document the approach (speaker turns? topic boundaries? fixed window with overlap?) and test it on diverse queries
- **Embedding quality:** Nomic-embed-text is chosen for semantic search quality; validate its performance on podcast transcripts
- **Manual QA:** During development, run 10+ diverse test queries and manually verify that the top-3 retrieved chunks support a good answer
- **Citation format:** Responses include episode name, speaker name, and timestamp (if available), enabling evaluator to verify claims
- **Testing:** Retrieval tests verify that top chunks contain the claimed information; essays include only claims traceable to retrieved chunks

---

## 9. Implementation Plan (High Level)

1. **Setup & Infrastructure**
   - Docker Compose configuration (FastAPI, Postgres, Ollama)
   - Environment template (.env.example with all required and optional variables)
   - Database schema: sessions, messages, transcript_chunks, embeddings

2. **Ingestion Pipeline**
   - `scripts/ingest_transcripts.py`: clone/fetch Lenny's Podcast repo, parse transcript files, chunk by speaker turn or fixed window, embed using Ollama, write to Postgres

3. **Backend (FastAPI)**
   - `/sessions` endpoints (create, list, get, delete)
   - `/chat` endpoint (submit message, retrieve chunks, call LLM, validate response, return with citations)
   - `/health` endpoint for debugging
   - Provider selection and error handling logic
   - Validation middleware (source attribution, structural compliance for essays)

4. **LLM Integration**
   - Anthropic SDK for Cloud (Claude) generation
   - Ollama client for Local (llama3.2:3b) generation
   - Routing logic based on selected provider
   - Prompt templates for Q&A and essay generation

5. **Frontend (React + Vite)**
   - Chat interface with message display and input
   - Session list and switching
   - Provider selector dropdown
   - Artifact Viewer component (Markdown via react-markdown, HTML via DOMPurify + dangerouslySetInnerHTML)
   - Error state UI

6. **Testing**
   - Unit tests for retrieval validation, source attribution, essay structural compliance
   - Integration tests for API endpoints
   - Artifact safety tests (injection attempts)
   - Latency benchmarks for cloud and local providers

7. **Documentation & Demo**
   - README.md with complete setup and troubleshooting
   - architecture.md with schema, API, retrieval, routing, and security details
   - design.md with UI/UX rationale
   - Demo video (2–3 min, on-camera)
   - Agent transcripts folder with coding logs

---

## 10. Success Looks Like

A fresh evaluator can:
1. Clone the repository
2. Follow the README steps to set up the system locally (15 minutes)
3. Run the ingestion script to load transcripts (5 minutes)
4. Ask 5 grounded questions and receive responses with valid citations (or explicit "not in KB" messages)
5. Generate an essay from a research answer and see a publish-ready draft in the artifact viewer
6. See that the HTML artifact is safe (no XSS, professional rendering)
7. Switch to local model and ask the same questions, with honest understanding of latency/quality trade-offs
8. Understand the system's boundaries, architecture, and limitations from the documentation
9. Have confidence that another team could run, test, and extend the system with minimal questions

---
