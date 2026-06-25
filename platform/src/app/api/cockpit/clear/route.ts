import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { computeDownstreamClosure, type RegistryEntry } from '@/lib/build/plan'
import { createHash } from 'crypto'
import { filterScopeAssets } from '@/lib/cockpit/clearScopeFilter'
import { deriveDeleteSqlFromCountSql, EXPLICIT_CLEAR_OPS } from '@/lib/cockpit/assetClearSpec'

interface RegistryRow extends RegistryEntry {
  scope: string
  target_table: string | null
  count_sql: string | null
}

async function requireUser() {
  const user = await getServerUser()
  if (!user) return null
  return user
}

async function getUserRole(uid: string): Promise<string> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role ?? 'guest'
}

const TABLE_NAME_RE = /^[a-z_][a-z0-9_]{0,62}$/

export async function POST(req: NextRequest) {
  const user = await requireUser()
  if (!user) return NextResponse.json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 })

  const body = await req.json().catch(() => null)
  if (!body?.chart_id || !body?.scope) {
    return NextResponse.json({ error: 'chart_id and scope are required', code: 'BAD_REQUEST' }, { status: 400 })
  }

  const { chart_id, scope, scope_target = null } = body as {
    chart_id: string
    scope: 'global' | 'layer' | 'asset'
    scope_target?: string | null
  }

  if (scope === 'asset' && !scope_target) {
    return NextResponse.json({ error: 'scope_target required for asset scope', code: 'BAD_REQUEST' }, { status: 400 })
  }
  if (scope === 'layer' && !scope_target) {
    return NextResponse.json({ error: 'scope_target required for layer scope', code: 'BAD_REQUEST' }, { status: 400 })
  }

  const role = await getUserRole(user.uid)
  const isSuperAdmin = role === 'super_admin'
  const allowedScopes: string[] = isSuperAdmin ? ['per_chart', 'global'] : ['per_chart']

  // Authorization: non-super-admin cannot clear L0 layer or global assets
  if (!isSuperAdmin) {
    if (scope === 'layer' && scope_target === 'brahmagyan') {
      return NextResponse.json({ error: 'Only super_admin can clear L0 Brahmagyan layer', code: 'FORBIDDEN_L0' }, { status: 403 })
    }
    if (scope === 'asset') {
      // Check if the target asset is global — need registry to know; do a quick lookup
      const { rows: assetRows } = await query<{ scope: string }>(
        'SELECT scope FROM asset_registry WHERE asset_id=$1',
        [scope_target]
      )
      if (assetRows[0]?.scope === 'global') {
        return NextResponse.json({ error: 'Only super_admin can clear global assets', code: 'FORBIDDEN_L0' }, { status: 403 })
      }
    }
  }

  // Load registry
  const { rows: registry } = await query<RegistryRow & { english_name?: string }>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds,
            scope, target_table, count_sql, english_name
     FROM asset_registry ORDER BY layer, sort_order`
  )
  // Build id→English name lookup for UI display
  const assetLabelMap = new Map<string, string>(
    registry.map(r => [r.asset_id, (r as RegistryRow & { english_name?: string }).english_name ?? r.asset_id])
  )

  // Determine scope assets — respect role-based allowed scopes
  const scopeAssets = filterScopeAssets(registry, scope, scope_target, allowedScopes) as RegistryRow[]

  // Validate target_table names for SQL safety
  for (const asset of scopeAssets) {
    if (asset.target_table && !TABLE_NAME_RE.test(asset.target_table)) {
      return NextResponse.json({ error: `Invalid target_table: ${asset.target_table}`, code: 'INVALID_TABLE' }, { status: 500 })
    }
  }

  // Determine clear-spec and count rows for EVERY scope asset — same resolution order as execute:
  //   1. EXPLICIT_CLEAR_OPS (null → zero-row service asset, array → explicit ops)
  //   2. deriveDeleteSqlFromCountSql (count_sql auto-transformable)
  //   3. target_table fallback
  //   4. no spec → not_clearable (surfaced, never silently omitted)
  interface AssetCountResult {
    asset_id: string
    target_table: string | null
    rows: number
    is_clearable: boolean
    error?: string
  }
  const assetCountResults: AssetCountResult[] = []

  for (const asset of scopeAssets) {
    let isClearable = false
    let isExplicitNull = false

    if (asset.asset_id in EXPLICIT_CLEAR_OPS) {
      const explicitOps = EXPLICIT_CLEAR_OPS[asset.asset_id]
      isExplicitNull = explicitOps === null
      isClearable = true
    } else if (asset.count_sql) {
      const deleteSql = deriveDeleteSqlFromCountSql(asset.count_sql)
      isClearable = deleteSql != null || asset.target_table != null
    } else if (asset.target_table) {
      isClearable = true
    }

    if (!isClearable) {
      assetCountResults.push({ asset_id: asset.asset_id, target_table: asset.target_table, rows: 0, is_clearable: false })
      continue
    }

    // Explicit null → zero-row service asset (no DB query needed)
    if (isExplicitNull || !asset.count_sql) {
      assetCountResults.push({ asset_id: asset.asset_id, target_table: asset.target_table, rows: 0, is_clearable: true })
      continue
    }

    try {
      const params = asset.scope === 'per_chart' ? [chart_id] : []
      const { rows: cnt } = await query<{ count: string }>(asset.count_sql, params)
      assetCountResults.push({
        asset_id: asset.asset_id,
        target_table: asset.target_table,
        rows: parseInt(cnt[0]?.count ?? '0', 10),
        is_clearable: true,
      })
    } catch (err) {
      console.warn(`[clear/preview] count_sql failed for ${asset.asset_id}:`, (err as Error).message)
      assetCountResults.push({
        asset_id: asset.asset_id,
        target_table: asset.target_table,
        rows: 0,
        error: ((err as Error).message ?? 'unknown').substring(0, 100),
        is_clearable: true,
      })
    }
  }

  const clearableResults = assetCountResults.filter(a => a.is_clearable)
  const notClearableResults = assetCountResults.filter(a => !a.is_clearable)

  // Aggregate per-asset counts by target_table for the display breakdown.
  // Multiple assets may write to the same table (e.g. chart_facts) with disjoint
  // WHERE clauses — sum their counts so the table row shows the true total deleted.
  interface TableCount { table: string; rows: number; error?: string }
  const tableRowsMap = new Map<string, { rows: number; error?: string }>()
  for (const a of clearableResults) {
    const key = a.target_table ?? a.asset_id
    const existing = tableRowsMap.get(key)
    if (existing) {
      existing.rows += a.rows
      if (a.error && !existing.error) existing.error = a.error
    } else {
      tableRowsMap.set(key, { rows: a.rows, ...(a.error ? { error: a.error } : {}) })
    }
  }
  const tableCounts: TableCount[] = Array.from(tableRowsMap.entries()).map(([table, v]) => ({
    table,
    rows: v.rows,
    ...(v.error ? { error: v.error } : {}),
  }))

  const totalRows = clearableResults.reduce((s, a) => s + a.rows, 0)
  const affectedAssetIds = scopeAssets.map(r => r.asset_id)

  // Not-clearable assets: no clear spec resolved (no count_sql, no target_table, not in EXPLICIT_CLEAR_OPS)
  const notClearableAssetsList = notClearableResults.map(a => ({
    id: a.asset_id,
    label: assetLabelMap.get(a.asset_id) ?? a.asset_id,
  }))

  // Compute transitive downstream (assets outside scope that would become stale)
  const downstreamSet = computeDownstreamClosure(affectedAssetIds, registry)
  // Remove any that are already in scope
  for (const id of affectedAssetIds) downstreamSet.delete(id)

  // Only show downstream assets that are actually built for this chart — dormant assets
  // are unaffected by a clear and shouldn't be listed as needing rebuild.
  const allDownstream = Array.from(downstreamSet)
  let downstreamAssets: string[] = []
  if (allDownstream.length > 0) {
    const { rows: builtRows } = await query<{ asset_id: string }>(
      `SELECT asset_id FROM asset_throughput
       WHERE chart_id=$1 AND state IN ('lit','building','error','stale')
         AND asset_id = ANY($2::text[])`,
      [chart_id, allDownstream]
    )
    downstreamAssets = builtRows.map(r => r.asset_id)
  }

  // Build preview_hash
  const hashInput = JSON.stringify({ chart_id, scope, scope_target, affectedAssetIds: affectedAssetIds.sort() })
  const preview_hash = createHash('sha256').update(hashInput).digest('hex').slice(0, 32)

  // Build per-layer summary using per-asset counts (not per-table)
  const layerRowsMap = new Map<string, number>()
  const layerAssetCountMap = new Map<string, number>()
  const acMap = new Map(assetCountResults.map(a => [a.asset_id, a]))
  for (const asset of scopeAssets) {
    const acr = acMap.get(asset.asset_id)
    const rows = acr?.rows ?? 0
    layerRowsMap.set(asset.layer, (layerRowsMap.get(asset.layer) ?? 0) + rows)
    layerAssetCountMap.set(asset.layer, (layerAssetCountMap.get(asset.layer) ?? 0) + 1)
  }
  const layer_summary = Array.from(layerRowsMap.entries()).map(([layer, rows]) => ({
    layer,
    rows,
    asset_count: layerAssetCountMap.get(layer) ?? 0,
  }))

  // Build downstream list with human labels for display
  const downstreamStaleAssets = downstreamAssets.map(id => ({
    id,
    label: assetLabelMap.get(id) ?? id,
  }))

  // For asset scope, provide the human label of the asset being cleared
  const scope_label = scope === 'asset' && scope_target
    ? (assetLabelMap.get(scope_target) ?? scope_target)
    : null

  const preview: Record<string, unknown> = {
    tables: tableCounts,
    total_rows: totalRows,
    affected_assets: affectedAssetIds,
    not_clearable_assets: notClearableAssetsList,        // assets with no resolvable clear spec
    downstream_stale_assets: downstreamAssets,           // kept as string[] for backward compat
    downstream_stale_assets_labeled: downstreamStaleAssets, // new: [{id, label}]
    scope_label,
    preview_hash,
    layer_summary,
  }

  // Global scope OR L0 layer-scope: require typed confirmation
  if (scope === 'global' || (scope === 'layer' && scope_target === 'brahmagyan')) {
    const { rows: charts } = await query<{ subject_name: string | null; name: string }>(
      'SELECT subject_name, name FROM charts WHERE id=$1',
      [chart_id]
    )
    const subjectName = charts[0]?.subject_name ?? charts[0]?.name ?? ''
    preview.requires_typed_confirmation = subjectName
  }

  return NextResponse.json({ preview })
}
