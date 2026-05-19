---
canonical_id: CHAT_V2_R8_S4_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S4
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_FOLDERS
authored: 2026-05-20
depends_on: []
---

## Context

R8-S4 adds pin, archive, and folder organisation to the conversation sidebar. Users can pin conversations to the top of the sidebar, archive conversations to remove them from the main list, and organise conversations into named colour-coded folders. All state persists in the database. This session delivers the DB migrations, API routes, and UI changes in one coherent slice; no feature flag gates the feature (it ships unconditionally on merge to `chat-v2/round8-capabilities`).

The sidebar grouping order after this session is:

1. **Pinned** — pinned conversations, newest-first, always at top
2. **Folders** — each folder is a collapsible group; conversations inside are excluded from date buckets
3. **Date buckets** — Today, Yesterday, Last 7 Days, Older (existing behaviour, unfolderd + unpinned conversations only)
4. **Archived view** — separate filtered list, not shown in main sidebar; reachable via "Archived" link at bottom of sidebar

---

## Files in scope

### Database migrations
- `platform/migrations/` — add one new migration file containing all three DDL statements below (naming convention: next sequential timestamp prefix, e.g. `20260520000000_r8_pin_archive_folders.sql`)

### API routes
- `platform/src/app/api/conversations/[id]/route.ts` — extend or create; handle `PATCH` body fields `pinned`, `archived`, `folder_id`
- `platform/src/app/api/conversations/route.ts` — extend `GET` to return `pinned`, `archived_at`, `folder_id` per row; support `?archived=true` query param
- `platform/src/app/api/folders/route.ts` — create; handle `GET` (list user folders) and `POST` (create folder)
- `platform/src/app/api/folders/[id]/route.ts` — create; handle `PATCH` (rename, recolor) and `DELETE`

### Types / schema
- `platform/src/types/conversations.ts` — extend `Conversation` type with `pinned: boolean`, `archived_at: string | null`, `folder_id: string | null`
- `platform/src/types/folders.ts` — create; export `ConversationFolder` type

### UI
- `platform/src/components/consume/ConversationSidebar.tsx` — primary UI change; add Pinned section, Folders section, Archived link, DropdownMenu per conversation and per folder header
- `platform/src/components/consume/ConversationSidebarItem.tsx` — create or extend; right-click / DropdownMenu trigger with actions: Pin/Unpin, Archive, Move to Folder, Delete
- `platform/src/components/consume/FolderGroup.tsx` — create; collapsible folder header + member list
- `platform/src/components/consume/ArchivedView.tsx` — create; filtered list shown when "Archived" link is active
- `platform/src/hooks/useConversations.ts` — extend mutation helpers: `pinConversation`, `archiveConversation`, `moveToFolder`
- `platform/src/hooks/useFolders.ts` — create; `useFolders()` hook wrapping folder CRUD API calls

### DB client / query helpers
- `platform/src/lib/db/conversations.ts` (or equivalent query file) — extend read/write helpers to join `conversation_folder_members` and return `folder_id`; add `pinned` and `archived_at` to INSERT/UPDATE surface
- `platform/src/lib/db/folders.ts` — create; CRUD helpers for `conversation_folders` and `conversation_folder_members`

---

## Files must not touch

- `platform/src/components/consume/ConsumeChatV2.tsx` — chat message rendering; unrelated to sidebar organisation
- `platform/src/app/api/query/` — query pipeline; no changes
- `platform/src/lib/synthesis/` — synthesis layer; no changes
- `01_FACTS_LAYER/` — L1 facts; no changes
- `025_HOLISTIC_SYNTHESIS/` — L2.5 synthesis artifacts; no changes
- `00_ARCHITECTURE/` (except this brief file itself) — governance artifacts; no changes
- `.geminirules` — Gemini-side mirror; no changes in this session
- `.gemini/project_state.md` — Gemini-side mirror; no changes in this session
- `platform/src/app/api/conversations/[id]/route.ts` message-fetch logic (read path for messages) — preserve existing GET behaviour; only extend PATCH

---

## Acceptance criteria

1. **Pinned conversations appear at top of sidebar above all date groups.** After calling `PATCH /api/conversations/[id]` with `{ pinned: true }`, the conversation moves to the Pinned section on next render (optimistic update) and persists across page reload.

2. **Archiving removes from main list.** After `PATCH /api/conversations/[id]` with `{ archived: true }`, the conversation disappears from Pinned, Folders, and date buckets. It is not deleted from the DB (`archived_at` is set to `now()`).

3. **Archived view shows archived conversations.** Clicking the "Archived" link at the bottom of the sidebar renders `<ArchivedView />`, which fetches `GET /api/conversations?archived=true` and lists results. Back navigation returns to normal sidebar view.

4. **Un-archiving restores to main list.** `PATCH /api/conversations/[id]` with `{ archived: false }` sets `archived_at = NULL`; conversation reappears in correct date bucket on next render and reload.

5. **Folder creation.** `POST /api/folders` with `{ name, color? }` creates a row in `conversation_folders`; `GET /api/folders` returns the new folder. The "New folder" button in the sidebar triggers this flow and immediately renders the folder group (empty, collapsible).

6. **Moving a conversation into a folder.** `PATCH /api/conversations/[id]` with `{ folder_id: "<uuid>" }` inserts a row into `conversation_folder_members` (upsert; remove prior membership first). The conversation disappears from date buckets and appears under the folder group. Persists across reload.

7. **Removing a conversation from a folder.** `PATCH /api/conversations/[id]` with `{ folder_id: null }` deletes the `conversation_folder_members` row. Conversation returns to the appropriate date bucket.

8. **Folder rename.** `PATCH /api/folders/[id]` with `{ name }` updates the folder name. Reflected in sidebar without reload.

9. **Folder delete.** `DELETE /api/folders/[id]` deletes the folder row; `ON DELETE CASCADE` removes all `conversation_folder_members` rows. Member conversations return to date buckets.

10. **DropdownMenu on each conversation.** Right-click or kebab-icon click opens a menu with: Pin (or Unpin if already pinned), Archive (or Unarchive), Move to Folder (sub-menu listing existing folders + "New folder"), Delete. Existing Delete action must remain wired.

11. **Auth.** All `/api/folders` routes and the extended `/api/conversations` routes verify the session (Supabase or equivalent auth helper already used in the codebase). Unauthenticated requests return `401`. Requests for resources belonging to a different user return `403`. Folder CRUD is scoped to `user_id` from the session.

12. **DB persistence confirmed.** Manual smoke: perform pin, archive, folder-create, folder-move actions; hard-reload the page; verify sidebar state matches DB rows.

13. **TypeScript clean.** `tsc --noEmit` exits 0 on the `platform/` workspace. No `any` escapes added to satisfy the new types.

14. **No regressions on existing sidebar behaviour.** Date bucket grouping (Today / Yesterday / Last 7 Days / Older) is preserved for conversations that are not pinned and not in a folder. Conversation rename and delete (existing) still work.

---

## Pre-commit gates

Run all of the following and confirm exit 0 before committing:

```bash
# 1. TypeScript
cd platform && npx tsc --noEmit

# 2. Lint
cd platform && npx eslint src --ext .ts,.tsx --max-warnings 0

# 3. Unit tests (if any exist for sidebar or API route helpers)
cd platform && npx jest --passWithNoTests --testPathPattern="conversations|folders|sidebar"

# 4. Migration syntax check — ensure the SQL file parses without error
# (run against local Postgres or use psql --dry-run equivalent)
# At minimum: verify the file exists and is non-empty
ls platform/migrations/*r8_pin_archive_folders* | xargs wc -l

# 5. Build
cd platform && npx next build 2>&1 | tail -20
```

If `npx next build` is slow in the worktree, `tsc --noEmit` + `eslint` are the hard gates; build may be deferred to CI.

---

## Commit message template

```
feat(sidebar): R8-S4 pin, archive, and folder organisation

- Add DB migration: conversations.pinned, conversations.archived_at,
  conversation_folders, conversation_folder_members
- Extend PATCH /api/conversations/[id] for pinned/archived/folder_id
- Extend GET /api/conversations with pinned/archived_at/folder_id + ?archived param
- Add GET/POST /api/folders and PATCH/DELETE /api/folders/[id]
- ConversationSidebar: Pinned section → Folders section → date buckets
- DropdownMenu per conversation: Pin/Unpin, Archive, Move to Folder, Delete
- ArchivedView component; "Archived" link at sidebar bottom
- FolderGroup collapsible component; "New folder" button
- useFolders hook; extend useConversations with pin/archive/moveToFolder
- TypeScript clean; no regressions on existing sidebar behaviour

Closes R8-S4.
```
