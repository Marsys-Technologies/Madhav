import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { ClientRoster } from '@/components/dashboard/ClientRoster'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { Suspense } from 'react'
import type { Chart } from '@/lib/db/types'
import { fetchConsumedTodayCount } from '@/lib/roster/stats'
import type { ChartWithMeta, RosterStats } from '@/lib/roster/types'
import { Navagraha } from '@/components/brand/Navagraha'
import { BRAHMA_LAYER_ORDER } from '@/lib/brahma/lexicon'
import { ChartCreatedToast } from '@/components/brahma/ChartCreatedToast'

/**
 * Dashboard — role-gated roster (Unit 3.consult_nav, Commit 1).
 *
 * Role behavior:
 *   - super_admin → all charts in roster (admin surfaces available via nav rail).
 *   - guest → owned (owner_id) + granted (chart_grants) charts only.
 *     A single-chart guest is NOT auto-redirected — they land on the dashboard
 *     just like a multi-chart guest, but with one card. They can still pick a
 *     chart, and after 2c sharing widens their roster, they have a single place
 *     to switch among them.
 *
 * Tier/depth selectors are not rendered anywhere (tier excision: concurrent unit).
 */
export default async function DashboardPage() {
  const user = await getServerUser()
  if (!user) redirect('/login')

  const profileResult = await query(
    'SELECT id, role, name, username, email, status FROM profiles WHERE id=$1',
    [user.uid]
  )
  const profile = (profileResult.rows[0] ?? null) as { id: string; role: string } | null

  // Resolve role — legacy 'client' is treated as 'guest' until migration 082 fully applies.
  const role: 'super_admin' | 'guest' =
    profile?.role === 'super_admin' ? 'super_admin' : 'guest'

  // Fetch the roster:
  //   super_admin → every chart in the system.
  //   guest       → owned (owner_id) ∪ granted (chart_grants) charts.
  // Always returns; no auto-redirect on the "single chart" guest case
  // (per Unit 3.consult_nav scope: "stop auto-redirecting a single-chart guest").
  const chartsResult = role === 'super_admin'
    ? await query('SELECT * FROM charts ORDER BY created_at DESC', [])
    : await query(
        `SELECT c.* FROM charts c
         WHERE c.owner_id = $1
            OR c.client_id = $1
            OR EXISTS (
              SELECT 1 FROM chart_grants g
              WHERE g.chart_id = c.id AND g.principal_id = $1
            )
         ORDER BY c.created_at DESC`,
        [user.uid]
      )
  const charts = chartsResult.rows as unknown as Chart[]

  const chartIds = charts.map((c) => c.id)

  // Pyramid layers, active builds, and consumed-today all depend on chartIds
  // but are independent of each other — run in parallel.
  // throughputResult: per-chart asset build state from asset_throughput (the orchestrator's
  // authoritative source). This replaces the legacy pyramid_layers query which was never
  // updated by the modern build system and caused the progress bar to be stale/incorrect.
  const [throughputResult, buildsResult, consumedToday] = await Promise.all([
    chartIds.length > 0
      ? query<{ chart_id: string; asset_id: string; state: string; rows_written: number | null; last_built_at: string | null }>(
          `SELECT at.chart_id, at.asset_id, at.state, at.rows_written, at.last_built_at
           FROM asset_throughput at
           JOIN asset_registry ar ON ar.asset_id = at.asset_id AND ar.is_active = true
           WHERE at.chart_id = ANY($1::uuid[])`,
          [chartIds]
        )
      : Promise.resolve({ rows: [] }),

    chartIds.length > 0
      ? query<{
          build_id: string
          chart_id: string
          status: string
          progress_pct: number
          ayanamshas: string[]
          started_at: string | null
          error_summary: string | null
        }>(
          `SELECT DISTINCT ON (chart_id)
             id AS build_id, chart_id, state AS status,
             COALESCE(
               (SELECT ROUND(
                 COUNT(*) FILTER (WHERE bra.state = 'complete')::numeric
                 / NULLIF(COUNT(*), 0) * 100
               ) FROM build_run_assets bra WHERE bra.run_id = build_runs.id),
               0
             )::int AS progress_pct,
             ARRAY[]::text[] AS ayanamshas,
             started_at,
             NULL::text AS error_summary
           FROM build_runs
           WHERE chart_id = ANY($1::uuid[])
             AND state IN ('planned', 'running', 'paused')
           ORDER BY chart_id, created_at DESC`,
          [chartIds]
        )
      : Promise.resolve({ rows: [] }),

    fetchConsumedTodayCount(chartIds),
  ])

  const pyramidPercents = new Map<string, number>()
  const lastActivityMap = new Map<string, string>()
  const inActiveBuildSet = new Set<string>()
  const layerPipsMap = new Map<string, import('@/lib/roster/types').LayerPip[]>()
  const buildStateMap = new Map<string, import('@/lib/roster/types').ChartBuildState>()

  for (const buildRow of buildsResult.rows) {
    buildStateMap.set(buildRow.chart_id, {
      build_id: buildRow.build_id,
      status: buildRow.status as import('@/lib/roster/types').ChartBuildState['status'],
      progress_pct: buildRow.progress_pct,
      ayanamshas: Array.isArray(buildRow.ayanamshas) ? buildRow.ayanamshas : [],
      started_at: buildRow.started_at,
      error_summary: buildRow.error_summary,
    })
  }

  // Map asset_id prefix → Brahma layer (ga_→ganita, bo_→bodha, ka_→kala, ph_→phala, mi_→mimamsa).
  // brahmagyan (L0) is global infrastructure with no per-chart throughput entries — always lit.
  const assetToBrahmaLayer = (assetId: string): string | null => {
    if (assetId.startsWith('ga_')) return 'ganita'
    if (assetId.startsWith('bo_')) return 'bodha'
    if (assetId.startsWith('ka_')) return 'kala'
    if (assetId.startsWith('ph_')) return 'phala'
    if (assetId.startsWith('mi_')) return 'mimamsa'
    return null
  }

  for (const chart of charts) {
    const rows = throughputResult.rows.filter((r) => r.chart_id === chart.id)

    // Last activity = max last_built_at across all assets for this chart.
    const timestamps = rows.map((r) => r.last_built_at).filter(Boolean) as string[]
    if (timestamps.length > 0) {
      const latest = timestamps.reduce((a, b) => (a > b ? a : b))
      lastActivityMap.set(chart.id, latest)
    }

    // In active build = any asset currently in 'building' state.
    if (rows.some((r) => r.state === 'building')) {
      inActiveBuildSet.add(chart.id)
    }

    // Aggregate per-Brahma-layer presence from asset_throughput.
    // A layer has data if any of its active assets has rows_written > 0 OR state = 'lit'
    // (state='lit' with rows_written=0 is valid for zero-row-by-design assets like ga_prashna).
    // Stale assets with rows count as lit — data exists even if rebuild is pending.
    const layerDataMap = new Map<string, { hasData: boolean; isBuilding: boolean }>()
    for (const row of rows) {
      const brahmaLayer = assetToBrahmaLayer(row.asset_id)
      if (!brahmaLayer) continue
      const current = layerDataMap.get(brahmaLayer) ?? { hasData: false, isBuilding: false }
      layerDataMap.set(brahmaLayer, {
        hasData: current.hasData || (row.rows_written != null && row.rows_written > 0) || row.state === 'lit',
        isBuilding: current.isBuilding || row.state === 'building',
      })
    }

    // Build layer pips from asset_throughput — reflects true orchestrator build state.
    // brahmagyan is always lit (L0 global infra, provisioned at platform setup).
    const pips: import('@/lib/roster/types').LayerPip[] = BRAHMA_LAYER_ORDER.map((brahmaLayer) => {
      if (brahmaLayer === 'brahmagyan') return { layer: brahmaLayer, state: 'lit' as const }
      const entry = layerDataMap.get(brahmaLayer)
      if (!entry) return { layer: brahmaLayer, state: 'dim' as const }
      if (entry.hasData) return { layer: brahmaLayer, state: 'lit' as const }
      if (entry.isBuilding) return { layer: brahmaLayer, state: 'building' as const }
      return { layer: brahmaLayer, state: 'dim' as const }
    })
    layerPipsMap.set(chart.id, pips)

    // pyramidPercent = lit Brahma layers / total Brahma layers — consistent with pips.
    const litCount = pips.filter((p) => p.state === 'lit').length
    pyramidPercents.set(chart.id, Math.round((litCount / BRAHMA_LAYER_ORDER.length) * 100))
  }

  const chartsWithMeta: ChartWithMeta[] = charts.map((c) => ({
    ...c,
    pyramidPercent: pyramidPercents.get(c.id) ?? 0,
    lastLayerActivity: lastActivityMap.get(c.id) ?? null,
    buildState: buildStateMap.get(c.id) ?? null,
    layerPips: layerPipsMap.get(c.id) ?? BRAHMA_LAYER_ORDER.map((layer) => ({ layer, state: 'dim' as const })),
    // BUILD = owner/super_admin only (Phase 2B). View-grantees get canBuild=false → disabled affordance.
    canBuild: role === 'super_admin' || c.owner_id === user.uid,
  }))

  const stats: RosterStats = {
    total: charts.length,
    inActiveBuild: inActiveBuildSet.size,
    consumedToday,
    predictionsOverdue: 0,
  }

  return (
    <div className="relative min-h-full overflow-hidden" data-testid="dashboard-root" data-role={role}>
      {/* Chart-created toast: shown when ?chart_created=[id] is present in URL */}
      <Suspense>
        <ChartCreatedToast />
      </Suspense>
      <Navagraha
        size={600}
        opacity={0.15}
        className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
      />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_50%,transparent_25%,rgba(2,2,1,0.5)_65%,rgba(2,2,1,0.88)_100%)]" />
      <div className="relative z-10 container mx-auto py-8 px-4">
        <div className="flex items-center justify-between mb-6">
          <h1 className="bt-display text-[#fce29a]">
            <span className="opacity-55 text-[#d4af37] font-serif mr-1">॥</span>
            Jātakas
            <span className="opacity-55 text-[#d4af37] font-serif ml-1">॥</span>
          </h1>
          {role === 'super_admin' && (
            <Link href="/clients/new" aria-label="Nava Jātaka (new chart)" className="brand-cta inline-flex items-center gap-1.5 rounded-lg px-5 py-2.5 text-sm" data-testid="new-client-link">
              <span className="text-base leading-none">+</span>
              Nava Jātaka
            </Link>
          )}
        </div>
        <Suspense>
          <ClientRoster charts={chartsWithMeta} stats={stats} />
        </Suspense>
      </div>
    </div>
  )
}
