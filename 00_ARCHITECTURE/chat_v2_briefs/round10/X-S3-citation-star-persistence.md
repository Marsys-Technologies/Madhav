---
canonical_id: R10_X_S3
version: 1.0
status: CURRENT
session_id: X-S3
title: Citation star persistence via localStorage
depends_on: [X-S2]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — localStorage, client-only"
authored: 2026-05-20
---

# X-S3 — Citation Star Persistence

## Context

The `CitationSidePanel` in Chat V2 has a star/bookmark toggle on individual citations. Currently the star state is ephemeral (resets on panel close or page reload). This session persists star state to `localStorage` keyed by `conversationId`, so starred citations survive page refreshes and re-opens.

**Amendment 3:** FLAGLESS — additive localStorage persistence, no backend, no schema change, no behavior change for users who never starred anything.

**Amendment 2:** Visible component (CitationSidePanel star button) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/citation/CitationSidePanel.tsx` — read/write star state from localStorage hook
- `platform/src/hooks/chat-v2/useStarredCitations.ts` (new) — `starredCitations: Record<conversationId, Set<citationKey>>` backed by localStorage
- `platform/tests/` — integration test

## Files Must NOT Touch

- Any server-side API routes
- Phase 4C files
- `.github/workflows/deploy.yml`
- `platform/src/components/chat-v2/CitationCtx.tsx` (unless needed for ctx extension — executor confirms)

## Acceptance Criteria

1. **click-path (Amendment 2):** User path: open Chat V2 conversation → receive a response with citations → open citation panel → click the star on a citation → refresh page → reopen citation panel → star is still filled/active. Document in commit body.
2. **Per-conversation scoping:** Stars are stored per `conversationId`. Switching conversations shows that conversation's own starred set.
3. **localStorage key:** `marsys_chat_v2_starred_<conversationId>` or equivalent; serialized as JSON array of citation keys.
4. **Star toggle:** Clicking a starred citation un-stars it (toggle); clicking an un-starred citation stars it.
5. **Parent-context integration test (Amendment 2):** At least one test mounts `CitationSidePanel` within its real parent provider chain (CitationCtx + conversationId prop) and asserts: (a) starring a citation writes to localStorage, (b) re-mounting the panel reads the persisted state and renders the star filled. Direct prop injection test alone does NOT satisfy this AC.
6. Empty localStorage case handled gracefully (no errors on first load).

## Pre-commit Gates

```bash
npx jest --testPathPattern="citation.*star|starredCitation|CitationSidePanel" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): persist citation stars to localStorage per conversationId

useStarredCitations hook backs CitationSidePanel star toggle with
localStorage. Stars survive refresh. Per-conversation scope prevents
cross-bleed. Flagless per §M.16.

Click-path: citation panel → star citation → refresh → star persists.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
