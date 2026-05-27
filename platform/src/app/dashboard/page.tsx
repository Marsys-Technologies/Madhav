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

export default async function DashboardPage() {
  const user = await getServerUser()
  if (!user) redirect('/login')

  const profileResult = await query(
    'SELECT id, role, name, username, email, status FROM profiles WHERE id=$1',
    [user.uid]
  )
  const profile = (profileResult.rows[0] ?? null) as { id: string; role: string } | null

  // Guests (renamed from 'client' in Unit 2c) go directly to their Consult view.
  // Backwards-compat: until profiles migration 082 applies, also accept legacy 'client'.
  if (profile?.role === 'guest' || profile?.role === 'client') {
    // Unit 2c: prefer owner_id; fall back to legacy client_id during cutover.
    const chartResult = await query(
      'SELECT * FROM charts WHERE owner_id=$1 OR client_id=$1 ORDER BY created_at DESC',
      [user.uid]
    )
    const chart = (chartResult.rows[0] ?? null) as { id: string } | null
    if (chart) redirect(`/clients/${chart.id}/consume`)
    redirect('/login')
  }

  // Super-admin: fetch all charts
  const chartsResult = await query('SELECT * FROM charts ORDER BY created_at DESC', [])
  const charts = chartsResult.rows as unknown as Chart[]

  const chartIds = charts.map((c) => c.id)

  // Fetch pyramid layers (build % + freshness + inActiveBuild)
  const layersResult = chartIds.length > 0
    ? await query(
        'SELECT chart_id, status, MAX(updated_at) AS last_updated FROM pyramid_layers WHERE chart_id = ANY($1::uuid[]) GROUP BY chart_id, status',
        [chartIds]
      )
    : { rows: [] }
  const layerRows = layersResult.rows as unknown as {
    chart_id: string
    status: string
    last_updated: string
  }[]

  // Compute per-chart pyramidPercent, lastLayerActivity, inActiveBuild flag
  const pyramidPercents = new Map<string, number>()
  const lastActivityMap = new Map<string, string>()
  const inActiveBuildSet = new Set<string>()

  for (const chart of charts) {
    const rows = layerRows.filter((r) => r.chart_id === chart.id)
    const complete = rows.filter((r) => r.status === 'complete').length
    pyramidPercents.set(chart.id, Math.round((complete / 6) * 100))

    // Most-recent updated_at across all statuses
    const timestamps = rows.map((r) => r.last_updated).filter(Boolean)
    if (timestamps.length > 0) {
      const latest = timestamps.reduce((a, b) => (a > b ? a : b))
      lastActivityMap.set(chart.id, latest)
    }

    if (rows.some((r) => r.status === 'in_progress')) {
      inActiveBuildSet.add(chart.id)
    }
  }

  // Fetch consumed-today count
  const consumedToday = await fetchConsumedTodayCount(chartIds)

  const chartsWithMeta: ChartWithMeta[] = charts.map((c) => ({
    ...c,
    pyramidPercent: pyramidPercents.get(c.id) ?? 0,
    lastLayerActivity: lastActivityMap.get(c.id) ?? null,
  }))

  const stats: RosterStats = {
    total: charts.length,
    inActiveBuild: inActiveBuildSet.size,
    consumedToday,
    predictionsOverdue: 0, // wired in R5
  }

  return (
    <div className="relative min-h-full overflow-hidden">
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
          <Link href="/clients/new" className="brand-cta inline-flex items-center gap-1.5 rounded-lg px-5 py-2.5 text-sm">
            <span className="text-base leading-none">+</span>
            New Client
          </Link>
        </div>
        <Suspense>
          <ClientRoster charts={chartsWithMeta} stats={stats} />
        </Suspense>
      </div>
    </div>
  )
}
