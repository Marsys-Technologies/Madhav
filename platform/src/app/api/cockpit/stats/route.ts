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
    }
  }

  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query("SET LOCAL statement_timeout = '2s'")

    // Substitute chart_id param for per_chart scoped assets
    const params = asset.scope === 'per_chart' && chartId ? [chartId] : []
    const countResult = await client.query<{ count: string }>(asset.count_sql, params)
    const actual_rows = parseInt(countResult.rows[0]?.count ?? '0', 10)

    let size_bytes: number | null = null
    if (asset.size_sql) {
      const sizeResult = await client.query<{ size: string }>(asset.size_sql, params)
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

    const settled = await Promise.allSettled(
      assets.map((asset) => fetchAssetStats(asset, chartId))
    )

    const assetStats: AssetStats[] = settled.map((result, i) => {
      if (result.status === 'fulfilled') return result.value
      return {
        asset_id: assets[i].asset_id,
        actual_rows: null,
        size_bytes: null,
        last_updated: new Date().toISOString(),
        error: (result.reason as Error)?.message ?? 'unknown',
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
