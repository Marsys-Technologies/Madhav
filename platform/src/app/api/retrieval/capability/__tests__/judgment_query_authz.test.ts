// @vitest-environment node
//
// OSR-015 security condition: `judgment_query` (which now fans out to the sidecar formation-band route)
// is a per_chart capability, and the capability dispatcher (/api/retrieval/capability -- the route every
// managed-MCP call to a registry capability goes through; judgment_query is not in the surgical
// /api/mcp/primitives whitelist) denies an unauthorized chart_id BEFORE the handler runs. Same gate
// (authorizeChartAccess -> entitlement_denied envelope) and same mocking pattern as
// capability_cache_wiring.test.ts.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { NextRequest } from 'next/server'

const { mockAuthorize } = vi.hoisted(() => ({ mockAuthorize: vi.fn() }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mockAuthorize }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('client') }))

const ORIGINAL_ENV = { ...process.env }
const URI = 'marsys://tool/L-JUDGMENT/judgment_query'
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function req(body: unknown, headers: Record<string, string> = {}): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-mcp-internal-token': 'test-token', ...headers },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.resetModules()
  mockAuthorize.mockReset()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
})
afterEach(() => { process.env = { ...ORIGINAL_ENV } })

describe('judgment_query entitlement (formation-band fan-out is per-chart gated)', () => {
  it('is a per_chart capability that requires chart_id', async () => {
    const { judgmentQueryCapability } = await import('@/lib/retrieval/registry/layers/register_d9_judgment')
    expect(judgmentQueryCapability.uri).toBe(URI)
    expect(judgmentQueryCapability.scope).toBe('per_chart')
    expect(judgmentQueryCapability.required_inputs).toContain('chart_id')
  })

  it('the dispatcher denies an unauthorized chart_id with the entitlement_denied envelope and never runs the handler', async () => {
    mockAuthorize.mockResolvedValue('deny')
    const { POST } = await import('../route')
    const { getCapability } = await import('@/lib/retrieval/registry')
    const res = await POST(req({ uri: URI, args: { chart_id: CHART, domain: 'wealth' } }, { 'x-mcp-user': 'uid-not-entitled' }))
    expect(res.status).toBe(401)
    const body = await res.json()
    expect(JSON.stringify(body)).toContain('entitlement_denied')
    expect(mockAuthorize).toHaveBeenCalledTimes(1)
    expect(mockAuthorize.mock.calls[0]![0]).toMatchObject({ chartId: CHART, principal: { uid: 'uid-not-entitled' } })
    // the registered capability resolved by the dispatcher is the per_chart judgment_query
    expect(getCapability(URI as never)?.scope).toBe('per_chart')
  })

  it('denies (fail closed) when no principal header is supplied, without consulting the handler', async () => {
    const { POST } = await import('../route')
    const res = await POST(req({ uri: URI, args: { chart_id: CHART, domain: 'wealth' } }))
    expect(res.status).toBe(401)
    expect(mockAuthorize).not.toHaveBeenCalled()
  })

  it('a header-supplied chart_id is gated too (chart_id in X-MCP-Chart-Id, none in args)', async () => {
    mockAuthorize.mockResolvedValue('deny')
    const { POST } = await import('../route')
    const res = await POST(req({ uri: URI, args: { domain: 'wealth' } }, { 'x-mcp-user': 'uid-x', 'x-mcp-chart-id': CHART }))
    expect(res.status).toBe(401)
    expect(mockAuthorize.mock.calls[0]![0]).toMatchObject({ chartId: CHART })
  })
})
