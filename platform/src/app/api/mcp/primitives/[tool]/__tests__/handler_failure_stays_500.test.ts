// @vitest-environment node
//
// Lahiri-primary PR-5: only the PR-1 InvalidAyanamshaError is remapped to 400. Any other handler
// failure must stay HTTP 500 `orchestrator_error` (a real server fault is not bad user input).

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

const retrieveMock = vi.fn()
vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return { ...real, getToolByName: () => ({ retrieve: retrieveMock }) }
})

import { POST } from '../route'

const ctx = { params: Promise.resolve({ tool: 'query_chart_facts' }) }
const req = () =>
  new Request('http://localhost/api/mcp/primitives/query_chart_facts', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-mcp-user': 'uid-1', 'x-mcp-key-id': 'key-1' },
    body: JSON.stringify({ params: { chart_id: '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa' } }),
  })

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [], rowCount: 0 })
  retrieveMock.mockReset()
  vi.spyOn(console, 'error').mockImplementation(() => {})
})
afterEach(() => vi.restoreAllMocks())

describe('/api/mcp/primitives/[tool]: non-ayanamsha handler failures stay 500', () => {
  it('a generic handler error is 500 orchestrator_error', async () => {
    retrieveMock.mockRejectedValue(new Error('db exploded'))
    const res = await POST(req(), ctx)
    expect(res.status).toBe(500)
    expect((await res.json()).error.class).toBe('orchestrator_error')
  })

  it('an error that merely mentions ayanamsha in its text is NOT remapped (class match, not message match)', async () => {
    retrieveMock.mockRejectedValue(new Error('Unknown ayanamsha_id in a downstream service'))
    const res = await POST(req(), ctx)
    expect(res.status).toBe(500)
  })
})
