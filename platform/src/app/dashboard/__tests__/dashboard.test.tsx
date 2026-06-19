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
  ClientRoster: ({ charts }: { charts: Array<{ id: string }> }) => (
    <div data-testid="roster">
      {charts.map((c) => (
        <div key={c.id} data-testid="chart-row" data-chart-id={c.id} />
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

describe('Nav role-gates (pure helper)', () => {
  it('super_admin sees Roster + Panchang + all admin surfaces', () => {
    const keys = visibleNavItems('super_admin').map((i) => i.key)
    expect(keys).toEqual(
      expect.arrayContaining(['roster', 'panchang', 'cockpit', 'audit', 'aiops', 'performance', 'admin'])
    )
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
