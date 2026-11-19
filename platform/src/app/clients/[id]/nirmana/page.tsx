import { readPreparationChartName, readPreparationChartIdentity } from '@/lib/charts/pageIdentity'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { CockpitShell } from '@/lib/components/cockpit/v2/CockpitShell'
import { PageTitle } from '@/components/journey1/Titles'
import { ChartNav } from '@/components/journey1/ChartNav'
import styles from '../folio.module.css'

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
  const { rows } = await readPreparationChartName(id).catch(() => ({ rows: [] }))
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
  const { rows: chartRows } = await readPreparationChartIdentity(id).catch(() => ({ rows: [] }))
  const initialChartMeta = chartRows[0] ?? null

  return (
    <div className={`j1-container ${styles.warmWorkspace} ${styles.preparation}`} data-testid="build-page-root" data-permission={access.permission}>
      <nav aria-label="Breadcrumb" className={styles.breadcrumb}>
        <Link href="/dashboard">Birth Charts</Link><span aria-hidden="true">/</span>
        <Link href={`/clients/${id}`}>{initialChartMeta?.subject_name ?? 'Chart'}</Link>
        <span aria-hidden="true">/</span><span>Chart Preparation</span>
      </nav>
      <ChartNav chartId={id} canBuild={access.canBuild} active="preparation" />
      <header className={styles.preparationHeader}>
        <PageTitle name="preparation" />
        <p className="j1-note">
          Each layer builds on the one beneath it. Partial readiness is normal;
          Consultation identifies any additional preparation a question needs.
        </p>
      </header>
      <CockpitShell chartId={id} initialChartMeta={initialChartMeta} variant="preparation" />
    </div>
  )
}
