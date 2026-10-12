// @vitest-environment node
//
// Lahiri-primary PR-5 (SS N-348 add-on): an unknown ayanamsha_id on /api/mcp/primitives/[tool] is bad
// USER input -> HTTP 400 `validation` envelope listing the stored ids, never HTTP 500
// `orchestrator_error`. The real bridge (PR-1 normaliser) throws InvalidAyanamshaError; only the
// DB, auth, rate limiter and trace emitter are mocked.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({
  query: (...a: unknown[]) => queryMock(...a),
  getPool: () => Promise.reject(new Error('no database in unit tests')),
  withTransaction: () => Promise.reject(new Error('no database in unit tests')),
}))
vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: () => true }))
vi.mock('@/lib/mcp/rate_limiter', () => ({
  checkRateLimit: vi.fn().mockResolvedValue({ allowed: true }),
  buildRateLimitErrorEnvelope: vi.fn(),
}))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn().mockResolvedValue('allow') }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('client') }))
vi.mock('@/lib/trace/emitter', () => ({ traceEmitter: { emitStep: vi.fn() } }))

import { POST } from '../route'
import { AYANAMSHA_SERVE_ORDER } from '@/lib/retrieval/registry/constants'

const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
// Surgical MCP primitive -> chart_facts_query (per-chart capability ; declares ayanamsha_id).
const TOOL = 'query_chart_facts'

function req(params: Record<string, unknown>): Request {
  return new Request(`http://localhost/api/mcp/primitives/${TOOL}`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-user': 'uid-1',
      'x-mcp-key-id': 'key-1',
    },
    body: JSON.stringify({ params: { chart_id: CHART, ...params } }),
  })
}
const ctx = { params: Promise.resolve({ tool: TOOL }) }

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [], rowCount: 0 })
  vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('network disabled in unit tests'))))
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('/api/mcp/primitives/[tool]: unknown ayanamsha_id is a 400, not a 500', () => {
  it.each(['nonsense', 'yukteshwar', 'kp_newcomb', 'lahiri_x'])('%j -> 400 validation with the stored ids listed', async (bad) => {
    const res = await POST(req({ ayanamsha_id: bad }), ctx)
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('validation')
    expect(body.error.class).not.toBe('orchestrator_error')
    expect(body.error.message).toContain('Unknown ayanamsha_id')
    for (const id of AYANAMSHA_SERVE_ORDER) {
      expect(body.error.message).toContain(id)
      expect(body.error.remediation).toContain(id)
    }
    // rejected before the handler ran any ayanamsha-bearing SQL (only the tool_registry probe ran)
    const sqls = queryMock.mock.calls.map((c) => String(c[0]))
    expect(sqls.every((s) => /tool_registry/.test(s))).toBe(true)
  })

  it('a valid short alias still works (normalised to the stored id, not rejected)', async () => {
    const res = await POST(req({ ayanamsha_id: 'lahiri' }), ctx)
    expect(res.status).toBe(200)
    const ayaParams = queryMock.mock.calls.flatMap((c) => (Array.isArray(c[1]) ? c[1] : []))
    expect(ayaParams).toContain('lahiri_chitrapaksha')
  })

  it('omitting ayanamsha_id defaults to Lahiri', async () => {
    const res = await POST(req({}), ctx)
    expect(res.status).toBe(200)
    const ayaParams = queryMock.mock.calls.flatMap((c) => (Array.isArray(c[1]) ? c[1] : []))
    expect(ayaParams).toContain('lahiri_chitrapaksha')
  })
})
