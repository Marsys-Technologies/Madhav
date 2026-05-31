/**
 * Per-chart page authorization tests — Unit 3.consult_nav Commit 2.
 *
 * AC.1 (per-chart): non-granted chart 403s (redirect); granted (view-only)
 *      chart shows no Build button; super-admin sees Build.
 * AC.2: Chart switcher persists + reflects chart_id in URL.
 * AC.4: No tier/depth selector mounted anywhere.
 *
 * Mounts each page's default-exported async server function with mocked
 * db/auth + permission resolver.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, fireEvent } from '@testing-library/react'

vi.mock('server-only', () => ({}))

const { mockQuery, mockResolveAccess, mockRedirect, mockGetServerUser, mockListConversations, mockFetchBuildState, mockGetForensicSnapshot, mockConfigService, mockListReports } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockResolveAccess: vi.fn(),
  mockRedirect: vi.fn((_url: string) => {
    throw new Error('NEXT_REDIRECT')
  }),
  mockGetServerUser: vi.fn(),
  mockListConversations: vi.fn(async () => []),
  mockFetchBuildState: vi.fn(async () => ({
    generated_at: '2026-05-28T00:00:00Z',
    macro_phase: { id: 'm5', macro_arc: [] },
    current_brief: null,
    mirror_pairs: [],
  })),
  mockGetForensicSnapshot: vi.fn(async () => ({ ascendant: null, planets: [] })),
  mockConfigService: { getFlag: vi.fn(() => false) },
  mockListReports: vi.fn(async () => ({ rows: [] })),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))
vi.mock('next/navigation', () => ({
  redirect: mockRedirect,
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/clients/test-chart',
  useSearchParams: () => new URLSearchParams(),
}))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/conversations', () => ({ listConversations: mockListConversations }))
vi.mock('@/lib/build/dataSource', () => ({ fetchBuildState: mockFetchBuildState }))
vi.mock('@/lib/forensic/snapshot', () => ({ getForensicSnapshot: mockGetForensicSnapshot }))
vi.mock('@/lib/config/index', () => ({ configService: mockConfigService }))

// Stub the v2 cockpit shell — not under test here.
vi.mock('@/components/cockpit/CockpitShell', () => ({
  CockpitShell: ({ chartId }: { chartId: string }) => (
    <div data-testid="cockpit-shell" data-chart-id={chartId} />
  ),
}))
vi.mock('@/components/consume/ConsumeChat', () => ({
  ConsumeChat: ({ chartId }: { chartId: string }) => (
    <div data-testid="consume-chat-mock" data-chart-id={chartId} />
  ),
}))
vi.mock('@/components/profile/ChartHero', () => ({ ChartHero: () => null }))
vi.mock('@/components/profile/ProfileSideRail', () => ({ ProfileSideRail: () => null }))
vi.mock('@/components/build/JourneyStrip', () => ({ JourneyStrip: () => null }))
vi.mock('@/components/profile/RoomCard', () => ({
  RoomCard: ({ title, cta, children }: { title: string; cta: { href: string; label: string }; children?: React.ReactNode }) => (
    <div data-testid="room-card" data-title={title}>
      <a href={cta.href} data-testid="room-card-cta">{cta.label}</a>
      {children}
    </div>
  ),
}))
vi.mock('@/components/shared/ZoneRoot', () => ({
  ZoneRoot: ({ children, ...rest }: { children: React.ReactNode } & Record<string, unknown>) => (
    <div {...rest}>{children}</div>
  ),
}))

const TEST_CHART_ID = 'test-chart'

function setAccess(permission: 'all' | 'view' | 'deny', role: 'super_admin' | 'guest' = 'guest') {
  mockResolveAccess.mockResolvedValue({
    user: { uid: 'u1', email: 'u@test' },
    role,
    permission,
    canBuild: permission === 'all',
  })
}

beforeEach(() => {
  mockQuery.mockReset()
  mockResolveAccess.mockReset()
  mockRedirect.mockClear()
  mockGetServerUser.mockReset()
})

// ── Profile page ────────────────────────────────────────────────────────────

describe('clients/[id] Profile page — access control + nav hub', () => {
  it('redirects to /login when no session', async () => {
    mockResolveAccess.mockResolvedValue(null)
    const { default: ClientPage } = await import('../[id]/page')
    await expect(ClientPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('AC.1 — non-granted chart (permission=deny) redirects to /dashboard (effective 403)', async () => {
    setAccess('deny')
    mockQuery.mockResolvedValue({ rows: [{ id: TEST_CHART_ID, name: 'X' }] })
    const { default: ClientPage } = await import('../[id]/page')
    await expect(ClientPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/dashboard')
  })

  it('AC.1 — granted guest (permission=view) sees Profile WITHOUT Build Room', async () => {
    setAccess('view', 'guest')
    // chart fetch + (canBuild=false → skipped pyramid+manifest fetches) + recent-conversations
    mockQuery
      .mockResolvedValueOnce({ rows: [{ id: TEST_CHART_ID, name: 'Chart', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'owner-x' }] })
      .mockResolvedValueOnce({ rows: [] })
    const { default: ClientPage } = await import('../[id]/page')
    const jsx = await ClientPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })
    const { container, queryByTestId, getByTestId } = render(jsx)
    expect(queryByTestId('build-room-card')).toBeNull()
    expect(getByTestId('consult-room-card')).toBeTruthy()
    expect(getByTestId('panchang-room-card')).toBeTruthy()
    expect(container.querySelector('[data-permission="view"]')).not.toBeNull()
  })

  it('AC.1 — super_admin (permission=all) sees Build Room', async () => {
    setAccess('all', 'super_admin')
    mockQuery
      .mockResolvedValueOnce({ rows: [{ id: TEST_CHART_ID, name: 'Chart', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'admin-uid' }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ layer: 'L1', sublayer: 'A', status: 'complete' }] })
      .mockResolvedValueOnce({ rows: [{ build_id: 'b1', promoted_at: '2026-05-28T00:00:00Z' }] })
    const { default: ClientPage } = await import('../[id]/page')
    const jsx = await ClientPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })
    const { getByTestId } = render(jsx)
    expect(getByTestId('build-room-card')).toBeTruthy()
    expect(getByTestId('consult-room-card')).toBeTruthy()
    expect(getByTestId('panchang-room-card')).toBeTruthy()
  })

  it('AC.1 — owner guest (permission=all on their own chart) sees Build Room', async () => {
    setAccess('all', 'guest')
    mockQuery
      .mockResolvedValueOnce({ rows: [{ id: TEST_CHART_ID, name: 'Chart', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'guest-uid' }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
    const { default: ClientPage } = await import('../[id]/page')
    const jsx = await ClientPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })
    const { getByTestId } = render(jsx)
    expect(getByTestId('build-room-card')).toBeTruthy()
  })
})

// ── Build page ──────────────────────────────────────────────────────────────

describe('clients/[id]/build — access control', () => {
  it('redirects to /login when no session', async () => {
    mockResolveAccess.mockResolvedValue(null)
    const { default: BuildPage } = await import('../[id]/build/page')
    await expect(BuildPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('AC.1 — view-only grantee CANNOT enter /build (redirected to /clients/[id])', async () => {
    setAccess('view', 'guest')
    const { default: BuildPage } = await import('../[id]/build/page')
    await expect(BuildPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith(`/clients/${TEST_CHART_ID}`)
  })

  it('AC.1 — super_admin can enter /build', async () => {
    setAccess('all', 'super_admin')
    mockQuery
      .mockResolvedValueOnce({ rows: [{ layer: 'L1', sublayer: 'A', status: 'complete' }] })
      .mockResolvedValueOnce({ rows: [{ id: TEST_CHART_ID, name: 'Chart' }] })
    const { default: BuildPage } = await import('../[id]/build/page')
    const jsx = await BuildPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })
    const { getByTestId } = render(jsx)
    expect(getByTestId('cockpit-shell').getAttribute('data-chart-id')).toBe(TEST_CHART_ID)
    expect(getByTestId('build-page-root').getAttribute('data-permission')).toBe('all')
  })
})

// ── Consult page ────────────────────────────────────────────────────────────

describe('clients/[id]/consult — access control', () => {
  it('redirects to /login when no session', async () => {
    mockResolveAccess.mockResolvedValue(null)
    const { default: ConsultPage } = await import('../[id]/consult/page')
    await expect(
      ConsultPage({
        params: Promise.resolve({ id: TEST_CHART_ID }),
        searchParams: Promise.resolve({}),
      }),
    ).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('AC.1 — non-granted (deny) chart redirects to /dashboard', async () => {
    setAccess('deny')
    const { default: ConsultPage } = await import('../[id]/consult/page')
    await expect(
      ConsultPage({
        params: Promise.resolve({ id: TEST_CHART_ID }),
        searchParams: Promise.resolve({}),
      }),
    ).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/dashboard')
  })

  it('AC.1 — view-only grantee CAN enter /consult', async () => {
    setAccess('view', 'guest')
    mockQuery
      .mockResolvedValueOnce({ rows: [{ name: 'Chart', birth_date: '1984-02-05', birth_place: 'Bhubaneswar', client_id: 'owner-x' }] })
      .mockResolvedValueOnce({ rows: [] })
    const { default: ConsultPage } = await import('../[id]/consult/page')
    const jsx = await ConsultPage({
      params: Promise.resolve({ id: TEST_CHART_ID }),
      searchParams: Promise.resolve({}),
    })
    const { getByTestId } = render(jsx)
    expect(getByTestId('consume-chat-mock').getAttribute('data-chart-id')).toBe(TEST_CHART_ID)
    expect(getByTestId('consult-page-root').getAttribute('data-permission')).toBe('view')
  })
})

// ── Panchang per-chart page ─────────────────────────────────────────────────

describe('clients/[id]/panchang — personalized panchang', () => {
  it('redirects to /login when no session', async () => {
    mockResolveAccess.mockResolvedValue(null)
    const { default: PanchangPage } = await import('../[id]/panchang/page')
    await expect(PanchangPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('AC.1 — non-granted (deny) chart redirects to /dashboard', async () => {
    setAccess('deny')
    const { default: PanchangPage } = await import('../[id]/panchang/page')
    await expect(PanchangPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/dashboard')
  })

  it('AC.1 — view-only grantee CAN view personalized panchang', async () => {
    setAccess('view', 'guest')
    mockQuery.mockResolvedValueOnce({ rows: [{ name: 'Chart', birth_place: 'Bhubaneswar' }] })
    const { default: PanchangPage } = await import('../[id]/panchang/page')
    const jsx = await PanchangPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })
    const { getByTestId } = render(jsx)
    expect(getByTestId('chart-panchang-root').getAttribute('data-permission')).toBe('view')
    expect(getByTestId('chart-panchang-root').getAttribute('data-chart-id')).toBe(TEST_CHART_ID)
  })
})

// ── Chart switcher — pure helper + interaction ──────────────────────────────

describe('ChartSwitcher — switching logic (AC.2)', () => {
  it('computeSwitchHref — root chart page', async () => {
    const { computeSwitchHref } = await import('@/components/nav/ChartSwitcher')
    expect(computeSwitchHref('/clients/old', 'new')).toBe('/clients/new')
  })

  it('computeSwitchHref — preserves Profile suffix', async () => {
    const { computeSwitchHref } = await import('@/components/nav/ChartSwitcher')
    expect(computeSwitchHref('/clients/old/panchang', 'new')).toBe('/clients/new/panchang')
  })

  it('computeSwitchHref — strips conversationId from /consult/<conv> (no silent mid-conversation switch)', async () => {
    const { computeSwitchHref } = await import('@/components/nav/ChartSwitcher')
    expect(computeSwitchHref('/clients/old/consult/conv-123', 'new')).toBe('/clients/new/consult')
  })

  it('computeSwitchHref — strips conversationId from /build/<conv>', async () => {
    const { computeSwitchHref } = await import('@/components/nav/ChartSwitcher')
    expect(computeSwitchHref('/clients/old/build/conv-9', 'new')).toBe('/clients/new/build')
  })

  it('computeSwitchHref — strips conversationId from /consume/<conv>', async () => {
    const { computeSwitchHref } = await import('@/components/nav/ChartSwitcher')
    expect(computeSwitchHref('/clients/old/consume/cv', 'new')).toBe('/clients/new/consume')
  })

  it('computeSwitchHref — non-chart path falls back to /clients/<new>', async () => {
    const { computeSwitchHref } = await import('@/components/nav/ChartSwitcher')
    expect(computeSwitchHref('/dashboard', 'new')).toBe('/clients/new')
  })

  it('AC.2 — switcher persists selection to localStorage on choose', async () => {
    const { ChartSwitcher, LAST_CHART_STORAGE_KEY } = await import('@/components/nav/ChartSwitcher')
    const { getByTestId, getAllByTestId } = render(
      <ChartSwitcher
        currentChartId="a"
        charts={[
          { id: 'a', name: 'Alpha' },
          { id: 'b', name: 'Beta' },
        ]}
      />
    )
    // Open the dropdown
    fireEvent.click(getByTestId('chart-switcher-trigger'))
    const options = getAllByTestId('chart-switcher-option')
    expect(options).toHaveLength(2)
    // Click the non-current one — persistence side effect.
    const beta = options.find((el) => el.getAttribute('data-chart-id') === 'b')!
    fireEvent.click(beta)
    expect(localStorage.getItem(LAST_CHART_STORAGE_KEY)).toBe('b')
  })

  it('AC.2 — clicking the SAME chart is a no-op (no localStorage write, no nav)', async () => {
    const { ChartSwitcher, LAST_CHART_STORAGE_KEY } = await import('@/components/nav/ChartSwitcher')
    localStorage.removeItem(LAST_CHART_STORAGE_KEY)
    const { getByTestId, getAllByTestId } = render(
      <ChartSwitcher
        currentChartId="a"
        charts={[
          { id: 'a', name: 'Alpha' },
          { id: 'b', name: 'Beta' },
        ]}
      />
    )
    fireEvent.click(getByTestId('chart-switcher-trigger'))
    const alpha = getAllByTestId('chart-switcher-option').find(
      (el) => el.getAttribute('data-chart-id') === 'a',
    )!
    fireEvent.click(alpha)
    expect(localStorage.getItem(LAST_CHART_STORAGE_KEY)).toBeNull()
  })

  it('AC.4 — switcher renders without any tier/depth selector', async () => {
    const { ChartSwitcher } = await import('@/components/nav/ChartSwitcher')
    const { container } = render(
      <ChartSwitcher currentChartId="a" charts={[{ id: 'a', name: 'Alpha' }]} />
    )
    expect(container.textContent?.toLowerCase()).not.toMatch(/tier|depth/)
  })
})
