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
  if (!body?.chart_id || !body?.scope || !body?.preview_hash) {
    return NextResponse.json({ error: 'chart_id, scope, and preview_hash are required', code: 'BAD_REQUEST' }, { status: 400 })
  }

  const { chart_id, scope, scope_target = null, preview_hash, typed_confirmation } = body as {
    chart_id: string
    scope: 'global' | 'layer' | 'asset'
    scope_target?: string | null
    preview_hash: string
    typed_confirmation?: string
  }

  // Load registry
  const { rows: registry } = await query<RegistryRow>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds,
            scope, target_table, count_sql
     FROM asset_registry ORDER BY layer, sort_order`
  )

  // Re-derive scope assets (same logic as preview)
  let scopeAssets: RegistryRow[]
  if (scope === 'global') {
    scopeAssets = registry.filter(r => r.scope === 'per_chart')
  } else if (scope === 'layer') {
    scopeAssets = registry.filter(r => r.layer === scope_target && r.scope === 'per_chart')
  } else {
    scopeAssets = registry.filter(r => r.asset_id === scope_target && r.scope === 'per_chart')
  }

  const affectedAssetIds = scopeAssets.map(r => r.asset_id)

  // Verify preview_hash
  const expectedHash = createHash('sha256')
    .update(JSON.stringify({ chart_id, scope, scope_target, affectedAssetIds: affectedAssetIds.sort() }))
    .digest('hex')
    .slice(0, 32)

  if (preview_hash !== expectedHash) {
    return NextResponse.json({ error: 'Preview hash mismatch — fetch a fresh preview', code: 'HASH_MISMATCH' }, { status: 409 })
  }

  // Global scope: verify typed confirmation
  if (scope === 'global') {
    const { rows: charts } = await query<{ subject_name: string | null; name: string }>(
      'SELECT subject_name, name FROM charts WHERE id=$1',
      [chart_id]
    )
    const subjectName = charts[0]?.subject_name ?? charts[0]?.name ?? ''
    if (!typed_confirmation || typed_confirmation !== subjectName) {
      return NextResponse.json({ error: 'Subject name confirmation required', code: 'SUBJECT_NAME_MISMATCH' }, { status: 403 })
    }
  }

  // Compute downstream (to be marked stale)
  const downstreamSet = computeDownstreamClosure(affectedAssetIds, registry)
  for (const id of affectedAssetIds) downstreamSet.delete(id)
  const downstreamAssets = Array.from(downstreamSet)

  // Execute: delete data + reset throughput + mark downstream stale
  const clearableAssets = scopeAssets.filter(r => r.target_table)
  // Delete in reverse topo order (downstream-first for FK safety)
  const reversedAssets = [...clearableAssets].reverse()

  const seen = new Set<string>()
  for (const asset of reversedAssets) {
    if (!asset.target_table || seen.has(asset.target_table)) continue
    seen.add(asset.target_table)
    await query(`DELETE FROM ${asset.target_table} WHERE chart_id = $1`, [chart_id])
  }

  // Reset asset_throughput for scope assets
  if (affectedAssetIds.length > 0) {
    await query(
      `UPDATE asset_throughput
       SET state='dormant', last_built_at=NULL,
           built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
           last_error=NULL
       WHERE chart_id=$1 AND asset_id = ANY($2::text[])`,
      [chart_id, affectedAssetIds]
    )
  }

  // Mark downstream as stale (only those currently lit/building/error — dormant stays dormant)
  if (downstreamAssets.length > 0) {
    await query(
      `UPDATE asset_throughput
       SET state='stale'
       WHERE chart_id=$1 AND asset_id = ANY($2::text[])
         AND state IN ('lit','building','error')`,
      [chart_id, downstreamAssets]
    )
  }

  return NextResponse.json({
    cleared: { assets: affectedAssetIds.length, downstream_stale: downstreamAssets.length },
  })
}
