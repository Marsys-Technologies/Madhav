---
canonical_id: CHAT_V2_R7_S4_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R7
session_id: R7-S4
owner: chat-v2/round7-polish worktree
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
flag_namespace: MARSYS_FLAG_R7_PANEL
authored: 2026-05-20
depends_on: [R7-S3]
---

## Context

The `CitationSidePanel` currently operates in a pin-gated mode: the panel only populates and reveals a citation's details when the user explicitly clicks the pin icon on a citation badge. This creates friction — users must discover and operate the pin control to see any citation context, even though the panel is the primary surface for citation depth.

R7-S4 removes the gate. When an assistant message finishes streaming and carries one or more citations, the panel slides open automatically, listing all citations from that message in order. The pin action is demoted from a visibility gate to a per-row "star/bookmark" affordance within the already-open panel. The panel becomes a passive, always-ready surface rather than an on-demand drill-down triggered by an explicit pin gesture.

This change is consistent with the R7 polish bundle goal of reducing interaction cost for power users (the native) while preserving all existing manual interactions (panel close button, citation badge scroll-to-row, mobile bottom drawer).

Scope is intentionally narrow: two files only (see below). No new feature flags are introduced; `MARSYS_FLAG_R7_PANEL` is reserved in the frontmatter for gating during QA but the implementation ships unconditionally once merged to `chat-v2/round7-polish` (consistent with the Chat V2 Big Bang no-flag-in-production policy established at §M.16 cutover).

---

## Files in scope

| File | Role |
|---|---|
| `platform/src/components/chat/CitationSidePanel.tsx` | Primary change. Remove pin-gated visibility logic. Render all citations in the active message in index order. Retain pin button as a per-row star toggle with visual highlight; decouple it from panel open/close state. Add scroll-to-row behaviour when a citation badge is clicked in the message body (via forwarded ref or context callback). |
| `platform/src/components/consume/ConsumeChatV2.tsx` | Secondary change. `CitationCtx` provider drives `onPin`; extend it to carry an `autoOpen` signal or derive panel-open from citation count. Add `useEffect` watching `isStreaming` transition (true → false) and `citationRichMap.size > 0`; call `setPanelOpen(true)` when both conditions are met. Wire `citationRichMap` entries into panel props so all citations are available without a pin event. |

---

## Files must not touch

- `platform/src/components/chat/CitationBadge.tsx` — badge click emits an event only; do not alter its rendering or click contract
- `platform/src/components/chat/MarkdownContent.tsx` — citation footnote rendering is frozen post R6.2; no changes
- `platform/src/lib/feature_flags.ts` — flag list is stable; do not add `MARSYS_FLAG_R7_PANEL` to this file (the flag is QA-internal only, not a runtime gate)
- `platform/src/app/consume/page.tsx` — consume page wrapper is out of scope
- `platform/src/components/consume/ConsumeChatLegacy.tsx` — deleted at §M.16; must not be recreated
- `platform/tests/e2e/` — E2E specs are governed by R7 follow-up task; do not modify in this session
- Any file outside `platform/src/components/chat/` and `platform/src/components/consume/` — hard boundary

---

## Acceptance criteria

**AC-1 — Auto-open on stream completion.**
After an assistant message with citations completes streaming (`isStreaming` transitions true → false and `citationRichMap.size > 0`), the `CitationSidePanel` slides open without any user interaction. The open animation uses the existing slide transition; no new animation primitives are introduced.

**AC-2 — All citations listed.**
The panel lists all N citations from the completed message in ascending index order (1, 2, 3 … N). Each row shows the citation number, signal reference, and any available snippet. No citation is hidden, greyed out, or deferred behind a secondary action.

**AC-3 — Pin button is a star toggle, not a gate.**
Clicking the pin/star button on a citation row toggles a "starred" visual state (e.g., filled vs. outline star icon, accent colour) on that row only. It does not collapse other rows, does not close the panel, and does not remove the row from the list. Starred state is local to the panel component (no persistence required in this session).

**AC-4 — Badge click scrolls panel to row.**
Clicking a citation badge (e.g., `[^1]`) in the assistant message body scrolls the `CitationSidePanel` to the corresponding citation row and briefly highlights it (flash or pulse animation, one cycle). The panel must already be open for scroll-to-row to fire; if the panel is closed when a badge is clicked, the panel opens first, then scrolls.

**AC-5 — Close button works as before.**
The panel's X (close) button closes the panel as it did pre-R7-S4. After manual close, the panel does not re-open unless another message with citations completes streaming.

**AC-6 — Manual open with no active stream.**
If the user opens the panel manually (via whatever trigger existed pre-R7-S4) when no stream is active but a previous message had citations, the panel shows those citations. It does not show a blank state when citations are available in the session.

**AC-7 — No citations = no auto-open.**
If an assistant message completes streaming with zero citations (`citationRichMap.size === 0`), the panel does not auto-open. The panel remains in whatever state (open or closed) the user last set it to.

**AC-8 — Mobile bottom drawer.**
On mobile viewports, the panel renders as a bottom drawer per the R7 POLISH BUNDLE O6 spec. The cite-count chip at the bottom of the message triggers the drawer open. Auto-open on stream completion also applies: the drawer slides up when streaming ends and citations exist. The drawer's collapse/expand toggle continues to function.

**AC-9 — No regression on existing panel interactions.**
All interactions that worked before R7-S4 (manual open, close, badge click, pin visual) continue to work. No interaction that was previously available is removed; pin is repurposed, not deleted.

**AC-10 — TypeScript compiles clean.**
`tsc --noEmit` exits 0 across the `platform/` workspace. No `any` suppressions added to satisfy the new prop shapes.

---

## Pre-commit gates

Run all gates from the `platform/` directory root before committing. All must pass (exit 0) with no suppressions.

```bash
# 1. Type-check
npx tsc --noEmit

# 2. Lint
npx eslint src/components/chat/CitationSidePanel.tsx src/components/consume/ConsumeChatV2.tsx --max-warnings 0

# 3. Unit tests (if citation panel has a test file)
npx jest --testPathPattern="CitationSidePanel" --passWithNoTests

# 4. Build (catch any module-resolution failures)
npx next build 2>&1 | tail -20
```

Confirm each gate's exit code in the commit message body (see template below). Do not skip or `--no-verify` any gate.

---

## Commit message template

```
feat(chat-v2/r7-s4): CitationSidePanel auto-opens post-stream with all citations

- isStreaming true→false + citationRichMap.size>0 triggers setPanelOpen(true) in ConsumeChatV2
- CitationSidePanel renders all N citations in index order; pin button becomes star toggle
- Badge click scrolls panel to citation row (opens panel first if closed)
- Mobile bottom drawer auto-opens on stream completion (O6 parity)
- Pin no longer gates panel visibility; starred state is local, non-persistent
- AC-1 through AC-10 verified

Gates: tsc ✓ | eslint ✓ | jest ✓ | next build ✓

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
