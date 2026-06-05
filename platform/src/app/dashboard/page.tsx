import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { ClientRoster } from '@/components/dashboard/ClientRoster'
import BuildsInProgressCard from '@/components/dashboard/BuildsInProgressCard'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { Suspense } from 'react'
import type { Chart } from '@/lib/db/types'
import { fetchConsumedTodayCount } from '@/lib/roster/stats'
import type { ChartWithMeta, RosterStats } from '@/lib/roster/types'
import { Navagraha } from '@/components/brand/Navagraha'
import { BRAHMA_LAYER_ORDER, PYRAMID_TO_BRAHMA } from '@/lib/brahma/lexicon'
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

  // Per-layer pyramid data — fetches individual rows so we can derive
  // Brahma-layer pip states for the ClientCard pip rail.
  const layersResult = chartIds.length > 0
    ? await query<{ chart_id: string; layer: string; sublayer: string; status: string; updated_at: string }>(
        'SELECT chart_id, layer, sublayer, status, updated_at FROM pyramid_layers WHERE chart_id = ANY($1::uuid[])',
        [chartIds]
      )
    : { rows: [] }

  // Active builds — latest per chart (queued/running/cancelling only).
  const buildsResult = chartIds.length > 0
    ? await query<{
        build_id: string
        chart_id: string
        status: string
        progress_pct: number
        ayanamshas: string[]
        started_at: string | null
        error_summary: string | null
      }>(
        `SELECT DISTINCT ON (chart_id)
           build_id, chart_id, status,
           COALESCE(
             (SELECT COUNT(*)::float / NULLIF(COUNT(*) FILTER (WHERE TRUE), 0) * 100
              FROM build_steps WHERE build_steps.build_id = builds.build_id),
             0
           )::int AS progress_pct,
           ayanamshas, started_at, error_summary
         FROM builds
         WHERE chart_id = ANY($1::uuid[])
           AND status IN ('queued', 'running', 'cancelling')
         ORDER BY chart_id, queued_at DESC`,
        [chartIds]
      )
    : { rows: [] }

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

  for (const chart of charts) {
    const rows = layersResult.rows.filter((r) => r.chart_id === chart.id)
    const complete = rows.filter((r) => r.status === 'complete').length
    pyramidPercents.set(chart.id, Math.round((complete / 6) * 100))

    const timestamps = rows.map((r) => r.updated_at).filter(Boolean)
    if (timestamps.length > 0) {
      const latest = timestamps.reduce((a, b) => (a > b ? a : b))
      lastActivityMap.set(chart.id, latest)
    }

    if (rows.some((r) => r.status === 'in_progress')) {
      inActiveBuildSet.add(chart.id)
    }

    // Build layer pips in Brahma layer order.
    const pips: import('@/lib/roster/types').LayerPip[] = BRAHMA_LAYER_ORDER.map((brahmaLayer) => {
      const row = rows.find((r) => PYRAMID_TO_BRAHMA[`${r.layer}:${r.sublayer}`] === brahmaLayer)
      if (!row) return { layer: brahmaLayer, state: 'dim' as const }
      if (row.status === 'complete') return { layer: brahmaLayer, state: 'lit' as const }
      if (row.status === 'in_progress') return { layer: brahmaLayer, state: 'building' as const }
      return { layer: brahmaLayer, state: 'dim' as const }
    })
    layerPipsMap.set(chart.id, pips)
  }

  const consumedToday = await fetchConsumedTodayCount(chartIds)

  const chartsWithMeta: ChartWithMeta[] = charts.map((c) => ({
    ...c,
    pyramidPercent: pyramidPercents.get(c.id) ?? 0,
    lastLayerActivity: lastActivityMap.get(c.id) ?? null,
    buildState: buildStateMap.get(c.id) ?? null,
    layerPips: layerPipsMap.get(c.id) ?? BRAHMA_LAYER_ORDER.map((layer) => ({ layer, state: 'dim' as const })),
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
            Roster
            <span className="opacity-55 text-[#d4af37] font-serif ml-1">॥</span>
          </h1>
          {role === 'super_admin' && (
            <Link href="/clients/new" className="brand-cta inline-flex items-center gap-1.5 rounded-lg px-5 py-2.5 text-sm" data-testid="new-client-link">
              <span className="text-base leading-none">+</span>
              New Client
            </Link>
          )}
        </div>
        <Suspense>
          <ClientRoster charts={chartsWithMeta} stats={stats} />
        </Suspense>
        {role === 'super_admin' && (
          <div className="mt-6">
            <BuildsInProgressCard />
          </div>
        )}
      </div>
    </div>
  )
}
