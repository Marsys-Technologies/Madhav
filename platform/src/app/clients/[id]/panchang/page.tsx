import { query } from '@/lib/db/client'
import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'

/**
 * Per-chart Panchang surface (Unit 3.consult_nav, Commit 2).
 *
 * "Personalized" means: the panchang view loads with the chart's birth location
 * as the default reference frame. Today's tithi/vara/nakshatra are still global
 * (panchang is panchang), but the chart context is surfaced so navigation back
 * to Consult preserves the chart_id.
 *
 * Available to permission ∈ {'all', 'view'} — Profile/Consult/Panchang is the
 * granted-guest's read-only triad per Unit 2c.
 */
export default async function ChartPanchangPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{ name: string; birth_place: string | null }>(
    'SELECT name, birth_place FROM charts WHERE id=$1',
    [id]
  )
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  return (
    <div
      className="mx-auto max-w-5xl px-6 py-8"
      data-testid="chart-panchang-root"
      data-permission={access.permission}
      data-chart-id={id}
    >
      <h1 className="text-2xl font-serif text-[var(--brand-gold-cream)] mb-2">
        Panchang
      </h1>
      <p className="text-xs opacity-60 text-[var(--brand-gold)]">
        Personalized for {chart.name ?? 'this chart'}
        {chart.birth_place ? ` — anchored at ${chart.birth_place}` : ''}
      </p>

      <div className="mt-6 space-y-3">
        <a
          href={`/panchang`}
          className="inline-block rounded-md border border-[rgba(212,175,55,0.28)] px-4 py-2 text-sm text-[var(--brand-gold)] hover:bg-[rgba(212,175,55,0.08)]"
          data-testid="open-global-panchang"
        >
          Open daily Panchang
        </a>
        <a
          href={`/clients/${id}/consult`}
          className="ml-3 inline-block rounded-md border border-[rgba(212,175,55,0.28)] px-4 py-2 text-sm text-[var(--brand-gold)] hover:bg-[rgba(212,175,55,0.08)]"
          data-testid="back-to-consult"
        >
          Ask Madhav about today
        </a>
      </div>
    </div>
  )
}
