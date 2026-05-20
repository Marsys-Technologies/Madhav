---
canonical_id: CHAT_V2_R8_S1_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S1
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_BRANCHES
authored: 2026-05-20
depends_on: []
---

## Context

Chat V2 Big Bang shipped in §M.16 (sealing-merge `6c431f9`, PR #82, 2026-05-18). The `useBranches.ts` hook manages in-memory branch state for message editing and conversation forking, but branch records are never persisted — a full page reload destroys all branch history and the user cannot resume a branched conversation across sessions.

R8-S1 closes that gap: a `conversation_branches` Postgres table stores branch metadata and snapshots, a REST API exposes CRUD for the table, and `useBranches.ts` is updated to hydrate from the API on mount and to fire-and-forget a POST on every branch creation. All existing in-memory logic is preserved; the persistence layer is additive.

This work runs inside the `chat-v2/round8-capabilities` branch in worktree `/Users/Dev/Vibe-Coding/Apps/MadhavR8`. It is independent of any M5 astrological-computation work and must not touch M5 or governance artifacts.

---

## Files in scope

| Path | Action |
|---|---|
| `platform/prisma/schema.prisma` | Add `ConversationBranch` model |
| `platform/prisma/migrations/20260520_add_conversation_branches/migration.sql` | New migration file (raw SQL) |
| `platform/src/app/api/conversations/[id]/branches/route.ts` | New file — GET + POST handlers |
| `platform/src/hooks/useBranches.ts` | Add API calls (mount fetch + branch-create POST); export `ConversationBranch` type |
| `platform/src/types/branches.ts` | New file — shared `ConversationBranch` type (if not co-located in hook) |

---

## Files must not touch

- `00_ARCHITECTURE/**` (all governance documents)
- `CLAUDE.md`
- `.geminirules`
- `.gemini/project_state.md`
- `01_FACTS_LAYER/**`
- `025_HOLISTIC_SYNTHESIS/**`
- `06_LEARNING_LAYER/**`
- `platform/src/components/consume/ConsumeChatV2.tsx` (modified on main; R8-S1 must not conflict)
- Any file outside `platform/` except this brief itself
- Existing migration files under `platform/prisma/migrations/`
- `platform/src/app/api/conversations/[id]/route.ts` (existing route — do not modify)

---

## Acceptance criteria

**AC.1 — Migration integrity**
`npx prisma migrate dev --name add_conversation_branches` runs without error on a clean dev database. `npx prisma migrate status` reports all migrations applied.

**AC.2 — Schema model consistency**
`platform/prisma/schema.prisma` declares a `ConversationBranch` model whose fields exactly match the SQL DDL:
- `id` String (UUID, default `dbgenerated("gen_random_uuid()")`, `@id`)
- `conversationId` String (maps to `conversation_id`; FK to `conversations.id` with `onDelete: Cascade`)
- `editedMessageId` String (maps to `edited_message_id`)
- `parentBranchId` String? (maps to `parent_branch_id`; self-referential optional FK)
- `snapshotJsonb` Json (maps to `snapshot_jsonb`, default `{}`)
- `createdAt` DateTime (maps to `created_at`, default `now()`)

**AC.3 — GET returns empty array for new conversation**
`GET /api/conversations/{id}/branches` returns HTTP 200 with body `{ branches: [] }` when no branches exist for the given conversation.

**AC.4 — GET returns branches ordered by created_at desc**
After two POSTs, GET returns both branches with the most-recently-created first.

**AC.5 — POST creates a row and returns id + created_at**
`POST /api/conversations/{id}/branches` with valid body `{ edited_message_id, snapshot_jsonb }` returns HTTP 201 with body `{ id: "<uuid>", created_at: "<iso-timestamp>" }`. A subsequent GET includes the new branch.

**AC.6 — POST with parent_branch_id sets the FK**
When `parent_branch_id` is supplied, the created row's `parent_branch_id` column is non-null and matches.

**AC.7 — Auth: unauthenticated request returns 401**
Both GET and POST return HTTP 401 when called without a valid session cookie or token, using the same auth-check pattern as other conversation API routes.

**AC.8 — Auth: conversation ownership enforced**
GET and POST return HTTP 404 when the `conversation_id` exists in the database but belongs to a different user.

**AC.9 — useBranches hydrates from API on mount**
On component mount, `useBranches` calls `GET /api/conversations/{id}/branches` and populates in-memory branch state with the returned branches. If the conversation has no branches, in-memory state remains empty (no error thrown).

**AC.10 — useBranches fires POST on branch creation**
When `createBranch` (or equivalent internal function) is called, `useBranches` fires `POST /api/conversations/{id}/branches` as a fire-and-forget side-effect. The call must not block the UI update; the branch appears in-memory immediately regardless of network latency or failure.

**AC.11 — Backwards compatibility**
All existing in-memory branch logic (branch switching, undo, re-apply, etc.) continues to work without modification. The persistence layer is strictly additive — no existing exported function signatures change.

**AC.12 — Exported type**
`useBranches.ts` (or `platform/src/types/branches.ts`) exports a `ConversationBranch` type with fields matching the DB row shape:
```ts
export interface ConversationBranch {
  id: string;
  conversationId: string;
  editedMessageId: string;
  parentBranchId: string | null;
  snapshotJsonb: Record<string, unknown>;
  createdAt: string; // ISO timestamp
}
```

**AC.13 — typecheck passes**
`npm run typecheck` (run from `platform/`) exits 0 with no new errors introduced by this session's changes.

**AC.14 — No regressions on existing conversation API routes**
`GET /api/conversations/[id]` and `DELETE /api/conversations/[id]` (and any other sibling routes) continue to function — confirm by inspection that the new `branches/route.ts` file does not shadow or conflict with sibling routes.

---

## Pre-commit gates

Run all of the following from `platform/` before committing. Every gate must exit 0 (or produce the expected output) — a failing gate is a blocker; do not commit around it.

```bash
# G1 — Prisma schema validates
npx prisma validate

# G2 — Migration status clean
npx prisma migrate status

# G3 — TypeScript typecheck
npm run typecheck

# G4 — Lint (no new errors)
npm run lint -- --max-warnings=0

# G5 — Unit tests (if test runner is configured)
npm test -- --passWithNoTests

# G6 — Confirm new route file exists and exports GET + POST
grep -n "export.*GET\|export.*POST" src/app/api/conversations/\[id\]/branches/route.ts

# G7 — Confirm useBranches imports include fetch calls
grep -n "fetch\|POST\|GET" src/hooks/useBranches.ts

# G8 — Confirm ConversationBranch type is exported
grep -n "export.*ConversationBranch" src/hooks/useBranches.ts src/types/branches.ts 2>/dev/null | head -5
```

---

## Commit message template

```
feat(chat-v2/r8-s1): persist branch state to conversation_branches table + REST API

- Add ConversationBranch Prisma model + migration 20260520_add_conversation_branches
- New route GET|POST /api/conversations/[id]/branches with session auth + ownership check
- useBranches: hydrate from API on mount; fire-and-forget POST on branch create
- Export ConversationBranch interface; all existing in-memory logic unchanged

AC.1–AC.14 verified. npm run typecheck: 0 errors. Lint: 0 warnings.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
