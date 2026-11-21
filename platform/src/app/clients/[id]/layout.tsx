import { readChartTitleName, readChartPageName } from '@/lib/charts/pageIdentity'
import { readAdminSwitcherCharts, readLegacyGuestSwitcherCharts } from '@/lib/roster/pageIdentity'
import type { Metadata } from 'next'
import { headers } from 'next/headers'
import { redirect } from 'next/navigation'
import { JourneyShell } from '@/components/journey1/JourneyShell'
import { AppShell } from '@/components/shared/AppShell'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { CHART_RETURN_PATH_HEADER, safeNextPath } from '@/lib/auth/safe_next'
import { ConditionalChartSwitcherBar } from '@/components/nav/ConditionalChartSwitcherBar'

// V3-E-018: generateMetadata has no guaranteed request-scoped session by
// default, so it must resolve access itself via the SAME resolveChartPageAccess
// path the layout body uses below — never a raw, unguarded query — before it
// may put the chart `name` (PII) into the <title>. This layout is the parent of
// every sibling chart route, so an unguarded read here leaked the name on all
// of them. The bar matches the layout body's own bar (`permission !== 'deny'`),
// not the stricter canBuild bar V3-E-007 needed: a chart_grants view-grantee
// legitimately sees this name in the breadcrumb already.
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access || access.permission === 'deny') {
    return { title: 'Chart — MARSYS-JIS' }
  }
  const result = await readChartTitleName(id)
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
  if (!access) {
    const next = safeNextPath((await headers()).get(CHART_RETURN_PATH_HEADER))
    const chartPath = `/clients/${id}`
    redirect(next && (next === chartPath || next.startsWith(`${chartPath}/`))
      ? `/login?next=${encodeURIComponent(next)}`
      : '/login')
  }

  // 2c-driven authz: 'deny' on a non-granted chart → redirect (effective 403
  // from the user's perspective; the chart simply does not exist for them).
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await readChartPageName(id)
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  // For the switcher dropdown: list every chart the principal can see.
  const switcherCharts = access.role === 'super_admin'
    ? (
        await readAdminSwitcherCharts()
      ).rows
    : (
        await readLegacyGuestSwitcherCharts(access.user.uid)
      ).rows

  return (
    <JourneyShell user={access.user} role={access.role} chartId={id} fallback={<ZoneRoot zone="ink">
      <AppShell
        user={access.user}
        profile={{ role: access.role === 'super_admin' ? 'super_admin' : 'guest', status: 'active' }}
        breadcrumb={[
          { label: 'Birth Charts', href: '/dashboard' },
          { label: chart.name ?? id, href: `/clients/${id}`, current: true },
        ]}
      >
        <div
          data-testid="chart-page-frame"
          data-permission={access.permission}
          data-chart-id={id}
          className="has-[[data-testid=v2-chat-shell]]:flex has-[[data-testid=v2-chat-shell]]:h-full has-[[data-testid=v2-chat-shell]]:min-h-0 has-[[data-testid=v2-chat-shell]]:flex-1 has-[[data-testid=v2-chat-shell]]:flex-col has-[[data-testid=historical-reading]]:flex has-[[data-testid=historical-reading]]:h-full has-[[data-testid=historical-reading]]:min-h-0 has-[[data-testid=historical-reading]]:flex-1 has-[[data-testid=historical-reading]]:flex-col"
        >
          <ConditionalChartSwitcherBar
            currentChartId={id}
            charts={switcherCharts}
          />
          {children}
        </div>
      </AppShell>
    </ZoneRoot>}>{children}</JourneyShell>
  )
}
