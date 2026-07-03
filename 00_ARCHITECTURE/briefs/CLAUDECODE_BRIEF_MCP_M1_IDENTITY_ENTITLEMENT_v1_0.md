---
canonical_id: CLAUDECODE_BRIEF_MCP_M1_IDENTITY_ENTITLEMENT
version: 1.0
status: READY-FOR-EXECUTION — M1 identity + entitlement foundation (builds on merged M0)
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASE M1)
depends_on: M0 (merged, PR #361 / 1e096d00 — role resolver + entitlement gate live)
authoritative_state: RETRIEVAL_TO_MCP_HANDOFF_v1_0 · CURRENT_STATE v6.07
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (entitlement at CHANNEL)
verification_basis: live code, read 2026-06-30
hard_constraints:
  - entitlement at the channel; retrieval stays chart-agnostic + FROZEN
  - reuse M0's role resolver — do NOT re-implement role lookup
  - VITEST not jest; `import { query } from '@/lib/db/client'` (no _ctx.db); scoped reads only
acceptance_criteria: see §5
---

# CLAUDE CODE BRIEF — MCP M1: IDENTITY + ENTITLEMENT FOUNDATION

> M0 gave us per-call entitlement (`authorizeChartAccess` at the chokepoint) + a role-carrying principal. M1
> makes the principal a full portal identity and adds the *list* side of entitlement (`getEntitledCharts`) —
> the foundation M2 (chart selection) stands on. This is mostly EXTRACT + REUSE, not new invention.

## §1 — What M0 already shipped (build on it, don't redo)
- `McpPrincipal.role: 'guest'|'super_admin'` (`platform/src/lib/mcp/types.ts:22-23`).
- `resolveMcpPrincipalRole(userUid)` helper — `SELECT role FROM profiles WHERE id=$1`, defaults `'guest'`
  (`platform/src/lib/mcp/auth.ts:141-154`); `validateMcpKey` calls it (`:122`).
- `authorizeChartAccess({principal:{uid,role}, chartId, db})` → `'all'|'view'|'deny'` is the per-call gate.

## §2 — M1.1 Identity core (one resolver, all front-doors)
Today role is resolved on the Bearer path; the OAuth path must reuse the SAME helper (M0 noted this, didn't
wire it). Make a single `resolveMcpPrincipal(user_uid): Promise<McpPrincipal>` that both the Bearer key path
(`auth.ts`) and the OAuth path (`server.ts` OAuth branch) call, returning `{ user_uid, key_id, role }`. No new
role logic — it wraps `resolveMcpPrincipalRole`. Acceptance: both auth front-doors produce an identical
role-bearing principal; one code path, no duplication.

## §3 — M1.2 `getEntitledCharts(uid)` (extract the portal's existing query)
The portal already computes a user's reachable charts inline in `platform/src/app/dashboard/page.tsx:46-58`.
**Extract it into a reusable helper** `getEntitledCharts(uid, role, db)`:
- super_admin → `SELECT * FROM charts ORDER BY created_at DESC` (all charts).
- guest → the dashboard guest-branch query (lines 49-57):
  ```sql
  SELECT c.* FROM charts c
   WHERE c.owner_id = $1 OR c.client_id = $1
      OR EXISTS (SELECT 1 FROM chart_grants g WHERE g.chart_id = c.id AND g.principal_id = $1)
   ORDER BY c.created_at DESC
  ```
- Return id + display name via `COALESCE(preferred_name, subject_name, name) AS display_name`
  (`charts.preferred_name` is the portal's canonical native display name; precedence matches
  `api/admin/charts/route.ts:16`). Put the helper in `platform/src/lib/auth/` (next to authorizeChartAccess) so
  both web + MCP reuse it. Refactor `dashboard/page.tsx` to call it (DRY; one query of record).

## §4 — M1.3 Enforcement (already true per-call; M1 adds list-scoping)
The per-call gate (M0) already prevents reading an unentitled chart. M1's addition: ensure any MCP surface that
*returns a set of charts* (the M2 `list_my_charts`, charts-as-resources) is scoped through `getEntitledCharts`,
never an unscoped `SELECT * FROM charts`. No new gate code — list surfaces consume the entitled set.

## §5 — Acceptance criteria
- `resolveMcpPrincipal` is the one resolver; Bearer + OAuth paths both produce `{user_uid,key_id,role}`.
- `getEntitledCharts(uid, role, db)` exists, extracted from the dashboard query, returns id + display_name;
  `dashboard/page.tsx` refactored to use it (no behavior change on the web side — verify the dashboard still
  lists the same charts).
- A user's MCP-reachable chart set == their portal entitlement (owner ∪ client_id ∪ view-grant; super_admin =
  all). Proven: user A sees only A's charts; super_admin sees all; cross-user isolation holds (prod).
- Retrieval stayed FROZEN; chart-agnostic gate green; Vitest; no native name in tests.

## §6 — VERIFICATION PHASE (mandatory; the phase is NOT done until ALL pass — independent Auditor)
This phase is verified by the swarm's independent Auditor (distinct from the builder), thoroughness
Auditor-decided but no weaker than this floor. Every claim is proven, not asserted. M0/M0.5 lesson: the gap is
always between "merged" and "behaviorally proven on prod" — close it here.

**V1 — Build gate (the M0-merged-broken catch):** `cd platform-mcp && npm run build` AND
`cd platform && npm run build` (or `npx tsc --noEmit`) BOTH exit 0. The new `typecheck-mcp` CI job is green on
the PR. No phase advances on a non-compiling package.
**V2 — Unit/integration tests:** new tests for `resolveMcpPrincipal` (Bearer + OAuth both yield role) and
`getEntitledCharts` (owner / client_id / view-grant / super_admin branches + the empty case); `npm test`
(Vitest) green; no test asserts the native name.
**V3 — Deploy + revision match:** merge → CI green → deploy fires → deployed `amjis-mcp` revision image SHA ==
merged SHA (gcloud describe). No "done" before the running revision is the merged code.
**V4 — Behavioral proof on PROD (≥2 users × ≥2 charts; deny needs a GUEST key — super_admin returns 'all'):**
  - super_admin key → entitled-set == all charts.
  - guest user A key → `getEntitledCharts` returns ONLY A's owned+granted charts (enumerate; assert B's charts absent).
  - guest A → any per-chart tool on a chart A is NOT entitled to → AUTHZ_DENIED (regression-guards M0).
  - the web dashboard for the same users still lists the identical chart set (no refactor regression).
**V5 — Invariants:** retrieval `lib/retrieval` untouched (git diff shows zero changes there); chart-agnostic CI
gate green; no entitlement logic pushed into retrieval; reverse-citation report if anything was deleted.
**V6 — Self-description truthful:** `/health` count unchanged-or-correct; no stale counts introduced.
**On ANY V-failure:** the Auditor triggers the remediation loop (charter §4) — fix + re-verify, or roll back to
the last good snapshot; the phase does not advance until V1–V6 all pass.

*End of CLAUDECODE_BRIEF_MCP_M1_IDENTITY_ENTITLEMENT v1.0. Next: M2 chart selection consumes getEntitledCharts.*
