---
canonical_id: R10_Y_S1
version: 1.0
status: CURRENT
session_id: Y-S1
title: Citation hover snippet tooltip on dwell
depends_on: [X-S11]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — client-only tooltip, reads from CitationCtx"
authored: 2026-05-20
---

# Y-S1 — Citation Hover Snippet

## Context

Chat V2 renders inline citation superscripts `[^1]` via `NumberedCitation` components. Hovering over them currently shows nothing (or the citation key only). This session adds a tooltip that shows the citation's text snippet on dwell (>350ms hover), drawn from the citation data already present in `CitationCtx`.

To expose snippets from `CitationCtx`, the context's `citationRichMap` may need to be extended to include a `snippet` field (check what is currently stored; if snippet is already there, no context change is needed).

**Amendment 3:** FLAGLESS — additive tooltip, reads existing context data, no backend call.

**Amendment 2:** Visible component (tooltip on NumberedCitation) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/citation/NumberedCitation.tsx` — add tooltip on dwell
- `platform/src/components/chat-v2/citation/CitationCtx.tsx` — extend `citationRichMap` to expose `snippet` field if not already present
- `platform/src/components/chat-v2/citation/CitationTooltip.tsx` (new, optional) — tooltip component if logic is complex enough to extract
- `platform/tests/` — integration test

## Files Must NOT Touch

- Server-side citation assembly
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

1. **click-path (Amendment 2):** User path: Chat V2 response with numbered citations → hover mouse over `[^1]` superscript for >350ms → a tooltip appears showing the citation's text snippet (first ~100 chars of the signal text) → mouse leaves → tooltip disappears. Document in commit body.
2. **Dwell delay:** Tooltip only appears after 350ms of continuous hover. Rapid mouse-overs do not flash the tooltip.
3. **Snippet content:** Tooltip shows the citation's `snippet` field from `CitationCtx`'s `citationRichMap`. If `snippet` is not yet in the map, extend the context + data flow to include it (first ~100 chars of signal body text, truncated with ellipsis if longer).
4. **Dismiss:** Tooltip disappears when mouse leaves the citation element. No click required to dismiss.
5. **Tooltip positioning:** Tooltip appears above or below the citation (whichever fits in viewport). Does not overflow viewport edges.
6. **Accessibility:** Tooltip content is available via `aria-describedby` or `title` attribute fallback.
7. **Parent-context integration test (Amendment 2):** At least one test mounts `NumberedCitation` within a real `CitationCtxProvider` (populated with citation data including snippet) and asserts: (a) before 350ms hover, no tooltip; (b) after 350ms simulated hover (fake timer), tooltip with snippet text is visible. Direct props test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
npx jest --testPathPattern="NumberedCitation|citation.*hover|CitationTooltip|citation.*snippet" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): citation hover tooltip shows snippet on 350ms dwell

NumberedCitation gains tooltip via CitationCtx citationRichMap.snippet.
350ms dwell delay, viewport-aware positioning, aria-describedby.
CitationCtx extended to expose snippet if not already present.
Flagless per §M.16.

Click-path: hover [^1] → 350ms → snippet tooltip appears.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
