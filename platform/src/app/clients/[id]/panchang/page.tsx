import { Suspense } from 'react'
import Link from 'next/link'
import { redirect } from 'next/navigation'
import { format } from 'date-fns'
import { query } from '@/lib/db/client'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { ChartNav } from '@/components/journey1/ChartNav'
import { PanchangClientView } from '@/app/panchang/components/PanchangClientView'

export default async function ChartPanchangPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const { rows: [chart] } = await query<{ name: string | null }>('SELECT name FROM charts WHERE id=$1', [id])
  if (!chart) redirect('/dashboard')

  return (
    <div data-testid="chart-panchang-root" data-permission={access.permission} data-chart-id={id}>
      <ChartNav chartId={id} canBuild={access.canBuild} active="almanac" />
      <header className="mx-auto max-w-4xl px-4 py-4">
        <h1 className="text-xl font-serif font-semibold">Personal Almanac</h1>
        <p className="text-sm text-muted-foreground">
          Daily timing for the selected location, in India Standard Time (UTC+05:30).
          Chart context: {chart.name ?? 'this chart'}.
        </p>
        <div className="mt-2 flex flex-wrap gap-4 text-sm">
          <Link href={`/clients/${id}/pariprashna`} className="underline">Open Consultation</Link>
          <Link href="/panchang" className="underline">General Almanac</Link>
        </div>
      </header>
      <Suspense fallback={<p role="status">Loading almanac…</p>}>
        <PanchangClientView
          key={id}
          initialData={null}
          initialDate={format(new Date(), 'yyyy-MM-dd')}
          fixedChartId={id}
        />
      </Suspense>
    </div>
  )
}
