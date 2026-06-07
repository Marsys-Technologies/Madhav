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
  return rows[0]?.role ?? 'client'
}

const TABLE_NAME_RE = /^[a-z_][a-z0-9_]{0,62}$/

export async function POST(req: NextRequest) {
  const user = await requireUser()
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

  const role = await getUserRole(user.uid)
  const isSuperAdmin = role === 'super_admin'
  const allowedScopes: string[] = isSuperAdmin ? ['per_chart', 'global'] : ['per_chart']

  // Authorization: non-super-admin cannot clear L0 layer or global assets
  if (!isSuperAdmin) {
    if (scope === 'layer' && scope_target === 'brahmagyan') {
      return NextResponse.json({ error: 'Only super_admin can clear L0 Brahmagyan layer', code: 'FORBIDDEN_L0' }, { status: 403 })
    }
    if (scope === 'asset') {
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

  // Re-derive scope assets (same logic as preview)
  const scopeAssets = filterScopeAssets(registry, scope, scope_target, allowedScopes) as RegistryRow[]

  const affectedAssetIds = scopeAssets.map(r => r.asset_id)

  // Verify preview_hash
  const expectedHash = createHash('sha256')
    .update(JSON.stringify({ chart_id, scope, scope_target, affectedAssetIds: affectedAssetIds.sort() }))
    .digest('hex')
    .slice(0, 32)

  if (preview_hash !== expectedHash) {
    return NextResponse.json({ error: 'Preview hash mismatch — fetch a fresh preview', code: 'HASH_MISMATCH' }, { status: 409 })
  }

  // Global scope OR L0 layer-scope: verify typed confirmation
  if (scope === 'global' || (scope === 'layer' && scope_target === 'brahmagyan')) {
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

  // Validate table names before interpolation (defense-in-depth)
  for (const asset of clearableAssets) {
    if (asset.target_table && !TABLE_NAME_RE.test(asset.target_table)) {
      return NextResponse.json({ error: `Invalid target_table: ${asset.target_table}`, code: 'INVALID_TABLE' }, { status: 500 })
    }
  }

  // Delete in reverse topo order (downstream-first for FK safety)
  const reversedAssets = [...clearableAssets].reverse()
  const seen = new Set<string>()

  for (const asset of reversedAssets) {
    if (!asset.target_table || seen.has(asset.target_table)) continue
    seen.add(asset.target_table)

    if (asset.scope === 'global') {
      // Global tables: full-table DELETE (no chart_id column); supports transactional rollback
      await query(`DELETE FROM ${asset.target_table}`, [])
    } else {
      // per_chart tables: scoped DELETE
      await query(`DELETE FROM ${asset.target_table} WHERE chart_id = $1`, [chart_id])
    }
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
