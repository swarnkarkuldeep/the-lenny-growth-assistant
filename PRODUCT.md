# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + Vite, plain CSS (no Tailwind/CSS framework), axios for API calls, react-markdown + DOMPurify for safe artifact rendering. Confirmed by the user for this build.

## Users

**Primary:** A growth/marketing manager (or similar operator) who needs to publish credible, practitioner-grounded content (blog posts, essays, internal memos) on product and growth topics. Not a developer — they judge the tool by trustworthiness of answers and speed to a usable draft, not by technical internals.

**Secondary:** The technical evaluator (Forward Deployed Engineer take-home reviewer) who will clone the repo, run it locally, and judge UI/UX polish, grounding correctness, and engineering judgment alongside the primary persona's experience.

## Product Purpose

The Lenny Growth Assistant turns Lenny's Podcast transcripts (400+ episodes) into a conversational research and writing tool. It answers product/growth questions with citations traceable to a real episode, speaker, and timestamp, and turns a grounded research thread into a publish-ready Ship 30-for-30-style essay rendered safely in an in-app artifact viewer — so the user never has to leave the product to go from question to shippable draft.

## Positioning

Unlike a generic LLM chat wrapper, every claim here is grounded and cited back to a specific podcast moment, and refuses to answer instead of hallucinating when the knowledge base doesn't cover the topic. It also collapses "research" and "first draft" into one flow: the same conversation that produced the grounded answer becomes the essay, rendered live beside the chat rather than as a copy-pasted blob of markdown.

## Operating Context

- Runs locally via Docker Compose (Postgres + Ollama + FastAPI + Vite frontend) — no cloud deployment for v1.
- Two LLM providers, selectable per message, no silent fallback: **Cloud (Google Gemini)** and **Local (Ollama + llama3.2:3b)**. Embeddings always run locally via Ollama (nomic-embed-text), regardless of the generation provider.
- A session is a single continuous chat thread with its own message history; multiple sessions are supported (session switcher), no auth/multi-tenancy.
- Two generation "skills" beyond plain Q&A: essay generation (`/essays`) and general artifact generation (`/artifacts`, markdown or HTML), both grounded in the same retrieved transcript chunks.
- Latency is real and provider-dependent: cloud answers target <15s, local answers <30s; cloud essays <2min, local essays <3min. The UI must make waiting legible (spinner, disabled input) rather than pretend it's instant.
- HTML artifacts are untrusted output from an LLM and must be sanitized (bleach on the backend; belt-and-suspenders sanitization again on the frontend) before ever touching the DOM.

## Capabilities and Constraints

- Backend: FastAPI. Endpoints already implemented: `POST/GET /sessions`, `GET/DELETE /sessions/{id}`, `POST /chat`, `POST /essays`, `POST /artifacts`, `GET /artifacts/{id}`, `GET /health`.
- `provider` field is literally `"cloud"` or `"local"` (not "gemini"/"ollama") in every request body.
- `/health` returns `{status, postgres, ollama, gemini_api_key}` — `status` is `"ok"` or `"degraded"`.
- Citations are extracted via a `[Speaker, Episode, HH:MM:SS]` pattern in the LLM's raw response text; a response is "compliant" if it either contains a bracketed citation or an explicit "don't have information" / "not in the knowledge base" phrase.
- Essay validation returns: `word_count_ok, has_headings, has_takeaway, has_citations, all_claims_traceable, compliance_passed, word_count`.
- Artifact viewer must render both Markdown (via react-markdown, never `dangerouslySetInnerHTML`) and HTML (DOMPurify-sanitized, whitelist: h1–h6, p, ul, ol, li, strong, em, a, blockquote, code, pre; href-only on `<a>`).
- No multi-user auth, no session-level provider lock (provider is chosen per message), no background/async jobs — every request is synchronous request/response with the UI showing a spinner for the duration.
- Undecided: whether the frontend ships inside the existing Docker Compose `frontend` service or is run separately for local dev — treat both as valid (Vite dev server for iteration, Dockerfile/nginx for the compose stack).

## Brand Commitments

- Product name: "The Lenny Growth Assistant." No existing logo, visual identity, or marketing site — this frontend build is the first visual expression of the product.
- Tone (from existing design.md, preserved): clear over clever, honest about trade-offs and limitations, encouraging but not falsely cheerful, never hides a failure behind vague copy.

## Evidence on Hand

- `PRD.md`, `docs/architecture.md`, `docs/design.md` — full product/UX spec written for this project; treat as authoritative product truth and existing (pre-visual-build) design direction.
- No real screenshots, logos, testimonials, or brand assets exist yet. Nothing here should be invented.

## Product Principles

1. **Grounding is the product.** Every answer's trustworthiness comes from a visible, verifiable citation — the UI must make sources prominent, not an afterthought.
2. **Never hide a failure.** Retrieval misses, provider errors, and empty knowledge-base results are surfaced honestly and specifically, never papered over with generic "something went wrong."
3. **Research and drafting are one flow.** The chat and the artifact viewer are peers, not chat-then-export — the essay/artifact appears live beside the conversation that produced it.
4. **Respect the user's patience.** Local-model latency is real; make waiting legible and give the user control (switch provider, keep chatting) rather than a blank frozen screen.
5. **This is an operator tool, not a marketing surface.** Optimize for scanability, low cognitive load, and task completion over spectacle.

## Accessibility & Inclusion

WCAG 2.1 AA target (carried over from docs/design.md): semantic HTML/landmarks, ≥4.5:1 text contrast, full keyboard navigation with visible focus, `aria-live` on the message stream, labeled icon-only buttons, 44px minimum touch targets.
