import type { Metadata } from 'next'
import { query } from '@/lib/db/client'
import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shared/AppShell'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { ConditionalChartSwitcherBar } from '@/components/nav/ConditionalChartSwitcherBar'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id } = await params
  const result = await query<{ name: string }>('SELECT name FROM charts WHERE id=$1', [id])
  const name = result.rows[0]?.name
  return { title: name ? `${name} — MARSYS-JIS` : 'Chart — MARSYS-JIS' }
}

export default async function ClientLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')

  // 2c-driven authz: 'deny' on a non-granted chart → redirect (effective 403
  // from the user's perspective; the chart simply does not exist for them).
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{ name: string | null }>(
    'SELECT name FROM charts WHERE id=$1',
    [id]
  )
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  // For the switcher dropdown: list every chart the principal can see.
  const switcherCharts = access.role === 'super_admin'
    ? (
        await query<{ id: string; name: string | null }>(
          'SELECT id, name FROM charts ORDER BY name NULLS LAST, created_at DESC LIMIT 100',
          []
        )
      ).rows
    : (
        await query<{ id: string; name: string | null }>(
          `SELECT c.id, c.name FROM charts c
           WHERE c.owner_id = $1
              OR c.client_id = $1
              OR EXISTS (SELECT 1 FROM chart_grants g WHERE g.chart_id = c.id AND g.principal_id = $1)
           ORDER BY c.name NULLS LAST, c.created_at DESC LIMIT 100`,
          [access.user.uid]
        )
      ).rows

  return (
    <ZoneRoot zone="ink">
      <AppShell
        user={access.user}
        profile={{ role: access.role === 'super_admin' ? 'super_admin' : 'client', status: 'active' }}
        breadcrumb={[
          { label: 'Roster', href: '/dashboard' },
          { label: chart.name ?? id, href: `/clients/${id}`, current: true },
        ]}
      >
        <div data-testid="chart-page-frame" data-permission={access.permission} data-chart-id={id}>
          <ConditionalChartSwitcherBar
            currentChartId={id}
            charts={switcherCharts}
          />
          {children}
        </div>
      </AppShell>
    </ZoneRoot>
  )
}
