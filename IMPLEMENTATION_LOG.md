# Implementation Log: The Lenny Growth Assistant

This is a factual log of how the project was actually built — decisions made, problems hit, and how they were resolved — not a restatement of the plan. Full session transcripts live in `agent-transcripts/`.

## Timeline & Milestones

### Phase 1: Infrastructure (`b557486`)
Docker Compose (Postgres, Ollama, FastAPI), SQLAlchemy models, raw-SQL migration, Pydantic v2 settings, `/health` endpoint.
- **Issue:** Pydantic v2 + SQLAlchemy declarative base interaction needed adjustment before the settings/model layer worked together; resolved during TDD before moving on (28/28 tests passing at close).
- **Decision:** switched the cloud LLM from Claude to Google Gemini (`f0bf941`) — done immediately after Phase 1, before any LLM integration code existed, so the change touched PRD/architecture/design docs, `requirements.txt`, `config.py`, `.env.example`, and `docker-compose.yml` in one pass rather than as a later migration.

### Phase 2: Retrieval & Ingestion (`cbe8d19`, `7acaf26`, `a3e1267`, `d116457`, `c069d21`)
Speaker-turn transcript chunker, ingestion script, retrieval service, `/retrieve` debug endpoint.
- **Issue:** initial schema stored embeddings as `TEXT` because pgvector wasn't available in the base `postgres:15` image and retrieval had to run a temporary keyword-fallback. Switched to `pgvector/pgvector:pg16`, added `CREATE EXTENSION vector`, and changed the embedding column to a real `vector(768)` type (`nomic-embed-text` produces 768-dim vectors, not 384 as originally assumed in the plan draft) — `c069d21`.
- **Issue:** host-side scripts/tests and in-Docker services need different `DATABASE_URL` values (`postgres:5432` internally vs. the host-mapped port) — introduced `.env.test` for host-side runs (`d116457`).
- **Result:** 180 chunks ingested from Lenny's Podcast transcripts, 8/8 retrieval tests passing, semantic search verified via `curl`.

### Phase 3: LLM Integration (`7ab3634`, `dd98706`, `bed598f`)
Provider abstraction (`GeminiProvider`/`OllamaProvider`), system prompts for Q&A/essay/artifact.
- **Issue:** `gemini-1.5-flash` (from the original plan) was not a valid/available model name at implementation time — corrected to `gemini-flash-latest` (`dd98706`).
- **Issue:** the Q&A prompt's grounding instruction was interpreted too literally by Gemini, causing it to refuse to answer questions that *were* actually supported by retrieved chunks (a false "no information" refusal). Root-caused during Phase 4 manual testing and fixed by relaxing the prompt's wording while keeping the grounding requirement (`bed598f`) — verified against both true-positive (answerable) and true-negative (genuinely unsupported) queries afterward.

### Phase 4: API Endpoints & Orchestration (`e528954`)
Session CRUD, `/chat` with retrieval + generation + citation extraction + attribution validation.
- Manual edge-case pass: 16 automated + 10 manual scenarios (missing session, invalid provider, empty message, provider unreachable, etc.) before moving on.

### Phase 5: Essay & Artifact Generation (`557dbfb`)
Ship 30/30 essay validator (word count, headings, takeaway, citations, claim traceability), `/essays` and `/artifacts` endpoints, `bleach`-based HTML sanitization.
- **Issue:** `bleach`'s dependency on `html5lib`/`protobuf` needed a version pin to resolve alongside `google-generativeai`'s own protobuf constraint.
- **Issue:** Gemini free-tier rate limits (`429`) intermittently blocked live-inference tests; resolved by waiting for quota reset and, longer-term, by writing tests that assert response *contracts* rather than requiring a live model call to succeed (see Phase 7).
- **Result:** 18/18 new automated tests passing at commit time; full suite 57 passed / 7 failed (the 7 were pre-existing, unrelated to this phase — see Phase 7 for the actual root cause).

### Phase 6: Frontend (`01b3da6`, merged to main in `a11cfa7`)
React + Vite chat UI, provider switch, session sidebar, artifact viewer (Markdown via `react-markdown`, HTML via `DOMPurify` + `dangerouslySetInnerHTML`), vinyl/cassette visual design system (`DESIGN.md`).
- **Bugs found and fixed during manual QA:** a message-stream layout bug in `App.css`, a stale-error state in `ChatPane.jsx` that didn't clear on a new successful request, and a nested-interactive-element accessibility violation in `Sidebar.jsx` (a `<button>` inside a `<button>`).
- **Bugs found and fixed post-merge:** citation timestamps weren't grounded correctly in `chat.py`, and `Sidebar.jsx` had a UTC/local timezone display bug.
- **Known gap:** true mobile-viewport rendering couldn't be verified by the agent directly (no device/browser access in that session) — verified manually, see `docs/manual-test-plan.md`.

### Phase 7: Testing & Documentation (this phase)
Added `tests/test_integration.py` (full session→chat→essay→artifact→delete workflow, plus a health-endpoint contract test) and `tests/test_artifact_safety.py` (14 XSS-payload cases run against the real `sanitize_if_html` function, not string literals — script tags in multiple cases, event handlers, `<iframe>`/`<object>`/`<embed>`/`<svg>`, `javascript:`/`data:` URIs, and a whitelist sanity check).

Five real defects surfaced while getting these tests to pass honestly (rather than writing them to fit existing behavior):

1. **Port collision on 5432.** A native Windows `postgresql-x64-18` service was already bound to port 5432, silently intercepting every host-side connection meant for the Dockerized Postgres — internal `docker exec psql` worked (bypasses the host port entirely), but `pytest` from the host got `password authentication failed` even with the correct password, because it was authenticating against the *wrong* Postgres server. Fixed by remapping the Docker service to host port **5433** (`docker-compose.yml`, `.env`, `.env.test`, `.env.example`) rather than touching the native service, since that's a reversible, repo-scoped change instead of a system-wide one.
2. **Source-attribution validator too strict for the local model's refusal wording.** `validate_response_citations()` in `src/routers/chat.py` only recognized two exact phrases ("don't have information", "not in the knowledge base") as a valid "no support" admission. Gemini reliably uses the system prompt's exact wording, but the local `llama3.2:3b` model paraphrases the same admission unpredictably ("I don't see any relevant information... unrelated to the topic", "I don't have **any** information on..."). This caused an honest, correctly-grounded refusal to fail the attribution check purely on wording. Replaced the exact-phrase list with a small set of regex patterns covering the paraphrasings actually observed in testing (captured verbatim as permanent regression cases in `tests/test_chat_api.py::test_validate_response_citations`).
3. **Same validator, a bigger gap: the local model doesn't reliably use the prompted bracket citation format at all**, even when it *does* ground its answer correctly. Observed live: asked "What is product market fit?", the local model answered correctly and cited `(Grenier, "When to invest in new acquisition channels", timestamp: 00:00:00)` — a real, correct attribution, just in parenthetical prose instead of `[Speaker, Episode, timestamp]`. The bracket-only check failed this as ungrounded. Rather than add ever more citation-format regexes (an unbounded space), `validate_response_citations` now also accepts a response as attributed if it names a speaker from the chunks that actually backed the answer *and* contains a timestamp anywhere in the text — a combination that can't happen by accident, only by referencing real retrieved evidence. Covered by `test_validate_response_citations_accepts_prose_style_citation` and a companion `test_validate_response_citations_rejects_untethered_mention` (speaker mention alone, or timestamp alone, or either without a real backing chunk, must still fail).

   **Follow-up finding after a larger sample:** repeated live runs (including a 5-call sample of the exact same gibberish query) showed `validation_passed` still isn't reliable on any *single* live call from the local provider — not just for refusals, but occasionally even for a clearly answerable question, because the 3B model at temperature 0.7 sometimes skips citing altogether or hedges without using a recognizable format. This isn't something a bigger regex list or a bounded retry count can close (a hard-3-retry version of the gibberish test still failed once in testing). Conclusion: `validation_passed` is a genuinely useful signal but is being measured on a small, chatty local model's free-text output, which is inherently non-deterministic - so the **deterministic unit tests in `test_chat_api.py` are the authoritative regression coverage for the attribution logic itself** (validated against real phrasings captured from these live runs), while `test_integration.py`'s live calls assert only what's actually reliable: the endpoint responds gracefully (200/503, well-formed body) and never crashes, without hard-asserting `validation_passed`'s value on any single non-deterministic call. This is the more consequential of the two attribution findings: it means the ≥95% source-attribution metric, if measured live against the local provider today, would need statistical sampling across many calls to report meaningfully - not a single pass/fail check - and is a candidate for the structured-output fix under Next Steps.
4. **A stray Windows *User* environment variable (`GEMINI_API_KEY=none`, paired with `GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:8090`) on the development machine was silently shadowing the real key from `.env` for every process launched in that shell** — this is a general gotcha, not specific to this project: `pydantic-settings`' `env_file` loading (correctly) gives real OS environment variables precedence over `.env` file values, and both of these looked like leftover config from an unrelated local LLM proxy/gateway tool. This initially produced a `400 API_KEY_INVALID` error that was misdiagnosed as an invalid/wrong-format key — the actual key value from `.env` (starting `AQ.`, a legitimate Google AI Studio key format) was never the problem; it was never being read at all. Removed both stray vars at the Windows User scope. With the real key actually reaching Google's API, the true (and expected) result is `429 RESOURCE_EXHAUSTED` — the free tier's `GenerateRequestsPerDayPerProjectPerModel` daily quota (20 requests/day, exhausted by repeated testing in this session). `test_llm_gemini.py::test_gemini_qa_response` now distinguishes the two: it skips gracefully on a quota/429 error (an expected operational condition for a free-tier key, not a defect) but still fails hard on a genuine `API_KEY_INVALID` — verified against both cases directly. **Lesson:** always verify a "credential invalid" error against the raw value actually being sent, not just the value in the config file, before concluding the credential itself is bad.

5. **Intermittent `ForeignKeyViolation` on `artifacts.session_id` — but only during a long (~8 minute) full-suite run, never in isolation.** `test_artifacts_api.py::test_generate_html_artifact_is_sanitized_end_to_end` failed once with Postgres reporting the session referenced by a fresh artifact insert simply didn't exist, despite that exact session having just been used successfully by a preceding `/chat` call in the same test. Re-ran the same test standalone 3 times (67s, 162s, 133s) with zero failures, which rules out a logic bug in the test or the endpoint and points at the pooled DB connection itself: `src/db/database.py`'s `create_engine()` had no `pool_pre_ping`, so a connection that had been idle in the pool for a while (plausible after several minutes of local-model generation elsewhere in a long suite run) can go stale under Docker Desktop's networking (idle TCP connections get silently dropped) and then be handed to a request that reads/writes against it, surfacing as a confusing downstream error rather than a clean "connection lost." Added `pool_pre_ping=True`, which makes SQLAlchemy cheaply verify (`SELECT 1`) a pooled connection before use and transparently reconnect if it's dead — the standard fix for exactly this symptom class, not specific to this project.

Note: the `/chat` response's structured `citations` list (used by the frontend to render clickable citation chips) is still only populated by the bracket-style extractor (`extract_citations_from_response`); a prose-style citation now passes the attribution *check* but won't appear as a structured citation chip in the UI. Extending extraction to prose style is listed under Next Steps.

**Final state:** `pytest tests/ -v` — **88 passed, 1 skipped** (Gemini free-tier daily quota; not a defect), 0 failed. Verified with a correctly-passed `GEMINI_API_KEY` (see defect 4) and after the `pool_pre_ping` fix (defect 5).

## Key Decisions

1. **Per-message provider selection** — lets one session compare Cloud vs. Local answers side by side, and keeps provider failures scoped to a single request instead of the whole session.
2. **Speaker-turn chunking** with token-based overflow splitting — respects natural dialogue boundaries in transcripts rather than fixed-size windows that could cut a citation mid-sentence.
3. **Strict provider mode, no silent fallback** — a provider failure surfaces as an explicit error so the user knows which model actually failed, rather than silently getting a different model's answer.
4. **Double sanitization for HTML artifacts** — `bleach` server-side before persistence, `DOMPurify` client-side before render — defense in depth rather than trusting a single layer.
5. **Attribution validated by evidence (real speaker + timestamp), not by a fixed citation format** — a small local model's phrasing and citation style are inherently non-deterministic; requiring an exact bracket format would keep failing correct, grounded answers, so the check also accepts prose citations that name a real retrieved speaker alongside a timestamp.
6. **Synchronous essay/artifact generation** — no background job queue; simpler for the assessment's scope, at the cost of the request blocking for the local model's full generation time (documented as a known latency trade-off, not hidden).

## Known Limitations

1. **Local model quality, phrasing, and citation-format variance** — `llama3.2:3b` is weaker than Gemini, paraphrases refusals unpredictably, and doesn't reliably follow the prompted bracket citation format even when correctly grounded (see Phase 7, defects 2–3); the evidence-based attribution check (real speaker + timestamp) is a practical mitigation, not a guarantee, and its structured `citations` list still only recognizes bracket-style output (see the Phase 7 note above).
2. **Static knowledge base** — no live/incremental transcript refresh; re-running `scripts/ingest_transcripts.py` rebuilds the chunk/embedding tables from scratch.
3. **Simplified claim traceability** — the essay validator checks that citations reference a speaker present in the retrieved chunks, not full semantic entailment of every claim.
4. **No multi-user auth** — single implicit user only, an explicit scope cut documented in `PRD.md`.
5. **Docs vs. code drift** — `docs/architecture.md`'s API Endpoints section predates a couple of implementation details (e.g. it doesn't list `/essays`, and shows `claude_api_key` in the health response instead of the current `gemini_api_key`). Not corrected in this phase since it was out of scope for testing/documentation deliverables, but worth a follow-up pass.

## Test Coverage (see README.md → Testing for the full breakdown)

Retrieval, ingestion, LLM providers (both), session/chat/essay/artifact API contracts, source-attribution validation (unit + live), essay structural compliance, artifact XSS safety (14 payload cases against the real sanitizer), end-to-end workflow, and infrastructure scaffolding.

## Next Steps (Post-v1)

1. Reconcile `docs/architecture.md`'s endpoint reference with the actual implementation.
2. Real-time transcript sync instead of a manual re-ingestion script.
3. Multi-user auth and per-user sessions.
4. Replace the heuristic attribution check with a small structured-output constraint on the local model (e.g. forcing a `{grounded: bool, citations: [...]}` shape) to remove the paraphrase/format-matching fragility at its root.
5. Extend `extract_citations_from_response` to recognize prose-style citations too, so they render as structured citation chips in the UI instead of only passing the attribution check invisibly.
5. Observability dashboard for retrieval quality, latency, and attribution-pass-rate over time.
