import { NextRequest, NextResponse } from 'next/server'
import { getPool } from '@/lib/db/client'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

type AssetState = 'lit' | 'building' | 'stale' | 'dormant' | 'error' | 'not_migrated'

function deriveState(
  asset: { is_active?: boolean; target_floor?: number | null },
  actualRows: number | null,
  error: string | null,
  throughputState: string | null
): AssetState {
  if (asset.is_active === false) return 'not_migrated'
  if (error) return 'error'
  if (throughputState === 'building') return 'building'
  if (throughputState === 'stale') return 'stale'
  if (actualRows === null || actualRows === 0) return 'dormant'
  if (asset.target_floor && actualRows < asset.target_floor) return 'building'
  return 'lit'
}

export interface AssetStats {
  asset_id: string
  actual_rows: number | null
  volume: number | null          // alias for actual_rows (canonical name)
  size_bytes: number | null
  last_updated: string
  error: string | null
  // Derived server-side; never null
  state: 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'not_migrated'
  last_built_at: string | null
}

interface RegistryAsset {
  asset_id: string
  count_sql: string | null
  size_sql: string | null
  scope: string
  is_active: boolean
  target_floor: number | null
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
      volume: null,
      size_bytes: null,
      last_updated: now,
      error: 'missing_table',
      state: 'error' as const,
      last_built_at: null,
    }
  }

  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query("SET LOCAL statement_timeout = '2s'")

    // Pass chartId whenever count_sql references $1, regardless of scope field
    const countParams = /\$1/.test(asset.count_sql) && chartId ? [chartId] : []
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
      volume: actual_rows,
      size_bytes,
      last_updated: now,
      error: null,
      state: 'dormant' as const,  // placeholder; GET handler overwrites via deriveState
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
      volume: null,
      size_bytes: null,
      last_updated: now,
      error: isTimeout ? 'timeout' : msg.slice(0, 120),
      state: 'error' as const,    // placeholder; GET handler overwrites via deriveState
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
      SELECT asset_id, count_sql, size_sql, scope, is_active, target_floor
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
      const asset = assets[i]
      const tp = throughputMap.get(asset.asset_id)
      const base = result.status === 'fulfilled'
        ? result.value
        : {
            asset_id: asset.asset_id,
            actual_rows: null,
            volume: null,
            size_bytes: null,
            last_updated: new Date().toISOString(),
            error: (result.reason as Error)?.message ?? 'unknown',
            state: deriveState(asset, null, (result.reason as Error)?.message ?? 'unknown', tp?.state ?? null),
            last_built_at: tp?.last_built_at ?? null,
          }
      const actual_rows = (base as AssetStats).actual_rows
      const error = (base as AssetStats).error
      return {
        ...base,
        volume: actual_rows,
        state: deriveState(asset, actual_rows, error, tp?.state ?? null),
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
