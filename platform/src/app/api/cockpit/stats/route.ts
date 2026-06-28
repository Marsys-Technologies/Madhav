import { NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'
export const maxDuration = 15 // seconds — Next.js route segment config

type AssetState = 'lit' | 'building' | 'stale' | 'dormant' | 'error' | 'not_migrated' | 'service_ok'

function deriveState(
  asset: { is_active?: boolean; target_floor?: number | null; asset_type?: string | null; asset_kind?: string | null },
  actualRows: number | null,
  error: string | null,
  throughputState: string | null
): AssetState {
  // Service assets have no count_sql/target_table by design — they are healthy
  // when registered + CURRENT. They must never fall through to the data-asset
  // dormant/error logic below. Check both asset_type (L1/L2 legacy) and
  // asset_kind (L3+ canonical) so new-layer service registrations are caught.
  if (asset.asset_type === 'service' || asset.asset_kind === 'service') return 'service_ok'
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
  // Live rows written during an active build — sourced from asset_throughput.rows_written.
  // Only populated when the asset is in 'building' state; null otherwise.
  rows_written?: number
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

type ThroughputEntry = { state: string; last_built_at: string | null; rows_written: number | null }

// Stats source hierarchy:
//   1. rows_written from asset_throughput (normal polls) — build-time truth, <100ms
//   2. live count_sql (?mode=live) — operator-triggered only, bypasses cache
// This eliminates the 40+ COUNT(*) query storm on every 5s poll.

async function fetchAllCounts(
  assets: RegistryAsset[],
  chartId: string | null,
  throughputMap: Map<string, ThroughputEntry>,
  liveMode: boolean,
): Promise<AssetStats[]> {
  const now = new Date().toISOString()

  const fetchOne = async (asset: RegistryAsset): Promise<AssetStats> => {
    if (asset.asset_type === 'service' || asset.asset_kind === 'service') {
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

    const tp = throughputMap.get(asset.asset_id)
    // rows_written shortcut: valid ONLY for per_chart assets.
    // Global scope assets (bg_*, mi_kula, etc.) have a single throughput row with
    // chart_id IS NULL. That row is NOT reset by per-chart clear operations, so
    // rows_written can be stale long after the underlying table was emptied.
    // Always run count_sql for global assets — their tables are small (no chart_id
    // filter) and the extra query cost is negligible.
    if (!liveMode && tp != null && tp.rows_written != null && asset.scope === 'per_chart') {
      return {
        asset_id: asset.asset_id,
        actual_rows: tp.rows_written,
        volume: tp.rows_written,
        size_bytes: null,
        last_updated: now,
        error: null,
        state: 'dormant' as const,
        last_built_at: tp.last_built_at ?? null,
        build_state_stale: false,
        service_health: null,
        last_invoked_at: null,
      }
    }

    // No throughput row, OR throughput row exists but rows_written is null (legacy entry without
    // count tracking) → fall back to live count_sql to get the real row count.
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

    try {
      const countParams = /\$1/.test(asset.count_sql) ? [chartId] : []
      const countResult = await query<{ count: string }>(asset.count_sql, countParams)
      const actual_rows = parseInt(countResult.rows[0]?.count ?? '0', 10)

      let size_bytes: number | null = null
      if (asset.size_sql) {
        const sizeResult = await query<{ size: string }>(asset.size_sql)
        const raw = sizeResult.rows[0]?.size
        size_bytes = raw != null ? parseInt(raw, 10) : null
      }

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
      const msg = (err as Error).message ?? ''
      const isTimeout = msg.includes('statement timeout') || msg.includes('canceling statement')
      const isDataPlane = msg.includes('ECONNREFUSED') || msg.includes('connection refused') ||
        msg.includes('ETIMEDOUT') || msg.includes('Connection terminated') ||
        msg.includes('connect ETIMEDOUT') || msg.includes('getaddrinfo') ||
        msg.includes('timeout exceeded when trying to connect')
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
    }
  }

  // Batch 8 at a time — only the fallback count_sql assets need DB calls now,
  // so this loop completes in one or two fast batches.
  const CONCURRENCY = 8
  const results: AssetStats[] = []
  for (let i = 0; i < assets.length; i += CONCURRENCY) {
    const batch = await Promise.all(assets.slice(i, i + CONCURRENCY).map(fetchOne))
    results.push(...batch)
  }
  return results
}

export async function GET(req: NextRequest) {
  const chartId = req.nextUrl.searchParams.get('chart_id')
  // C2: ?mode=live bypasses the rows_written shortcut (used by Refresh path + post-build refetch)
  const liveMode = req.nextUrl.searchParams.get('mode') === 'live'

  // Abort-aware: if client disconnects, skip the DB work
  if (req.signal?.aborted) {
    return NextResponse.json({ data: { assets: [] }, fetched_at: new Date().toISOString(), stale_after_seconds: 0, errors: ['aborted'] })
  }

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
    const throughputMap = new Map<string, ThroughputEntry>()
    if (chartId) {
      const { rows: tpRows } = await query<{ asset_id: string; state: string; last_built_at: string | null; rows_written: number | null }>(
        `SELECT DISTINCT ON (asset_id) asset_id, state, last_built_at, rows_written
           FROM asset_throughput
          WHERE chart_id = $1 OR chart_id IS NULL
          ORDER BY asset_id, (chart_id = $1) DESC NULLS LAST, last_built_at DESC NULLS LAST`,
        [chartId]
      )
      for (const r of tpRows) throughputMap.set(r.asset_id, r)
    }

    const rawStats = await fetchAllCounts(assets, chartId, throughputMap, liveMode)

    // Build a lookup map so we can correlate rawStats back to assets and throughput
    // regardless of insertion order (service_ok and missing_table assets are prepended).
    const rawMap = new Map(rawStats.map(r => [r.asset_id, r]))

    const assetStats: AssetStats[] = assets.map((asset) => {
      const tp = throughputMap.get(asset.asset_id)
      const base = rawMap.get(asset.asset_id) ?? {
        asset_id: asset.asset_id,
        actual_rows: null,
        volume: null,
        size_bytes: null,
        last_updated: new Date().toISOString(),
        error: 'not_fetched',
        state: 'error' as const,
        last_built_at: null,
        build_state_stale: false,
        service_health: null,
        last_invoked_at: null,
      }
      const derivedState = deriveState(asset, base.actual_rows, base.error, tp?.state ?? null)
      // build_state_stale: data is present (count_sql > 0) but asset_throughput says
      // stale/dormant/error/absent — signals the bar to badge "build-state stale".
      // Excludes 'building': an actively-building asset with committed substep rows is not stale.
      const buildStateStale = derivedState === 'lit'
        && (base.actual_rows != null && base.actual_rows > 0)
        && (tp?.state === 'stale' || tp?.state === 'dormant' || tp?.state === 'error' || tp == null)
      return {
        ...base,
        volume: base.actual_rows,
        state: derivedState,
        last_built_at: tp?.last_built_at ?? null,
        build_state_stale: buildStateStale,
        rows_written: (tp?.rows_written != null && derivedState === 'building')
          ? tp.rows_written
          : undefined,
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
