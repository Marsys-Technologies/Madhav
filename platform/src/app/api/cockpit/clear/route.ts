import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { computeDownstreamClosure, type RegistryEntry } from '@/lib/build/plan'
import { createHash } from 'crypto'
import { filterScopeAssets } from '@/lib/cockpit/clearScopeFilter'

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
  const { rows: registry } = await query<RegistryRow>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds,
            scope, target_table, count_sql
     FROM asset_registry ORDER BY layer, sort_order`
  )

  // Determine scope assets — respect role-based allowed scopes
  const scopeAssets = filterScopeAssets(registry, scope, scope_target, allowedScopes) as RegistryRow[]

  const clearableAssets = scopeAssets.filter(r => r.target_table && r.count_sql)

  // Validate table names before use
  for (const asset of clearableAssets) {
    if (asset.target_table && !TABLE_NAME_RE.test(asset.target_table)) {
      return NextResponse.json({ error: `Invalid target_table: ${asset.target_table}`, code: 'INVALID_TABLE' }, { status: 500 })
    }
  }

  // Count rows for each clearable asset
  interface TableCount { table: string; rows: number; error?: string }
  const tableCounts: TableCount[] = []
  // Deduplicate by target_table (some assets share a table)
  const seen = new Set<string>()

  for (const asset of clearableAssets) {
    if (!asset.target_table || !asset.count_sql || seen.has(asset.target_table)) continue
    seen.add(asset.target_table)
    try {
      // Global assets have no $1 parameter in count_sql; per_chart assets do
      const params = asset.scope === 'per_chart' ? [chart_id] : []
      const { rows: cnt } = await query<{ count: string }>(asset.count_sql, params)
      tableCounts.push({ table: asset.target_table, rows: parseInt(cnt[0]?.count ?? '0', 10) })
    } catch (err) {
      console.warn(`[clear/preview] count_sql failed for ${asset.asset_id}:`, (err as Error).message)
      tableCounts.push({ table: asset.target_table, rows: 0, error: ((err as Error).message ?? 'unknown').substring(0, 100) })
    }
  }

  const totalRows = tableCounts.reduce((s, t) => s + t.rows, 0)
  const affectedAssetIds = scopeAssets.map(r => r.asset_id)

  // Compute transitive downstream (assets outside scope that would become stale)
  const downstreamSet = computeDownstreamClosure(affectedAssetIds, registry)
  // Remove any that are already in scope
  for (const id of affectedAssetIds) downstreamSet.delete(id)
  const downstreamAssets = Array.from(downstreamSet)

  // Build preview_hash
  const hashInput = JSON.stringify({ chart_id, scope, scope_target, affectedAssetIds: affectedAssetIds.sort() })
  const preview_hash = createHash('sha256').update(hashInput).digest('hex').slice(0, 32)

  // Build per-layer summary (useful for global scope display)
  const layerRowsMap = new Map<string, number>()
  const layerAssetCountMap = new Map<string, number>()
  for (const asset of scopeAssets) {
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
