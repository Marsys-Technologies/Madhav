---
canonical_id: CHAT_V2_R9_S3_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R9
session_id: R9-S3
owner: chat-v2/round9-elevation worktree
branch: chat-v2/round9-elevation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR9
flag_namespace: MARSYS_FLAG_R9_PERSONAS
authored: 2026-05-20
depends_on: []
---

## Context

R9-S3 implements a persona library — named, user-editable system prompt variants that appear as quick-switches in the `ModelStylePicker`. A persona bundles a custom system prompt with optional default style and stack pre-selections. Only one persona may be marked default per user, enforced at the DB level via a unique partial index. When a persona is active, its `system_prompt` is prepended to the synthesis call's system prompt; if a project context (R9-S1) is also active, the persona prompt leads, followed by the project addition.

This session is self-contained: it authors the Drizzle schema migration, four API route handlers, the `ModelStylePicker` integration, the `/settings/personas` settings page, and the synthesis-prompt injection. It does not alter any R9-S1 or R9-S2 logic beyond the single injection point in the synthesis prompt assembly.

---

## Files in scope

### New files

```
platform/src/db/migrations/YYYYMMDD_add_personas.sql
platform/src/db/schema/personas.ts
platform/src/app/api/personas/route.ts          # GET + POST
platform/src/app/api/personas/[id]/route.ts     # PATCH + DELETE
platform/src/app/settings/personas/page.tsx
platform/src/app/settings/personas/PersonaCard.tsx
platform/src/app/settings/personas/PersonaForm.tsx
platform/src/hooks/usePersonas.ts
platform/src/types/personas.ts
```

### Existing files (modify only)

```
platform/src/components/chat/ModelStylePicker.tsx
platform/src/lib/synthesis/prompt-assembly.ts   # or equivalent synthesis prompt builder
```

---

## Files must not touch

```
platform/src/components/consume/ConsumeChatV2.tsx   # R9 post-cutover; do not touch
platform/src/lib/pipeline/**                        # pipeline internals; no scope here
platform/src/db/schema/projects.ts                  # R9-S1 artifact; read-only this session
platform/src/app/api/projects/**                    # R9-S1 artifact; read-only this session
platform/src/app/settings/projects/**               # R9-S1 artifact; read-only this session
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
00_ARCHITECTURE/CURRENT_STATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG.md
```

---

## Acceptance criteria

### AC-1 — Database schema

- Migration SQL creates `personas` table exactly as specified, including the `unique partial index` on `(user_id) WHERE is_default = TRUE`.
- Drizzle schema file (`personas.ts`) matches the migration; `drizzle-kit generate` produces no diff after migration is applied.

### AC-2 — API: GET /api/personas

- Returns array of personas for the authenticated user.
- Ordering: default persona first (`is_default DESC`), then alphabetical by `name`.
- Returns `[]` (empty array, HTTP 200) when user has no personas; never 404.

### AC-3 — API: POST /api/personas

- Creates a new persona with the provided `{ name, system_prompt, default_style?, default_stack?, is_default? }`.
- If `is_default: true`, atomically unsets `is_default` on any existing default for that user before setting the new one (single transaction).
- Returns created persona row (HTTP 201).
- Validation: `name` required (max 50 chars); `system_prompt` required (max 4000 chars); returns HTTP 422 with field-level error detail on violation.

### AC-4 — API: PATCH /api/personas/[id]

- Updates supplied fields; ignores fields not present in body.
- If `is_default: true` is supplied, performs the same atomic unset-then-set transaction as POST.
- Scoped to authenticated user; returns HTTP 403 if persona belongs to a different user.
- Returns updated persona row (HTTP 200).

### AC-5 — API: DELETE /api/personas/[id]

- Deletes the persona.
- If the persona is the user's only persona, returns HTTP 409 with body `{ error: "cannot_delete_last_persona" }` and performs no deletion.
- Scoped to authenticated user; returns HTTP 403 if persona belongs to a different user.
- Returns HTTP 204 on success.

### AC-6 — ModelStylePicker integration

- On mount, `ModelStylePicker` fetches `/api/personas` (via `usePersonas` hook).
- A "Personas" group is rendered above the existing stacks list.
- Each persona row displays: persona `name` + small chip showing `default_style` and/or `default_stack` when set.
- Selecting a persona sets the active persona in component/context state, applies `default_style` and `default_stack` as pre-selections in the picker.
- A "Manage Personas" link at the bottom of the Personas group navigates to `/settings/personas`.
- When no personas exist, the Personas group renders a single "No personas yet — Manage" link (no empty list).

### AC-7 — Synthesis integration

- When an active persona is set, `persona.system_prompt` is prepended to the system prompt passed to the synthesis call.
- When both a project (R9-S1 `system_prompt_addition`) and a persona are active: persona prompt is prepended first, project addition second, then the main system prompt.
- The injected persona prompt is visible in the `query_trace` under a `persona_injection` key (or equivalent trace step) when `AUDIT_ENABLED=true`.
- When no persona is active, synthesis behavior is identical to pre-R9-S3 (no regression).

### AC-8 — Settings page: /settings/personas

- Renders a card grid of all user personas.
- Each card shows: `name`, a truncated excerpt of `system_prompt` (max ~120 chars), `default_style`/`default_stack` chips if set, an "Edit" button, a "Delete" button.
- "New Persona" button opens an inline form or modal containing: `name` input, `system_prompt` textarea, optional `default_style` dropdown, optional `default_stack` dropdown, "Set as default" toggle.
- Edit button populates the same form with existing values.
- Delete button shows a confirmation prompt; calls DELETE API; removes card on success.
- Cannot delete last persona: Delete button is disabled (or shows tooltip) when user has exactly one persona.
- Client-side validation mirrors AC-3 constraints before submission.

### AC-9 — TypeScript

- `tsc --noEmit` exits 0 across all new and modified files.
- No `any` escape hatches on public API surface types.
- `Persona` and `PersonaCreate` / `PersonaUpdate` types are exported from `platform/src/types/personas.ts` and consumed by routes, hooks, and components (no inline type duplication).

### AC-10 — No regression

- Existing `ModelStylePicker` style/stack selection behavior is unchanged when no persona is selected.
- Synthesis prompt assembly for non-persona, non-project sessions is byte-for-byte identical to pre-R9-S3.

---

## Pre-commit gates

Run all of the following from the worktree root (`/Users/Dev/Vibe-Coding/Apps/MadhavR9`) before committing:

```bash
# 1. TypeScript
pnpm tsc --noEmit

# 2. Lint
pnpm lint

# 3. Unit tests (if any exist for prompt-assembly or personas hook)
pnpm test --filter=platform -- --testPathPattern="personas|prompt-assembly"

# 4. Schema drift check (requires local DB with migration applied)
pnpm drizzle-kit check:pg   # or equivalent drizzle generate + diff; expect zero diff

# 5. Governance drift detector
python3 platform/scripts/governance/drift_detector.py --manifest 00_ARCHITECTURE/CAPABILITY_MANIFEST.json

# 6. Schema validator
python3 platform/scripts/governance/schema_validator.py
```

All gates must exit 0. Any non-zero exit is a hard block — do not commit until resolved.

---

## Commit message template

```
feat(personas): R9-S3 persona library — CRUD API, ModelStylePicker quick-switch, settings page, synthesis injection

- Add `personas` table migration + Drizzle schema with unique partial index on (user_id) WHERE is_default
- GET/POST /api/personas + PATCH/DELETE /api/personas/[id] with atomic default-swap and 409 last-persona guard
- ModelStylePicker: Personas group above stacks, per-persona style/stack chips, "Manage Personas" link
- /settings/personas: card grid with inline create/edit/delete form and last-persona delete guard
- Synthesis prompt assembly: persona.system_prompt prepended first; project addition second when both active
- Persona injection visible in query_trace under persona_injection key when AUDIT_ENABLED=true
- usePersonas hook + Persona/PersonaCreate/PersonaUpdate types in platform/src/types/personas.ts
- tsc clean; no regressions to existing style/stack selection or non-persona synthesis paths

Part of chat-v2/round9-elevation. Flag namespace: MARSYS_FLAG_R9_PERSONAS.
Closes R9-S3.
```
