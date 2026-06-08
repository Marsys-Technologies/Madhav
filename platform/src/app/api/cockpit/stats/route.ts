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

// Mutable reference so the timeout callback can reach the pool client acquired
// inside fetchAssetStats and destroy it (see fetchAssetStatsWithTimeout).
type ClientRef = { value: import('pg').PoolClient | null }

async function fetchAssetStats(
  asset: RegistryAsset,
  chartId: string | null,
  clientRef?: ClientRef
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
  if (clientRef) clientRef.value = client
  try {
    await client.query('BEGIN')
    await client.query("SET LOCAL statement_timeout = '2s'")

    const countParams = /\$1/.test(asset.count_sql) && chartId ? [chartId] : []
    const countResult = await client.query<{ count: string }>(asset.count_sql, countParams)
    const actual_rows = parseInt(countResult.rows[0]?.count ?? '0', 10)

    let size_bytes: number | null = null
    if (asset.size_sql) {
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
      state: 'dormant' as const,
      last_built_at: null,
    }
  } catch (err) {
    try { await client.query('ROLLBACK') } catch {}
    const msg = (err as Error).message ?? ''
    const isTimeout = msg.includes('statement timeout') || msg.includes('canceling statement')
    return {
      asset_id: asset.asset_id,
      actual_rows: null,
      volume: null,
      size_bytes: null,
      last_updated: now,
      error: isTimeout ? 'timeout' : msg.slice(0, 120),
      state: 'error' as const,
      last_built_at: null,
    }
  } finally {
    // Only release if the timeout hasn't already destroyed this client.
    // clientRef.value is set to null by the timeout before calling release(true).
    if (!clientRef || clientRef.value === client) {
      client.release()
      if (clientRef) clientRef.value = null
    }
  }
}

// Per-asset wall-clock timeout.
//
// Problem: Promise.race alone is not enough. When the timeout fires and the
// outer race resolves, fetchAssetStats is still running and still holds its
// pool.connect() slot. On a half-open TCP connection (e.g. after a Cloud SQL
// proxy restart) pool.connect() or the first query hangs for 30-60 s waiting
// for the kernel TCP timeout (macOS keepidle = 7200 s, so OS keepalive is
// useless here). With batchSize=6 stale connections, all 6 pool slots stay
// occupied for 30-60 s — any concurrent request that needs a connection hits
// connectionTimeoutMillis and crashes (the "Something went wrong" page).
//
// Fix: pass a clientRef into fetchAssetStats so we can call client.release(true)
// (destroy = close the TCP socket immediately) when the timeout fires. This
// frees the pool slot within 3.5 s instead of 30-60 s.
const ASSET_TIMEOUT_MS = 3_500

function fetchAssetStatsWithTimeout(
  asset: RegistryAsset,
  chartId: string | null
): Promise<AssetStats> {
  const timeoutResult: AssetStats = {
    asset_id: asset.asset_id,
    actual_rows: null,
    volume: null,
    size_bytes: null,
    last_updated: new Date().toISOString(),
    error: 'conn_timeout',
    state: 'error' as const,
    last_built_at: null,
  }
  const clientRef: ClientRef = { value: null }
  const timeout = new Promise<AssetStats>((resolve) =>
    setTimeout(() => {
      // Destroy the hanging connection to free the pool slot immediately.
      const c = clientRef.value
      if (c) {
        clientRef.value = null
        try { c.release(true) } catch { /* already destroyed */ }
      }
      resolve(timeoutResult)
    }, ASSET_TIMEOUT_MS)
  )
  return Promise.race([fetchAssetStats(asset, chartId, clientRef), timeout])
}

// Run asset fetches in batches to avoid saturating the pg pool (default max=10).
// batchSize=6 → ceil(N/6) rounds × max(ASSET_TIMEOUT_MS, ~600ms) per round.
async function fetchAssetStatsBatched(
  assets: RegistryAsset[],
  chartId: string | null,
  batchSize = 6
): Promise<PromiseSettledResult<AssetStats>[]> {
  const all: PromiseSettledResult<AssetStats>[] = []
  for (let i = 0; i < assets.length; i += batchSize) {
    const batch = await Promise.allSettled(
      assets.slice(i, i + batchSize).map(a => fetchAssetStatsWithTimeout(a, chartId))
    )
    all.push(...batch)
  }
  return all
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

    const settled = await fetchAssetStatsBatched(assets, chartId)

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
            state: 'error' as const,
            last_built_at: null,
          }
      return {
        ...base,
        volume: base.actual_rows,
        state: deriveState(asset, base.actual_rows, base.error, tp?.state ?? null),
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
