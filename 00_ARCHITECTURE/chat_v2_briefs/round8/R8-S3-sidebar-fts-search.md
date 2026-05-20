---
canonical_id: CHAT_V2_R8_S3_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S3
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_SEARCH
authored: 2026-05-20
depends_on: []
---

## Context

R8-S3 adds Postgres `pg_trgm` full-text / trigram search over conversation message bodies, exposes it through a dedicated search API route, and wires the result into the ConversationSidebar filter so users can locate conversations by content — not just title. The existing client-side title filter is preserved and remains the fallback for short queries (< 2 chars).

Prior R8 sessions (R8-S1, R8-S2) are not prerequisites; this session is independently executable. The sidebar component targeted is `ConversationSidebarV2.tsx` (or the equivalent component currently rendered in the Chat V2 path). The Chat V2 Big Bang workstream (sealing commit `6c431f9`, PR #82) is COMPLETE; this session extends capability within the stable V2 surface.

No L1 / L2.5 synthesis layer is touched. All changes are platform-layer (database migration, API route, React component).

## Files in scope

```
platform/
  prisma/migrations/
    <timestamp>_add_pg_trgm_conversation_messages/
      migration.sql                          # new — pg_trgm extension + GIN index
  src/
    app/
      api/
        conversations/
          search/
            route.ts                         # new — GET /api/conversations/search
    components/
      consume/
        ConversationSidebarV2.tsx            # modify — debounced search wiring
```

If the sidebar is implemented under a different filename (e.g. `ConversationSidebar.tsx`, `ConverseSidebar.tsx`), target that file instead and record the actual filename in the session-close checklist.

## Files must not touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
00_ARCHITECTURE/**
06_LEARNING_LAYER/**
platform/src/app/api/conversations/route.ts        # existing list route — do not modify
platform/src/app/api/conversations/[id]/route.ts   # existing single-conversation route
platform/src/components/consume/ConsumeChatV2.tsx  # chat surface — not in scope
platform/src/lib/query/**                          # query pipeline — not in scope
platform/src/lib/pipeline/**                       # pipeline — not in scope
platform/tests/e2e/**                              # e2e specs — not in scope this session
.geminirules
.gemini/project_state.md
CLAUDE.md
```

## Acceptance criteria

1. **Extension + index** — `migration.sql` runs cleanly on a fresh database: `CREATE EXTENSION IF NOT EXISTS pg_trgm` succeeds; `CREATE INDEX IF NOT EXISTS idx_conv_messages_body_trgm ON conversation_messages USING GIN (body gin_trgm_ops)` succeeds; no errors on re-run (idempotent guards present).

2. **API — title match** — `GET /api/conversations/search?q=moon` returns conversations whose `title` matches `ILIKE '%moon%'`, even if no message body matches.

3. **API — body match** — `GET /api/conversations/search?q=moon` returns conversations containing the word "moon" in a message body where `similarity(cm.body, $q) > 0.2`, even if the title does not match.

4. **API — snippet** — each result object carries `snippet`: the first 120 characters of the first matching message body. If the match is title-only, `snippet` may be an empty string or the first 120 chars of the earliest message body.

5. **API — auth** — the route reads the current session's `userId`; results contain only that user's conversations. An unauthenticated request returns HTTP 401. A request authenticated as user A never returns conversations owned by user B.

6. **API — limit** — response contains at most 20 conversations (`LIMIT 20`).

7. **API — response shape** — response is `{ conversations: Array<{ id: string, title: string, snippet: string }> }` with HTTP 200 on success.

8. **Sidebar — debounce** — typing into the search input does not trigger an API call on every keystroke; the call fires no earlier than 300 ms after the last keypress. Verified by inspecting that rapid successive keystrokes produce at most one in-flight request per 300 ms window.

9. **Sidebar — short-query fallback** — when `query.length < 2`, no API call is made; the sidebar reverts to the existing local title filter behaviour. The transition is seamless (no flicker, no empty state).

10. **Sidebar — loading state** — while the API call is in flight, a skeleton or spinner is displayed in the conversation list area. The previous results (or empty state) do not flash back during loading.

11. **Sidebar — error state** — if the API call fails (network error or non-200), the sidebar displays "Search unavailable" and falls back to the local title filter. No unhandled exception propagates to the React error boundary.

12. **Sidebar — snippet display** — results returned by the API show the `snippet` text below the conversation title in a muted / secondary text style (smaller font-size or reduced opacity consistent with the existing sidebar visual language).

13. **Sidebar — existing behaviour preserved** — when the search input is empty or cleared, the sidebar reverts to its pre-R8-S3 state (full unfiltered conversation list) without a page reload.

14. **TypeScript** — no new `ts` compiler errors introduced. `tsc --noEmit` exits 0.

15. **No migration regression** — `prisma migrate deploy` (or equivalent) completes without error in CI; the existing migration history is not altered.

## Pre-commit gates

Run the following in order before committing. All must pass (exit 0) unless a known residual is declared in the session-close checklist with a tracking reference.

```bash
# 1. TypeScript typecheck
cd platform && npx tsc --noEmit

# 2. Lint
cd platform && npx eslint src/app/api/conversations/search/route.ts \
  src/components/consume/ConversationSidebarV2.tsx --max-warnings 0

# 3. Unit / integration tests (if test files exist for these paths)
cd platform && npx jest --testPathPattern="conversations/search|ConversationSidebar" \
  --passWithNoTests

# 4. Migration idempotency smoke (requires local Postgres with pg_trgm available)
# Run migration twice; second run must also exit 0
psql $DATABASE_URL -f prisma/migrations/<timestamp>_add_pg_trgm_conversation_messages/migration.sql
psql $DATABASE_URL -f prisma/migrations/<timestamp>_add_pg_trgm_conversation_messages/migration.sql

# 5. Build
cd platform && npx next build 2>&1 | tail -20
```

Gate 4 may be skipped in CI if `DATABASE_URL` is not available; declare the skip as a known residual `KR.R8S3.1` in the session-close checklist with note "migration idempotency verified locally only".

## Commit message template

```
feat(chat-v2/r8-s3): pg_trgm message-body search + sidebar FTS wiring

- Add pg_trgm GIN index on conversation_messages.body (idempotent migration)
- New GET /api/conversations/search?q=<query>&limit=20 route (auth-gated,
  trigram similarity > 0.2, returns id + title + 120-char snippet)
- ConversationSidebarV2: debounced (300ms) API search when query >= 2 chars;
  snippet shown below title in muted style; loading skeleton + error fallback;
  query < 2 chars reverts to existing local title filter

Acceptance: AC-1 through AC-15 (R8-S3 brief v1.0)
Flag namespace: MARSYS_FLAG_R8_SEARCH (no runtime flag required for this
session — feature is always-on behind auth)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
