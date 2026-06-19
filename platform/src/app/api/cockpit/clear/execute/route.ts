import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query, getPool } from '@/lib/db/client'
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

  let cleared_table_count = 0
  let cleared_rows_total = 0
  const failed_tables: { table: string; error: string }[] = []

  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')

    const seen = new Set<string>()
    let spIdx = 0
    for (const asset of reversedAssets) {
      if (!asset.target_table || seen.has(asset.target_table)) continue
      seen.add(asset.target_table)

      // Use a SAVEPOINT per DELETE so a single table failure rolls back only
      // that statement, not the whole transaction (PostgreSQL marks the txn
      // aborted on any error — without SAVEPOINT every subsequent statement
      // would fail with "current transaction is aborted").
      const sp = `clr_${spIdx++}`
      await client.query(`SAVEPOINT ${sp}`)
      try {
        const sql = asset.scope === 'global'
          ? `DELETE FROM ${asset.target_table}`
          : `DELETE FROM ${asset.target_table} WHERE chart_id = $1`
        const params = asset.scope === 'global' ? [] : [chart_id]
        const result = await client.query(sql, params)
        await client.query(`RELEASE SAVEPOINT ${sp}`)
        cleared_table_count++
        cleared_rows_total += result.rowCount ?? 0
      } catch (err) {
        await client.query(`ROLLBACK TO SAVEPOINT ${sp}`)
        await client.query(`RELEASE SAVEPOINT ${sp}`)
        failed_tables.push({
          table: asset.target_table,
          error: ((err as Error).message ?? 'unknown').substring(0, 200),
        })
      }
    }

    // Reset asset_throughput for scope assets
    if (affectedAssetIds.length > 0) {
      await client.query(
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
      await client.query(
        `UPDATE asset_throughput
         SET state='stale'
         WHERE chart_id=$1 AND asset_id = ANY($2::text[])
           AND state IN ('lit','building','error')`,
        [chart_id, downstreamAssets]
      )
    }

    await client.query('COMMIT')
  } catch (outerErr) {
    await client.query('ROLLBACK').catch(() => null)
    console.error('[/api/cockpit/clear/execute] transaction failed:', outerErr)
    return NextResponse.json({
      error: 'Clear transaction failed; rolled back. ' + ((outerErr as Error).message ?? 'unknown').substring(0, 200),
      code: 'TRANSACTION_FAILED',
      details: { failed_tables },
    }, { status: 500 })
  } finally {
    client.release()
  }

  return NextResponse.json({
    cleared: {
      assets: affectedAssetIds.length,
      tables: cleared_table_count,
      rows: cleared_rows_total,
      downstream_stale: downstreamAssets.length,
    },
    ...(failed_tables.length > 0 ? { failed_tables } : {}),
  })
}
