---
canonical_id: R10_Y_S6
version: 1.0
status: CURRENT
session_id: Y-S6
title: Branch-on-regen — archive prior response before regenerating
depends_on: [Y-S2]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — extends useBranches hook from R8-S2"
authored: 2026-05-20
---

# Y-S6 — Branch on Regenerate

## Context

R8-S2 shipped `BranchPicker` — a UI to navigate between multiple response branches for the same prompt. Currently, clicking "Regenerate" in `MessageActions` discards the previous response. This session wires the regenerate action to first call `useBranches.archiveBranch(messageId)` to save the current response as a branch, THEN trigger the regeneration. The `BranchPicker` UI (from R8-S2) then lets users navigate between the original and regenerated responses.

**Amendment 3:** FLAGLESS — additive preservation behavior. The regenerate flow is strictly improved (prior response is never lost). Builds on R8-S2 infrastructure.

**Amendment 2:** Visible component (BranchPicker) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/messages/MessageActions.tsx` — wire `onRegenerateWithModel` to call `useBranches.archiveBranch` first
- `platform/src/hooks/chat-v2/useBranches.ts` — ensure `archiveBranch(messageId)` API is correct; add if missing
- `platform/src/components/chat-v2/messages/BranchPicker.tsx` (R8-S2 component) — confirm it surfaces the archived branch (read-only; no change expected but must be confirmed)
- `platform/tests/` — integration test

## Files Must NOT Touch

- Server-side message store (branch data lives client-side per R8-S2 design)
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

1. **click-path (Amendment 2):** User path: Chat V2 → receive a response → click MessageActions "Regenerate" → prior response is archived as branch 1 → new response streams in as branch 2 → `BranchPicker` (R8-S2) shows "1 / 2" navigation → clicking left arrow shows the archived original response. Document in commit body.
2. **Archive-then-regenerate:** `MessageActions.onRegenerateWithModel` calls `useBranches.archiveBranch(messageId)` synchronously BEFORE dispatching the regenerate action. The archived branch is immediately available in `BranchPicker`.
3. **No prior-response loss:** After regeneration, the original response is always reachable via `BranchPicker`. It is never discarded.
4. **Multiple regenerations:** Regenerating again archives branch 2, creating branch 3. `BranchPicker` shows "1 / 3" with ← → navigation through all branches.
5. **R8-S2 BranchPicker unchanged:** No modifications to `BranchPicker.tsx` are required (it already reads from `useBranches` store). Executor confirms by reading the component; if a change is needed, document it and make the minimal change.
6. **Parent-context integration test (Amendment 2):** At least one test mounts `MessageActions` within the real message context/provider chain (including `useBranches` provider) and asserts: (a) clicking regenerate calls `archiveBranch` before re-generation, (b) `BranchPicker` renders with branch count = 2 after one regeneration. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
npx jest --testPathPattern="branch.*regen|regen.*branch|useBranches|BranchPicker|MessageActions" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): archive prior response as branch before regenerating

MessageActions.onRegenerateWithModel calls useBranches.archiveBranch
first, preserving the current response. BranchPicker (R8-S2) surfaces
both branches for navigation. No prior response is ever lost.
Flagless per §M.16.

Click-path: Regenerate → prior response archived → BranchPicker shows "1/2".
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
