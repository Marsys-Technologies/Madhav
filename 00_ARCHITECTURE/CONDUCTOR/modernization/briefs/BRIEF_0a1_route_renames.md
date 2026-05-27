---
unit: 0a.1
wave: 0a
title: Route renames — consume→consult + merge /api/panchang(+a)
stream: A
worktree: ../MadhavStreamA
blockedBy: [naming_ci]
on_red: rollback
---

## Context (self-contained)
Pure, safe renames (MASTER_PLAN §3.7). "Consume" → "Consult" across UI/route/code; merge the duplicate
`/api/panchang` + `/api/panchanga` trees into one (`/api/panchang`). NO tenant-key or tool-name renames here
(those are strangler/contract work in later waves). Keep a redirect alias for `consume` for one release so
in-flight clients don't break.

## Scope
- Rename route dirs + identifiers `consume` → `consult`: `/api/chat/consume`→`/api/chat/consult`,
  `/consume`→`/consult`, `/clients/[id]/consume`→`/clients/[id]/consult`. Add a thin alias/redirect at the old
  paths (308 → new) retained for one release.
- Merge `/api/panchanga/route.ts` into the `/api/panchang/*` tree; single canonical path; alias the old.
- Update all internal references (links, fetches, tests) to the new paths.

## Acceptance criteria (all automated)
1. `pnpm vitest run platform/src/app/api/chat` green.
2. `python platform/scripts/governance/naming_lint.py` green (no duplicate panchang tree).
3. **Click-through reaches the behavior:** an integration test that mounts the consult page/route and asserts
   a request flows end-to-end on the NEW path (not just file existence).
4. Old `consume` path returns a redirect to `consult` (alias test).

## must_not_touch
`platform/src/lib/synthesis/**`, `platform-mcp/**`, `platform/migrations/**`.

## Commit cadence / rollback
Commits: (1) consult rename + alias, (2) panchang merge + alias, (3) reference updates. Each cherry-pickable.
Rollback = revert commits; no data/infra effect (routes only).
