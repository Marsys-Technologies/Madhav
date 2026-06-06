import { NextRequest, NextResponse } from 'next/server'
import { getPool } from '@/lib/db/client'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export interface AssetStats {
  asset_id: string
  actual_rows: number | null
  size_bytes: number | null
  last_updated: string
  error: string | null
  // From asset_throughput (null when no chart_id supplied or no row yet)
  state: 'dormant' | 'building' | 'lit' | 'stale' | 'error' | null
  last_built_at: string | null
}

interface RegistryAsset {
  asset_id: string
  count_sql: string | null
  size_sql: string | null
  scope: string
  is_active: boolean
}

async function fetchAssetStats(
  asset: RegistryAsset,
  chartId: string | null
): Promise<AssetStats> {
  const now = new Date().toISOString()

  if (!asset.count_sql) {
    return {
      asset_id: asset.asset_id,
      actual_rows: null,
      size_bytes: null,
      last_updated: now,
      error: 'missing_table',
      state: null,
      last_built_at: null,
    }
  }

  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query("SET LOCAL statement_timeout = '2s'")

    // Substitute chart_id param for per_chart scoped assets (count only)
    const countParams = asset.scope === 'per_chart' && chartId ? [chartId] : []
    const countResult = await client.query<{ count: string }>(asset.count_sql, countParams)
    const actual_rows = parseInt(countResult.rows[0]?.count ?? '0', 10)

    let size_bytes: number | null = null
    if (asset.size_sql) {
      // size_sql is always pg_total_relation_size('tablename') — never binds $1
      const sizeResult = await client.query<{ size: string }>(asset.size_sql, [])
      const raw = sizeResult.rows[0]?.size
      size_bytes = raw != null ? parseInt(raw, 10) : null
    }

    await client.query('COMMIT')

    return {
      asset_id: asset.asset_id,
      actual_rows,
      size_bytes,
      last_updated: now,
      error: null,
      state: null,        // merged from throughput in GET handler
      last_built_at: null,
    }
  } catch (err) {
    try { await client.query('ROLLBACK') } catch {}
    const msg = (err as Error).message ?? ''
    const isTimeout =
      msg.includes('statement timeout') || msg.includes('canceling statement')
    return {
      asset_id: asset.asset_id,
      actual_rows: null,
      size_bytes: null,
      last_updated: now,
      error: isTimeout ? 'timeout' : msg.slice(0, 120),
      state: null,
      last_built_at: null,
    }
  } finally {
    client.release()
  }
}

export async function GET(req: NextRequest) {
  const chartId = req.nextUrl.searchParams.get('chart_id')

  try {
    // Load active assets that have count_sql
    const registryResult = await query<RegistryAsset>(`
      SELECT asset_id, count_sql, size_sql, scope, is_active
      FROM asset_registry
      WHERE is_active = true
      ORDER BY asset_id
    `)

    const assets = registryResult.rows

    // Batch-fetch throughput state+last_built_at for this chart
    const throughputMap = new Map<string, { state: string; last_built_at: string | null }>()
    if (chartId) {
      const { rows: tpRows } = await query<{ asset_id: string; state: string; last_built_at: string | null }>(
        `SELECT asset_id, state, last_built_at FROM asset_throughput WHERE chart_id = $1`,
        [chartId]
      )
      for (const r of tpRows) throughputMap.set(r.asset_id, r)
    }

    const settled = await Promise.allSettled(
      assets.map((asset) => fetchAssetStats(asset, chartId))
    )

    const assetStats: AssetStats[] = settled.map((result, i) => {
      const tp = throughputMap.get(assets[i].asset_id)
      const base = result.status === 'fulfilled'
        ? result.value
        : {
            asset_id: assets[i].asset_id,
            actual_rows: null,
            size_bytes: null,
            last_updated: new Date().toISOString(),
            error: (result.reason as Error)?.message ?? 'unknown',
          }
      return {
        ...base,
        state: (tp?.state as AssetStats['state']) ?? null,
        last_built_at: tp?.last_built_at ?? null,
      }
    })

    const response = NextResponse.json({
      data: { assets: assetStats },
      fetched_at: new Date().toISOString(),
      stale_after_seconds: 0,
      errors: [],
    })

    response.headers.set('Cache-Control', 'no-store')
    return response
  } catch (err) {
    console.error('[cockpit/stats] db error', err)
    return NextResponse.json(
      {
        data: { assets: [] },
        fetched_at: new Date().toISOString(),
        stale_after_seconds: 0,
        errors: [(err as Error).message ?? 'unknown error'],
      },
      { status: 500 }
    )
  }
}
