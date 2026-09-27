/**
 * Dashboard role-gating tests — Unit 3.consult_nav Commit 1.
 *
 * AC.1 (partial): guest session sees only owned + granted charts;
 *                 super-admin sees all + admin surfaces.
 * AC.4 (partial): no tier/depth selector anywhere — asserted by absence.
 *
 * Mount strategy: invoke the page's default export (an async server function)
 * with mocked db/auth, then render the JSX result into jsdom.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'

vi.mock('server-only', () => ({}))

const { mockQuery, mockGetServerUser, mockRedirect } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
  mockRedirect: vi.fn((_url: string) => {
    throw new Error('NEXT_REDIRECT')
  }),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('next/navigation', () => ({
  redirect: mockRedirect,
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/dashboard',
}))

vi.mock('@/lib/roster/stats', () => ({
  fetchConsumedTodayCount: vi.fn(async () => 0),
}))

// Mock the ClientRoster — it's a heavy client component; we only care here
// that the dashboard page selects the right charts and passes them through.
vi.mock('@/components/dashboard/ClientRoster', () => ({
  ClientRoster: ({
    charts,
    stats,
  }: {
    charts: Array<{ id: string; readiness?: { state: string; percent: number }; pyramidPercent?: number }>
    stats?: { inActiveBuild: number }
  }) => (
    <div data-testid="roster" data-in-active-build={stats?.inActiveBuild}>
      {charts.map((c) => (
        <div
          key={c.id}
          data-testid="chart-row"
          data-chart-id={c.id}
          data-readiness={c.readiness?.state}
          data-readiness-percent={c.readiness?.percent}
          data-pyramid-percent={c.pyramidPercent}
        />
      ))}
    </div>
  ),
}))

vi.mock('@/components/brand/Navagraha', () => ({
  Navagraha: () => null,
}))

vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}))

import DashboardPage from '../page'
import { visibleNavItems, isAdminSurface, normalizeRole } from '@/components/nav/role-gates'

const SUPER_ADMIN_UID = 'admin-uid'
const GUEST_UID = 'guest-uid'

function setUser(uid: string) {
  mockGetServerUser.mockResolvedValue({ uid, email: `${uid}@test` })
}

function setProfile(role: 'super_admin' | 'guest') {
  mockQuery.mockImplementationOnce(async () => ({
    rows: [{ id: 'x', role, name: null, username: null, email: null, status: 'active' }],
  }))
}

function setCharts(rows: Array<{ id: string }>) {
  mockQuery.mockImplementationOnce(async () => ({ rows }))
}

function setLayers(rows: unknown[] = []) {
  mockQuery.mockImplementationOnce(async () => ({ rows }))
}

function setBuilds(rows: unknown[] = []) {
  mockQuery.mockImplementationOnce(async () => ({ rows }))
}

beforeEach(() => {
  mockQuery.mockReset()
  // Queries not queued by a test (e.g. the readiness resolver's latest-full-rebuild
  // read) resolve empty.
  mockQuery.mockResolvedValue({ rows: [] })
  mockGetServerUser.mockReset()
  mockRedirect.mockClear()
})

describe('Dashboard — role-gated roster (AC.1)', () => {
  it('redirects to /login when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    await expect(DashboardPage()).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('super_admin sees ALL charts via SELECT * FROM charts', async () => {
    setUser(SUPER_ADMIN_UID)
    setProfile('super_admin')
    setCharts([
      { id: 'chart-a' },
      { id: 'chart-b' },
      { id: 'chart-c' },
    ])
    setLayers([])
    setBuilds([])

    const jsx = await DashboardPage()
    const { getAllByTestId } = render(jsx)

    expect(getAllByTestId('chart-row')).toHaveLength(3)

    // The 2nd query (the charts fetch) should be the unfiltered admin path.
    const chartFetchCall = mockQuery.mock.calls[1]
    expect(chartFetchCall[0]).toMatch(/SELECT \* FROM charts ORDER BY created_at/)
    expect(chartFetchCall[1]).toEqual([])
  })

  it('guest sees owned + granted charts only — filtered SQL with EXISTS chart_grants', async () => {
    setUser(GUEST_UID)
    setProfile('guest')
    setCharts([{ id: 'owned-1' }, { id: 'granted-1' }])
    setLayers([])
    setBuilds([])

    const jsx = await DashboardPage()
    const { getAllByTestId } = render(jsx)

    expect(getAllByTestId('chart-row')).toHaveLength(2)

    const chartFetchCall = mockQuery.mock.calls[1]
    expect(chartFetchCall[0]).toMatch(/owner_id\s*=\s*\$1/)
    expect(chartFetchCall[0]).toMatch(/chart_grants/)
    expect(chartFetchCall[0]).toMatch(/EXISTS/)
    expect(chartFetchCall[1]).toEqual([GUEST_UID])
  })

  it('guest with EXACTLY ONE chart is NOT auto-redirected to /consume', async () => {
    setUser(GUEST_UID)
    setProfile('guest')
    setCharts([{ id: 'only-one' }])
    setLayers([])
    setBuilds([])

    const jsx = await DashboardPage()
    expect(mockRedirect).not.toHaveBeenCalled()

    const { getAllByTestId } = render(jsx)
    expect(getAllByTestId('chart-row')).toHaveLength(1)
  })

  it('guest with ZERO charts is NOT redirected to /login — sees empty roster', async () => {
    setUser(GUEST_UID)
    setProfile('guest')
    setCharts([])
    setLayers([])

    const jsx = await DashboardPage()
    expect(mockRedirect).not.toHaveBeenCalled()
    const { queryAllByTestId } = render(jsx)
    expect(queryAllByTestId('chart-row')).toHaveLength(0)
  })

  it('guest role uses filtered SQL (owned + granted charts)', async () => {
    setUser(GUEST_UID)
    setProfile('guest')
    setCharts([{ id: 'c1' }])
    setLayers([])
    setBuilds([])

    await DashboardPage()
    const chartFetchCall = mockQuery.mock.calls[1]
    expect(chartFetchCall[0]).toMatch(/chart_grants/)
    expect(chartFetchCall[1]).toEqual([GUEST_UID])
  })

  it('only super_admin sees the "New Client" CTA', async () => {
    setUser(SUPER_ADMIN_UID)
    setProfile('super_admin')
    setCharts([])
    setLayers([])

    const jsx = await DashboardPage()
    const { container } = render(jsx)
    expect(container.querySelector('[data-testid="new-client-link"]')).not.toBeNull()

  })

  it('guest does NOT see "New Client" CTA', async () => {
    setUser(GUEST_UID)
    setProfile('guest')
    setCharts([{ id: 'x' }])
    setLayers([])
    setBuilds([])

    const jsx = await DashboardPage()
    const { container } = render(jsx)
    expect(container.querySelector('[data-testid="new-client-link"]')).toBeNull()
  })

  it('dashboard-root carries role attribute for downstream assertions', async () => {
    setUser(GUEST_UID)
    setProfile('guest')
    setCharts([])
    setLayers([])

    const jsx = await DashboardPage()
    const { container } = render(jsx)
    const root = container.querySelector('[data-testid="dashboard-root"]')
    expect(root?.getAttribute('data-role')).toBe('guest')

  })
})

describe('Dashboard — shared readiness authority (Jātaka Task 1)', () => {
  it('derives each chart readiness from the shared resolver, never pyramid_layers', async () => {
    setUser(SUPER_ADMIN_UID)
    setProfile('super_admin')
    setCharts([{ id: 'chart-a' }, { id: 'chart-b' }])
    setLayers([
      { chart_id: 'chart-a', asset_id: 'ga_positions', state: 'lit', rows_written: 9, last_built_at: '2026-09-01T00:00:00Z' },
    ])
    setBuilds([
      { id: 'run-b', chart_id: 'chart-b', state: 'failed', action: 'rebuild', last_error: 'JOB_DISPATCH_FAILED: spawn', created_at: '2026-09-02T00:00:00Z', started_at: null, ended_at: null },
    ])

    const jsx = await DashboardPage()
    const { getAllByTestId, getByTestId } = render(jsx)
    const rows = getAllByTestId('chart-row')
    const a = rows.find((r) => r.dataset.chartId === 'chart-a')!
    const b = rows.find((r) => r.dataset.chartId === 'chart-b')!
    expect(a.dataset.readiness).toBe('partially-built')
    expect(a.dataset.readinessPercent).toBe(a.dataset.pyramidPercent)
    expect(b.dataset.readiness).toBe('needs-rebuild')
    expect(b.dataset.readinessPercent).toBe('0')
    expect(getByTestId('roster').dataset.inActiveBuild).toBe('0')

    for (const [sql] of mockQuery.mock.calls) {
      if (typeof sql === 'string') expect(sql).not.toMatch(/pyramid_layers/)
    }
    const runSql = mockQuery.mock.calls.map(([s]) => s).find((s) => typeof s === 'string' && s.includes('build_runs')) as string
    // Latest run regardless of state — a failed dispatch must be visible, not filtered out.
    expect(runSql).not.toMatch(/r\.state IN/)
  })

  it('counts charts whose shared readiness is building as in active build', async () => {
    setUser(SUPER_ADMIN_UID)
    setProfile('super_admin')
    setCharts([{ id: 'chart-a' }, { id: 'chart-b' }])
    setLayers([])
    setBuilds([
      { id: 'run-a', chart_id: 'chart-a', state: 'running', action: 'rebuild', last_error: null, created_at: '2026-09-02T00:00:00Z', started_at: null, ended_at: null },
    ])
    const { getByTestId } = render(await DashboardPage())
    expect(getByTestId('roster').dataset.inActiveBuild).toBe('1')
  })
})

describe('Nav role-gates (pure helper)', () => {
  it('keeps Observatory out of the left sidebar because it lives inside Cockpit', () => {
    const items = visibleNavItems('super_admin')

    expect(items.find((item) => item.key === 'aiops')).toBeUndefined()
    expect(items.find((item) => item.key === 'cockpit')?.href).toBe('/cockpit')
  })

  it('super_admin sees Cockpit and the remaining top-level admin surfaces', () => {
    const keys = visibleNavItems('super_admin').map((i) => i.key)
    expect(keys).toEqual(['roster', 'panchang', 'cockpit', 'audit', 'performance', 'admin'])
  })

  it('guest sees only Roster + Panchang — no admin surfaces', () => {
    const items = visibleNavItems('guest')
    const keys = items.map((i) => i.key)
    expect(keys).toEqual(['roster', 'panchang'])
    expect(items.every((i) => !i.admin)).toBe(true)
  })

  it('legacy "client" role is normalized to guest', () => {
    expect(normalizeRole('client')).toBe('guest')
    expect(normalizeRole(null)).toBe('guest')
    expect(normalizeRole(undefined)).toBe('guest')
    expect(normalizeRole('super_admin')).toBe('super_admin')
  })

  it('admin surfaces are correctly tagged', () => {
    expect(isAdminSurface('/cockpit')).toBe(true)
    expect(isAdminSurface('/audit')).toBe(true)
    expect(isAdminSurface('/admin')).toBe(true)
    expect(isAdminSurface('/information/atlas')).toBe(true)
    expect(isAdminSurface('/dashboard')).toBe(false)
    expect(isAdminSurface('/panchang')).toBe(false)
  })

  it('AC.4 — no tier/depth selector mentioned in NAV_ITEMS', () => {
    const items = visibleNavItems('super_admin')
    for (const item of items) {
      expect(item.label.toLowerCase()).not.toMatch(/tier|depth/)
      expect(item.href).not.toMatch(/tier|depth/)
    }
  })
})
