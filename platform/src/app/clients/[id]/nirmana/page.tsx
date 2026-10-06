import Link from 'next/link'
import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { CockpitShell } from '@/lib/components/cockpit/v2/CockpitShell'
import { query } from '@/lib/db/client'
import { PageTitle } from '@/components/journey1/Titles'
import { ChartNav } from '@/components/journey1/ChartNav'

// Journey 3 reuses the guarded cockpit services with the reviewed preparation layout.

// V3-E-007: generateMetadata has no guaranteed request-scoped session by
// default, so it must resolve access itself via the SAME
// resolveChartPageAccess path the page body uses below — never a raw,
// unguarded query — before it may put subject_name (PII) into the <title>.
// An unauthenticated caller or one without build access on this chart gets a
// generic title; the real name never reaches the response for them.
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access || !access.canBuild) {
    return { title: 'Nirmāṇa — MARSYS-JIS' }
  }
  const { rows } = await query<{ subject_name: string | null }>(
    'SELECT subject_name FROM charts WHERE id=$1',
    [id]
  ).catch(() => ({ rows: [] }))
  const name = rows[0]?.subject_name ?? 'Chart'
  return { title: `Nirmāṇa · ${name} — MARSYS-JIS` }
}

export default async function BuildPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')

  // Deny access only to users with no permission on this chart.
  if (!access.canBuild) redirect(`/clients/${id}`)

  // Prefetch chart metadata server-side so CockpitShell doesn't show "Loading chart…"
  const { rows: chartRows } = await query<{ subject_name: string | null; birth_date: string | null; birth_time: string | null; birth_place: string | null }>(
    'SELECT subject_name, birth_date, birth_time::text, birth_place FROM charts WHERE id=$1',
    [id]
  ).catch(() => ({ rows: [] }))
  const initialChartMeta = chartRows[0] ?? null

  return (
    <div className="j1-container" data-testid="build-page-root" data-permission={access.permission}>
      <nav aria-label="Breadcrumb" className="j1-note" style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
        <Link href="/dashboard">Birth Charts</Link><span aria-hidden="true">/</span>
        <Link href={`/clients/${id}`}>{initialChartMeta?.subject_name ?? 'Chart'}</Link>
        <span aria-hidden="true">/</span><span>Chart Preparation</span>
      </nav>
      <ChartNav chartId={id} canBuild={access.canBuild} active="preparation" />
      <PageTitle name="preparation" />
      <p className="j1-note" style={{ margin: '12px 0 24px', maxWidth: '72ch' }}>
        Each layer builds on the one beneath it. Partial readiness is normal;
        Consultation identifies any additional preparation a question needs.
      </p>
      <CockpitShell chartId={id} initialChartMeta={initialChartMeta} variant="preparation" />
    </div>
  )
}
