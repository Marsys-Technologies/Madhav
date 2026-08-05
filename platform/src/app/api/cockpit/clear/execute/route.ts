import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query, getPool } from '@/lib/db/client'
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
  const [{ rows: registry }, { rows: protectedRows }] = await Promise.all([
    query<RegistryRow>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds,
              scope, target_table, count_sql
       FROM asset_registry ORDER BY layer, sort_order`
    ),
    // SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2. Re-derived identically to
    // clear/route.ts's preview so a protected asset is excluded from BOTH the hash
    // input AND the actual DELETE loop below — a protected pair is never merely hidden
    // from the preview while still being cleared here, and the hash still matches a
    // preview computed the same way. kala_gochara_windows additionally carries a
    // DB-level trigger guard (migration 540) as defense-in-depth; this exclusion is
    // the ONLY guard for any other asset a native later adds to build_protected_assets.
    query<{ asset_id: string }>(
      'SELECT asset_id FROM build_protected_assets WHERE chart_id=$1',
      [chart_id]
    ),
  ])
  const protectedAssetIds = new Set(protectedRows.map(r => r.asset_id))

  // Re-derive scope assets (same logic as preview), then withhold protected ones —
  // must match clear/route.ts's exclusion exactly or the hash below never matches a
  // genuine preview.
  const rawScopeAssets = filterScopeAssets(registry, scope, scope_target, allowedScopes) as RegistryRow[]
  const scopeAssets = rawScopeAssets.filter(a => !protectedAssetIds.has(a.asset_id))

  const affectedAssetIds = scopeAssets.map(r => r.asset_id)

  // Verify preview_hash
  // L-10: Match the timeSlot formula from clear/route.ts so hashes older than ~15 min are rejected.
  const timeSlot = Math.floor(Date.now() / (15 * 60 * 1000))
  const expectedHash = createHash('sha256')
    .update(JSON.stringify({ chart_id, scope, scope_target, affectedAssetIds: affectedAssetIds.sort(), timeSlot }))
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
  // Delete in reverse topo order (downstream-first for FK safety)
  // No pre-filter by target_table — every scope asset must either clear or report failure
  const reversedAssets = [...scopeAssets].reverse()

  let cleared_op_count = 0
  let cleared_rows_total = 0
  const failed_tables: { table: string; error: string }[] = []

  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')

    let spIdx = 0
    for (const asset of reversedAssets) {
      // Resolve the clear operations for this asset
      let ops: Array<{ sql: string; params: unknown[] }> | null = null

      if (asset.asset_id in EXPLICIT_CLEAR_OPS) {
        const explicitOps = EXPLICIT_CLEAR_OPS[asset.asset_id]
        if (explicitOps === null) continue  // no data rows, skip cleanly
        ops = explicitOps.map(op => ({
          sql: op.sql,
          params: op.sql.includes('$1') ? [chart_id] : [],
        }))
      } else if (asset.count_sql) {
        const deleteSql = deriveDeleteSqlFromCountSql(asset.count_sql)
        if (deleteSql) {
          ops = [{ sql: deleteSql, params: deleteSql.includes('$1') ? [chart_id] : [] }]
        }
      }

      // Fallback to target_table for assets without count_sql
      if (!ops && asset.target_table) {
        if (!TABLE_NAME_RE.test(asset.target_table)) {
          return NextResponse.json({ error: `Invalid target_table: ${asset.target_table}`, code: 'INVALID_TABLE' }, { status: 500 })
        }
        const sql = asset.scope === 'global'
          ? `DELETE FROM ${asset.target_table}`
          : `DELETE FROM ${asset.target_table} WHERE chart_id = $1`
        ops = [{ sql, params: asset.scope === 'global' ? [] : [chart_id] }]
      }

      if (!ops) {
        // No clear spec resolved — surface as failure (no silent skips)
        failed_tables.push({
          table: asset.asset_id,
          error: 'no clear spec: target_table and count_sql both null',
        })
        continue
      }

      // Use a SAVEPOINT per ASSET so all ops for an asset are atomic.
      // If any op fails, the entire asset's changes are rolled back, preventing
      // partial-clear inconsistency (e.g., ga_condition_composite cleared but
      // chart_facts avastha rows still present).
      const assetSp = `clr_${spIdx++}`
      await client.query(`SAVEPOINT ${assetSp}`)
      let assetFailed = false
      let assetRows = 0
      let assetOps = 0
      for (const op of ops) {
        try {
          const result = await client.query(op.sql, op.params)
          assetRows += result.rowCount ?? 0
          assetOps++
        } catch (err) {
          await client.query(`ROLLBACK TO SAVEPOINT ${assetSp}`)
          await client.query(`RELEASE SAVEPOINT ${assetSp}`)
          failed_tables.push({
            table: asset.asset_id,
            error: ((err as Error).message ?? 'unknown').substring(0, 200),
          })
          assetFailed = true
          break
        }
      }
      if (!assetFailed) {
        await client.query(`RELEASE SAVEPOINT ${assetSp}`)
        cleared_op_count += assetOps
        cleared_rows_total += assetRows
      }
    }

    // Reset asset_throughput for scope assets (chart-scoped rows) — but ONLY for assets
    // that actually cleared. An asset in failed_tables did NOT have its rows deleted (the
    // op errored and was rolled back to its savepoint); marking it dormant/rows_written=0
    // anyway would tell the cockpit UI the clear succeeded when it silently didn't — the
    // exact false-success bug this fix closes (ga_structural's JOIN-derived DELETE used to
    // fail here every time while the UI reported a clean clear).
    const failedAssetIds = new Set(failed_tables.map(f => f.table))
    const successfulAssetIds = affectedAssetIds.filter(id => !failedAssetIds.has(id))
    if (successfulAssetIds.length > 0) {
      await client.query(
        `UPDATE asset_throughput
         SET state='dormant', last_built_at=NULL, rows_written=0,
             built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
             last_error=NULL
         WHERE chart_id=$1 AND asset_id = ANY($2::text[])`,
        [chart_id, successfulAssetIds]
      )
    }

    // Also reset global throughput rows (chart_id IS NULL) for any global-scope assets
    // that were cleared. Without this, the stats route's rows_written cache returns
    // the pre-clear count (e.g. mi_kula shows 15 after the underlying table is empty).
    const globalAssetIds = scopeAssets
      .filter(a => a.scope === 'global' && !failedAssetIds.has(a.asset_id))
      .map(a => a.asset_id)
    if (globalAssetIds.length > 0) {
      await client.query(
        `UPDATE asset_throughput
         SET state='dormant', last_built_at=NULL, rows_written=0,
             built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
             last_error=NULL
         WHERE chart_id IS NULL AND asset_id = ANY($1::text[])`,
        [globalAssetIds]
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
      ops: cleared_op_count,
      rows: cleared_rows_total,
      downstream_stale: downstreamAssets.length,
    },
    ...(failed_tables.length > 0 ? { failed_tables } : {}),
  })
}
