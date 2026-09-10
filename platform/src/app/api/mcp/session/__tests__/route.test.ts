/**
 * route.test.ts — GET/POST /api/mcp/session.
 *
 * V3-E-011 finding 1 (HIGH): neither verb performed any chart-ownership check
 * before resolving/persisting a provenance stamp for an explicitly-supplied
 * `pin_chart_id` (GET query param / POST body field). Any caller holding a
 * valid MCP service token + X-MCP-User header could pass any other tenant's
 * chart_id and receive that chart's build_id/build_status/ledger_version/
 * priors_version/now_context_date — a cross-tenant metadata disclosure.
 *
 * These tests exercise the route directly (not the platform-mcp `session_recall`
 * tool layer, which lives in a separate service/repo location) with an explicit,
 * unauthorized `pin_chart_id` to prove and then close the disclosure.
 *
 * Mocks mirror the sibling MCP routes' established pattern
 * (prashna_ask/__tests__/route.test.ts, bundles/[name]/route.ts):
 * `authorizeChartAccess` + `resolveMcpPrincipalRole` are the one authorization
 * brain every MCP route gates chart access through.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn() }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))

const {
  mockGetOrCreateSession,
  mockUpdateActiveChart,
  mockGetOrRefreshProvenanceStamp,
} = vi.hoisted(() => ({
  mockGetOrCreateSession: vi.fn(),
  mockUpdateActiveChart: vi.fn(),
  mockGetOrRefreshProvenanceStamp: vi.fn(),
}))
vi.mock('@/lib/mcp/sessions', () => ({
  getOrCreateSession: mockGetOrCreateSession,
  updateActiveChart: mockUpdateActiveChart,
  listUserSessions: vi.fn(),
  getOrRefreshProvenanceStamp: mockGetOrRefreshProvenanceStamp,
}))

import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { GET, POST } from '../route'

const OWNER_UID = 'owner-uid'
const OTHER_TENANT_CHART = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
const OWNED_CHART = '482012f1-710e-4a25-994a-93821f5871aa'

const FAKE_SESSION = {
  session_id: 'sess-1',
  user_uid: OWNER_UID,
  session_key: 'device-1',
  active_chart_id: null,
  created_at: '2026-08-01T00:00:00.000Z',
  last_seen_at: '2026-08-01T00:00:00.000Z',
  state_json: {},
}

const FAKE_STAMP = {
  pin: {
    build_id: 'build-123',
    build_status: 'complete',
    ledger_version: 1,
    priors_version: 1,
    now_context_date: '2026-08-28',
  },
  judgment_flags: [] as string[],
}

function makeGetReq(chartId: string, headers: Record<string, string> = {}): Request {
  const url = new URL('http://localhost/api/mcp/session')
  url.searchParams.set('pin_chart_id', chartId)
  return new Request(url, {
    method: 'GET',
    headers: {
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': OWNER_UID,
      'x-mcp-session-key': 'device-1',
      ...headers,
    },
  })
}

function makePostReq(body: object, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/mcp/session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': OWNER_UID,
      'x-mcp-session-key': 'device-1',
      ...headers,
    },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  mockGetOrCreateSession.mockResolvedValue({ ...FAKE_SESSION })
  mockUpdateActiveChart.mockResolvedValue(undefined)
  mockGetOrRefreshProvenanceStamp.mockResolvedValue({ ...FAKE_STAMP })
  ;(resolveMcpPrincipalRole as ReturnType<typeof vi.fn>).mockResolvedValue('guest')
  ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('all')
})

describe('GET /api/mcp/session — pin_chart_id authorization', () => {
  it('DENY: rejects an explicit pin_chart_id the caller has no grant on, and never resolves/persists its provenance stamp', async () => {
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('deny')

    const res = await GET(makeGetReq(OTHER_TENANT_CHART))

    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error).toBe('AUTHZ_DENIED')
    expect(body.denial.chart_id).toBe(OTHER_TENANT_CHART)
    // The exploit chain: no provenance stamp (build_id/build_status/ledger_version/
    // priors_version/now_context_date) may ever be computed or written for a
    // chart_id the caller was denied on.
    expect(mockGetOrRefreshProvenanceStamp).not.toHaveBeenCalled()
    expect(body.provenance_stamp).toBeUndefined()
  })

  it('ALLOW: an owner may pin their own chart and receives the provenance stamp', async () => {
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('all')

    const res = await GET(makeGetReq(OWNED_CHART))

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.provenance_stamp.build_id).toBe('build-123')
    expect(mockGetOrRefreshProvenanceStamp).toHaveBeenCalledWith('sess-1', OWNER_UID, OWNED_CHART)
  })

  it('ALLOW: super_admin may pin any existing chart', async () => {
    ;(resolveMcpPrincipalRole as ReturnType<typeof vi.fn>).mockResolvedValue('super_admin')
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('all')

    const res = await GET(makeGetReq(OTHER_TENANT_CHART))

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.provenance_stamp.build_id).toBe('build-123')
  })

  it('ALLOW: a view-grantee (chart_grants) may pin a chart they were granted view access to', async () => {
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('view')

    const res = await GET(makeGetReq(OWNED_CHART))

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.provenance_stamp.build_id).toBe('build-123')
  })

  it('unaffected: no pin_chart_id present skips the authz check entirely (unchanged behavior)', async () => {
    const req = new Request('http://localhost/api/mcp/session', {
      method: 'GET',
      headers: {
        'x-mcp-internal-token': 'test-token',
        'x-mcp-user': OWNER_UID,
        'x-mcp-session-key': 'device-1',
      },
    })
    const res = await GET(req)
    expect(res.status).toBe(200)
    expect(authorizeChartAccess).not.toHaveBeenCalled()
    expect(mockGetOrRefreshProvenanceStamp).not.toHaveBeenCalled()
  })
})

describe('POST /api/mcp/session — pin_chart_id authorization', () => {
  it('DENY: rejects an explicit pin_chart_id the caller has no grant on, and never resolves/persists its provenance stamp', async () => {
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('deny')

    const res = await POST(makePostReq({ pin_chart_id: OTHER_TENANT_CHART }))

    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error).toBe('AUTHZ_DENIED')
    expect(body.denial.chart_id).toBe(OTHER_TENANT_CHART)
    expect(mockGetOrRefreshProvenanceStamp).not.toHaveBeenCalled()
    expect(body.provenance_stamp).toBeUndefined()
  })

  it('ALLOW: an owner may pin their own chart and receives the provenance stamp', async () => {
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('all')

    const res = await POST(makePostReq({ pin_chart_id: OWNED_CHART }))

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.provenance_stamp.build_id).toBe('build-123')
  })

  it('ALLOW: super_admin may pin any existing chart', async () => {
    ;(resolveMcpPrincipalRole as ReturnType<typeof vi.fn>).mockResolvedValue('super_admin')
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('all')

    const res = await POST(makePostReq({ pin_chart_id: OTHER_TENANT_CHART }))

    expect(res.status).toBe(200)
  })

  it('ALLOW: a view-grantee may pin a chart they were granted view access to', async () => {
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('view')

    const res = await POST(makePostReq({ pin_chart_id: OWNED_CHART }))

    expect(res.status).toBe(200)
  })

  it('unaffected: active_chart_id write with no pin_chart_id is still unchecked here by design (checked upstream by the MCP sidecar)', async () => {
    const res = await POST(makePostReq({ active_chart_id: OTHER_TENANT_CHART }))
    expect(res.status).toBe(200)
    expect(mockUpdateActiveChart).toHaveBeenCalledWith('sess-1', OWNER_UID, OTHER_TENANT_CHART)
    expect(authorizeChartAccess).not.toHaveBeenCalled()
  })
})
