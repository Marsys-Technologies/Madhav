import { readChartPageName } from '@/lib/charts/pageIdentity'
import { Suspense } from 'react'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { todayISTKey } from '@/lib/build/derive'
import { ChartNav } from '@/components/journey1/ChartNav'
import { PageTitle } from '@/components/journey1/Titles'
import { PanchangClientView } from '@/app/panchang/components/PanchangClientView'
import styles from '../folio.module.css'

export default async function ChartPanchangPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const { rows: [chart] } = await readChartPageName(id)
  if (!chart) redirect('/dashboard')

  return (
    <div className={`${styles.warmWorkspace} ${styles.almanac} j1-container`} data-testid="chart-panchang-root" data-permission={access.permission} data-chart-id={id}>
      <ChartNav chartId={id} canBuild={access.canBuild} active="almanac" />
      <header className={styles.almanacHeader}>
        <PageTitle name="almanac" />
        <p>Chart context: <strong>{chart.name ?? 'this chart'}</strong></p>
        <p>Daily timing for the selected location, in India Standard Time (UTC+05:30).</p>
        <div className={styles.almanacLinks}>
          <Link href={`/clients/${id}/pariprashna`}>Open Consultation</Link>
          <Link href="/panchang">General Almanac</Link>
        </div>
      </header>
      <Suspense fallback={<p role="status">Loading almanac…</p>}>
        <PanchangClientView
          key={id}
          initialData={null}
          initialDate={todayISTKey()}
          fixedChartId={id}
        />
      </Suspense>
    </div>
  )
}
