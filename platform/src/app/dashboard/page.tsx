import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { ClientRoster } from '@/components/dashboard/ClientRoster'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { Suspense } from 'react'
import type { Chart } from '@/lib/db/types'
import { fetchConsumedTodayCount } from '@/lib/roster/stats'
import type { ChartWithMeta, RosterStats } from '@/lib/roster/types'
import { PageTitle } from '@/components/journey1/Titles'
import { emptyChartReadiness, getChartReadinessMap } from '@/lib/charts/readiness'
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

  // Readiness (asset_throughput + latest build_runs) and consumed-today depend on
  // chartIds but are independent of each other — run in parallel. Readiness comes
  // from the shared resolver so the directory, workspace and Paripraśna gate agree.
  const [readinessMap, consumedToday] = await Promise.all([
    getChartReadinessMap(chartIds),
    fetchConsumedTodayCount(chartIds),
  ])

  const chartsWithMeta: ChartWithMeta[] = charts.map((c) => {
    const readiness = readinessMap.get(c.id) ?? emptyChartReadiness()
    return {
      ...c,
      readiness,
      pyramidPercent: readiness.percent,
      lastLayerActivity: readiness.lastActivity,
      buildState: null,
      layerPips: readiness.layerPips,
      // BUILD = owner/super_admin only (Phase 2B). View-grantees get canBuild=false → disabled affordance.
      canBuild: role === 'super_admin' || c.owner_id === user.uid,
    }
  })

  const stats: RosterStats = {
    total: charts.length,
    inActiveBuild: chartsWithMeta.filter((c) => c.readiness.state === 'building').length,
    consumedToday,
    predictionsOverdue: 0,
  }

  return (
    <div className="relative min-h-full overflow-hidden" data-testid="dashboard-root" data-role={role}>
      {/* Chart-created toast: shown when ?chart_created=[id] is present in URL */}
      <Suspense>
        <ChartCreatedToast />
      </Suspense>
      <div className="j1-container">
        <div className="flex items-center justify-between mb-6">
          <PageTitle name="charts"/>
          {role === 'super_admin' && (
            <Link href="/clients/new" aria-label="Nava Jātaka (new chart)" className="j1-btn j1-btn-secondary" data-testid="new-client-link">
              <span className="text-base leading-none">+</span>
              <PageTitle name="new" as="span" compact/>
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
