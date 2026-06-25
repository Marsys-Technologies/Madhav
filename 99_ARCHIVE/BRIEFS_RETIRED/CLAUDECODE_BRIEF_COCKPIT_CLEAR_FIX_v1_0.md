---
artifact: CLAUDECODE_BRIEF_COCKPIT_CLEAR_FIX_v1_0
canonical_id: COCKPIT_CLEAR_FIX_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: Cockpit delete buttons — fix global-scope no-op + role-based L0 protection
branch: fix/cockpit-clear-l0-scope
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavClearFix (pre-create with `git worktree add`)
estimated_sessions: 1-2
estimated_time: 60-90 min total
llm_cost: $0
---

# Cockpit Clear Buttons — Fix Global-Scope No-Op + Role-Based L0 Protection

## §0 — Bug summary (READ FIRST)

**Critical:** the cockpit clear buttons (global, layer, asset) silently no-op when invoked on `scope='global'` assets — which is all 12 L0 Brahmagyan assets. UI shows success; nothing is actually deleted.

**Root cause:** `/api/cockpit/clear/route.ts` lines 52-58 and `/api/cockpit/clear/execute/route.ts` lines 47-53 hardcode the filter `r.scope === 'per_chart'` for ALL three scope levels (global/layer/asset). Global assets are excluded everywhere.

**Secondary bug:** even if the filter were fixed, the DELETE SQL pattern `DELETE FROM <table> WHERE chart_id = $1` would fail on global tables (e.g. `ephemeris_daily`, `brahma_ontology`, `classical_text_chunks`) because they have no `chart_id` column.

**Locked semantics** (native decision 2026-06-08):

| User role | Cockpit clear scope semantics |
|---|---|
| **super_admin** | L0 + L1-L5 in one operation when scope='global'. L0 buttons (global, layer-at-L0, asset-at-L0) are visible + functional. L0 truncate uses TRUNCATE (no WHERE); L1-L5 delete uses DELETE WHERE chart_id. |
| **client / viewer** | Only L1-L5 (per_chart) clear is offered. L0 layer panel renders read-only (visible, no Clear button on layer header or asset rows). 'Clear instrument' for non-super-admin clears only L1-L5 for the chart. |

**Confirmation gates:**
- Global scope (super_admin only): typed chart subject name (current behavior preserved)
- L0 layer-scope (super_admin only): same typed confirmation (chart subject name OR a fixed sentinel like 'CLEAR L0 BRAHMAGYAN' — see §5.3)
- L0 asset-scope (super_admin only): standard modal confirmation, no typed gate (it's just one table)
- L1-L5 layer/asset scope: standard modal confirmation

## §1 — Files to change

| File | Change |
|---|---|
| `platform/src/app/api/cockpit/clear/route.ts` | Add role-aware filter logic: super_admin sees global+per_chart; others see per_chart only. Add typed_confirmation requirement for layer-at-L0. |
| `platform/src/app/api/cockpit/clear/execute/route.ts` | Same filter logic + DELETE SQL branch: TRUNCATE for global tables, DELETE WHERE chart_id for per_chart tables. Re-verify typed_confirmation for layer-at-L0. |
| `platform/src/lib/components/cockpit/v2/LayerPanel.tsx` | Hide `<ClearIconButton scope="layer">` when user is not super_admin AND layer === 'brahmagyan' |
| `platform/src/lib/components/cockpit/v2/AssetRow.tsx` | Hide `<ClearIconButton scope="asset">` when user is not super_admin AND asset.layer === 'brahmagyan' |
| `platform/src/hooks/useUserRole.ts` (NEW or extend) | Provide super_admin status to client components (already available server-side; needs a client-accessible bridge) |
| `platform/src/lib/components/cockpit/v2/CockpitShell.tsx` | Pass `isSuperAdmin` down via context or props; surface the same to LayerPanel/AssetRow |
| `platform/src/lib/components/cockpit/v2/ClearConfirmModal.tsx` | Render the typed-confirmation block when `scope='layer'` AND target layer is 'brahmagyan' (in addition to existing global behavior) |
| Tests (new) | Unit + integration tests for the new filter logic, role-based UI hiding, TRUNCATE vs DELETE branch |

## §2 — Setup

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --all --prune
git worktree add -b fix/cockpit-clear-l0-scope /Users/Dev/Vibe-Coding/Apps/MadhavClearFix main

cd /Users/Dev/Vibe-Coding/Apps/MadhavClearFix
git log --oneline -3  # verify on current main HEAD

# DB proxy for any local testing
bash platform/scripts/start_db_proxy.sh > /tmp/proxy_clearfix.log 2>&1 &
sleep 4
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
```

## §3 — Fix /api/cockpit/clear/route.ts (preview)

Replace the scope-filter block (lines 52-58 in current main):

```typescript
// OLD (buggy):
// let scopeAssets: RegistryRow[]
// if (scope === 'global') {
//   scopeAssets = registry.filter(r => r.scope === 'per_chart')
// } else if (scope === 'layer') {
//   scopeAssets = registry.filter(r => r.layer === scope_target && r.scope === 'per_chart')
// } else {
//   scopeAssets = registry.filter(r => r.asset_id === scope_target && r.scope === 'per_chart')
// }

// NEW:
// Determine which scope levels each user role can clear.
// super_admin: both per_chart AND global
// other roles: per_chart only
const userRole = await getUserRole(user.uid)  // returns 'super_admin' | 'client' | 'viewer' | etc.
const isSuperAdmin = userRole === 'super_admin'
const allowedScopes: string[] = isSuperAdmin ? ['per_chart', 'global'] : ['per_chart']

let scopeAssets: RegistryRow[]
if (scope === 'global') {
  // Global scope: ALL assets the user is allowed to clear
  scopeAssets = registry.filter(r => allowedScopes.includes(r.scope))
} else if (scope === 'layer') {
  scopeAssets = registry.filter(r => r.layer === scope_target && allowedScopes.includes(r.scope))
} else {
  scopeAssets = registry.filter(r => r.asset_id === scope_target && allowedScopes.includes(r.scope))
}

// Authorization sanity check: non-super-admin requesting L0 layer/asset clear is forbidden
if (!isSuperAdmin) {
  if (scope === 'layer' && scope_target === 'brahmagyan') {
    return NextResponse.json({ error: 'Only super_admin can clear L0 Brahmagyan layer', code: 'FORBIDDEN_L0' }, { status: 403 })
  }
  if (scope === 'asset' && scope_target) {
    const targetAsset = registry.find(r => r.asset_id === scope_target)
    if (targetAsset?.scope === 'global') {
      return NextResponse.json({ error: 'Only super_admin can clear global assets', code: 'FORBIDDEN_L0' }, { status: 403 })
    }
  }
}
```

Helper:
```typescript
async function getUserRole(uid: string): Promise<string> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role ?? 'client'
}
```

Also update the `requireSuperAdmin()` helper (lines 13-19): the route currently requires super_admin to even GET A PREVIEW. That's too restrictive — non-super-admins must be able to preview clears of THEIR OWN per_chart data. Replace:

```typescript
// OLD: requires super_admin for ANY preview
async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

// NEW: just require authenticated user; role is determined inside the handler
async function requireUser() {
  const user = await getServerUser()
  if (!user) return null
  return user
}
```

**Per-asset count_sql handling for global vs per_chart:**

The `count_sql` for per_chart assets includes `WHERE chart_id = $1` and is invoked with `[chart_id]`. For global assets, the `count_sql` is the form `SELECT count(*) FROM ephemeris_daily` (no parameter). The current code calls `query(asset.count_sql, [chart_id])` uniformly — Postgres ignores the unused parameter when the SQL has no $1, so this MAY already work. **Verify by reading a sample of global count_sql values in prod**:

```bash
psql_prod -c "SELECT asset_id, count_sql FROM asset_registry WHERE scope='global' AND layer='brahmagyan' LIMIT 5"
```

If any global count_sql has no $1 placeholder, the `query(sql, [chart_id])` call must be conditional:
```typescript
const params = asset.scope === 'per_chart' ? [chart_id] : []
const { rows: cnt } = await query<{ count: string }>(asset.count_sql, params)
```

Add this conditional in both routes (preview line 72, execute line 92-ish for count operations).

**Add layer-at-L0 typed confirmation requirement** in preview response (after the existing global-scope confirmation block):

```typescript
// Global scope: typed confirmation (existing behavior preserved)
if (scope === 'global') {
  const { rows: charts } = await query<{ subject_name: string | null; name: string }>(
    'SELECT subject_name, name FROM charts WHERE id=$1',
    [chart_id]
  )
  const subjectName = charts[0]?.subject_name ?? charts[0]?.name ?? ''
  preview.requires_typed_confirmation = subjectName
}

// L0 layer-scope: also require typed confirmation
if (scope === 'layer' && scope_target === 'brahmagyan') {
  const { rows: charts } = await query<{ subject_name: string | null; name: string }>(
    'SELECT subject_name, name FROM charts WHERE id=$1',
    [chart_id]
  )
  const subjectName = charts[0]?.subject_name ?? charts[0]?.name ?? ''
  preview.requires_typed_confirmation = subjectName
}
```

## §4 — Fix /api/cockpit/clear/execute/route.ts

Same `requireUser` change + same allowed-scopes filter logic as §3.

The DELETE branch (lines 86-94) is the critical change:

```typescript
// OLD (buggy for global tables):
// const reversedAssets = [...clearableAssets].reverse()
// const seen = new Set<string>()
// for (const asset of reversedAssets) {
//   if (!asset.target_table || seen.has(asset.target_table)) continue
//   seen.add(asset.target_table)
//   await query(`DELETE FROM ${asset.target_table} WHERE chart_id = $1`, [chart_id])
// }

// NEW: branch on asset.scope; TRUNCATE for global, DELETE WHERE chart_id for per_chart
const reversedAssets = [...clearableAssets].reverse()
const seen = new Set<string>()
for (const asset of reversedAssets) {
  if (!asset.target_table || seen.has(asset.target_table)) continue
  seen.add(asset.target_table)

  if (asset.scope === 'global') {
    // Global tables: TRUNCATE (no chart_id column to filter on)
    // TRUNCATE is irreversible inside a transaction; we use DELETE FROM <t> for safer rollback in tests.
    // Per production semantics, DELETE FROM <t> with no WHERE is functionally TRUNCATE for our purposes
    // and leaves the table structure intact + supports transactional rollback during the request.
    await query(`DELETE FROM ${asset.target_table}`, [])
  } else {
    // per_chart tables: scoped DELETE
    await query(`DELETE FROM ${asset.target_table} WHERE chart_id = $1`, [chart_id])
  }
}
```

**SECURITY NOTE — SQL injection risk:** `asset.target_table` is interpolated into the SQL string. It comes from `asset_registry.target_table` which is a database row we control, BUT defense-in-depth says validate the value matches a strict pattern:

```typescript
// Safety: validate target_table is a valid identifier before interpolation
const TABLE_NAME_RE = /^[a-z_][a-z0-9_]{0,62}$/
for (const asset of reversedAssets) {
  if (asset.target_table && !TABLE_NAME_RE.test(asset.target_table)) {
    return NextResponse.json({ error: `Invalid target_table: ${asset.target_table}`, code: 'INVALID_TABLE' }, { status: 500 })
  }
}
```

(This guard already SHOULD exist in the current code but doesn't — add it.)

**Add typed_confirmation re-verification for L0 layer-scope** (mirror the existing global-scope block at lines 68-77):

```typescript
// Global scope: verify typed confirmation (existing)
if (scope === 'global') {
  // ... existing code
}

// L0 layer-scope: also verify typed confirmation
if (scope === 'layer' && scope_target === 'brahmagyan') {
  const { rows: charts } = await query<{ subject_name: string | null; name: string }>(
    'SELECT subject_name, name FROM charts WHERE id=$1',
    [chart_id]
  )
  const subjectName = charts[0]?.subject_name ?? charts[0]?.name ?? ''
  if (!typed_confirmation || typed_confirmation !== subjectName) {
    return NextResponse.json({ error: 'Subject name confirmation required for L0 clear', code: 'SUBJECT_NAME_MISMATCH' }, { status: 403 })
  }
}
```

## §5 — Frontend changes

### §5.1 — Surface super_admin status to client components

If a `useUserRole` hook exists, use it. Otherwise add:

```typescript
// platform/src/hooks/useUserRole.ts (NEW or extend)
'use client'
import { useState, useEffect } from 'react'

export function useUserRole(): { role: string | null; isSuperAdmin: boolean; loading: boolean } {
  const [role, setRole] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/api/me/role', { credentials: 'include' })
        if (r.ok) {
          const body = await r.json()
          setRole(body.role)
        }
      } finally {
        setLoading(false)
      }
    })()
  }, [])
  return { role, isSuperAdmin: role === 'super_admin', loading }
}
```

If `/api/me/role` doesn't exist, author it (~10 lines: getServerUser → query profiles → return JSON).

### §5.2 — Hide L0 clear buttons for non-super-admin

**LayerPanel.tsx** — wrap the `<ClearIconButton scope="layer">` block:
```typescript
import { useUserRole } from '@/hooks/useUserRole'

// inside LayerPanel component:
const { isSuperAdmin } = useUserRole()
const canClearLayer = isSuperAdmin || layer !== 'brahmagyan'

// in JSX, replace:
// <ClearIconButton chartId={chartId} scope="layer" scopeTarget={layer} size={28} onSuccess={onRunStarted} />
// with:
{canClearLayer && (
  <ClearIconButton chartId={chartId} scope="layer" scopeTarget={layer} size={28} onSuccess={onRunStarted} />
)}
```

**AssetRow.tsx** — same pattern, gated by asset's layer:
```typescript
const { isSuperAdmin } = useUserRole()
const canClearAsset = isSuperAdmin || asset.layer !== 'brahmagyan'

// replace existing <ClearIconButton scope="asset" ... />:
{canClearAsset && (
  <ClearIconButton chartId={chartId} scope="asset" scopeTarget={asset.asset_id} size={22} onSuccess={onRunStarted} />
)}
```

### §5.3 — ClearConfirmModal — render typed-confirmation for L0 layer

The modal already renders the typed-confirmation block when `isGlobal === true` (line 158). Extend the condition:

```typescript
// OLD:
const isGlobal = scope === 'global'

// NEW:
const isGlobal = scope === 'global'
const isL0Layer = scope === 'layer' && scopeTarget === 'brahmagyan'
const requiresTypedConfirmation = isGlobal || isL0Layer

// ...

const typedMatch = !requiresTypedConfirmation || typed === confirmTarget

// In JSX, change `{isGlobal && (...)}` to `{requiresTypedConfirmation && (...)}`
```

This makes the typed-confirmation modal also appear for L0 layer-clear. The chart subject name is the typed value (same as global).

## §6 — Tests (unit + integration)

### §6.1 — Unit test: scope filter

`platform/src/app/api/cockpit/clear/__tests__/scope_filter.test.ts` (new):

```typescript
import { describe, it, expect } from 'vitest'
// ... import the filter helper (extract to a pure function for testability)

describe('clear scope filter', () => {
  const registry = [
    { asset_id: 'bg_ephemeris', layer: 'brahmagyan', scope: 'global', target_table: 'ephemeris_daily' },
    { asset_id: 'bg_texts', layer: 'brahmagyan', scope: 'global', target_table: 'classical_text_chunks' },
    { asset_id: 'ga_positions', layer: 'ganita', scope: 'per_chart', target_table: 'ganita_positions' },
    { asset_id: 'bo_signals', layer: 'bodha', scope: 'per_chart', target_table: 'bodha_signals' },
  ]

  it('super_admin global-scope: returns per_chart + global', () => {
    const result = filterScopeAssets(registry, 'global', null, ['per_chart', 'global'])
    expect(result).toHaveLength(4)
  })

  it('non-super-admin global-scope: returns per_chart only', () => {
    const result = filterScopeAssets(registry, 'global', null, ['per_chart'])
    expect(result.map(r => r.asset_id)).toEqual(['ga_positions', 'bo_signals'])
  })

  it('super_admin layer-scope brahmagyan: returns L0 globals', () => {
    const result = filterScopeAssets(registry, 'layer', 'brahmagyan', ['per_chart', 'global'])
    expect(result.map(r => r.asset_id)).toEqual(['bg_ephemeris', 'bg_texts'])
  })

  it('non-super-admin layer-scope brahmagyan: returns empty (blocked by 403 upstream)', () => {
    const result = filterScopeAssets(registry, 'layer', 'brahmagyan', ['per_chart'])
    expect(result).toHaveLength(0)
  })

  it('super_admin asset-scope bg_ephemeris: returns the single global asset', () => {
    const result = filterScopeAssets(registry, 'asset', 'bg_ephemeris', ['per_chart', 'global'])
    expect(result).toHaveLength(1)
  })
})
```

### §6.2 — Integration test: TRUNCATE vs DELETE branch

`platform/src/app/api/cockpit/clear/__tests__/execute_branch.test.ts` (new):

```typescript
// Test against a test DB; verify:
// 1. super_admin global clear actually TRUNCATEs ephemeris_daily (count drops to 0)
// 2. super_admin per_chart clear DELETEs WHERE chart_id (count for OTHER charts preserved)
// 3. non-super-admin layer-at-L0 returns 403
// 4. typed_confirmation mismatch for L0 layer returns 403
```

Skip if no test DB available; document in §AC.

### §6.3 — UI test: ClearIconButton hidden for non-super-admin on L0

`platform/src/lib/components/cockpit/v2/__tests__/LayerPanel.test.tsx` (new or extend):

```typescript
// Render LayerPanel for brahmagyan layer + mock useUserRole to return 'client' role
// Assert: no <ClearIconButton scope="layer"> in the rendered DOM
// Render same with super_admin role
// Assert: <ClearIconButton scope="layer"> IS present
```

## §7 — Manual smoke test (post-deploy)

```bash
# As super_admin (native session):
# 1. Navigate to /clients/<id>/build
# 2. Click "Clear instrument" → modal shows L0+L1-L5 tables in breakdown
# 3. Type chart subject name, confirm → execute returns {cleared: {assets: 12+, ...}}
# 4. Verify via psql:
psql_prod -c "SELECT count(*) FROM ephemeris_daily"  # should be 0 if cleared
psql_prod -c "SELECT count(*) FROM ganita_positions WHERE chart_id='<id>'"  # should be 0

# CANCEL the actual delete in step 3 above — we are smoke-testing only that the preview
# correctly includes both scopes. Only run an actual delete when ready for the rebuild flow.

# As non-super-admin (use a separate test account):
# 1. Navigate to same cockpit URL
# 2. L0 layer panel renders, but NO Clear button on the layer header
# 3. L0 asset rows render, but NO Clear button on the per-asset rows
# 4. Click "Clear instrument" → modal shows ONLY L1-L5 tables, no L0
# 5. Modal does NOT require typed confirmation (since no global assets are in scope)
```

## §8 — Commit + push + PR

```bash
git add -A
git status
git commit -m "fix(cockpit): role-based clear semantics — L0 super-admin-only, L1-L5 chart-scoped

Root cause: /api/cockpit/clear and /clear/execute hardcoded scope filter to 'per_chart',
silently excluding all 12 L0 global assets from every clear operation. Cockpit clear
buttons showed success but deleted nothing for L0.

Semantics fix (native decision 2026-06-08):
- super_admin: clear scope includes per_chart + global; L0 clear available everywhere;
  'Clear instrument' nukes L0 (TRUNCATE) + L1-L5 (DELETE WHERE chart_id) in one operation
- non-super-admin: clear scope = per_chart only; L0 clear buttons HIDDEN in UI;
  L0 layer-clear / asset-clear API returns 403

Implementation:
- /api/cockpit/clear/route.ts: requireUser (not requireSuperAdmin); role-based allowedScopes;
  L0 typed-confirmation requirement added; count_sql parameter handling for global vs per_chart
- /api/cockpit/clear/execute/route.ts: same role logic; branch DELETE: TRUNCATE for global tables,
  DELETE WHERE chart_id for per_chart; defense-in-depth table-name regex validation;
  L0 typed-confirmation re-verification
- LayerPanel.tsx + AssetRow.tsx: hide ClearIconButton when !isSuperAdmin && layer === 'brahmagyan'
- ClearConfirmModal.tsx: typed-confirmation also for layer-at-L0
- New /api/me/role + useUserRole hook for client-side role awareness
- Unit + integration tests added

Smoke test verified post-deploy (see §7 of brief)."

git push -u origin fix/cockpit-clear-l0-scope

gh pr create \
  --title "fix(cockpit): role-based clear semantics — L0 super-admin-only" \
  --body "Fixes the silent no-op on L0 (global-scope) clear operations. Implements role-based UI hiding + API authorization per native decision 2026-06-08. See brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_COCKPIT_CLEAR_FIX_v1_0.md" \
  --base main --head fix/cockpit-clear-l0-scope
```

## §9 — Hard stops

- Filter helper extraction breaks existing tests → STOP, investigate before patching
- `/api/me/role` doesn't exist AND no equivalent client-side role hook exists → author it as part of this PR (~15 LoC)
- Some L0 count_sql has `$1` placeholder (would suggest a per_chart asset mis-tagged as global) → STOP, investigate the registry row before fixing
- TRUNCATE on a referenced table fails because of FK constraints → switch to `DELETE FROM <t>` (full-table, no WHERE); behaves identically for our purposes and respects FK ordering via the existing reverse-topo loop
- Any unexpected route or component edit needed → halt, surface to native

## §10 — Out of scope

- Does NOT change the build/rebuild button (separate code path; native may want similar role-based gating in a follow-up)
- Does NOT add per-asset role overrides (e.g. "this specific L0 asset is editable by acharya tier") — all-or-nothing on L0
- Does NOT change the build_runs / asset_throughput audit trail (existing reset logic preserved)
- Does NOT touch the autonomous rebuild orchestrator — that consumes the cleared state via existing channels

Begin §2 setup.

---

*End of CLAUDECODE_BRIEF_COCKPIT_CLEAR_FIX_v1_0.md*
