---
artifact: CLAUDECODE_BRIEF_COCKPIT_POLISH_ROUND_v1_0
canonical_id: COCKPIT_POLISH_ROUND_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: Cockpit polish round — 11 issues bundle (delete-bugs + UX features + perf)
branch: fix/cockpit-polish-round
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavCockpitPolish (pre-create with `git worktree add`)
estimated_sessions: 2-3
estimated_time: 3-4 hours total
llm_cost: $0
---

# Cockpit Polish Round — 11-Issue Comprehensive Fix

> **Scope:** all 11 cockpit issues surfaced 2026-06-08, in one PR. Mix of critical bug fixes (execute crash; count_sql drift) + UX features (refresh buttons; layer-grouped modal; chart_id display) + perf fixes (loading-state delay; sequential fetches). Tightly scoped per issue.

## §0 — Issue table + priority

| # | Issue | Type | Owner section |
|---|---|---|---|
| 1 | Clear modal: `Failed to execute 'json' on 'Response': Unexpected end of JSON input` | CRITICAL BUG | §1 |
| 2 | bg_reference clear fails (returns only 1 table, 61 rows instead of 15-table sum) | CRITICAL BUG | §2 |
| 3 | Global modal: "5 tables + 32 more" → want per-layer summary (layer name + total rows) | UX FEATURE | §3 |
| 4 | "Loading chart…" delay when entering cockpit | PERF | §4 |
| 5 | Action buttons appear sequentially with ~2s gap | PERF | §4 (same root cause) |
| 6 | Refresh button needed at global/layer/asset levels (mirroring delete button) | UX FEATURE | §5 |
| 7 | last_built_at column not populated + display format broken | BUG + UX | §6 |
| 8 | Progress bar takes too long to update | PERF | §4 (same root cause) |
| 9 | Chart ID truncated to 8 chars then `…` — wants more (or full) | UX | §7 |
| 10 | (same as #3) | — | — |
| 11 | (same as #4) | — | — |

## §0.5 — Pre-read

1. `00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md` (v1.1)
2. `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_COCKPIT_CLEAR_FIX_v1_0.md` (the predecessor brief — its semantics are now in main but with bugs that this brief fixes)
3. Memory: `[[cockpit-clear-fix-shipped]]`, `[[cockpit-v1-v2-split]]`

## §1 — CRITICAL: fix execute route 500 → JSON crash

**Root cause:** `/api/cockpit/clear/execute/route.ts` lines 117-128 run DELETE statements OUTSIDE any try/catch. When any DELETE fails (FK constraint, missing column on a global table, etc.), the route throws → Next.js returns 500 with HTML body → modal's `await r.json()` crashes with "Unexpected end of JSON input."

### §1.1 — Wrap DELETEs + asset_throughput updates in transaction + try/catch

Edit `platform/src/app/api/cockpit/clear/execute/route.ts` lines 113-151:

```typescript
// REPLACE: bare DELETEs + bare UPDATEs (lines 113-151)
// WITH: transaction-wrapped block, with explicit error handling that ALWAYS returns JSON

import { getClient } from '@/lib/db/client'  // assuming a getClient() exists alongside query(); else implement

let cleared_asset_count = 0
let cleared_table_count = 0
let cleared_rows_total = 0
const failed_tables: { table: string; error: string }[] = []

try {
  const client = await getClient()
  try {
    await client.query('BEGIN')

    // Delete data in reverse topo order
    const seen = new Set<string>()
    for (const asset of reversedAssets) {
      if (!asset.target_table || seen.has(asset.target_table)) continue
      seen.add(asset.target_table)

      try {
        const sql = asset.scope === 'global'
          ? `DELETE FROM ${asset.target_table}`
          : `DELETE FROM ${asset.target_table} WHERE chart_id = $1`
        const params = asset.scope === 'global' ? [] : [chart_id]
        const result = await client.query(sql, params)
        cleared_table_count++
        cleared_rows_total += result.rowCount ?? 0
      } catch (err) {
        // Per-table failure: log + collect, don't abort the whole transaction
        // (we may still want to clear other tables; native sees the report)
        failed_tables.push({
          table: asset.target_table,
          error: (err as Error).message?.substring(0, 200) ?? 'unknown',
        })
      }
    }

    // Reset asset_throughput
    if (affectedAssetIds.length > 0) {
      await client.query(
        `UPDATE asset_throughput
         SET state='dormant', last_built_at=NULL,
             built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
             last_error=NULL
         WHERE chart_id=$1 AND asset_id = ANY($2::text[])`,
        [chart_id, affectedAssetIds]
      )
      cleared_asset_count = affectedAssetIds.length
    }

    // Mark downstream stale
    if (downstreamAssets.length > 0) {
      await client.query(
        `UPDATE asset_throughput
         SET state='stale'
         WHERE chart_id=$1 AND asset_id = ANY($2::text[])
           AND state IN ('lit','building','error')`,
        [chart_id, downstreamAssets]
      )
    }

    await client.query('COMMIT')
  } catch (innerErr) {
    await client.query('ROLLBACK').catch(() => null)
    throw innerErr
  } finally {
    client.release?.()
  }
} catch (outerErr) {
  console.error('[/api/cockpit/clear/execute] transaction failed:', outerErr)
  return NextResponse.json({
    error: 'Clear transaction failed; rolled back. ' + ((outerErr as Error).message?.substring(0, 200) ?? 'unknown'),
    code: 'TRANSACTION_FAILED',
    details: { failed_tables },
  }, { status: 500 })
}

return NextResponse.json({
  cleared: {
    assets: cleared_asset_count,
    tables: cleared_table_count,
    rows: cleared_rows_total,
    downstream_stale: downstreamAssets.length,
  },
  failed_tables: failed_tables.length > 0 ? failed_tables : undefined,
})
```

**Hard AC:** the response is ALWAYS valid JSON regardless of which DELETE failed. If a table fails, it's collected into `failed_tables` array; other tables still proceed. Whole transaction commits OR rolls back atomically.

### §1.2 — Mirror the same try/catch wrapping in the preview route

`/api/cockpit/clear/route.ts` — wrap the count loop (lines 64-77) so a failing count_sql doesn't 500 the whole preview:

```typescript
for (const asset of clearableAssets) {
  if (!asset.target_table || !asset.count_sql || seen.has(asset.target_table)) continue
  seen.add(asset.target_table)
  try {
    const params = asset.scope === 'per_chart' ? [chart_id] : []
    const { rows: cnt } = await query<{ count: string }>(asset.count_sql, params)
    tableCounts.push({ table: asset.target_table, rows: parseInt(cnt[0]?.count ?? '0', 10) })
  } catch (err) {
    // Asset's count_sql is broken; report 0 rows + log
    console.warn(`[clear/preview] count_sql failed for ${asset.asset_id}:`, (err as Error).message)
    tableCounts.push({ table: asset.target_table, rows: 0, error: (err as Error).message?.substring(0, 100) })
  }
}
```

(Note: `tableCounts` type needs `error?: string` added — adjust the interface.)

### §1.3 — Modal: handle non-200 response gracefully

`ClearConfirmModal.tsx` `handleConfirm` — instead of `await r.json()` directly, defensively parse:

```typescript
const txt = await r.text()
let body: any
try {
  body = JSON.parse(txt)
} catch {
  // Server returned non-JSON; surface the raw text
  throw new Error(`Server error (${r.status}): ${txt.substring(0, 200) || 'no response body'}`)
}
if (!r.ok) throw new Error(body?.error ?? `Clear failed (${r.status})`)
// continue with body.cleared etc.
```

Same fix at `ClearIconButton.tsx`'s preview fetch and `CockpitShell.tsx`'s `openGlobalClearModal`.

**§1 hard AC:** open the clear modal for bg_reference (or any L0 asset). Click "Clear data". If success: modal closes. If server error: a `toast.error` shows the actual error message (NOT "Unexpected end of JSON input").

## §2 — CRITICAL: bg_reference count_sql drift in prod

**Root cause:** prod's `asset_registry.count_sql` for `bg_reference` is `SELECT count(*) FROM reference_nakshatras` (61 rows) — the OLD value. Migration 179 was supposed to update it to the 15-table sum. Either: (a) migration 179 didn't apply for bg_reference; (b) `asset_registry_seed.ts` re-ran and overwrote with the old value (the seed file was supposed to be updated to match, but maybe wasn't); (c) two writers compete on every deploy.

### §2.1 — Investigate which one is the truth

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavCockpitPolish
bash platform/scripts/start_db_proxy.sh > /tmp/proxy.log 2>&1 &
sleep 4
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }

# Confirm current prod count_sql for bg_reference
psql_prod -c "SELECT asset_id, count_sql FROM asset_registry WHERE asset_id='bg_reference'"

# Read what migration 179 set it to
cat platform/supabase/migrations/179_l0_phase_alpha_asset_registry.sql | grep -A 3 "bg_reference"

# Read what asset_registry_seed.ts sets it to
grep -A 12 "asset_id: 'bg_reference'" platform/scripts/seed/asset_registry_seed.ts
```

**CHECKPOINT 2.1:** prod count_sql shows `reference_nakshatras` only. Migration 179 SHOULD have set it to the 15-table sum. asset_registry_seed.ts — verify it matches the 15-table sum. If seed has the OLD value, that's the culprit — every seed re-run reverts migration 179.

### §2.2 — Fix root cause

Two-pronged fix:

1. **Make the seed correct** — update `asset_registry_seed.ts` so `bg_reference` entry uses the same 15-table count_sql migration 179 sets. The seed becomes the authoritative source on every deploy; migration files document the schema and act as a one-time install.

2. **Re-apply migration 179 once to fix prod NOW** — instead of running a fresh migration, just UPDATE bg_reference's count_sql in place:

```bash
# Apply the count_sql fix immediately
psql_prod <<'SQL'
UPDATE asset_registry SET count_sql = $$
  SELECT (SELECT count(*) FROM reference_planets)
       + (SELECT count(*) FROM reference_nakshatras)
       + (SELECT count(*) FROM reference_signs)
       + (SELECT count(*) FROM reference_aspects)
       + (SELECT count(*) FROM reference_vargas)
       + (SELECT count(*) FROM reference_houses)
       + (SELECT count(*) FROM reference_strength_systems)
       + (SELECT count(*) FROM reference_karakas)
       + (SELECT count(*) FROM reference_upagrahas)
       + (SELECT count(*) FROM reference_constants)
       + (SELECT count(*) FROM reference_topic_tags)
       + (SELECT count(*) FROM reference_glossary)
       + (SELECT count(*) FROM reference_yogas)
       + (SELECT count(*) FROM reference_doshas)
       + (SELECT count(*) FROM reference_dasha_systems)
  AS count
$$,
target_table = 'reference_nakshatras'
WHERE asset_id = 'bg_reference';

-- Verify
SELECT asset_id, substring(count_sql, 1, 200) FROM asset_registry WHERE asset_id='bg_reference';
SQL
```

**Hard AC for §2:** `/api/cockpit/clear?scope=asset&scope_target=bg_reference` returns `tables: [{table: 'reference_nakshatras', rows: <sum-of-15>}], total_rows: <sum-of-15>`.

### §2.3 — Apply same audit to all 12 L0 asset count_sql values

Run the seed locally + dry-run against prod to find any other drift:

```bash
cd platform
DATABASE_URL=$PROD_DB_URL DRY_RUN=1 npx tsx scripts/seed/asset_registry_seed.ts 2>&1 | grep -i "update\|insert\|brahmagyan"
# Expect: 0 diffs after §2.2 lands; if non-zero, the seed disagrees with prod on more assets
cd ..
```

## §3 — UX: Global Clear modal — layer-grouped summary

**Current:** lists 5 individual tables, then "32 more tables". Hard to grasp scope.

**Wanted:** when scope='global', group tables by layer and show layer-name + total-rows-per-layer instead of individual tables.

### §3.1 — API: extend preview response with per-layer summary

`/api/cockpit/clear/route.ts` — after computing `tableCounts`, add a layer-grouped summary:

```typescript
// Build per-layer summary (only meaningful for global scope, but harmless for others)
const layerRowsMap = new Map<string, number>()
const layerAssetCountMap = new Map<string, number>()
for (const asset of scopeAssets) {
  // find the rows for this asset's table
  const tc = tableCounts.find(t => t.table === asset.target_table)
  const rows = tc?.rows ?? 0
  layerRowsMap.set(asset.layer, (layerRowsMap.get(asset.layer) ?? 0) + rows)
  layerAssetCountMap.set(asset.layer, (layerAssetCountMap.get(asset.layer) ?? 0) + 1)
}
const layer_summary = Array.from(layerRowsMap.entries()).map(([layer, rows]) => ({
  layer,
  rows,
  asset_count: layerAssetCountMap.get(layer) ?? 0,
}))

const preview: Record<string, unknown> = {
  tables: tableCounts,
  total_rows: totalRows,
  affected_assets: affectedAssetIds,
  downstream_stale_assets: downstreamAssets,
  preview_hash,
  layer_summary,  // NEW
}
```

### §3.2 — Modal: render layer-grouped summary for global scope

`ClearConfirmModal.tsx` — when `scope === 'global'` AND `preview.layer_summary` exists, render layer rows INSTEAD of the existing 5-table breakdown:

```typescript
const showLayerSummary = scope === 'global' && Array.isArray((preview as any).layer_summary)
const layerSummary = (preview as any).layer_summary as { layer: string; rows: number; asset_count: number }[] | undefined

// Replace the existing tables loop with conditional rendering:
{showLayerSummary && layerSummary ? (
  <div style={{ marginBottom: '12px' }}>
    {layerSummary.map(ls => {
      const labels: Record<string, string> = {
        brahmagyan: 'Brahma Jñāna (L0)',
        ganita: 'Gaṇita (L1)',
        bodha: 'Bodha (L2)',
        kala: 'Kāla (L3)',
        phala: 'Phala (L4)',
        mimamsa: 'Mīmāṃsā (L5)',
      }
      return (
        <div key={ls.layer} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '13px' }}>
          <span style={{ color: 'var(--on-dark-mut)' }}>{labels[ls.layer] ?? ls.layer} <span style={{ color: 'var(--on-dark-faint)', fontSize: '11px' }}>({ls.asset_count} assets)</span></span>
          <span style={{ color: 'var(--on-dark)', fontFamily: 'var(--mono-stack)' }}>{ls.rows.toLocaleString()} rows</span>
        </div>
      )
    })}
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0 4px', fontSize: '13px', fontWeight: 600 }}>
      <span style={{ color: 'var(--on-dark-mut)' }}>{preview.affected_assets.length} assets total</span>
      <span style={{ color: 'var(--on-dark)' }}>{preview.total_rows.toLocaleString()} rows</span>
    </div>
  </div>
) : (
  // existing per-table display for asset/layer scope
  <div style={{ marginBottom: '12px' }}>
    {/* ... existing code with visibleTables + remaining ... */}
  </div>
)}
```

## §4 — PERF: Loading-chart delay + sequential action buttons + slow progress bar

These three are likely one root cause: the cockpit makes multiple sequential fetch calls in mount-time effects, each waiting for the prior to complete.

### §4.1 — Audit current fetch pattern

```bash
grep -rn "useEffect\|useCallback" platform/src/lib/components/cockpit/v2/*.tsx | grep -E "fetch|api\/" | head -20
grep -rn "fetch.*api" platform/src/hooks/use*.ts platform/src/hooks/use*.tsx 2>/dev/null | head -20
```

**Hot suspects:**
- `useChartContext` (fetches `/api/charts/<id>`)
- `useAssetRegistry` (fetches `/api/cockpit/registry`)
- `useAssetStats` (fetches `/api/cockpit/stats?chart_id=<id>` — likely per-mount, possibly per-asset)
- `useActiveRun` (fetches `/api/cockpit/runs/active`)
- `useCockpitSSE` (opens SSE channel)
- `useUserRole` (fetches `/api/me/role`)

### §4.2 — Parallelize independent fetches

Each hook currently mounts independently. Run them in parallel by ensuring no hook waits for another. If `useAssetStats` waits for `useChartContext` to return chartName, that's a synchronous chain. Audit + remove the wait where possible.

### §4.3 — Server-side prefetch (optional, bigger change)

If the loading delay is dominated by initial chart fetch, consider prefetching `chartName + birthDate + birthPlace` in the SERVER component (`app/clients/[id]/build/page.tsx`) and passing as props to CockpitShell. The chart data is already loaded server-side for layout's `<title>` tag — reuse it.

```typescript
// In app/clients/[id]/build/page.tsx (server component):
import { query } from '@/lib/db/client'

const { rows: chartRows } = await query<{ subject_name: string; birth_date: string; birth_place: string }>(
  'SELECT subject_name, birth_date, birth_place FROM charts WHERE id=$1',
  [id]
)
const chartMeta = chartRows[0] ?? null

return <CockpitShell chartId={id} initialChartMeta={chartMeta} />
```

CockpitShell accepts `initialChartMeta` prop and seeds `useChartContext` with it, skipping the initial fetch.

**Skip §4.3 if §4.2 alone solves the perceived delay.** §4.3 is a bigger change.

### §4.4 — Action button stagger fix

If buttons appear sequentially with a 2-sec gap, likely cause: each AssetRow does its own `useAssetStats` mount-fetch. Move stats fetching UP to LayerPanel or DataAssetsView (one fetch for all assets in scope) and pass results down as props. Already discussed in §4.2's audit; this is the concrete instance.

## §5 — UX: Refresh buttons at global/layer/asset scopes

Mirror the `ClearIconButton` pattern. New component `RefreshIconButton.tsx`:

```typescript
'use client'
import { useState } from 'react'
import { toast } from 'sonner'
import { RefreshCw } from 'lucide-react'

interface Props {
  chartId: string
  scope: 'global' | 'layer' | 'asset'
  scopeTarget?: string | null
  size?: number
  onRefreshed?: () => void
}

export function RefreshIconButton({ chartId, scope, scopeTarget, size = 22, onRefreshed }: Props) {
  const [loading, setLoading] = useState(false)
  async function handleClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (loading) return
    setLoading(true)
    try {
      // For now: trigger the existing /api/cockpit/stats with no-cache + refresh hint;
      // OR call a dedicated /api/cockpit/refresh endpoint (NEW; see §5.1)
      const r = await fetch('/api/cockpit/refresh', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget ?? null }),
      })
      if (!r.ok) throw new Error((await r.json()).error ?? 'Refresh failed')
      toast.success(`Refreshed ${scope === 'asset' ? scopeTarget : scope}`)
      onRefreshed?.()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setLoading(false)
    }
  }
  return (
    <button onClick={handleClick} disabled={loading} title={`Refresh ${scope === 'asset' ? scopeTarget ?? 'asset' : scope}`}
      style={{ width: size, height: size, /* ... same styling pattern as ClearIconButton ... */ }}>
      <RefreshCw size={Math.round(size * 0.55)} className={loading ? 'animate-spin' : ''} />
    </button>
  )
}
```

### §5.1 — New API endpoint `/api/cockpit/refresh`

```typescript
// platform/src/app/api/cockpit/refresh/route.ts
export async function POST(req: NextRequest) {
  // For now: refresh = re-poll stats. This invalidates any cached stats and forces fresh count_sql execution.
  // Future: could trigger a re-derive of derived assets, but L0 doesn't need that yet.
  const user = await requireUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  // Simply return the freshly-computed stats for the scope; client uses it to update local cache
  // ... (similar pattern to /api/cockpit/stats but always fresh)
}
```

### §5.2 — Wire RefreshIconButton next to ClearIconButton

- `CockpitHeader.tsx` — add `<RefreshIconButton scope="global" ... />` next to "Clear instrument"
- `LayerPanel.tsx` — add `<RefreshIconButton scope="layer" scopeTarget={layer} ... />` next to layer-level `<ClearIconButton>`
- `AssetRow.tsx` — add `<RefreshIconButton scope="asset" scopeTarget={asset.asset_id} ... />` next to asset-level `<ClearIconButton>`

Like ClearIconButton, hide Refresh at L0 for non-super-admin: `{(isSuperAdmin || layer !== 'brahmagyan') && <RefreshIconButton ... />}`.

## §6 — BUG + UX: last_built_at write-path + display

### §6.1 — Investigate write-path

```bash
grep -rn "last_built_at" platform/python-sidecar platform/src/app/api/cockpit 2>&1 | head -10
```

The writers should set `asset_throughput.last_built_at = NOW()` on every successful build. Confirm:
- Build orchestrator sets it
- Per-writer functions set it after successful insert
- Cockpit stats query reads from `asset_throughput.last_built_at`

If any writer is missing the update, add it.

### §6.2 — Display format

`AssetRow.tsx` currently has `formatDateTime` and `formatRelative` imported. Find where last_built_at is rendered and ensure it uses `formatDateTime` (e.g. "08-Jun-2026 14:32") for the date column. If it shows raw ISO string or "Invalid Date", that's the bug.

```typescript
{stat?.last_built_at ? formatDateTime(stat.last_built_at) : '—'}
```

## §7 — UX: Chart ID display

`CockpitHeader.tsx:120`:
```typescript
{chartId.slice(0, 8)}…
```

Change to show full chart ID OR a longer prefix with copy-on-click:
```typescript
<span
  style={{ /* existing */, cursor: 'pointer' }}
  onClick={() => { navigator.clipboard.writeText(chartId); toast.success('Chart ID copied') }}
  title={`Click to copy: ${chartId}`}
>
  {chartId}
</span>
```

Or if full ID is too wide for the header, use a 14-char prefix with full ID on hover/click.

## §8 — Verification + smoke

### §8.1 — JSON-crash regression test (Phase §1)

Open the cockpit, trigger "Clear instrument" — expect either:
- Success: modal closes, toast shows success
- Failure: toast shows a SPECIFIC error (not "Unexpected end of JSON input")

### §8.2 — bg_reference clear preview (Phase §2)

`/api/cockpit/clear?scope=asset&scope_target=bg_reference` — `total_rows` should be sum across all 15 reference tables (currently 88 with only the 5 OLD tables seeded; will be larger when phase β fills the 10 new ones).

### §8.3 — Global modal layer summary (Phase §3)

Click "Clear instrument" → modal shows layer rows like "Brahma Jñāna (L0) (12 assets) — 0 rows", "Gaṇita (L1) (8 assets) — N rows", etc.

### §8.4 — Cockpit landing perf (Phase §4)

Open `/clients/<id>/build` — chart name + birth date should render within 1 sec (was 3-5 sec).

### §8.5 — Refresh buttons (Phase §5)

Three new refresh buttons visible: top of cockpit, each layer header, each asset row. Clicking refresh shows the spinner + success toast.

### §8.6 — last_built_at (Phase §6)

After a successful build (when phase β/γ writers run), the AssetRow shows a proper "08-Jun-2026 14:32" date. Until then, expect "—".

### §8.7 — Chart ID (Phase §7)

CockpitHeader shows full chart ID (or longer prefix); clicking copies to clipboard.

## §9 — Commit + PR

```bash
git add -A
git status
git commit -m "fix+feat(cockpit): polish round — 11 issues bundled

Critical fixes:
- §1 execute route: transaction + try/catch; always returns JSON
- §2 bg_reference count_sql drift in prod fixed (seed + migration sync); UPDATE applied to prod

UX features:
- §3 global modal: per-layer summary (layer name + asset count + total rows) instead of per-table overflow
- §5 RefreshIconButton at global/layer/asset scopes (super_admin sees L0; others don't)
- §6 last_built_at display formatted via formatDateTime
- §7 chart ID displayed in full with copy-on-click

Perf:
- §4 parallelize independent cockpit fetches; remove sequential stats per AssetRow

Source brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_COCKPIT_POLISH_ROUND_v1_0.md"

git push -u origin fix/cockpit-polish-round

gh pr create --title "fix+feat(cockpit): polish round — 11 issues bundled" \
  --body "Bundle of cockpit fixes per CLAUDECODE_BRIEF_COCKPIT_POLISH_ROUND_v1_0. Critical: execute-route JSON crash + bg_reference count_sql drift. UX: refresh buttons + layer-summary modal + last_built_at + chart_id. Perf: parallelize fetches." \
  --base main --head fix/cockpit-polish-round
```

## §10 — Hard stops

- §1.1 transaction block fails to compile → fall back to per-table try/catch without explicit transaction (same crash protection, no atomicity guarantee)
- §2.1 reveals prod schema doesn't HAVE the 10 new reference_* tables → migration 178 didn't apply; STOP and report; this changes Phase α's sealed state
- §3 layer_summary calculation produces unexpected per-layer totals → likely a join issue in clearable assets vs. counted tables; halt + investigate
- §4 parallelization causes hydration mismatch → revert to sequential; perf optimization is lowest priority
- §5 /api/cockpit/refresh design questioned → drop the dedicated endpoint and just call existing /api/cockpit/stats with no-cache; same UX effect
- Any test failure in CI → investigate; this PR adds significant surface area

## §11 — Out of scope

- Phase β/γ/δ/ε/ζ/η L0 build work
- Authentication / authorization beyond what already exists
- L1-L5 writer changes (last_built_at write-path is in writers; this brief only fixes display + audits one writer to confirm pattern — full writer audit is its own work)
- Major re-architecture of the cockpit fetch pipeline (beyond parallelization)

Begin pre-flight: `cd /Users/Dev/Vibe-Coding/Apps/Madhav; git fetch --all; git worktree add -b fix/cockpit-polish-round /Users/Dev/Vibe-Coding/Apps/MadhavCockpitPolish main`.

---

*End of brief.*
