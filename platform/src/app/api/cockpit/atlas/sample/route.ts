import { NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

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
