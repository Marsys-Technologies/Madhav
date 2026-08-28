import { Suspense } from 'react'
import { query } from '@/lib/db/client'
import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shared/AppShell'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'

// V3-E-019: this route used to carry its own `chart.client_id !== user.uid`
// check — the exact inline model `authorizeChartAccess` (Unit 2c) says it
// replaces. That model consults neither `charts.owner_id` nor `chart_grants`,
// so it bounced view-grantees the parent `clients/[id]/layout.tsx` guard had
// already admitted, while admitting principals matching only the legacy
// `client_id` column that the canonical model denies. Converged onto
// resolveChartPageAccess, on the same `permission === 'deny'` bar the parent
// layout uses.
export default async function TimelineLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{ name: string }>('SELECT name FROM charts WHERE id=$1', [id])
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  return (
    <AppShell
      user={access.user}
      profile={{ role: access.role === 'super_admin' ? 'super_admin' : 'guest', status: 'active' }}
      breadcrumb={[
        { label: 'Roster', href: '/dashboard' },
        { label: chart.name ?? id, href: `/clients/${id}` },
        { label: 'Timeline', href: `/clients/${id}/timeline`, current: true },
      ]}
    >
      <Suspense>{children}</Suspense>
    </AppShell>
  )
}
