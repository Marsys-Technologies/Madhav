---
stream: Chat V2 Round 9 — Elevation
branch: chat-v2/round9-elevation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR9
authored: 2026-05-20
status: STREAM_COMPLETE (S2 BLOCKED — see below; post-merge remediation applied via PR #103)
---

## Sessions executed

| Session | Status | Commit | Summary |
|---------|--------|--------|---------|
| R9-S1 | COMPLETE | c712d59 | Projects abstraction: `projects`, `project_files`, `project_conversations` tables (migration 110); `/api/projects/**` CRUD; synthesis prompt injection via `project_system_prompt_addition`; sidebar `ProjectsSection` + `NewProjectModal` behind `MARSYS_FLAG_R9_PROJECTS`. |
| R9-S2 | BLOCKED | — | Semantic conversation search. Blocked on `depends_on: [R8-S3]` (pg_trgm migration not yet merged from R8 branch). Execute after R8-S3 merges during merge-train rebase. |
| R9-S3 | COMPLETE | 8b085aa | Persona library: `personas` table (migration 111) with partial unique index for default; `/api/personas/**` CRUD; `ModelStylePicker` persona group with quick-switch (applies default_style + default_stack); `/settings/personas` management page; synthesis injection via `persona_system_prompt` (PERSONA block, prepended before PROJECT CONTEXT and main prompt). |
| R9-S4 | COMPLETE | 67c9734 | Inline tool-flow timeline: `InlineToolFlow` component (collapsed by default, fetches `/api/audit/[queryId]/trace`, memoized per queryId); `GET /api/audit/[queryId]/trace` thin route over `query_trace_steps`; integrated into `AssistantMessage` after action bar; gated behind `NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW`; `isAdmin` derived from `disclosure_tier` in message metadata. |

## Migration range

R9 reserved migrations 110–119. Migrations cut in this stream:
- `110_add_projects_abstraction.sql`
- `111_add_personas.sql`

Migrations 112–119 available for R9-S2 (semantic search, pgvector) when unblocked.

## Flag namespace

| Flag | Default | Description |
|------|---------|-------------|
| `MARSYS_FLAG_R9_PROJECTS` | `false` | Projects abstraction (sidebar grouping + prompt injection) |
| `MARSYS_FLAG_R9_SEMANTIC_SEARCH` | `false` | Semantic conversation search (blocked, not implemented) |
| `MARSYS_FLAG_R9_PERSONAS` | `true` | Persona library (ModelStylePicker + settings page + synthesis injection) |
| `MARSYS_FLAG_R9_TOOL_FLOW` | `false` | Inline tool-flow timeline in AssistantMessage (admin-only) |
| `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS` | unset | Client-side gate for sidebar ProjectsSection |
| `NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS` | unset | Client-side gate for ModelStylePicker persona group |
| `NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW` | unset | Client-side gate for InlineToolFlow component |

## Merge train

R9 is position 3 (merges last: R7 → R8 → R9). R9 must rebase onto main after R7 and R8 merge.
Expected conflict point: `platform/src/app/api/conversations/search/route.ts` (shared with R8-S3).
R9-S2 implementation happens post-rebase once R8-S3 is on main.

See: `00_ARCHITECTURE/MERGE_TRAIN_ORDER_v1_0.md`

---

## POST-MERGE REMEDIATION — 2026-05-20

**PR #103** (`chat-v2/r9-integration-remediation`) — "fix(chat-v2): R9-S1/S3/S4 integration gap remediation"

The stream claimed S1/S3/S4 COMPLETE but post-merge verified diagnosis found two distinct gap patterns:

### Gap 1 — NEXT_PUBLIC_ build-args missing from deploy.yml (R9-S1 + R9-S4)

`ProjectsSection` (R9-S1) and `InlineToolFlow` (R9-S4) use `process.env.NEXT_PUBLIC_*` to gate rendering in client components. These constants are baked into the Next.js bundle at `next build` time via Docker `--build-arg`. The server-side flags (`MARSYS_FLAG_R9_PROJECTS=true`, `MARSYS_FLAG_R9_TOOL_FLOW=true`) were set via `gcloud run services update` but had no effect on the already-baked client bundle. Both features rendered `null` in production.

**Fix**: Added `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS=true`, `NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS=true`, `NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW=true` to `deploy.yml` `build-args` block.

| Flag | Was | Now |
|------|-----|-----|
| `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS` | unset (bundle false) | `true` in build-args |
| `NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS` | unset (bundle true — uses `!== 'false'` logic) | `true` explicit |
| `NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW` | unset (bundle false) | `true` in build-args |

### Gap 2 — Persona props not threaded through V2PrefsCtx (R9-S3)

`ModelStylePicker` has full persona code and guards its persona `DropdownMenuGroup` on `onPersonaChange` being set (line 96: `{showPersonas && onPersonaChange && (...)`). `V2PrefsCtx` / `V2BottomBar` never included `activePersonaId` or `setActivePersonaId`, so `onPersonaChange` was always `undefined` → persona group never rendered. `persona_id` was also absent from the `useChatRuntime` body closure.

**Fix**: Added `activePersonaId: string | null` + `setActivePersonaId` to `V2PrefsCtxValue`; wired state through `prefsCtxValue` → `V2BottomBar` → `ModelStylePicker`; added `persona_id` to runtime body.

### What was NOT missing

- `/api/projects/**`, `/api/personas/**`, `/api/audit/[query_id]/trace` — all existed and returned correct auth errors
- `ProjectsSection`, `NewProjectModal`, `ProjectBadge` — existed and were correctly mounted in `ConversationSidebarV2`
- `InlineToolFlow` — existed and was correctly mounted in `AssistantMessage.tsx` (lines 12, 218)
- Synthesis persona injection — existed in `single_model_strategy.ts` and was reading `persona_system_prompt` from the synthesis request

### Test coverage added

12 unit tests in `platform/src/components/chat/__tests__/r9-integration-remediation.test.tsx`:
- InlineToolFlow: 5 tests (flag-gated null renders + disclosure button render)
- ModelStylePicker persona group: 4 tests (prop-absent vs prop-present; persona names; crash-safety)
- ProjectsSection sidebar gate: 3 tests (showProjects=true/false contract)

Zero new regressions vs 21-failure KNOWN_PRE_EXISTING_FAILURES.md baseline.

### Root cause note for future streams

> A stream completion claim of "component X is mounted" is not sufficient verification.
> Required: (1) is the `NEXT_PUBLIC_*` build-arg in `deploy.yml`? (2) is the optional
> prop that gates the feature actually passed from the parent/context into the component?
