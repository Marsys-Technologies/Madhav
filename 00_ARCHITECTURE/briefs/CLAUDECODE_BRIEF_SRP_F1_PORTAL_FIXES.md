---
canonical_id: CLAUDECODE_BRIEF_SRP_F1
version: 1.0
status: CURRENT
phase: SRP-F-1
session_type: fix
authored: 2026-05-25
worktree: MadhavSRP-F1
branch: fix/srp-f1-portal-fixes
deploy_target: amjis-web
may_touch:
  - platform/src/lib/mcp/primitives_registry.ts
  - platform/src/lib/retrieve/msr_sql.ts
  - platform-mcp/src/tools/lel_query.ts
must_not_touch:
  - platform-mcp/src/server.ts
  - platform/src/app/api/mcp/primitives/**
  - platform/src/lib/retrieve/index.ts
  - 00_ARCHITECTURE/**
---

# CLAUDECODE BRIEF: SRP-F-1 — Portal Fixes

## Context

You are executing fixes for the MARSYS-JIS System Repair Plan (SRP). This session addresses
four bugs confirmed by the Cross-Channel Parity Audit v2.0 (2026-05-25). All bugs are in the
**portal/web service** (`amjis-web`). No MCP sidecar files are modified in this session
(except `lel_query.ts` source_version annotation which is cosmetic and lives in platform-mcp
but requires only a one-line string change and no logic change).

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-F1`
Branch: `fix/srp-f1-portal-fixes`

## Fix 1 — FIX-1: Add 14 UDA tools to primitives_registry.ts

**File**: `platform/src/lib/mcp/primitives_registry.ts`

**Root cause**: The Universal Parity Campaign (UDA) added 14 tools to `platform-mcp/src/server.ts`
and created their schemas but never updated `primitives_registry.ts`. The MCP primitive dispatcher
at `platform/src/app/api/mcp/primitives/[tool]/route.ts` calls `isAllowedSurgicalTool()` which
uses `Object.hasOwn(MCP_TO_RETRIEVAL_TOOL, mcpToolName)`. Any tool not in `MCP_TO_RETRIEVAL_TOOL`
gets a 400 validation error before reaching the retrieval layer.

**Current state of SURGICAL_TOOLS** (ends at line 69):
```typescript
  'jaimini_chara_dasha_full',
] as const
```

**Current state of MCP_TO_RETRIEVAL_TOOL** (ends at line ~107):
```typescript
  jaimini_chara_dasha_full: 'jaimini_chara_dasha_full',
}
```

**14 tools to add** (all exist in `platform/src/lib/retrieve/index.ts` RETRIEVAL_TOOLS array
with these exact names — verify by grepping `index.ts` before adding):

| MCP tool name (server.ts key) | Platform retrieval tool name (index.ts `name:`) |
|-------------------------------|--------------------------------------------------|
| `msr_sql` | `msr_sql` |
| `temporal` | `temporal` |
| `kp_query` | `kp_query` |
| `query_kp_ruling_planets` | `query_kp_ruling_planets` |
| `pattern_register` | `pattern_register` |
| `resonance_register` | `resonance_register` |
| `cluster_atlas` | `cluster_atlas` |
| `contradiction_register` | `contradiction_register` |
| `query_ucn_walk` | `query_ucn_walk` |
| `query_cdlm_lookup` | `query_cdlm_lookup` |
| `query_rm_walk` | `query_rm_walk` |
| `query_jaimini_drishti` | `query_jaimini_drishti` |
| `timeline_query` | `timeline_query` |
| `query_signal_state` | `query_signal_state` |

**IMPORTANT**: Before adding, grep `platform/src/lib/retrieve/index.ts` for each tool name
to confirm the exact `name:` string used in the RETRIEVAL_TOOLS array. Use that exact string
as the value in `MCP_TO_RETRIEVAL_TOOL`. If any name does not exist, log it and skip it
(do not add tools that have no platform counterpart).

**Change to make**:

In `SURGICAL_TOOLS as const` array, append the 14 names (confirm each exists in index.ts first).

In `MCP_TO_RETRIEVAL_TOOL`, append the 14 key-value pairs.

**Verification**:
```typescript
// Quick smoke — paste this into a test or REPL:
import { isAllowedSurgicalTool } from './primitives_registry'
console.assert(isAllowedSurgicalTool('msr_sql'))
console.assert(isAllowedSurgicalTool('temporal'))
console.assert(isAllowedSurgicalTool('kp_query'))
console.assert(isAllowedSurgicalTool('query_kp_ruling_planets'))
console.assert(isAllowedSurgicalTool('pattern_register'))
console.assert(isAllowedSurgicalTool('resonance_register'))
console.assert(isAllowedSurgicalTool('cluster_atlas'))
console.assert(isAllowedSurgicalTool('contradiction_register'))
console.assert(isAllowedSurgicalTool('query_ucn_walk'))
console.assert(isAllowedSurgicalTool('query_cdlm_lookup'))
console.assert(isAllowedSurgicalTool('query_rm_walk'))
console.assert(isAllowedSurgicalTool('query_jaimini_drishti'))
console.assert(isAllowedSurgicalTool('timeline_query'))
console.assert(isAllowedSurgicalTool('query_signal_state'))
// Existing tools must still pass:
console.assert(isAllowedSurgicalTool('query_chart_facts'))
console.assert(isAllowedSurgicalTool('jaimini_chara_dasha_full'))
// Random string must still fail:
console.assert(!isAllowedSurgicalTool('nonexistent_tool'))
```

---

## Fix 2 — FIX-2: Fix forward_looking filter in msr_sql.ts

**File**: `platform/src/lib/retrieve/msr_sql.ts`

**Root cause**: The primitive dispatcher builds a `QueryPlan` with `forward_looking: false`
hardcoded. `msr_sql.ts` reads `plan.forward_looking` to build the SQL filter. When an MCP
caller sends `forward_looking: true`, it arrives in `params` but the SQL filter reads `plan`
and always sees `false`.

**Current code** (around line 153):
```typescript
const forwardLookingFilter: boolean | null = plan.forward_looking ? true : null
```

**Fix**: Read from `params` first, fall back to `plan`:
```typescript
const rawForwardLooking = (params as Record<string, unknown>)?.forward_looking
const forwardLookingFilter: boolean | null =
  rawForwardLooking === true ? true :
  rawForwardLooking === false ? null :
  plan.forward_looking ? true : null
```

**Logic explanation**:
- If `params.forward_looking === true`: filter to forward-looking signals only (`= true`).
- If `params.forward_looking === false`: no filter (return all, same as `null`). This matches
  the intent of "I don't care about forward_looking direction".
- If `params.forward_looking` is absent: fall back to `plan.forward_looking` (preserves
  existing behaviour for non-primitive callers).

**Why `null` for false**: The SQL is `AND ($4::boolean IS NULL OR is_forward_looking = $4)`.
When we want all signals (no filter), we must pass `null`, not `false`. Passing `false` would
return only historical signals, which is wrong for a general query.

**Verify**: After the change, a call with `params: { forward_looking: true }` must produce
SQL where `$4 = true`, and a call with no `params.forward_looking` must produce `$4 = null`.
Add a unit test for both cases (see SRP-T-1 brief for test suite; add at minimum a smoke
assertion here).

---

## Fix 3 — FIX-6: Update lel_query source_version annotation

**File**: `platform-mcp/src/tools/lel_query.ts`

**Root cause**: The tool returns `source_version: "1.6"` but the canonical LEL is v1.7
(path `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`, version 1.7 per CANONICAL_ARTIFACTS).

**Find the line**: `grep -n "source_version" platform-mcp/src/tools/lel_query.ts`

**Change**: Update `"1.6"` → `"1.7"` in the response object.

This is a cosmetic fix but important for audit trail accuracy — the version annotation
is the only indicator to MCP callers of which LEL they're querying against.

---

## Fix 4 — FIX-7: Fix params_json logging in msr_sql.ts

**File**: `platform/src/lib/retrieve/msr_sql.ts`

**Root cause**: The `params_json` field in the structured log (around line 104) logs:
```typescript
params_json: { domains: plan.domains, planets: plan.planets ?? [], forward_looking: plan.forward_looking }
```
This logs `plan.*` values, not the actual filter values computed from `params.*`. After FIX-2
is applied, `plan.forward_looking` will still be the logged value, even though the SQL now
uses the params-derived value. This makes the log actively misleading for debugging.

**Fix**: After applying FIX-2, update the `params_json` log entry to log the actual
filter values that will be used in the SQL:

```typescript
params_json: {
  domains: effectiveDomains,          // already computed above from params.domain
  planets: effectivePlanets,          // compute similarly if not already
  forward_looking: forwardLookingFilter,  // the value actually sent to SQL
  valence: valenceArr.length > 0 ? valenceArr : null,  // actual valence filter
}
```

Read the surrounding code carefully to use the correct variable names — `effectiveDomains`
may be named differently. The goal is: logged values = SQL-parameter values, always.

---

## Acceptance Criteria

- [ ] All 14 UDA tools return `isAllowedSurgicalTool() === true`.
- [ ] `forward_looking: true` in MCP params produces `is_forward_looking = true` SQL filter
      (verify via unit test or query trace log).
- [ ] `lel_query` tool reports `source_version: "1.7"`.
- [ ] `params_json` log reflects actual SQL filter values, not plan values.
- [ ] `npx vitest run` inside `platform/` shows 0 failures, 0 regressions.
- [ ] PR opened against `main` from `fix/srp-f1-portal-fixes`.
- [ ] PR description lists the 4 fixes with before/after code snippets.

## Session Close

Commit message format:
```
fix(srp-f1): portal fixes — primitives_registry 14 tools, forward_looking param, lel_query version, params_json log

FIX-1: primitives_registry.ts — add 14 UDA tools to SURGICAL_TOOLS + MCP_TO_RETRIEVAL_TOOL
FIX-2: msr_sql.ts — read forward_looking from params, not plan
FIX-6: lel_query.ts — source_version 1.6 → 1.7
FIX-7: msr_sql.ts — params_json log now reflects actual SQL filter values
```

After commit, open PR and **stop** — do not merge. Human gates the merge and `amjis-web` deploy.
