// @vitest-environment node
//
// S9 item 9 (held) — HYGIENE, not authentication. Before this change the principal headers
// (X-MCP-User, X-MCP-Key-Id) were consulted only inside the per_chart branch of the capability
// dispatcher, so a `scope: 'global'` capability was reachable with the service token alone.
// Presence of both headers is now required for EVERY scope, before any handler runs. The headers
// are caller-asserted; the real fix is OIDC-bound service requests (production env
// MCP_CALLER_OIDC_AUDIENCE and MCP_CALLER_OIDC_SERVICE_ACCOUNT).

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { NextRequest } from 'next/server'

const { mockAuthorize } = vi.hoisted(() => ({ mockAuthorize: vi.fn() }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mockAuthorize }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('client') }))

const ORIGINAL_ENV = { ...process.env }
const GLOBAL_URI = 'marsys://tool/test/s9_global_probe'
const PER_CHART_URI = 'marsys://tool/test/s9_per_chart_probe'
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function req(body: unknown, headers: Record<string, string> = {}): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-mcp-internal-token': 'test-token', ...headers },
    body: JSON.stringify(body),
  })
}

const PRINCIPAL = { 'x-mcp-user': 'owner-uid', 'x-mcp-key-id': 'mcp_test_KEY001' }

beforeEach(() => {
  vi.resetModules()
  mockAuthorize.mockReset()
  mockAuthorize.mockResolvedValue('view')
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
})
afterEach(() => { process.env = { ...ORIGINAL_ENV } })

async function setup(scope: 'global' | 'per_chart', uri: string, handler: ReturnType<typeof vi.fn>) {
  const { registerCapability, getCapability } = await import('@/lib/retrieval/registry')
  const { POST } = await import('../route')
  registerCapability({
    uri,
    type: 'tool',
    layer: 'L0',
    name: 's9_probe',
    description: 'S9 principal-header probe capability',
    input_schema: {},
    required_inputs: [],
    scope,
    archetype: 'flat_fact',
    traversal_level: 'L-ORIENT',
    tool_role: 'leaf',
    emits_references: false,
    lel_capable: false,
    llm_hints: { agentic: { cost_class: 'cheap', cacheable: false } },
    handler,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any)
  return { POST, scopeOf: () => getCapability(uri as never)?.scope }
}

describe('capability dispatcher — principal headers are required for every scope (hygiene)', () => {
  it('a GLOBAL capability with the service token but NO principal headers is 401 (auth) and the handler never runs', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const { POST, scopeOf } = await setup('global', GLOBAL_URI, handler)
    expect(scopeOf()).toBe('global')

    const res = await POST(req({ uri: GLOBAL_URI, args: {} }))

    expect(res.status).toBe(401)
    const body = await res.json() as { ok: boolean; error: { class: string } }
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('auth')
    expect(handler).not.toHaveBeenCalled()
  })

  it.each([
    ['only X-MCP-User', { 'x-mcp-user': 'owner-uid' }],
    ['only X-MCP-Key-Id', { 'x-mcp-key-id': 'mcp_test_KEY001' }],
    ['an empty X-MCP-User', { 'x-mcp-user': '', 'x-mcp-key-id': 'mcp_test_KEY001' }],
    ['a blank X-MCP-Key-Id', { 'x-mcp-user': 'owner-uid', 'x-mcp-key-id': '   ' }],
  ])('a GLOBAL capability with %s is 401 and the handler never runs', async (_name, headers) => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const { POST, scopeOf } = await setup('global', GLOBAL_URI, handler)
    expect(scopeOf()).toBe('global')

    const res = await POST(req({ uri: GLOBAL_URI, args: {} }, headers))

    expect(res.status).toBe(401)
    expect(handler).not.toHaveBeenCalled()
  })

  it('a GLOBAL capability with both principal headers still works', async () => {
    const handler = vi.fn(() => Promise.resolve({ rows: [1] }))
    const { POST, scopeOf } = await setup('global', GLOBAL_URI, handler)
    expect(scopeOf()).toBe('global')

    const res = await POST(req({ uri: GLOBAL_URI, args: {} }, PRINCIPAL))

    expect(res.status).toBe(200)
    await expect(res.json()).resolves.toEqual({ ok: true, content: { rows: [1] } })
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it("the internal sentinel principal that platform-mcp's L0 tools send satisfies the presence check", async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const { POST } = await setup('global', GLOBAL_URI, handler)

    const res = await POST(req({ uri: GLOBAL_URI, args: {} }, { 'x-mcp-user': 'mcp-internal', 'x-mcp-key-id': 'mcp-internal' }))

    expect(res.status).toBe(200)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('a PER_CHART capability with no principal headers is 401 (auth) before any entitlement lookup or handler', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const { POST, scopeOf } = await setup('per_chart', PER_CHART_URI, handler)
    expect(scopeOf()).toBe('per_chart')

    const res = await POST(req({ uri: PER_CHART_URI, args: { chart_id: CHART } }))

    expect(res.status).toBe(401)
    const body = await res.json() as { error: { class: string } }
    expect(body.error.class).toBe('auth')
    expect(mockAuthorize).not.toHaveBeenCalled()
    expect(handler).not.toHaveBeenCalled()
  })

  it('a PER_CHART capability with both headers still reaches the entitlement gate and handler', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const { POST } = await setup('per_chart', PER_CHART_URI, handler)

    const res = await POST(req({ uri: PER_CHART_URI, args: { chart_id: CHART } }, PRINCIPAL))

    expect(res.status).toBe(200)
    expect(mockAuthorize).toHaveBeenCalledTimes(1)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('the service-token gate is unchanged: no token is still 403 regardless of principal headers', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const { POST } = await setup('global', GLOBAL_URI, handler)

    const noToken = new NextRequest('http://localhost/api/retrieval/capability', {
      method: 'POST',
      headers: { 'content-type': 'application/json', ...PRINCIPAL },
      body: JSON.stringify({ uri: GLOBAL_URI, args: {} }),
    })
    const res = await POST(noToken)

    expect(res.status).toBe(403)
    expect(handler).not.toHaveBeenCalled()
  })
})
