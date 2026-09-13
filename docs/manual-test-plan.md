# Manual Test Plan — Frontend (Phase 6)

Companion to the automated backend suite in `tests/`. Run this against a live stack
(`docker-compose up`, or `npm run dev` in `frontend/` against a locally running
backend) before a demo or handoff. Each row: action → expected result.

## 1. Startup & health

| # | Action | Expected |
|---|--------|----------|
| 1.1 | Load the app with backend + Postgres + Ollama all up | Header health badge shows a solid green dot and "System ready" |
| 1.2 | Stop the `fastapi` container, reload the app | Health badge turns red/"Backend unreachable"; sidebar and composer still render without crashing |
| 1.3 | With backend up but Ollama stopped, reload | Health badge shows amber/"System degraded" (hover shows which subsystem failed) |

## 2. Sessions (tracklist)

| # | Action | Expected |
|---|--------|----------|
| 2.1 | Fresh load, no sessions | Empty tracklist message; clicking "New" creates a session and switches to it |
| 2.2 | Create 2+ sessions | Newest appears at top, numbered sequentially; relative timestamps ("just now", "Xm ago") |
| 2.3 | Click a different session row | Deck reloads that session's message history; artifact viewer clears |
| 2.4 | Hover a session row, click the trash icon | Row is removed; if it was the active session, deck returns to the "select a session" state |
| 2.5 | Keyboard: Tab to a session row, press Enter | Row activates same as a click |

## 3. Grounded Q&A (the deck)

| # | Action | Expected |
|---|--------|----------|
| 3.1 | New session, no messages | Welcome copy + 3 example question cards; clicking one fills the composer |
| 3.2 | Type a question, submit with Cloud (Gemini) selected | User bubble appears immediately; assistant bubble shows a spinner; composer disables ("Waiting for response…") |
| 3.3 | Response arrives | Assistant bubble shows provider tag ("gemini"); any `[Speaker, Episode, HH:MM:SS]` in the text renders as amber cue-point chip(s) below the message |
| 3.4 | Ask a question clearly outside the knowledge base (e.g. "How do I fix a Kubernetes CrashLoopBackOff?") | Response explicitly states it has no information — no fabricated citations |
| 3.5 | Switch the provider switch to Local (Ollama) mid-session, ask another question | Same session, no new session created; response tagged "ollama"; expect longer latency (up to ~30s) |
| 3.6 | Trigger a Gemini quota/auth error (or stop Ollama and select Local) | Red error card appears above the composer with the raw provider error message and a Dismiss control; message history is preserved; composer re-enables |
| 3.7 | Reload the page mid-session | Full message history reloads from `GET /sessions/{id}`; citations re-derived from stored text still render as chips |

## 4. Essay generation (sleeve insert)

| # | Action | Expected |
|---|--------|----------|
| 4.1 | Before any message exists | "Cut an Essay" / "Generate Markdown" / "Generate HTML" buttons are hidden |
| 4.2 | After at least one exchange, click "Cut an Essay" | Button shows "Working…", disables the other two generation buttons; sleeve insert eventually shows the essay |
| 4.3 | Inspect the compliance panel | Shows word count and a ✓/× line per check (word count range, headings, takeaway, citations, claims traceable) — a failing check must show ×, not be hidden |
| 4.4 | Click Copy | Button label flips to "Copied" for ~2s; clipboard contains the raw markdown |
| 4.5 | Click Download | Browser downloads `lenny-essay-<date>.md` |
| 4.6 | Click Regenerate | Re-runs generation with the same provider/kind; insert updates in place |

## 5. Artifact generation & safety

| # | Action | Expected |
|---|--------|----------|
| 5.1 | Click "Generate Markdown" | Insert shows Markdown-rendered content via react-markdown (headings, lists, bold) — no raw `**`/`#` characters visible |
| 5.2 | Click "Generate HTML" | Insert shows sanitized HTML; open DevTools and confirm no `<script>`, `<iframe>`, or `on*` attributes exist anywhere in the rendered DOM subtree |
| 5.3 | Download the HTML artifact and open the file directly in a browser | Renders as plain static HTML with no active script execution |

## 6. Responsive & accessibility

| # | Action | Expected |
|---|--------|----------|
| 6.1 | Resize/DevTools device toolbar to ≤768px width | Header shows a hamburger + Deck/Insert tabs; tracklist becomes an off-canvas drawer with a scrim; only one of deck/insert is visible at a time |
| 6.2 | Open the drawer, select a session | Drawer closes automatically, Deck tab is shown |
| 6.3 | Tab through the page with keyboard only, no mouse | Every interactive element (session rows, provider switch, composer, send, CTA buttons, artifact controls) is reachable and shows a visible focus ring |
| 6.4 | Screen reader (NVDA/VoiceOver) on the message stream | New messages are announced (`aria-live="polite"` region) |
| 6.5 | Run a Lighthouse accessibility audit against the built app | No critical contrast or landmark violations |

> **Known tooling gap:** the automated browser check in this pass could not resize an
> actual window (the `resize_window` tool no-oped in this environment), so 6.1–6.2 were
> verified by CSS/code review, not a live screenshot. Re-verify with real DevTools
> device emulation before the demo recording.
