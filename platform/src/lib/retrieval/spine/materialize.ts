/**
 * materialize.ts — persistence + read path for spine bundles (W5 Lane L5,
 * migration 463 `bodha_spine_bundles`).
 *
 * TWO ways a bundle gets (re)computed, both funneling through the same
 * computeSpineBundle() (compute_spine_bundle.ts) so the persisted row and a fresh
 * computation are always byte-identical in content:
 *
 *   1. POST-BUILD HOOK (primary): platform/src/app/api/admin/internal/
 *      spine-bundle-refresh/route.ts calls materializeAllDomainsForChart() —
 *      intended to be invoked right after a chart's build reaches a terminal
 *      'completed' state (the same build_runs.state the cockpit SSE route and
 *      watchdog already key off — see that route's header comment for the wiring
 *      note). This keeps the spine-bundle refresh OUTSIDE the FROZEN orchestrator:
 *      nothing here runs on ctx.db_conn or touches WriterBase/asset_throughput —
 *      it is a downstream consumer of the orchestrator's completion signal, not a
 *      modification of it (CLAUDE.md §N.2).
 *
 *   2. LAZY FALLBACK (safety net): getOrMaterializeSpineBundle(), the function the
 *      query_spine_bundle capability actually calls on every read, checks the
 *      persisted row's freshness against source_asset_marker (see below) and
 *      recomputes+persists on the spot when the row is missing OR stale. This
 *      guarantees no PERMANENT staleness even if the post-build hook is never
 *      wired in a given environment (dev, a missed cron, a webhook outage) — the
 *      first real request after a rebuild self-heals the materialized view, at
 *      the cost of that one request paying the full 4-capability fan-out. This
 *      mirrors the self-healing discipline already used elsewhere in this
 *      registry (e.g. query_signals.ts's resolveOptionalElevationColumns()).
 *
 * WHY A PLAIN TABLE, NOT `CREATE MATERIALIZED VIEW` (see migration 463's header
 * for the fuller version): every existing MV in this codebase (mv_tool_metrics_24h,
 * mv_calibration_score, ...) is a GLOBAL view refreshed in full on a schedule —
 * REFRESH MATERIALIZED VIEW has no per-chart-scoped variant. A spine bundle is
 * chart-scoped and refreshes once per chart build, so the CLAUDE.md §N.3 L1+
 * idempotency standard (per-chart delete-then-insert on a natural key) is the
 * correct "materialize, never accrete" mechanism here, not a genuine PG MV.
 *
 * STALENESS DETECTION: source_asset_marker (stamped at compute time) is
 * MAX(asset_throughput.last_built_at) across the four constituent source assets.
 * A persisted row is considered fresh iff the CURRENT max last_built_at for those
 * same assets is <= the row's stored marker — i.e. none of the four source assets
 * has rebuilt since this bundle was computed. No silent staleness: a caller can
 * always see which path served them via the `source` field on the returned result.
 */

import { query } from '@/lib/db/client'
import { computeSpineBundle } from './compute_spine_bundle'
import { DEFAULT_AYANAMSHA } from '../registry/constants'
import { DEFAULT_SPINE_TOP_K, SPINE_SOURCE_ASSET_IDS } from './constants'
import type { SpineBundleContent } from './types'

export interface GetOrMaterializeArgs {
  chart_id: string
  ayanamsha_id?: string
  domain: string
  top_k?: number
}

export type SpineBundleSource = 'materialized' | 'fresh_materialized' | 'fresh_recomputed_stale'

export interface GetOrMaterializeResult {
  bundle: SpineBundleContent
  source: SpineBundleSource
  computed_at: string
}

interface PersistedRow {
  bundle_jsonb: SpineBundleContent
  top_k: number
  computed_at: string
  source_asset_marker: string | null
}

/** MAX(last_built_at) across the spine's source assets for this chart, or null if none built yet. */
export async function getSourceAssetMarker(chartId: string): Promise<string | null> {
  const result = await query<{ latest: string | null }>(
    `SELECT MAX(last_built_at) AS latest
       FROM asset_throughput
      WHERE chart_id = $1 AND asset_id = ANY($2::text[])`,
    [chartId, [...SPINE_SOURCE_ASSET_IDS]],
  )
  return result.rows[0]?.latest ?? null
}

/** Compute one (chart, ayanamsha, domain) spine bundle and persist it (delete-then-insert). */
export async function materializeSpineBundle(
  chartId: string,
  domain: string,
  opts: { ayanamshaId?: string; topK?: number } = {},
  ctx?: import('../registry/types').CapabilityContext,
): Promise<SpineBundleContent> {
  const ayanamsha_id = opts.ayanamshaId ?? DEFAULT_AYANAMSHA
  const top_k = opts.topK ?? DEFAULT_SPINE_TOP_K

  const [bundle, sourceMarker] = await Promise.all([
    computeSpineBundle({ chart_id: chartId, ayanamsha_id, domain, top_k }, ctx),
    getSourceAssetMarker(chartId),
  ])

  // §N.3 L1+ idempotency: per-chart delete-then-insert scoped to the natural key
  // (chart_id, ayanamsha_id, domain) — replace, never accrete.
  await query(
    `DELETE FROM bodha_spine_bundles WHERE chart_id = $1 AND ayanamsha_id = $2 AND domain = $3`,
    [chartId, ayanamsha_id, domain],
  )
  await query(
    `INSERT INTO bodha_spine_bundles
       (chart_id, ayanamsha_id, domain, top_k, signal_count, bundle_jsonb, source_asset_marker, computed_at)
     VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, now())`,
    [chartId, ayanamsha_id, domain, top_k, bundle.signal_count, JSON.stringify(bundle), sourceMarker],
  )

  return bundle
}

/** Materialize a spine bundle for every domain in SPINE_DOMAINS for one chart. */
export async function materializeAllDomainsForChart(
  chartId: string,
  ayanamshaId: string = DEFAULT_AYANAMSHA,
  ctx?: import('../registry/types').CapabilityContext,
): Promise<{ domain: string; signal_count: number }[]> {
  const { SPINE_DOMAINS } = await import('./constants')
  const results: { domain: string; signal_count: number }[] = []
  for (const domain of SPINE_DOMAINS) {
    const bundle = await materializeSpineBundle(chartId, domain, { ayanamshaId }, ctx)
    results.push({ domain, signal_count: bundle.signal_count })
  }
  return results
}

/**
 * The read path query_spine_bundle actually calls: serve the persisted row if it
 * exists, satisfies the requested top_k, and is not stale relative to the source
 * assets' current build state; otherwise recompute + persist (lazy fallback) and
 * serve that.
 */
export async function getOrMaterializeSpineBundle(
  args: GetOrMaterializeArgs,
  ctx?: import('../registry/types').CapabilityContext,
): Promise<GetOrMaterializeResult> {
  const ayanamsha_id = args.ayanamsha_id ?? DEFAULT_AYANAMSHA
  const top_k = args.top_k ?? DEFAULT_SPINE_TOP_K

  const existing = await query<PersistedRow>(
    `SELECT bundle_jsonb, top_k, computed_at, source_asset_marker
       FROM bodha_spine_bundles
      WHERE chart_id = $1 AND ayanamsha_id = $2 AND domain = $3`,
    [args.chart_id, ayanamsha_id, args.domain],
  )
  const row = existing.rows[0]

  if (row && row.top_k >= top_k) {
    const currentMarker = await getSourceAssetMarker(args.chart_id)
    const isStale =
      currentMarker !== null &&
      (row.source_asset_marker === null || new Date(currentMarker) > new Date(row.source_asset_marker))

    if (!isStale) {
      return { bundle: row.bundle_jsonb, source: 'materialized', computed_at: row.computed_at }
    }
    const bundle = await materializeSpineBundle(args.chart_id, args.domain, { ayanamshaId: ayanamsha_id, topK: top_k }, ctx)
    return { bundle, source: 'fresh_recomputed_stale', computed_at: new Date().toISOString() }
  }

  const bundle = await materializeSpineBundle(args.chart_id, args.domain, { ayanamshaId: ayanamsha_id, topK: top_k }, ctx)
  return { bundle, source: 'fresh_materialized', computed_at: new Date().toISOString() }
}
