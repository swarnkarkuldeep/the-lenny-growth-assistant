---
name: The Lenny Growth Assistant
description: A podcast archive turned into evidence — sessions as a tracklist, chat as a deck, citations as stamped cue-point chips, generated essays as a paper sleeve insert inside a dark record-sleeve board.
colors:
  ink-void: "#0d0c0a"
  board: "#15130f"
  board-raised: "#1c1a15"
  board-line: "#2c2820"
  board-line-strong: "#3c362a"
  paper: "#efe9db"
  paper-raised: "#f7f3e9"
  paper-line: "#d9d0b8"
  paper-ink: "#221f18"
  paper-ink-dim: "#58513f"
  bone: "#f3efe4"
  bone-dim: "#b8b2a0"
  bone-faint: "#7a7565"
  amber: "#e8a23d"
  amber-strong: "#ffb85c"
  amber-dim: "#7a5a2c"
  amber-ink: "#1f1608"
  signal-good: "#7fb787"
  signal-warn: "#e8a23d"
  signal-bad: "#d9705f"
typography:
  display:
    fontFamily: "IBM Plex Sans, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "normal"
  headline:
    fontFamily: "IBM Plex Sans, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "normal"
  body:
    fontFamily: "IBM Plex Sans, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  read:
    fontFamily: "IBM Plex Serif, Georgia, serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "normal"
  label:
    fontFamily: "IBM Plex Mono, SFMono-Regular, Consolas, monospace"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.08em"
rounded:
  sm: "3px"
  md: "5px"
  chip: "999px"
spacing:
  1: "0.25rem"
  2: "0.5rem"
  3: "0.75rem"
  4: "1rem"
  5: "1.5rem"
  6: "2rem"
  7: "3rem"
  8: "4rem"
components:
  button-primary:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.amber-ink}"
    rounded: "{rounded.md}"
    padding: "0 1rem"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.amber-strong}"
    textColor: "{colors.amber-ink}"
    rounded: "{rounded.md}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.bone-dim}"
    rounded: "{rounded.md}"
    padding: "0 1rem"
    height: "44px"
  citation-chip:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.amber-strong}"
    typography: "{typography.label}"
    rounded: "{rounded.chip}"
    padding: "2px 0.5rem"
  session-row-active:
    backgroundColor: "{colors.board-raised}"
    textColor: "{colors.bone}"
    rounded: "{rounded.md}"
    padding: "0.5rem 0.75rem"
  insert-control:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.paper-ink}"
    rounded: "{rounded.sm}"
    padding: "0 0.75rem"
    height: "36px"
---

# Design System: The Lenny Growth Assistant

## Overview

**Creative North Star: "The Sleeve Board and the Liner Notes"**

The product is a podcast archive turned into cited evidence, and the UI refuses the generic "chat bubble app" shape to say so. Sessions read as a **tracklist**, the conversation is **the deck**, citations are **stamped cue-point chips**, and a generated essay slides in as a **sleeve insert** — a distinct paper-toned reading register set inside a near-black record-sleeve board. The world is a committed dark identity, not a light/dark toggle: charcoal board, warm bone ink, and exactly one accent (vinyl-label amber) reserved for interactive, active, and citation elements only.

The pairing of a geometric grotesk (IBM Plex Sans) for chrome, a disciplined monospace (IBM Plex Mono) for every numeral/id/timestamp, and a serif built for reading (IBM Plex Serif) for essay body copy gives the board a "catalog" register and the insert a "booklet" register without breaking the shared token system. Depth is conveyed by tonal layering and a single soft ambient shadow under raised panels, never by hard-offset neobrutalist blocks. The build stays true to its own restraint: amber never appears in paragraph text, and every mechanical indicator (health dot, essay-compliance checklist, provider switch thumb) renders a real state change rather than a flat badge.

**Key Characteristics:**
- Near-black charcoal board with a single warm-amber accent, used only for interaction/citation/status, never decoration.
- Three-zone frame: tracklist (sessions) / deck (chat) / insert (artifact), each a materially distinct register.
- IBM Plex Sans (UI), IBM Plex Mono (all numerals, ids, timestamps, labels), IBM Plex Serif (essay/artifact reading copy).
- Citations are stamped mono cue-point chips (`Speaker · Episode · HH:MM:SS`), never bare hyperlinks.
- Flat-by-default surfaces; the only shadows are soft ambient panel/insert shadows, never hard offset blocks.

## Colors

The board is achromatic charcoal and bone; amber is the sole accent and is rationed to interactive and evidentiary elements.

### Primary
- **Vinyl-Label Amber** (`#e8a23d`, hover/strong `#ffb85c`, dim/border `#7a5a2c`, ink-on-amber `#1f1608`): the one accent. Used on the active session's left-edge marker, the primary CTA ("Cut an Essay"), the send button, citation chips, the provider-switch active label, and the health dot's good state. Never used for decorative fills or in paragraph text.

### Neutral
- **Ink Void** (`#0d0c0a`): the app's outermost background and the assistant message bubble fill — the darkest register.
- **Board** (`#15130f`): the sleeve-board ground — header, sidebar, deck base.
- **Board Raised** (`#1c1a15`): one step up for hover/active rows, user message bubbles, example-prompt cards.
- **Board Line / Board Line Strong** (`#2c2820` / `#3c362a`): hairline dividers and input/control borders on the dark board.
- **Bone** (`#f3efe4`): primary text on the board.
- **Bone Dim / Bone Faint** (`#b8b2a0` / `#7a7565`): secondary text, metadata, placeholder copy on the board.
- **Paper** (`#efe9db`, raised `#f7f3e9`, line `#d9d0b8`): the sleeve-insert ground — a warm, achromatic paper tone distinct from the board, never amber-tinted.
- **Paper Ink / Paper Ink Dim** (`#221f18` / `#58513f`): text on the paper register.

### Named Rules
**The One-Accent Rule.** Amber is the only chromatic accent in the system. It appears exclusively on interactive, active, or citation-bearing elements (buttons, active rows, chips, the provider-switch thumb, the good-state health dot) and never as a decorative fill or paragraph-text color.

**The Board/Paper Split Rule.** The deck (chat) and sidebar live on the dark board register; the artifact/insert lives on the paper register. The two never swap: essay and artifact reading copy is always paper-toned, chat and chrome are always board-toned. A visible seam (`--shadow-insert`) marks the transition, it is never a flat abutment.

## Typography

**Display/UI Font:** IBM Plex Sans (with `-apple-system, Segoe UI, sans-serif`)
**Reading Font:** IBM Plex Serif (with `Georgia, serif`)
**Label/Mono Font:** IBM Plex Mono (with `SFMono-Regular, Consolas, monospace`)

**Character:** A geometric grotesk runs the chrome (nav, buttons, chat prose), a disciplined monospace stamps every numeral and metadata field to a strict grid (session numbers, timestamps, citation codes, health/validation labels), and a serif takes over only inside the paper insert for essay/artifact body copy — a deliberate register change that signals "you are now reading a document," not chatting.

### Hierarchy
- **Display** (600, 1.75rem/28px, 1.25 line-height): the insert's H1 for generated essay titles.
- **Headline** (600, 1.375rem/22px, 1.25): insert H2, deck section headers.
- **Title** (500, 0.9375rem/15px): session row titles, message bubble prose lead lines.
- **Body** (400, 0.9375rem/15px, 1.5 line-height): chat message prose on the board.
- **Read** (400, 1.0625rem/17px, 1.7 line-height, IBM Plex Serif, ~38rem measure): essay/artifact body copy inside the insert — the one place line-height opens up for sustained reading.
- **Label** (600, 0.6875rem/11px, 0.08em tracking, uppercase, IBM Plex Mono): stamped metadata — sidebar title, message role tag, citation chip text, insert stamp/type line.

### Named Rules
**The Stamped-Metadata Rule.** Every id, timestamp, role tag, and reference code renders in IBM Plex Mono at 11px with 0.08em tracking, uppercase where it's a label. This is the one place the type system enforces a strict grid; prose never borrows this treatment.

**The Register-Change Rule.** Serif (IBM Plex Serif) is reserved for the insert's generated reading content. It never appears in the deck, sidebar, or chrome — the font change itself is what tells the user they've crossed from conversation into document.

## Layout

Desktop is a fixed three-zone frame under a single header: sidebar (240px, tracklist) / deck (flexible, ~58%) / insert (flexible, ~0.75fr of the remaining space). The header is a 4-column grid (hamburger · brand · mobile tabs · health badge) and stays pinned; a dismissible error banner can appear beneath it. Spacing runs a 4px-based scale (`--space-1` 4px through `--space-8` 64px); component internal padding sits mostly at `--space-3`/`--space-4` (12–16px), section rhythm at `--space-5`/`--space-6` (24–32px). All interactive targets hold a 44px minimum height (send button, composer input, session rows, CTA buttons), matching PRODUCT.md's accessibility commitment.

At ≤1024px the sidebar narrows to 220px. At ≤768px the frame collapses to a single visible pane: a hamburger opens the sidebar as a fixed off-canvas drawer (`translateX`, 320px max, with a dark scrim behind it) and a header tab pair ("Deck"/"Insert") switches which of the two remaining panes is visible via `data-mobile-hidden`. **This mobile layout is written and reviewed in source (`App.css` `@media (max-width: 768px)` block, `App.jsx` `shell__hamburger`/`shell__mobile-tabs`/`shell__scrim`) but has not been rendered or screenshotted at a real narrow viewport in this session** — see Do's and Don'ts / open items.

## Elevation & Depth

The board is flat by default; depth comes from tonal layering (`board` → `board-raised`) plus two soft ambient shadows, never hard offset blocks. `--shadow-panel` sits under raised board surfaces; `--shadow-insert` sits under the paper insert to mark its seam against the board. The active session row uses an inset amber edge (`inset 2px 0 0 var(--amber)`) rather than a shadow to signal selection — elevation is reserved for whole-panel separation, not per-row state.

### Shadow Vocabulary
- **Panel** (`box-shadow: 0 1px 0 rgba(0,0,0,0.4), 0 12px 32px -16px rgba(0,0,0,0.6)`): ambient ground-separation shadow, available for board-level raised surfaces.
- **Insert** (`box-shadow: 0 1px 0 rgba(0,0,0,0.15), 0 16px 40px -20px rgba(0,0,0,0.45)`): marks the paper insert's seam against the dark board.

### Named Rules
**The Soft-Ambient-Only Rule.** Shadows in this system are diffuse and ambient (large blur, negative spread, low opacity), used to separate the paper insert from the board or to lift a panel off its ground. Hard-offset, high-contrast "sticker" shadows are not part of this world.

## Shapes

Corners are cut, not bubbled: radius scale is `--radius-sm` (3px, controls/inputs/hover targets), `--radius-md` (5px, panels/bubbles/buttons), and `--radius-chip` (999px, reserved for pill-shaped elements — citation chips, mobile tabs, scrollbar thumbs). Chat bubbles use the modest `--radius-md`, deliberately less rounded than a typical chat product, to keep the "deck," not a messaging app, as the reference. Borders are 1px hairlines in `board-line`/`board-line-strong` on the board and `paper-line` on the insert; there is no double-border or outline stacking outside the focus ring.

## Components

### Buttons
- **Shape:** 5px radius (`--radius-md`), 44px min height on primary/CTA/send, 36px on insert utility controls (copy/download/regenerate).
- **Primary:** amber fill (`#e8a23d`) with dark ink text (`#1f1608`) — used for "Cut an Essay"/generate CTAs and the composer send button.
- **Hover / Focus:** primary hover lightens to `#ffb85c`; all focusable elements get the shared 2px-offset amber focus ring (`--focus-ring`), never a browser default outline.
- **Ghost:** transparent fill, `bone-dim` text, `board-line-strong` border; hover shifts border to `amber-dim` and text to `bone`. Used for secondary actions (regenerate, cancel) beside a primary CTA.

### Chips
- **Style:** citation chips are pill-shaped (`--radius-chip`), amber-tinted background (`color-mix` 10% amber over transparent), amber-dim border, mono text at 11px — `▸ Speaker HH:MM:SS`, rendered as a real `<a>` when a source video URL exists, otherwise a `<span role="note">`.
- **State:** hover/focus deepens the amber tint and solidifies the border; chips never lose their border treatment, they are never bare text links.

### Cards / Containers
- **Corner Style:** 5px radius on message bubbles and example-prompt cards.
- **Background:** user bubbles use `board-raised`; assistant bubbles use `ink-void` (the darkest ground) to read as "the deck speaking."
- **Shadow Strategy:** none at the bubble level; depth comes from the tonal fill difference only (see Elevation & Depth).
- **Border:** 1px `board-line`, strengthening to `board-line-strong` on user bubbles.
- **Internal Padding:** `--space-3` vertical, `--space-4` horizontal.

### Inputs / Fields
- **Style:** `ink-void` background, 1px `board-line-strong` border, 5px radius, 44px min height (composer input).
- **Focus:** border shifts to `amber-dim`; the shared focus-ring box-shadow applies on `:focus-visible`.
- **Disabled:** 0.6 opacity, no color change.

### Navigation (Sidebar / Tracklist)
- Sessions render as numbered track rows (mono track number, title, mono relative-date "runtime"). Hover raises to `board-raised`; the active row keeps that same fill plus an inset amber left edge and promotes its track number to amber-strong — the single-elevation-over-siblings rule made concrete. Delete affordance is icon-only, hidden until row hover/focus, 44px row height throughout. Mobile treatment: fixed off-canvas drawer with scrim, per Layout.

### Provider Switch (signature component)
A two-position hardware-style toggle (`role="radiogroup"`, two `role="radio"` buttons: "Cloud · Gemini" / "Local · Ollama") with a sliding thumb (`translateX`, 200ms `--ease-deck`) rather than a `<select>` or checkbox — the literal embodiment of the direction contract's "hardware switch" raise. Repeated in the header and inline in the composer so provider choice is always visible without navigation.

### Health Badge / Compliance Checklist (signature component)
The header health dot and the insert's essay-validation checklist share one doctrine: state is shown by an actual color/animation change (`good`/`warn`/`bad`/`idle`-pulsing dot; per-check pass/fail mono marks with distinct green/amber-brown ink), never a flat static badge. This is the "honest mechanical indicator" raise from the direction contract's nixie-tube reference.

## Do's and Don'ts

### Do:
- **Do** ration amber to interactive, active, and citation elements only (The One-Accent Rule).
- **Do** render citations as stamped mono cue-point chips (`Speaker · Episode · HH:MM:SS`) with a real anchor when a source URL exists.
- **Do** keep the insert's reading copy in IBM Plex Serif and everything else in IBM Plex Sans/Mono (The Register-Change Rule).
- **Do** show real state changes for health/compliance/status indicators (color, animation) rather than a static badge.
- **Do** keep every interactive target at a 44px minimum (composer input/send, session rows, CTA buttons), per PRODUCT.md's accessibility commitment.

### Don't:
- **Don't** let amber bleed into paragraph or prose text on either the board or the paper register — it is confirmed reserved for interactive/citation/status use only.
- **Don't** round chat bubbles into a generic messaging-app shape; the 5px radius is deliberately restrained to keep "the deck" distinct from a chat product.
- **Don't** use hard-offset "sticker" shadows; this system's depth vocabulary is soft ambient panel/insert shadows and tonal layering only (The Soft-Ambient-Only Rule).
- **Don't** treat the mobile off-canvas/tab-switcher layout as finish-verified — it is implemented and reviewed in source but has never been rendered or screenshotted at a real mobile viewport (tooling limitation in this session; see sidecar `narrative.donts` and Layout section).
