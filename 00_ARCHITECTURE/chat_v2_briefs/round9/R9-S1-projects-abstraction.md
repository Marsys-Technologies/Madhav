---
canonical_id: CHAT_V2_R9_S1_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R9
session_id: R9-S1
owner: chat-v2/round9-elevation worktree
branch: chat-v2/round9-elevation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR9
flag_namespace: MARSYS_FLAG_R9_PROJECTS
authored: 2026-05-20
depends_on: []
estimated_sessions: 2
---

## Context

R9-S1 introduces the **Projects abstraction** — a top-level organisational layer that sits above individual conversations in the MARSYS-JIS platform. A Project groups related conversations, optionally pins a chart context, and injects a `system_prompt_addition` that is prepended to the synthesis prompt at query time. This makes it possible to maintain persistent, scoped system-level context across multiple conversations without repeating it per message.

This brief covers the full first session: database schema, API routes, synthesis prompt integration hook, and the sidebar UI grouping. Advanced features (project-scoped file retrieval, full `chart_id` resolution pipeline, bulk conversation assignment) are deferred to R9-S2+.

This work runs inside the `chat-v2/round9-elevation` branch in the `/Users/Dev/Vibe-Coding/Apps/MadhavR9` worktree. All changes are scoped to the `platform/` tree except the migration files. The `MARSYS_FLAG_R9_PROJECTS` feature flag gates the sidebar grouping and the prompt-injection path so production is unaffected until the flag is enabled.

---

## Files in scope

### Database migrations
```
platform/prisma/migrations/YYYYMMDD_add_projects_abstraction/migration.sql
```
or, if the project uses raw SQL migration scripts rather than Prisma Migrate:
```
platform/db/migrations/YYYYMMDD_add_projects_abstraction.sql
```
Determine from existing migration conventions before creating. The migration must contain exactly the following DDL (order preserved):

```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  system_prompt_addition TEXT,
  chart_id TEXT,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE project_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  storage_path TEXT NOT NULL,
  filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE project_conversations (
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, conversation_id)
);

CREATE INDEX idx_project_conv_project ON project_conversations(project_id);
CREATE INDEX idx_project_conv_conv    ON project_conversations(conversation_id);
```

Note: `deleted_at TIMESTAMPTZ` is included in `projects` to support soft-delete. A hard-delete variant is acceptable if the codebase has no soft-delete precedent — but the API layer must be consistent with whichever choice is made.

### Prisma schema (if Prisma is in use)
```
platform/prisma/schema.prisma
```
Add `Project`, `ProjectFile`, `ProjectConversation` models mirroring the DDL above. Run `prisma generate` after editing.

### API routes
```
platform/src/app/api/projects/route.ts                                    — GET (list) + POST (create)
platform/src/app/api/projects/[id]/route.ts                               — GET (detail) + PATCH (update) + DELETE
platform/src/app/api/projects/[id]/conversations/route.ts                 — POST (add conversation)
platform/src/app/api/projects/[id]/conversations/[conversationId]/route.ts — DELETE (remove conversation)
```

### Synthesis prompt integration
```
platform/src/lib/synthesis/prompts/synthesis_prompt_v2.ts
```
or whichever module builds the final system prompt passed to the LLM at query time. Locate the exact file before editing by tracing from the query pipeline entry point.

### Sidebar UI components
```
platform/src/components/consume/ConsumeChatV2.tsx           — may require sidebar wiring
platform/src/components/sidebar/ProjectsSection.tsx         — NEW: project grouping list
platform/src/components/sidebar/ProjectBadge.tsx            — NEW: chip rendered on conversations in project view
platform/src/components/modals/NewProjectModal.tsx          — NEW: creation modal
platform/src/hooks/useProjects.ts                           — NEW: data-fetching hook (SWR or React Query, match existing pattern)
```

Locate the sidebar composition root (likely inside `ConsumeChatV2.tsx` or a dedicated `Sidebar.tsx`) before creating new files; extend the existing structure rather than adding a parallel sidebar tree.

### Feature flag
```
platform/src/lib/feature_flags.ts
```
Add `MARSYS_FLAG_R9_PROJECTS` entry. Default: `false`.

### TypeScript types
```
platform/src/types/projects.ts   — NEW: shared Project, ProjectFile, ProjectConversation interfaces
```

---

## Files must not touch

- `01_FACTS_LAYER/**` — L1 facts layer; no session touches this without explicit native approval.
- `025_HOLISTIC_SYNTHESIS/**` — synthesis corpus; read-only from platform code.
- `00_ARCHITECTURE/**` — governance artifacts; this brief is the only exception and was written by the Conductor, not by the executing session.
- `platform/src/lib/synthesis/**` except the single prompt-assembly file identified above (and only the `system_prompt_addition` injection point within it).
- `platform/src/app/api/consume/**` — live query pipeline routes; do not refactor, only read for reference.
- `platform/tests/e2e/**` — existing smoke specs; do not modify (may add new spec files for R9-S1 under `platform/tests/e2e/chat-v2/round9/`).
- `.geminirules`, `.gemini/project_state.md` — Gemini mirror surfaces; no Claude-session touch without a mirroring step.
- `CLAUDE.md`, `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, `00_ARCHITECTURE/SESSION_LOG.md` — governance live surfaces; updated only by session-close protocol, not by feature execution.
- Any file not listed under "Files in scope" above.

---

## Acceptance criteria

### AC-1 — Project CRUD persists to DB
- `POST /api/projects` creates a row in `projects`; response includes `id`, `name`, `system_prompt_addition`, `chart_id`, `created_at`.
- `GET /api/projects` returns only projects owned by the authenticated user (`user_id` match), excluding soft-deleted rows.
- `PATCH /api/projects/[id]` updates `name`, `system_prompt_addition`, and/or `chart_id`; sets `updated_at`; rejects unknown fields.
- `DELETE /api/projects/[id]` sets `deleted_at` (soft-delete) or removes the row (hard-delete, consistent with codebase convention). Returns `204`.

### AC-2 — Conversation assignment
- `POST /api/projects/[id]/conversations` with `{ "conversation_id": "<id>" }` inserts a row in `project_conversations`.
- `DELETE /api/projects/[id]/conversations/[conversationId]` removes the row.
- `GET /api/projects/[id]` response includes `conversation_ids: string[]` and `files: ProjectFile[]`.

### AC-3 — Auth ownership check on every route
- All project routes validate that the authenticated user is the owner of the requested project. A request for a project owned by a different user returns `403`. An unauthenticated request returns `401`. No project data leaks across user boundaries.

### AC-4 — Synthesis prompt injection
- When `MARSYS_FLAG_R9_PROJECTS=true`: if the conversation resolved by the current query belongs to a project and that project has a non-null, non-empty `system_prompt_addition`, it is prepended to the system prompt before the main synthesis content with a clear delimiter, e.g.:
  ```
  [PROJECT CONTEXT]
  <system_prompt_addition text>
  [END PROJECT CONTEXT]

  <main synthesis prompt>
  ```
- The `query_trace` object (or equivalent tracing surface already in the pipeline) includes a `project_id` field and a `system_prompt_addition_applied: boolean` field when the flag is active.
- If `chart_id` is set on the project but full retrieval is not implemented in R9-S1, the trace emits `project_chart_retrieval: "[PROJECT_CHART_RETRIEVAL_DEFERRED]"` — no silent omission.
- When `MARSYS_FLAG_R9_PROJECTS=false` (default), the prompt assembly path is unchanged from pre-R9-S1 behaviour.

### AC-5 — Sidebar UI (flag-gated)
- When `MARSYS_FLAG_R9_PROJECTS=true`: a "Projects" section appears above "All Conversations" in the sidebar.
- Each project is listed by name; clicking a project filters the conversation list to only conversations belonging to that project.
- A "New Project" button in the sidebar header (or immediately above the Projects section) opens `NewProjectModal`, which accepts `name` and optional `system_prompt_addition` fields and calls `POST /api/projects` on submit.
- Conversations displayed in project-filtered view render a `ProjectBadge` chip showing the project name.
- When flag is false, sidebar renders exactly as it did before R9-S1.

### AC-6 — Migrations run cleanly
- `pnpm prisma migrate dev` (or the equivalent migration command for this codebase) applies the migration without errors on a fresh local DB.
- Down-migration or rollback notes are included as a comment block in the migration SQL file.

### AC-7 — TypeScript clean
- `pnpm tsc --noEmit` exits 0 with no new errors introduced by R9-S1 changes.
- No `any` types introduced in new files without an explanatory inline comment.

### AC-8 — No regression to existing chat flows
- Conversations that do not belong to any project continue to work without modification.
- The synthesis prompt for non-project conversations is byte-identical to the pre-R9-S1 output when the flag is false.

---

## Pre-commit gates

Run the following in order before committing. All must pass (exit 0) except where explicitly noted.

```bash
# 1. TypeScript
pnpm --filter platform tsc --noEmit

# 2. Lint
pnpm --filter platform lint

# 3. Unit tests (if any project-related unit tests exist or are added)
pnpm --filter platform test --passWithNoTests

# 4. Migration dry-run (adjust command to match codebase migration tooling)
pnpm --filter platform prisma migrate dev --name add_projects_abstraction --create-only
# Review generated SQL, then apply:
pnpm --filter platform prisma migrate dev

# 5. Prisma client regeneration (if Prisma is in use)
pnpm --filter platform prisma generate

# 6. Synthesis prompt injection smoke check
# With MARSYS_FLAG_R9_PROJECTS=true in .env.local, send a test query on a conversation
# that belongs to a project with system_prompt_addition set.
# Verify query_trace contains:
#   project_id: <uuid>
#   system_prompt_addition_applied: true
# And that the system prompt in the LLM call contains [PROJECT CONTEXT] block.

# 7. Flag-off regression
# With MARSYS_FLAG_R9_PROJECTS unset (or false), verify sidebar and synthesis are unchanged.
```

Gate 6 is a manual smoke check; document the result in the commit body or a brief session note. Gates 1–5 and 7 must be automated-pass.

---

## Commit message template

```
feat(projects): R9-S1 Projects abstraction — schema, API, prompt injection, sidebar

- Add `projects`, `project_files`, `project_conversations` tables (migration)
- API routes: GET/POST /api/projects, GET/PATCH/DELETE /api/projects/[id],
  POST/DELETE /api/projects/[id]/conversations/[conversationId]
- Synthesis prompt: prepend system_prompt_addition when MARSYS_FLAG_R9_PROJECTS=true;
  project_chart_retrieval deferred (R9-S2+)
- Sidebar: Projects section + NewProjectModal + ProjectBadge (flag-gated)
- All routes enforce user-ownership auth check
- TypeScript clean; no regression to non-project conversation flows

Flag: MARSYS_FLAG_R9_PROJECTS (default false — production unaffected)
Ref: 00_ARCHITECTURE/chat_v2_briefs/round9/R9-S1-projects-abstraction.md

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
