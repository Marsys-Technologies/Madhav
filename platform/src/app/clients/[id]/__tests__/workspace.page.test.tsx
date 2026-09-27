/**
 * /clients/[id] — Jātaka chart workspace (Jātaka chart workspace, Task 3).
 *
 * Access control + composition contract: shared readiness (never
 * pyramid_layers), D1 from this chart's own L1 rows (never the canonical
 * snapshot), permission-aware capability deck, viewer-scoped non-archived
 * recent conversations.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render } from '@testing-library/react'

vi.mock('server-only', () => ({}))

const { mockQuery, mockResolveAccess, mockRedirect, mockReadinessMap, mockWorkspaceSummary, mockGetForensicSnapshot } =
  vi.hoisted(() => ({
    mockQuery: vi.fn(),
    mockResolveAccess: vi.fn(),
    mockRedirect: vi.fn(() => {
      throw new Error('NEXT_REDIRECT')
    }),
    mockReadinessMap: vi.fn(),
    mockWorkspaceSummary: vi.fn(),
    mockGetForensicSnapshot: vi.fn(),
  }))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))
vi.mock('next/navigation', () => ({
  redirect: mockRedirect,
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}))
vi.mock('@/lib/forensic/snapshot', () => ({ getForensicSnapshot: mockGetForensicSnapshot }))
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: mockReadinessMap,
  emptyChartReadiness: () => readinessFixture('not-built'),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))
vi.mock('@/lib/charts/workspaceSummary', () => ({ getChartWorkspaceSummary: mockWorkspaceSummary }))
vi.mock('@/components/sharing/SharingPanel', () => ({ SharingPanel: () => null }))
vi.mock('@/components/dialogs/DeleteChartDialog', () => ({ DeleteChartDialog: () => null }))
vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))

const TEST_CHART_ID = 'test-chart'

function readinessFixture(state: string, ganita: 'lit' | 'dim' = 'dim') {
  return {
    state,
    percent: state === 'ready' ? 100 : 0,
    label: state,
    layerPips: [
      { layer: 'brahmagyan', state: 'lit' },
      { layer: 'ganita', state: ganita },
      { layer: 'bodha', state: 'dim' },
      { layer: 'kala', state: 'dim' },
      { layer: 'phala', state: 'dim' },
      { layer: 'mimamsa', state: 'dim' },
    ],
    lastActivity: null,
    activeRunId: null,
    latestRunId: null,
    latestError: null,
  }
}

const EMPTY_SUMMARY = {
  d1: {
    chartId: TEST_CHART_ID,
    lagnaSign: '',
    lagnaDegreeDms: '',
    houses: Array.from({ length: 12 }, (_, i) => ({ house: i + 1, sign: '', planets: [] })),
    topYogas: [],
    currentDasha: null,
    isEmpty: true,
  },
  currentDasha: null,
  confirmedYogas: [],
  flags: [],
}

const CHART_ROW = {
  id: TEST_CHART_ID,
  name: 'Test Native',
  birth_date: '1990-01-02',
  birth_time: '06:30:00',
  birth_place: 'Puri',
  timezone_id: 'Asia/Kolkata',
  owner_id: 'owner-uid',
  client_id: 'owner-uid',
}

function setAccess(permission: 'all' | 'view' | 'deny', role: 'super_admin' | 'guest' = 'guest') {
  mockResolveAccess.mockResolvedValue({ user: { uid: 'viewer-uid' }, role, permission, canBuild: permission === 'all' })
}

function setReadiness(state: string, ganita: 'lit' | 'dim' = 'dim') {
  mockReadinessMap.mockResolvedValue(new Map([[TEST_CHART_ID, readinessFixture(state, ganita)]]))
}

function setQueries(conversations: unknown[] = []) {
  mockQuery.mockImplementation(async (sql?: string) => {
    if (typeof sql !== 'string') return { rows: [] }
    if (sql.includes('FROM charts')) return { rows: [CHART_ROW] }
    if (sql.includes('FROM conversations')) return { rows: conversations }
    return { rows: [] }
  })
}

async function renderPage() {
  const { default: ClientPage } = await import('../page')
  const jsx = await ClientPage({ params: Promise.resolve({ id: TEST_CHART_ID }) })
  const { container } = render(jsx)
  return { html: container.innerHTML, doc: document }
}

const byTestId = (doc: Document, id: string) => doc.querySelector(`[data-testid="${id}"]`)

beforeEach(() => {
  cleanup()
  mockQuery.mockReset()
  mockResolveAccess.mockReset()
  mockRedirect.mockClear()
  mockReadinessMap.mockReset()
  mockWorkspaceSummary.mockReset()
  mockGetForensicSnapshot.mockReset()
  mockWorkspaceSummary.mockResolvedValue(EMPTY_SUMMARY)
  setReadiness('ready', 'lit')
  setQueries()
})

describe('clients/[id] workspace — access control', () => {
  it('redirects to /login when no session', async () => {
    mockResolveAccess.mockResolvedValue(null)
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/login')
  })

  it('redirects a caller without access to /dashboard', async () => {
    setAccess('deny')
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/dashboard')
  })

  it('a view grantee gets Paripraśna and Pañcāṅga but no Nirmāṇa and no secondary actions', async () => {
    setAccess('view')
    const { doc } = await renderPage()
    expect(byTestId(doc, 'build-room-card')).toBeNull()
    expect(byTestId(doc, 'consult-room-card')).not.toBeNull()
    expect(byTestId(doc, 'panchang-room-card')).not.toBeNull()
    expect(doc.querySelector('[data-permission="view"]')).not.toBeNull()
    expect(doc.body.textContent).not.toMatch(/Chart actions/)
  })

  it('an owner gets Nirmāṇa and the chart actions control', async () => {
    setAccess('all')
    const { doc } = await renderPage()
    expect(byTestId(doc, 'build-room-card')?.getAttribute('href')).toBe(`/clients/${TEST_CHART_ID}/nirmana`)
    expect(doc.body.textContent).toMatch(/Chart actions/)
  })
})

describe('clients/[id] workspace — composition', () => {
  it('reads readiness from the shared resolver and never queries pyramid_layers', async () => {
    setAccess('all')
    const { doc } = await renderPage()
    expect(mockReadinessMap).toHaveBeenCalledWith([TEST_CHART_ID])
    expect(byTestId(doc, 'chart-readiness-band')).not.toBeNull()
    for (const [sql] of mockQuery.mock.calls) {
      if (typeof sql === 'string') expect(sql).not.toMatch(/pyramid_layers/)
    }
  })

  it('renders D1 from this chart’s own summary — never the canonical snapshot', async () => {
    setAccess('all')
    const { doc } = await renderPage()
    expect(mockGetForensicSnapshot).not.toHaveBeenCalled()
    expect(mockWorkspaceSummary).toHaveBeenCalledWith(TEST_CHART_ID)
    expect(byTestId(doc, 'd1-chart')).not.toBeNull()
  })

  it('places D1 before identity in source order and shows name, birth line and timezone', async () => {
    setAccess('all')
    const { doc, html } = await renderPage()
    expect(html.indexOf('data-testid="d1-chart"')).toBeLessThan(html.indexOf('id="jw-identity-name"'))
    expect(doc.querySelector('h1')?.textContent).toBe('Test Native')
    expect(doc.body.textContent).toMatch(/06:30 Asia\/Kolkata/)
    expect(doc.body.textContent).toMatch(/Puri/)
  })

  it('lists only the viewer’s own non-archived conversations', async () => {
    setAccess('all')
    setQueries([{ id: 'conv-1', title: 'First reading', created_at: '2026-09-01T00:00:00Z' }])
    const { doc } = await renderPage()
    const [convSql, convParams] = mockQuery.mock.calls.find(([q]) => typeof q === 'string' && q.includes('FROM conversations'))!
    expect(convSql).toMatch(/archived_at IS NULL/)
    expect(convSql).toMatch(/user_id\s*=\s*\$2/)
    expect(convParams).toEqual([TEST_CHART_ID, 'viewer-uid'])
    expect(doc.querySelector(`a[href="/clients/${TEST_CHART_ID}/consult/conv-1"]`)?.textContent).toBe('First reading')
  })

  it.each([
    ['building', 'dim', false, false],
    ['needs-rebuild', 'dim', false, false],
    ['failed', 'lit', false, false],
    ['partially-built', 'lit', false, true],
    ['not-built', 'dim', false, false],
    ['ready', 'lit', true, true],
  ] as const)('readiness %s (Gaṇita %s) → Paripraśna available=%s, Pañcāṅga available=%s', async (state, ganita, pariprashna, panchang) => {
    setAccess('all')
    setReadiness(state, ganita)
    const { doc } = await renderPage()
    expect(byTestId(doc, 'consult-room-card')?.getAttribute('data-available')).toBe(String(pariprashna))
    expect(byTestId(doc, 'panchang-room-card')?.getAttribute('data-available')).toBe(String(panchang))
    // Nirmāṇa stays reachable so the owner can inspect or retry any build.
    expect(byTestId(doc, 'build-room-card')?.getAttribute('data-available')).toBe('true')
  })

  it('explains why Paripraśna is unavailable during recomputation', async () => {
    setAccess('all')
    setReadiness('needs-rebuild')
    const { doc } = await renderPage()
    expect(byTestId(doc, 'consult-room-card')?.textContent).toMatch(/recomputation/i)
  })

  it('does not render the disabled Timeline placeholder or an invented daśā/yoga claim', async () => {
    setAccess('all')
    const { doc } = await renderPage()
    expect(doc.body.textContent).not.toMatch(/timeline room/i)
    expect(doc.body.textContent).not.toMatch(/Kalpadruma|Mercury/)
    expect(doc.body.textContent).toMatch(/Current daśā[\s\S]*Not yet computed/)
  })

  it('shows current daśā and confirmed yogas when this chart has them', async () => {
    setAccess('all')
    mockWorkspaceSummary.mockResolvedValue({
      ...EMPTY_SUMMARY,
      currentDasha: { md: 'Venus', ad: 'Moon', adEnd: '2027-03-04' },
      confirmedYogas: [{ id: 'gajakesari', name: 'Gajakesari Yoga' }],
    })
    const { doc } = await renderPage()
    expect(doc.body.textContent).toMatch(/Venus/)
    expect(doc.body.textContent).toMatch(/Gajakesari Yoga/)
  })
})
