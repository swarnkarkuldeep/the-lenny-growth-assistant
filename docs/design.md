# Design: The Lenny Growth Assistant

> **Direction:** The frontend (Phase 6) ships a committed visual identity chosen via the Impeccable design skill:
> a "liner notes / tracklist" system. Sessions render as a **tracklist**, the chat is the **deck**, citations are
> stamped **cue-point chips**, and the artifact viewer is a **sleeve insert** — a distinct paper-toned reading
> surface beside the dark board. Full direction contract, the six candidate directions considered, and the
> reasoning against six dealt reference-world challengers live in `.impeccable/surfaces/frontend.md`. The
> sections below (Visual Design) describe what actually shipped; everything else in this document (information
> architecture, interaction states, accessibility, responsive rules) still holds and was preserved through the
> re-skin.

## Design Principles

1. **Clarity over cleverness** — Users should always know what the system is doing and why. Transparent about sources, limitations, and failures.
2. **Grounding first** — Every answer traces back to a real expert. Show citations prominently.
3. **Scaffolding, not blank page** — Generated essays provide a strong starting point, not a finished product. Users can edit and ship.
4. **Low friction** — Minimal setup, one-command run, clear error messages guide troubleshooting.
5. **Honest about trade-offs** — Local model is slower and lower-quality; this is expected and documented.

---

## Information Architecture

### Main Layout: Two-Pane Responsive

**Desktop (>768px):**
```
┌─────────────────────────────────────────────────────────┐
│ Header: Logo | Title | Provider Selector | Health Badge │
├──────────────────┬──────────────────────────────────────┤
│                  │                                       │
│   Chat Pane      │     Artifact Viewer Pane             │
│   (60%)          │     (40%)                             │
│                  │                                       │
│  - Message List  │  - Rendered Markdown/HTML            │
│  - Input + Send  │  - Copy / Download buttons           │
│                  │                                       │
└──────────────────┴──────────────────────────────────────┘
```

**Mobile (<768px):**
```
┌──────────────────────────────────┐
│ Header (compact)                  │
├──────────────────────────────────┤
│ Chat Pane (full width)            │
│  - Message List                   │
│  - Input + Send                   │
│  - Artifact Viewer (expandable)   │
└──────────────────────────────────┘
```

### Chat Pane Components

- **Message History:** Scrollable list, user messages right-aligned (light background), assistant messages left-aligned (darker background)
- **Citations:** Inline links for each cited episode (episode name, speaker, timestamp) with hover tooltip showing video URL
- **Input Area:** Text input field + Send button + Provider selector (sticky at bottom)
- **Session Switcher:** Collapsible sidebar or top dropdown showing recent sessions

### Artifact Viewer Components

- **Rendered Content:** Full-width rendered HTML/Markdown, scrollable
- **Controls:** 
  - Copy button (copy artifact to clipboard)
  - Download button (save as .md or .html)
  - Regenerate button (re-run artifact generation with same context)
- **Fallback (no artifact):** "No artifact yet. Ask a question or click 'Generate Essay' to create one."

---

## Key Interaction States

### 1. **Empty State** (First Load)
- Chat pane shows welcome message: "Ask a question about product, growth, or strategy. I'll ground my answer in Lenny's Podcast."
- Provider selector visible: defaults to "Cloud (Gemini)" with tooltip explaining the difference
- Example questions displayed as clickable cards (e.g., "What makes a good pricing model?")
- Artifact viewer pane shows: "No artifact yet."

### 2. **Waiting for Response** (User Submitted Message)
- User message appears in chat immediately
- Spinner appears in assistant message area
- Input field disabled ("Waiting for response...")
- Provider selector disabled (locked to prevent mid-request switches)
- Artifact viewer unchanged

### 3. **Response Received (Success)**
- Assistant response appears with citations rendered as links
- Spinner disappears
- Input field re-enabled
- Provider selector re-enabled
- **New button appears:** "Generate Essay" (or `/essay` command)
- If essay/artifact is present, Artifact Viewer updates with rendered content

### 4. **Response Received (No Retrieval Results)**
- Assistant response: "I don't have information on this topic in the knowledge base. Try a different question."
- Citations empty
- Artifact viewer remains unchanged
- Input field re-enabled

### 5. **Provider Error**
- Assistant response (error state):
  ```
  Error: Claude API rate limited
  Reason: Rate limit exceeded; try again in 30 seconds
  Suggested action: Switch to local model (Ollama) or wait
  ```
- Provider selector highlighted in red
- User can change provider and resubmit without losing message history
- Input field re-enabled

### 6. **Artifact Generation**
- User clicks "Generate Essay" button (or `/essay` command)
- Spinner appears in artifact viewer
- Chat continues to function (user can ask follow-ups while artifact generates)
- Once artifact is ready:
  - Rendered Markdown/HTML appears in artifact viewer
  - "Copy" and "Download" buttons appear
  - "Regenerate" button available
  - Artifact scrolls into view (or notification)

### 7. **Artifact in Viewer (Safe Rendering)**
- Rendered HTML/Markdown is sanitized (safe to display)
- All external links open in new tab
- Code blocks have light background, monospace font
- Blockquotes have left border, light background
- No scripts run, no iframes load, no onclick handlers fire

### 8. **Artifact Copy/Download**
- User clicks "Copy" → text copied to clipboard, button shows "Copied!" for 2 seconds
- User clicks "Download" → browser downloads file as `lenny-essay-{timestamp}.md` or `.html`
- Both are non-disruptive

---

## Visual Design

As shipped in `frontend/src/styles/tokens.css`. This is a committed single identity (see note above), not a
light/dark toggle: the board is deliberately dark, the sleeve insert is deliberately paper-toned, and every
text/background pairing below was checked against WCAG AA (≥4.5:1 for body text).

### Color System

**The board** (header, tracklist, deck — `.shell`, `.sidebar`, `.deck`):
- Ground: `#0d0c0a` (void) / `#15130f` (board) / `#1c1a15` (raised surfaces)
- Ink: `#f3efe4` (bone, primary text) / `#b8b2a0` (dim) / `#7a7565` (faint/metadata)
- Lines: `#2c2820` / `#3c362a`
- **The one accent** — vinyl-label amber `#e8a23d` (`#ffb85c` hover/active) — used only for interactive
  elements, citations, and the active session marker. Never decorative, never in paragraph text.
- Signal colors (status only): good `#7fb787`, warn `#e8a23d`, bad `#d9705f`

**The sleeve insert** (artifact viewer — a distinct paper register inside the dark board):
- Ground: `#efe9db` (paper) / `#f7f3e9` (raised)
- Ink: `#221f18` (primary) / `#58513f` (dim)
- Rule: `#d9d0b8`

### Typography

- **UI chrome** (nav, buttons, headers, message roles): IBM Plex Sans
- **Metadata / ids / timestamps / citation chips**: IBM Plex Mono, uppercase, letter-spacing 0.08em for stamped
  labels ("TRACKLIST", "SLEEVE INSERT")
- **Essay / artifact reading copy** (inside the sleeve insert only): IBM Plex Serif, 17px, 1.7 line-height —
  a deliberately different, slower register from the app chrome around it
- **Type scale:** 11 / 12 / 13 / 15 / 17 / 22 / 28px (`--text-2xs` through `--text-xl`)

### Spacing & Components

- 4px base spacing scale (`--space-1` = 4px … `--space-8` = 64px)
- Corners are precise, not bubbly: 3–5px radii on cards/inputs, full pill only for chips and the tab switcher
- Provider selection is a two-position hardware-style switch (`ProviderSwitch`), not a `<select>` — reinforces
  that Cloud/Local is a real, consequential toggle (per PRD Assumption 3), not an incidental preference
- Every validation/health readout (essay compliance checks, health badge) renders as an honest state change on a
  literal indicator (a dot, a check/× list) rather than a flat badge
- Citations render as stamped `[Speaker · timestamp]` cue-point chips below a message, not as inline bare links
- Deck max message width: 44rem · Sleeve insert reading column: 38rem, centered

---

## Responsive Behavior

### Breakpoints

- **Mobile:** <768px
  - Single column layout (chat full-width, artifact below or modal)
  - Smaller fonts (14px base)
  - Collapsed session switcher (hamburger menu or dropdown)
  - Provider selector inline with input
  - Artifact viewer as expandable section below chat

- **Tablet:** 768px–1024px
  - Two-column layout starts to appear
  - Consider 50/50 split or 60/40

- **Desktop:** >1024px
  - Full two-pane layout (60/40)
  - Sidebar with session switcher
  - All controls visible

### Touch Interactions

- Larger touch targets: 44px minimum height for buttons
- Tap to cite (opens episode details or links to YouTube)
- Swipe to reveal artifact (on mobile, swipe left to see artifact pane)

---

## Accessibility Considerations

### WCAG 2.1 Level AA Target

1. **Semantic HTML:**
   - Use `<button>` for buttons (not `<div>`)
   - Use `<a>` for links with proper `href`
   - Use `<main>`, `<aside>`, `<nav>` landmarks

2. **Color Contrast:**
   - Text and background contrast ≥4.5:1 for normal text, ≥3:1 for large text
   - Don't rely on color alone; use icons/labels

3. **Keyboard Navigation:**
   - All interactive elements focusable via Tab
   - Focus indicator visible (outline or color change)
   - Tab order logical (left-to-right, top-to-bottom)
   - Escape key closes modals/expandables

4. **Screen Readers:**
   - `aria-label` on icon buttons (e.g., "Generate essay", "Copy to clipboard")
   - `aria-live="polite"` on message list (announces new messages)
   - `aria-expanded` on collapsible sections
   - Alt text not needed for decorative images; use `alt=""` or `aria-hidden="true"`

5. **Focus Management:**
   - When a response arrives, focus moves to new message (or announce via `aria-live`)
   - When artifact updates, focus moves to artifact pane or announcement made

6. **Form Inputs:**
   - `<label>` associated with input (or `aria-label`)
   - Error messages associated with inputs via `aria-describedby`
   - Clear, descriptive placeholder text

### Testing

- Manual testing with keyboard-only navigation (no mouse)
- Screen reader testing (NVDA, JAWS, or VoiceOver)
- Lighthouse audit for accessibility score

---

## Error UI States

### Validation Error (Invalid Input)
- Input field border turns red
- Error message below input: "Message cannot be empty."
- User can correct and resubmit

### Provider Error (LLM Unavailable)
- Error card appears above chat:
  ```
  ⚠️ Claude API Error
  Rate limited; try again in 30 seconds
  Or switch to Local (Ollama)
  [Dismiss]
  ```
- User can click provider selector to switch

### Retrieval No Results
- Assistant response: "No information found on this topic."
- Citation list empty
- User can rephrase question and try again

### Network Error
- Error card: "Network error. Check your connection and try again."
- Retry button available
- Message history is preserved

---

## Microcopy & Tone

- **Friendly, not robotic:** "I don't have that information yet" (not "null retrieval result")
- **Honest about limitations:** "The local model is slower but works fully offline"
- **Clear call-to-action:** "Generate an essay from this answer" (not "Proceed to artifact generation")
- **Encouraging:** "Great question! Here's what I found:" (not just the answer)

---
