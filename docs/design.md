# Design: The Lenny Growth Assistant

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

### Color Scheme (Light & Dark Mode Support)

**Light Mode:**
- Background: #FFFFFF
- Text (primary): #1a1a1a
- Text (secondary): #666666
- Accent: #0066CC (Claude blue)
- Error: #CC0000
- Success: #00AA00
- Citation link: #0066CC (underlined)
- Message (user): #E8F4FF (light blue)
- Message (assistant): #F5F5F5 (light gray)

**Dark Mode:**
- Background: #1a1a1a
- Text (primary): #FFFFFF
- Text (secondary): #CCCCCC
- Accent: #66B3FF (lighter Claude blue)
- Error: #FF6666
- Success: #66FF66
- Citation link: #66B3FF (underlined)
- Message (user): #003D99 (dark blue)
- Message (assistant): #333333 (dark gray)

### Typography

- **Font family:** System stack (SF Pro, -apple-system, Segoe UI, Roboto, sans-serif)
- **Base size:** 16px (on desktop), 14px (mobile)
- **Headings:** Bold, 20px (H2), 18px (H3)
- **Code:** Monospace (Monaco, Courier New), 13px, light background
- **Citations:** 14px, blue, underlined, cursor: pointer

### Spacing & Layout

- **Padding:** 16px (desktop), 12px (mobile)
- **Gap between messages:** 12px
- **Chat pane max-width:** 100% (responsive)
- **Artifact pane max-width:** none (scrollable, full height)

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
