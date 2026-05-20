---
canonical_id: R10_Y_S7
version: 1.0
status: CURRENT
session_id: Y-S7
title: Search mode toggle — Exact / Semantic in conversation sidebar
depends_on: [Y-S6]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — UI affordance only; wires existing ?semantic=true query param from R9-S2"
authored: 2026-05-20
---

# Y-S7 — Search Mode Toggle

## Context

R9-S2 shipped a semantic search route (`?semantic=true`) for the conversation sidebar search. However, the UI only exposes a single text field with no affordance to toggle between exact (keyword) and semantic search modes. This session adds an "Exact / Semantic" toggle to the conversation sidebar search UI, wiring the existing `?semantic=true` parameter.

**Amendment 3:** FLAGLESS — UI affordance only; the backend route already exists (merged via PR #103). No new backend code.

**Dependency:** If the semantic search route (`?semantic=true`) is somehow absent from the base branch, set `blocked_on: [R9-S2 missing]` and skip. Executor verifies by checking: `grep -rn "semantic" platform/src/app/api/ --include="*.ts"`.

**Amendment 2:** Visible component (toggle in sidebar search) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/sidebar/ConversationSidebar.tsx` — add toggle to search bar
- `platform/src/hooks/chat-v2/useConversationSearch.ts` (or equivalent) — add `searchMode: 'exact' | 'semantic'` state
- `platform/tests/` — integration test

## Files Must NOT Touch

- Any server-side API route (backend already exists)
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

0. **Prerequisite check:** Before implementing, run `grep -rn "semantic" platform/src/app/api/ --include="*.ts"`. If the semantic route is absent, set `blocked_on: R9-S2-missing` in this brief, skip implementation, and commit this brief with the blocked_on note. Do NOT implement against a missing backend.
1. **click-path (Amendment 2):** User path: Chat V2 sidebar → focus search input → a small "Exact | Semantic" toggle (pill or segmented control) appears adjacent to the search input → clicking "Semantic" switches to semantic search mode → typing a query sends `?semantic=true` to the search API → clicking "Exact" reverts to keyword search. Document in commit body.
2. **Default mode:** "Exact" is the default (preserves current behavior for users who never touch the toggle).
3. **Param wiring:** When mode is "Semantic", the search hook appends `?semantic=true` to the search request. When mode is "Exact", no `?semantic` param is sent (existing behavior).
4. **Persistence (optional):** If feasible, persist the last-used mode to `useChatPreferences`. Not required if it adds significant complexity.
5. **Parent-context integration test (Amendment 2):** At least one test mounts `ConversationSidebar` within its real provider chain (ConvListCtx or search context) and asserts: (a) toggle renders in search bar, (b) clicking "Semantic" sets mode and the next search request includes `?semantic=true`. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Check R9-S2 semantic route exists
grep -rn "semantic" platform/src/app/api/ --include="*.ts" && echo "PASS: semantic route present" || echo "BLOCKED: R9-S2 route missing — set blocked_on and skip"

npx jest --testPathPattern="searchMode|search.*toggle|semantic.*toggle|ConversationSidebar.*search" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): Exact/Semantic search mode toggle in conversation sidebar

ConversationSidebar search gains Exact|Semantic toggle. "Semantic" mode
appends ?semantic=true (R9-S2 route). "Exact" preserves current behavior.
Default: Exact. Flagless per §M.16.

Click-path: sidebar search → toggle Semantic → query uses semantic route.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
