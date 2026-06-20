import { NextRequest, NextResponse } from 'next/server'
import { getPool } from '@/lib/db/client'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

type AssetState = 'lit' | 'building' | 'stale' | 'dormant' | 'error' | 'not_migrated' | 'service_ok'

function deriveState(
  asset: { is_active?: boolean; target_floor?: number | null; asset_type?: string | null },
  actualRows: number | null,
  error: string | null,
  throughputState: string | null
): AssetState {
  // Service assets have no count_sql/target_table by design — they are healthy
  // when registered + CURRENT. They must never fall through to the data-asset
  // dormant/error logic below.
  if (asset.asset_type === 'service') return 'service_ok'
  if (asset.is_active === false) return 'not_migrated'
  if (error) return 'error'
  // §N.4: count_sql is authoritative for data presence. Rows present = lit,
  // regardless of throughput state or target_floor. Floors are aspirational,
  // NOT gates — an asset with rows > 0 and no active zero-row build is lit.
  // An orphaned 'building' record or cascade-stale flag does NOT override real
  // data confirmed by count_sql. Under-floor is shown as an informational badge
  // (build_state_stale), never as 'building' or 'incomplete'.
  if (actualRows != null && actualRows > 0) return 'lit'
  // No rows at all: fall back to throughput state for in-progress vs stale vs dormant.
  // 'lit' here means the writer ran and zero rows is correct by design (e.g. ga_prashna
  // on a natal chart with no horary questions submitted).
  if (throughputState === 'lit') return 'lit'
  if (throughputState === 'building') return 'building'
  if (throughputState === 'stale') return 'stale'
  return 'dormant'
}

export interface AssetStats {
  asset_id: string
  actual_rows: number | null
  volume: number | null          // alias for actual_rows (canonical name)
  size_bytes: number | null
  last_updated: string
  error: string | null
  // 'dataplane' = Cloud SQL proxy / connection-level failure (transient).
  // 'query'     = per-asset SQL error (real data problem).
  // undefined   = no error.
  error_class?: 'dataplane' | 'query'
  // Derived server-side; never null
  state: 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'not_migrated' | 'service_ok'
  last_built_at: string | null
  // True when count_sql shows rows present but asset_throughput says stale/dormant/absent.
  // The bar shows lit-equivalent; this flag enables a "build-state stale" badge.
  build_state_stale: boolean
  // Service-asset health fields (populated for asset_type='service'; null for data assets)
  service_health: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | null
  last_invoked_at: string | null
}

interface RegistryAsset {
  asset_id: string
  count_sql: string | null
  size_sql: string | null
  scope: string
  is_active: boolean
  target_floor: number | null
  asset_type: 'data' | 'service' | null
  asset_kind: 'data' | 'service' | 'artifact' | null
  health_probe: Record<string, unknown> | null
  service_health: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | null
  last_invoked_at: string | null
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

  // Service assets carry count_sql:null / target_table:null by design. They are
  // not table-backed, so we never run SQL for them — a registered service is
  // healthy. (Health-probe execution is a follow-up; default to service_ok so a
  // correctly-registered service never renders as errored / missing_table.)
  if (asset.asset_type === 'service') {
    return {
      asset_id: asset.asset_id,
      actual_rows: null,
      volume: null,
      size_bytes: null,
      last_updated: now,
      error: null,
      state: 'service_ok' as const,
      last_built_at: null,
      build_state_stale: false,
      service_health: asset.service_health ?? null,
      last_invoked_at: asset.last_invoked_at ?? null,
    }
  }

  if (!asset.count_sql) {
    return {
      asset_id: asset.asset_id,
      actual_rows: null,
      volume: null,
      size_bytes: null,
      last_updated: now,
      error: 'missing_table',
      error_class: 'query' as const,
      state: 'error' as const,
      last_built_at: null,
      build_state_stale: false,
      service_health: null,
      last_invoked_at: null,
    }
  }

  const pool = await getPool()
  const client = await pool.connect()
  if (clientRef) clientRef.value = client
  try {
    await client.query('BEGIN')
    await client.query("SET LOCAL statement_timeout = '2s'")

    const countParams = /\$1/.test(asset.count_sql) ? [chartId] : []
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
      build_state_stale: false,
      service_health: null,
      last_invoked_at: null,
    }
  } catch (err) {
    try { await client.query('ROLLBACK') } catch {}
    const msg = (err as Error).message ?? ''
    const isTimeout = msg.includes('statement timeout') || msg.includes('canceling statement')
    const isDataPlane = msg.includes('ECONNREFUSED') || msg.includes('connection refused') ||
      msg.includes('ETIMEDOUT') || msg.includes('Connection terminated') ||
      msg.includes('connect ETIMEDOUT') || msg.includes('getaddrinfo')
    return {
      asset_id: asset.asset_id,
      actual_rows: null,
      volume: null,
      size_bytes: null,
      last_updated: now,
      error: isTimeout ? 'timeout' : msg.slice(0, 120),
      error_class: isDataPlane ? 'dataplane' as const : 'query' as const,
      state: 'error' as const,
      last_built_at: null,
      build_state_stale: false,
      service_health: null,
      last_invoked_at: null,
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
    error_class: 'dataplane' as const,
    state: 'error' as const,
    last_built_at: null,
    build_state_stale: false,
    service_health: null,
    last_invoked_at: null,
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
      SELECT asset_id, count_sql, size_sql, scope, is_active, target_floor,
             asset_type, asset_kind, health_probe, service_health, last_invoked_at
      FROM asset_registry
      WHERE is_active = true
      ORDER BY asset_id
    `)

    const assets = registryResult.rows

    // Batch-fetch throughput state+last_built_at for this chart
    const throughputMap = new Map<string, { state: string; last_built_at: string | null }>()
    if (chartId) {
      const { rows: tpRows } = await query<{ asset_id: string; state: string; last_built_at: string | null }>(
        `SELECT DISTINCT ON (asset_id) asset_id, state, last_built_at
           FROM asset_throughput
          WHERE chart_id = $1 OR chart_id IS NULL
          ORDER BY asset_id, (chart_id = $1) DESC NULLS LAST, last_built_at DESC NULLS LAST`,
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
            build_state_stale: false,
            service_health: null,
            last_invoked_at: null,
          }
      const derivedState = deriveState(asset, base.actual_rows, base.error, tp?.state ?? null)
      // build_state_stale: data is present (count_sql > 0) but asset_throughput says
      // building/stale/dormant/error/absent — signals the bar to badge "build-state stale".
      const buildStateStale = derivedState === 'lit'
        && (base.actual_rows != null && base.actual_rows > 0)
        && (tp?.state === 'stale' || tp?.state === 'dormant' || tp?.state === 'building' || tp?.state === 'error' || tp == null)
      return {
        ...base,
        volume: base.actual_rows,
        state: derivedState,
        last_built_at: tp?.last_built_at ?? null,
        build_state_stale: buildStateStale,
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
