import { NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { getServerUser } from '@/lib/firebase/server'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'

export const dynamic = 'force-dynamic'

function envelope(errors: string[], status: number) {
  return NextResponse.json(
    { data: null, fetched_at: new Date().toISOString(), stale_after_seconds: 0, errors },
    { status }
  )
}

const MAX_LIMIT = 50

type AssetMeta = {
  asset_id: string
  target_table: string | null
  count_sql: string | null
  scope: string
  asset_type: string | null
  storage_type: string
}

// Build a safe SELECT query from asset registry metadata.
// The table name is always sourced from the DB, never from client input.
function buildSampleQuery(
  asset: AssetMeta,
  chartId: string | null,
  limit: number
): { sql: string; params: unknown[] } | null {
  if (asset.asset_type === 'service') return null
  if (asset.storage_type === 'postgres_view') return null

  // Case 1: asset has a dedicated target_table
  if (asset.target_table) {
    // Double-check table name format (it came from DB but sanity-gate here too)
    if (!/^[a-z_][a-z0-9_]{0,62}$/.test(asset.target_table)) return null

    if (asset.scope === 'per_chart' && chartId) {
      return {
        sql: `SELECT * FROM ${asset.target_table} WHERE chart_id = $1 LIMIT $2`,
        params: [chartId, limit],
      }
    }
    return {
      sql: `SELECT * FROM ${asset.target_table} LIMIT $1`,
      params: [limit],
    }
  }

  // Case 2: no target_table — asset writes into a shared table (e.g. chart_facts).
  // Extract the FROM <table> WHERE ... clause from count_sql and rebuild as a SELECT.
  // Pattern: SELECT count(*) [AS count] FROM <table> WHERE <clause>
  if (!asset.count_sql) return null
  const match = asset.count_sql.match(/FROM\s+(\w+)\s+(WHERE\s+.+?)(?:\s*$)/i)
  if (!match) return null
  const tableName = match[1]
  const whereClause = match[2]

  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(tableName)) return null

  if (asset.scope === 'per_chart' && chartId) {
    // count_sql uses $1 for chart_id; add $2 for LIMIT
    return {
      sql: `SELECT * FROM ${tableName} ${whereClause} LIMIT $2`,
      params: [chartId, limit],
    }
  }
  return {
    sql: `SELECT * FROM ${tableName} ${whereClause} LIMIT $1`,
    params: [limit],
  }
}

export async function GET(req: NextRequest) {
  // P2-B-008 (CRITICAL): this route had NO authentication whatsoever — zero
  // getServerUser() calls — and served `SELECT * FROM <target_table> WHERE
  // chart_id = $1` for any caller-supplied asset + chart_id. An anonymous HTTP
  // request could read another person's chart_facts, bodha_*, kala_*, phala_*
  // rows in full. Authentication is the first gate; ownership (below, once the
  // asset's scope is known) is the second.
  const user = await getServerUser()
  if (!user) return envelope(['authentication required'], 401)

  const assetId = req.nextUrl.searchParams.get('asset')
  const chartId = req.nextUrl.searchParams.get('chart_id') || null
  const rawLimit = parseInt(req.nextUrl.searchParams.get('limit') ?? '10', 10)
  const limit = Math.min(isNaN(rawLimit) || rawLimit < 1 ? 10 : rawLimit, MAX_LIMIT)

  if (!assetId) {
    return NextResponse.json(
      { data: null, fetched_at: new Date().toISOString(), stale_after_seconds: 0, errors: ['asset param required'] },
      { status: 400 }
    )
  }

  try {
    // Resolve asset_id → table config server-side; never accept a table name from the client
    const assetResult = await query<AssetMeta>(
      `SELECT asset_id, target_table, count_sql, scope, asset_type, storage_type
       FROM asset_registry WHERE asset_id = $1`,
      [assetId]
    )

    if (!assetResult.rows.length) {
      return NextResponse.json(
        { data: null, fetched_at: new Date().toISOString(), stale_after_seconds: 0, errors: ['asset not found'] },
        { status: 404 }
      )
    }

    const asset = assetResult.rows[0]

    // P2-B-008, second gate. Two distinct holes are closed here, and BOTH are
    // required — authentication alone would leave the second one wide open.
    //
    //   1. A per_chart asset WITH a chart_id: the rows belong to that chart's
    //      owner, so the caller needs at least a 'view' relationship to it.
    //   2. A per_chart asset WITHOUT a chart_id: `buildSampleQuery` used to fall
    //      through to the unscoped `SELECT * FROM <table> LIMIT $1` branch,
    //      returning rows from ALL charts mixed together. Any logged-in user
    //      could read everyone's data simply by omitting the parameter. A
    //      per_chart asset now REQUIRES a chart_id; the unscoped branch is
    //      reachable only by genuinely global-scope assets.
    //
    // Global-scope assets (bg_* reference corpora and the like) have no owner to
    // check — for those, authentication above is the whole gate.
    if (asset.scope === 'per_chart') {
      if (!chartId) {
        return envelope(['chart_id is required for a per-chart asset'], 400)
      }
      const denied = await requireChartPermission({
        uid: user.uid,
        chartId,
        access: 'read',
      })
      if (denied) return envelope(['forbidden'], 403)
    }

    const querySpec = buildSampleQuery(asset, chartId, limit)

    if (!querySpec) {
      return NextResponse.json({
        data: {
          columns: [],
          rows: [],
          table: null,
          note: 'Sample data not available for this asset type',
          fetched_at: new Date().toISOString(),
        },
        fetched_at: new Date().toISOString(),
        stale_after_seconds: 0,
        errors: [],
      })
    }

    const result = await query<Record<string, unknown>>(querySpec.sql, querySpec.params)
    const columns = result.rows.length > 0 ? Object.keys(result.rows[0]) : []

    return NextResponse.json({
      data: {
        columns,
        rows: result.rows,
        table: asset.target_table ?? '(shared table)',
        fetched_at: new Date().toISOString(),
      },
      fetched_at: new Date().toISOString(),
      stale_after_seconds: 0,
      errors: [],
    })
  } catch (err) {
    console.error('[cockpit/atlas/sample] db error', err)
    return NextResponse.json(
      {
        data: null,
        fetched_at: new Date().toISOString(),
        stale_after_seconds: 0,
        errors: [(err as Error).message ?? 'unknown error'],
      },
      { status: 500 }
    )
  }
}
