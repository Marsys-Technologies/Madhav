import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { computeDownstreamClosure, type RegistryEntry } from '@/lib/build/plan'
import { createHash } from 'crypto'

interface RegistryRow extends RegistryEntry {
  scope: string
  target_table: string | null
  count_sql: string | null
}

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

export async function POST(req: NextRequest) {
  const user = await requireSuperAdmin()
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

  // Load registry
  const { rows: registry } = await query<RegistryRow>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds,
            scope, target_table, count_sql
     FROM asset_registry ORDER BY layer, sort_order`
  )

  // Determine scope assets (only per_chart assets can be cleared per chart)
  let scopeAssets: RegistryRow[]
  if (scope === 'global') {
    scopeAssets = registry.filter(r => r.scope === 'per_chart')
  } else if (scope === 'layer') {
    scopeAssets = registry.filter(r => r.layer === scope_target && r.scope === 'per_chart')
  } else {
    scopeAssets = registry.filter(r => r.asset_id === scope_target && r.scope === 'per_chart')
  }

  const clearableAssets = scopeAssets.filter(r => r.target_table && r.count_sql)

  // Count rows for each clearable asset
  interface TableCount { table: string; rows: number }
  const tableCounts: TableCount[] = []
  // Deduplicate by target_table (some assets share a table)
  const seen = new Set<string>()

  for (const asset of clearableAssets) {
    if (!asset.target_table || !asset.count_sql || seen.has(asset.target_table)) continue
    seen.add(asset.target_table)
    try {
      const { rows: cnt } = await query<{ count: string }>(asset.count_sql, [chart_id])
      tableCounts.push({ table: asset.target_table, rows: parseInt(cnt[0]?.count ?? '0', 10) })
    } catch {
      tableCounts.push({ table: asset.target_table, rows: 0 })
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

  const preview: Record<string, unknown> = {
    tables: tableCounts,
    total_rows: totalRows,
    affected_assets: affectedAssetIds,
    downstream_stale_assets: downstreamAssets,
    preview_hash,
  }

  // Global scope: add typed confirmation requirement
  if (scope === 'global') {
    const { rows: charts } = await query<{ subject_name: string | null; name: string }>(
      'SELECT subject_name, name FROM charts WHERE id=$1',
      [chart_id]
    )
    const subjectName = charts[0]?.subject_name ?? charts[0]?.name ?? ''
    preview.requires_typed_confirmation = subjectName
  }

  return NextResponse.json({ preview })
}
