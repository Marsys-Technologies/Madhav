# Chat V2 Round 8 — Capabilities Stream: COMPLETE

**Branch**: `chat-v2/round8-capabilities`
**Worktree**: `/Users/Dev/Vibe-Coding/Apps/MadhavR8`
**Completed**: 2026-05-20
**Executor**: Claude Sonnet 4.6 (autonomous)

---

## Sessions Completed

| Session | Description | Commit |
|---------|-------------|--------|
| R8-S1 | Conversation Branches Persistence | ddcb350 |
| R8-S2 | BranchPicker UI Component | 757f34d |
| R8-S3 | Sidebar FTS Search (pg_trgm) | 0816fd9 |
| R8-S4 | Pin / Archive / Folders | b5ca24b |
| R8-S5 | Live Token Count in Composer | 18f5e44 |
| R8-S6 | Slash Command Menu | 237b366 |
| R8-S7 | Vision Pipeline (GeminiVisionAdapter) | 6e074df |
| R8-S8 | Conversation Export (MD / JSON / PDF) | 5e248fc |

---

## New Files

### Migrations
- `platform/supabase/migrations/066_conversation_branches.sql`
- `platform/supabase/migrations/067_pg_trgm_conversation_messages.sql`
- `platform/supabase/migrations/068_pin_archive_folders.sql`

### API Routes
- `platform/src/app/api/conversations/[id]/branches/route.ts`
- `platform/src/app/api/conversations/search/route.ts`
- `platform/src/app/api/conversations/[id]/export/route.ts`
- `platform/src/app/api/folders/route.ts`
- `platform/src/app/api/folders/[id]/route.ts`

### Components
- `platform/src/components/chat/BranchPicker.tsx`
- `platform/src/components/chat/SlashCommandMenu.tsx`
- `platform/src/components/chat/ExportDropdown.tsx`
- `platform/src/components/consume/FolderGroup.tsx`
- `platform/src/components/consume/ArchivedView.tsx`

### Hooks / Lib
- `platform/src/hooks/useBranches.ts` (modified)
- `platform/src/hooks/useFolders.ts` (new)
- `platform/src/hooks/useTokenCount.ts` (new)
- `platform/src/hooks/useAttachments.ts` (modified — mimeType field)
- `platform/src/lib/chat-commands.ts` (new)
- `platform/src/lib/adapters/geminiVisionAdapter.ts` (new)
- `platform/src/lib/adapters/index.ts` (modified)

### Types
- `platform/src/types/branches.ts`
- `platform/src/types/folders.ts`

### Tests
- `platform/src/components/chat/BranchPicker.test.tsx` (7 tests)
- `platform/tests/unit/useTokenCount.test.ts` (5 tests)
- `platform/tests/e2e/chat-v2/vision-smoke.spec.ts`

---

## Feature Flags

All R8 flags added to `platform/src/lib/config/feature_flags.ts` (default false):
- `R8_BRANCHES_ENABLED`
- `R8_SEARCH_ENABLED`
- `R8_FOLDERS_ENABLED`
- `R8_TOKENS_ENABLED`
- `R8_SLASH_ENABLED`
- `R8_VISION_ENABLED`
- `R8_EXPORT_ENABLED`

---

## Test Results

- Pre-existing failures: 21 (unchanged from R8-S1 baseline)
- New tests added: 12 (7 BranchPicker + 5 useTokenCount)
- All new tests pass

---

## Merge Train Position

**Position 2** — merge AFTER R7 PR (`chat-v2/round7-polish`) is merged to main.

Potential conflict: `platform/src/app/api/conversations/search/route.ts` (shared with R9-S2).
See `00_ARCHITECTURE/chat_v2_briefs/MERGE_TRAIN_ORDER_v1_0.md` for rebase sequence.

---

## Known Limitations / Fix-Forwards

- **R8-S5**: `tokensEnabled` prop is not yet wired from page → BuildChat → Composer (flag defaults false; no UI visible until wired)
- **R8-S6**: `slashEnabled` is not yet wired from page → ConsumeChatV2 (flag defaults false)
- **R8-S7**: GeminiVisionAdapter created; integration into consume route is a fix-forward (existing route uses token-based system)
- **R8-S8**: PDF export returns 501 (html-pdf-node not installed); MD and JSON work fully
