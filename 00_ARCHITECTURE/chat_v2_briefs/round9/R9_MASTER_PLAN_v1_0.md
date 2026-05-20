---
canonical_id: CHAT_V2_R9_MASTER_PLAN
version: 1.0
status: CURRENT
authored: 2026-05-20
owner: Abhisek Mohanty
branch: chat-v2/round9-elevation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR9
parallel_with:
  - chat-v2/round7-polish (R7 — merges first; no direct file conflicts)
  - chat-v2/round8-capabilities (R8 — merges second; R9 depends on R8-S3 for semantic search)
merge_train_position: 3 (merges last — heaviest schema, highest blast radius)
flag_namespace: MARSYS_FLAG_R9_*
---

# R9 — Chat V2 Elevation Round

## Scope

R9 implements the highest-leverage architectural features: Projects abstraction (multi-conversation organisational layer), semantic conversation search (vector embeddings), persona library (system-prompt variants), and inline tool-flow timeline (admin debugging aid). These are the heaviest changes in the R7→R9 train — new tables, new embedding pipeline, new top-level routes. Each session ships as an independent PR. R9 rebases on top of merged R7+R8.

Prerequisite: R8-S3 (`pg_trgm` index) must be merged before R9-S2 is executed.

## Sessions

| # | ID | Brief | Files Primary | DB? | Embeddings? | Flag | Depends |
|---|---|---|---|---|---|---|---|
| 1 | R9-S1 | R9-S1-projects-abstraction.md | 3 new tables, /api/projects/**, synthesis prompt, sidebar UI | YES | — | MARSYS_FLAG_R9_PROJECTS | — |
| 2 | R9-S2 | R9-S2-semantic-conversation-search.md | conversation_message_embeddings, embedConversationMessage.ts, search/route.ts | YES | YES | MARSYS_FLAG_R9_SEMANTIC_SEARCH | R8-S3 |
| 3 | R9-S3 | R9-S3-persona-library.md | personas table, /api/personas/**, ModelStylePicker.tsx, settings/personas/page.tsx | YES | — | MARSYS_FLAG_R9_PERSONAS | — |
| 4 | R9-S4 | R9-S4-inline-tool-flow-timeline.md | InlineToolFlow.tsx, /api/audit/[id]/trace, AssistantMessage.tsx | — | — | MARSYS_FLAG_R9_TOOL_FLOW | — |

**Recommended execution order:** S1 (Projects, establishes foundation), S3 (Personas, independent), S4 (Tool flow, independent), S2 (Semantic search, depends on R8-S3 being live).

## Flag Namespace

All R9 flags follow `MARSYS_FLAG_R9_<FEATURE>`. R9 owns `MARSYS_FLAG_R9_*` exclusively. R7 owns `MARSYS_FLAG_R7_*`; R8 owns `MARSYS_FLAG_R8_*`.

**R9 flag defaults (production):**
- `MARSYS_FLAG_R9_PROJECTS`: OFF initially (beta, gated to admin)
- `MARSYS_FLAG_R9_SEMANTIC_SEARCH`: OFF initially (requires embedding backfill job to complete)
- `MARSYS_FLAG_R9_PERSONAS`: ON (additive, no risk)
- `MARSYS_FLAG_R9_TOOL_FLOW`: ON for super-admin; OFF for clients

## Files Locked to Other Streams

R9 must not touch:
- Any R7/R8 session files already merged to main
- `platform/src/app/api/conversations/branches/**` (R8-S1/S2 — read-only after merge)
- `platform/src/app/api/conversations/search/route.ts` (R9-S2 *extends* this file from R8-S3; coordinate carefully on rebase)
- `.github/workflows/deploy.yml` (append-only)
- `00_ARCHITECTURE/` governance files

**Special coordination:** R9-S2 extends `search/route.ts` introduced by R8-S3. On rebase, the R9-S2 executor must pick up R8-S3's changes cleanly and add the `?semantic=true` branch to the existing handler — do not replace the entire file.

## Round Acceptance

The R9 round is COMPLETE when:
1. All 4 sessions have their ACs verified
2. All DB migrations run cleanly (timestamp-prefixed after R8 migrations)
3. `npm run typecheck` exits 0
4. `npm test` exits 0 with no new failures
5. Projects group visible in sidebar for admin users (manual smoke)
6. Persona quick-switch works in ModelStylePicker (manual smoke)
7. Semantic search returns semantically-related results (manual smoke with "Chandra" → "moon" example)
8. InlineToolFlow disclosure shows for super-admin messages (manual smoke)
9. PR merged to main via `--no-ff` (after R7+R8 are merged)

## Merge Train Position

R9 merges last (position 3). Must rebase on top of R7+R8-merged main. Command sequence:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR9
git fetch origin
git rebase origin/main
# resolve any conflicts (expect: search/route.ts if R8-S3 touched it)
git push --force-with-lease origin chat-v2/round9-elevation
```
See `MERGE_TRAIN_ORDER_v1_0.md` for full sequence and conflict resolution guidance.

## Rollback Plan

R9 is the heaviest round. Rollback options:
1. **Flag rollback (preferred):** Set `MARSYS_FLAG_R9_PROJECTS=false`, `MARSYS_FLAG_R9_SEMANTIC_SEARCH=false` in Cloud Run env vars. Feature disappears without code change.
2. **Code rollback:** `git revert <merge-sha>` + `npx prisma migrate rollback` for each R9 migration (projects, project_files, project_conversations, conversation_message_embeddings, personas).
3. **DB-only rollback:** If code is rolled back but DB tables remain, they are inert (no foreign key constraint violations on existing data).

The `conversation_message_embeddings` table is the highest-risk migration (vector column requires `pgvector` extension). Verify extension is available in the production Postgres instance before executing R9-S2.

---
*R9 Master Plan v1.0 — authored 2026-05-20 as part of `chat-v2/governance-r7-r9-setup` branch.*
