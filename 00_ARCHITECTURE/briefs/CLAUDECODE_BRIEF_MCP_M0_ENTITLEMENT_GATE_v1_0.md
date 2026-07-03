---
canonical_id: CLAUDECODE_BRIEF_MCP_M0_ENTITLEMENT_GATE
version: 1.0
status: READY-FOR-EXECUTION — the fully-resolved M0 wave (entitlement gate + principal→role + health/health-count)
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm's FIRST + highest-stakes phase
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASE M0)
authoritative_state: RETRIEVAL_TO_MCP_HANDOFF_v1_0 · CURRENT_STATE v6.07 · git HEAD 2b02f924
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (entitlement at CHANNEL = Option 1)
verification_basis: live code, read 2026-06-30 (all file:line below are from the live tree)
session_type: implementation — Claude Code in Antigravity, worktree-isolated, prod-verify after merge
hard_constraints:
  - entitlement lives at the CHANNEL; retrieval stays chart-agnostic + FROZEN (never pushed into it)
  - chart-agnostic principle #14; no audience tier; reverse-citation before any delete; scoped DELETE only
  - VITEST not jest; CapabilityContext carries no db (use `import { query } from '@/lib/db/client'`)
  - never green a test by re-embedding the native name
acceptance_criteria: see §6
---

# CLAUDE CODE BRIEF — MCP M0: ENTITLEMENT GATE (fully resolved)

> **This is the swarm's first and most dangerous wave.** It closes the one remaining P0 security hole: any
> valid MCP key can currently read ANY chart. After this wave, every chart-scoped MCP surface authorizes the
> caller against the chart before any retrieval, exactly as the portal already does. M0.1 (401 fix) and M0.3
> (kala_temporal native fallback) are ALREADY DONE retrieval-side — this wave is M0.2 + M0.4-a (principal→role)
> + M0.4-b (health/tool_list staleness) + two adjudicated special cases.

## §0 — The core gap (one sentence)

`authorizeChartAccess` expects a principal `{ uid, role: 'guest'|'super_admin' }`; the MCP principal carries
only `{ user_uid, key_id }` (no role), and **no MCP path ever calls the gate**. Close it by (a) making the MCP
principal carry `role` + a real `uid`, and (b) calling `authorizeChartAccess` before dispatch on every
chart-scoped surface, mapping `'deny'` → 401/error.

## §1 — Exact code shapes (verified live; build against these, do not re-derive)

**The gate** — `platform/src/lib/auth/authorizeChartAccess.ts`:
```ts
export type Principal = { uid: string; role: 'guest' | 'super_admin' }
export type Permission = 'all' | 'view' | 'deny'
export async function authorizeChartAccess(
  args: { principal: Principal; chartId: string; db: DbLike }
): Promise<Permission>
// Rule 1: role==='super_admin' → 'all'
// Rule 2: SELECT owner_id FROM charts WHERE id=$1; owner_id===principal.uid → 'all'
// Rule 3: SELECT permission FROM chart_grants WHERE chart_id=$1 AND principal_id=$2; row → 'view'|'deny'
// Rule 4: else → 'deny'
// DbLike = { query<T>(sql, params?): Promise<{rows:T[]}> }
```

**The chokepoint pattern to mirror** — `platform/src/lib/gateway/invoke_tool.ts:86-103`:
authorize is a hard gate STRICTLY BEFORE executor dispatch. Order: contract → validate → resolve chartId
(`ctx.chartId ?? params.chart_id`; per_chart && missing → `CHART_REQUIRED`) → **authorize (deny → throw)** →
… → dispatch. `'view'` is sufficient for reads; write tools must demand `'all'`.

**MCP principal today** — `platform-mcp/src/types.ts:100-104`: `interface Principal { user_uid: string; key_id: string }`.
`KeyValidateResponse` (109-115): `{ valid, user_uid?, key_id?, error? }`.

**Validate path** — `platform-mcp/src/auth.ts:67` → `GET /api/mcp/keys/validate`
(`platform/src/app/api/mcp/keys/validate/route.ts:51-56` returns `{valid, user_uid, key_id}`); underlying
`validateMcpKey` (`platform/src/lib/mcp/auth.ts:97-126`) selects `key_id,key_hash,user_uid` from `mcp_api_keys`.
**Neither returns role.**

**Role source** — `profiles` table: `SELECT role FROM profiles WHERE id=$1`
(`id` = Firebase UID; `role` CHECK IN ('guest','super_admin') DEFAULT 'guest'; `001_baseline.sql:58-61`).
Web callers do this inline (`chart-page-guard.ts:32-38`, `consult/route.ts:295-322`). **No reusable
user_uid→role helper exists for the MCP path — create one.**

**Owner + grant tables:** `charts.owner_id TEXT` (Firebase UID; `001_baseline.sql:150`);
`chart_grants(chart_id UUID, principal_id TEXT, permission TEXT CHECK IN ('view'), UNIQUE(chart_id,principal_id))`
(`001_baseline.sql:195-203`). The gate reads both; you do not query them directly.

## §2 — The work, resolved

### M0.4-a — Principal carries role + uid (do FIRST; gates M0.2)
1. Extend MCP `Principal` (`platform-mcp/src/types.ts`) to `{ user_uid, key_id, role: 'guest'|'super_admin' }`.
   Keep `user_uid` as the field name MCP-side; map to the gate's `uid` at the call site (field-name-only diff).
2. Make the validate path return role: extend `validateMcpKey` (`platform/src/lib/mcp/auth.ts`) to also
   `SELECT role FROM profiles WHERE id = user_uid` (LEFT JOIN or second query; default `'guest'` if no row),
   and add `role` to the `/api/mcp/keys/validate` response + `KeyValidateResponse` + `validateMcpKeyFromHeader`.
3. Add a single helper `resolveMcpPrincipalRole(user_uid): Promise<'guest'|'super_admin'>` (the one reusable
   user_uid→role lookup) used by both auth front-doors (Bearer key + OAuth).

### M0.2 — Call the gate on every chart-scoped surface (the security keystone)
**Placement decision (resolved): gate at the platform primitives route, not in each tool file.** Rationale: the
registry-served tools already flow through `/api/mcp/primitives/[tool]/route.ts`, and that route already
resolves `chartId` from params/headers. Putting the gate there mirrors `invoke_tool.ts`, covers all
registry-bridge tools at once, and keeps the check in ONE place (single chokepoint). For the still-direct
tools (sidecar/REST ones not yet migrated), add the same gate call at the top of each handler as those migrate
(the keystone wave) — until migrated, add a thin inline gate so no chart-scoped surface ships ungated.

Concretely in `platform/src/app/api/mcp/primitives/[tool]/route.ts` (before dispatch, ~line 95):
```ts
const role = await resolveRole(userUid)              // SELECT role FROM profiles WHERE id=userUid
const chartId = params.chart_id ?? request.headers.get('x-mcp-chart-id')
if (contractIsPerChart(toolName)) {
  if (!chartId) return json(400, { error: 'CHART_REQUIRED' })
  const perm = await authorizeChartAccess({ principal: { uid: userUid, role }, chartId, db })
  if (perm === 'deny') return json(401, { error: 'AUTHZ_DENIED', chartId })
  // write tools (record_outcome) require 'all', not 'view'
}
```
Use `import { query } from '@/lib/db/client'` for `db` (NOT `_ctx.db` — it's undefined). Map deny → a tool
ERROR result (`isError:true`) at the MCP envelope layer so the LLM can self-correct, not a protocol crash.

### M0.4-b — Truthful self-description
- `platform-mcp/src/server.ts:178` health endpoint: replace hardcoded `tools: 13` with a dynamic count of
  actual registrations (live count = 43 tools + 10 resources; compute, don't hardcode).
- Regenerate or delete the stale `generated/tool_list.json` (11 URIs vs live surface).
- Fix two wrong code comments: `server.ts:127-128` label `holistic_bundle_chart_facts` + `kala_temporal_bundle`
  "chart-agnostic" — both are chart-SCOPED (required `chart_id`). Correct the comments.

## §3 — The gate-target list (resolved; this is the wave's scope)

**HARD gate targets — 18 tools (required chart_id) + 2 resources = 20 surfaces:**
Tools: `holistic_bundle`, `holistic_bundle_chart_facts`, `kala_temporal_bundle`, `event_anchors`,
`mitigation_map`, `muhurta_finder`, `phala_outlook`, `lel_query`, and the 10 registry_bridge per-chart tools
`get_chart_orientation`, `get_domain_reading`, `get_signals`, `traverse_graph`, `get_positions`, `get_dashas`,
`get_temporal_windows`, `get_projections`, `get_remedies`, `get_chart_quality`.
Resources: `marsys://chart-bundle/{chart_id}`, `marsys://multi-ayanamsha/{chart_id}`.

**SPECIAL CASES — 3 (adjudicated):**
- `record_outcome` + `query_calibration` (`mimamsa_outcome.ts`, chart_id OPTIONAL) → **gate-when-present**: if
  `chart_id` supplied, enforce (`record_outcome` is a write → require `'all'`); if absent, it's cross-chart
  aggregate calibration (L5 corpus) → ungated.
- `marsys://chart-snapshot` resource (`chart_snapshot.ts:199-209`) → **hidden per-chart leak**: no `{chart_id}`
  in the URI but `generateChartSnapshot()` calls `query_chart_facts`/`query_dasha_periods`/`query_panchanga`
  with no chart_id → resolves a single default (native) chart server-side. **Fix: parametrize with `{chart_id}`
  + gate, OR confirm it is intentionally native-only and remove it from the multi-user surface.** Human-Proxy
  decides; default to parametrize-and-gate (safer for multi-user).

**CHART-AGNOSTIC — 30 surfaces, NO gate** (do not add one — would break corpus/reference/ephemeris access):
L0 brahmagyan (5), ephemeris (5), pyhora birth-params compute (3), remedy corpus (7 — incl. the misleadingly
named `query_remedies_for_chart` which takes only an `affliction` keyword, NOT chart_id), registry_bridge
global `get_classical_citation` + `list_assets`, and 8 reference resources.

**SEPARATE cleanup (not a gate target):** `ephemeris_cache_native_lifetime` (`l0_ephemeris.ts:243-265`) is
native-hardcoded (description "native's lifetime window 1984-2070", endpoint `/native_lifetime_meta`, empty
input schema). It takes no chart_id so it can't be chart-gated — it's a native-contamination item: retire it
or reparametrize to a generic `ephemeris_cache_range(start,end)`. Reverse-citation gate before removal.

## §4 — OAuth identity (fold in; blocks real multi-user but not the Bearer path)
`platform-mcp/src/oauth/token.ts:95` issues `issueTokens(authCode.uid ?? 'anonymous', …)` — the auth-code
grant drops identity (the Firebase redirect never sets `uid` on the code). **Minimum for M0:** make it
fail-closed (reject if `uid` unset) rather than mint an `'anonymous'`-owned token that would then fail the gate
opaquely. Full DB-backed OAuth is M5; here just stop issuing anonymous-owned tokens. (Bearer-key path already
carries a real `user_uid`; it's the production path and works once role is added.)

## §5 — Test + verification (the Auditor decides final thoroughness; this is the floor)

**Isolation test matrix (the security proof — run against PROD):** ≥2 users × ≥2 charts.
| Principal | Chart | Relationship | Expected |
|---|---|---|---|
| User A (owner) | Chart A | owner | 200 / `'all'` |
| User A | Chart B | no relation | 401 `AUTHZ_DENIED` |
| User B (view-grant on A) | Chart A | grant 'view' | 200 read; write (`record_outcome`) → deny |
| User B | Chart A | grant 'view' | write tool → 401 (needs 'all') |
| super_admin | any chart | role | 200 / `'all'` |
| any key | missing chart_id on per-chart tool | — | 400 `CHART_REQUIRED` |
| any key | `chart-snapshot` resource | hidden-per-chart | gated (or removed) — NOT native data to a stranger |

Plus: run one chart-AGNOSTIC tool per category to confirm the gate did NOT over-reach (corpus/ephemeris still
200 without chart_id). Tests are **Vitest**; do not assert the native name anywhere. Confirm the deployed
`amjis-mcp` Cloud Run revision == merged SHA before claiming done (the verify-revision rule).

## §6 — Acceptance criteria
- MCP `Principal` carries `role`; validate path + OAuth path both populate it; `resolveMcpPrincipalRole` is the
  one helper.
- All 20 hard chart-scoped surfaces (+ the 3 adjudicated special cases) call `authorizeChartAccess` before any
  retrieval; deny → tool error / 401; missing chart_id → `CHART_REQUIRED`. Verified by the isolation matrix on PROD.
- No chart-agnostic surface was gated (corpus/ephemeris/birth-params still reachable without chart_id).
- `chart-snapshot` no longer serves native data to a non-entitled caller (parametrized+gated or removed).
- `/health` reports the true count; `tool_list.json` regenerated/removed; the two wrong "chart-agnostic"
  comments corrected; OAuth no longer mints `'anonymous'`-owned tokens.
- Retrieval stayed FROZEN + chart-agnostic (zero entitlement pushed into `lib/retrieval`); any deletion has a
  reverse-citation report; prod revision == merged SHA; no native name in any test.
- Charter §0.B invariants intact; chart-agnostic CI gate green.

*End of CLAUDECODE_BRIEF_MCP_M0_ENTITLEMENT_GATE v1.0 — the resolved first wave. After this merges + prod-verifies,
the swarm advances to M1 (identity core + getEntitledCharts) per the charter DAG.*
