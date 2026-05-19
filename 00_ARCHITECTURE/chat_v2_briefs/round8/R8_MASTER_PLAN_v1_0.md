---
canonical_id: CHAT_V2_R8_MASTER_PLAN
version: 1.0
status: CURRENT
authored: 2026-05-20
owner: Abhisek Mohanty
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
parallel_with:
  - chat-v2/round7-polish (R7 — no shared files; merges before R8)
  - chat-v2/round9-elevation (R9 — no shared DB migrations overlap; flag namespaces isolated)
merge_train_position: 2 (merges after R7, before R9)
flag_namespace: MARSYS_FLAG_R8_*
---

# R8 — Chat V2 Capabilities Round

## Scope

R8 adds persistent capabilities to the Chat V2 surface: conversation branching, full-text search, folder organisation, token count estimation, slash commands, vision input, and export. These require database schema changes (migrations) and new API routes. The round ships as separate PRs per session (recommended) or as a bundle — executor's choice. Each session's PR must pass automated gates independently before merging.

Baseline: R8 branch is created from main post-R7-merge. All R7 polish is assumed live.

## Sessions

| # | ID | Brief | Files Primary | DB? | Flag | Depends |
|---|---|---|---|---|---|---|
| 1 | R8-S1 | R8-S1-branches-persistence.md | useBranches.ts, new branches/route.ts, migration | YES | MARSYS_FLAG_R8_BRANCHES | — |
| 2 | R8-S2 | R8-S2-branch-picker-ui.md | BranchPicker.tsx, UserMessage.tsx | — | MARSYS_FLAG_R8_BRANCHES | R8-S1 |
| 3 | R8-S3 | R8-S3-sidebar-fts-search.md | search/route.ts, ConversationSidebarV2.tsx, migration | YES | MARSYS_FLAG_R8_SEARCH | — |
| 4 | R8-S4 | R8-S4-pin-archive-folders.md | migration, conversations routes, sidebar | YES | MARSYS_FLAG_R8_FOLDERS | — |
| 5 | R8-S5 | R8-S5-token-estimate-composer.md | Composer.tsx, useTokenCount hook | — | MARSYS_FLAG_R8_TOKENS | — |
| 6 | R8-S6 | R8-S6-slash-command-menu.md | SlashCommandMenu.tsx, lib/chat-commands.ts, Composer.tsx | — | MARSYS_FLAG_R8_SLASH | — |
| 7 | R8-S7 | R8-S7-vision-pipeline.md | geminiVisionAdapter.ts, route.ts, useAttachments.ts | — | MARSYS_FLAG_R8_VISION | — |
| 8 | R8-S8 | R8-S8-pdf-md-export.md | export/route.ts, ExportDropdown.tsx, ChatShell.tsx | — | MARSYS_FLAG_R8_EXPORT | — |

**Dependency graph:** S1 → S2 (branch UI requires persistence). S3 is prerequisite for R9-S2 (semantic search). All others independent.

**Recommended session order:** S1, S3, S4 first (migrations early to catch conflicts); then S2 (depends on S1); then S5, S6, S7, S8 in any order.

## Flag Namespace

All R8 flags follow `MARSYS_FLAG_R8_<FEATURE>`. They live in `platform/src/lib/feature_flags.ts`. R8 owns and may append to the `MARSYS_FLAG_R8_*` namespace only.

## Files Locked to Other Streams

R8 must not touch:
- Any R7 session's primary files already merged to main (treat as read-only)
- `platform/src/components/chat/InlineToolFlow.tsx` (R9-S4)
- `platform/src/app/api/projects/**` (R9-S1)
- `platform/src/app/api/personas/**` (R9-S3)
- `platform/src/components/chat/ModelStylePicker.tsx` (R9-S3 extends this — coordinate)
- `00_ARCHITECTURE/` governance files

**Migration ordering:** If R8 and R9 both have migrations, R8 migrations must be numbered/timestamped before R9 migrations. Use timestamp prefix `20260520_r8_*` for R8 migrations, `20260520_r9_*` for R9.

## Round Acceptance

The R8 round is COMPLETE when:
1. All 8 sessions have their ACs verified
2. All DB migrations run cleanly on a fresh DB (`npx prisma migrate dev --name r8-capabilities`)
3. `npm run typecheck` exits 0
4. `npm test` exits 0 with no new failures
5. Branch picker shows on edited messages (manual smoke)
6. FTS search returns body-matched results (manual smoke)
7. PR merged to main via `--no-ff` (after R7 is merged)

## Merge Train Position

R8 merges second (position 2). Must rebase on top of R7-merged main before opening PR. Command: `git rebase main` from R8 worktree. Resolve any conflicts before CI. See `MERGE_TRAIN_ORDER_v1_0.md`.

## Rollback Plan

R8 introduces DB migrations. Rollback: `npx prisma migrate rollback` (if Prisma supports it for the specific migration) OR `git revert <merge-sha>` + manual `DROP TABLE` for the new tables. New tables (`conversation_branches`, `conversation_folders`, `conversation_folder_members`) are additive and do not alter existing table structure — rollback risk is low.

---
*R8 Master Plan v1.0 — authored 2026-05-20 as part of `chat-v2/governance-r7-r9-setup` branch.*
