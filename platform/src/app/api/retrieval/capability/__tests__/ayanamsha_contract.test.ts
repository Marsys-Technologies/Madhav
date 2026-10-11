/**
 * ayanamsha_contract.test.ts — SS N-339 / N-342 on the MCP capability dispatcher.
 *
 * /api/retrieval/capability reaches handlers DIRECTLY (it does not go through
 * tool_name_bridge), so it applies the ayanamsha BOUNDARY contract: aliases -> stored id, "all" ->
 * unfiltered opt-out, unknown -> a 400 validation envelope listing the stored ids. It does NOT
 * default an omitted id to Lahiri (platform-mcp callers pin it; direct callers keep their
 * handler default until PR-2). Capabilities without an ayanamsha_id input are untouched.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { NextRequest } from 'next/server'

const mockAuthorize = vi.fn().mockResolvedValue('view')
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mockAuthorize }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('client') }))

const ORIGINAL_ENV = { ...process.env }
const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const AYA_URI = 'marsys://tool/test/ayanamsha_probe'
const NOAYA_URI = 'marsys://tool/test/no_ayanamsha_probe'
const KP_URI = 'marsys://tool/L1/get_kp_cusps'

function makeReq(body: unknown): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': 'test-user-uid',
      // #3410 (principal headers on every scope): the route 401s without BOTH principal headers.
      'x-mcp-key-id': 'mcp_test_KEY001',
    },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.resetModules()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  delete process.env.REDIS_HOST
  delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
})

afterEach(() => {
  process.env = { ...ORIGINAL_ENV }
})

async function setup(uri: string, schema: Record<string, unknown>, handler: ReturnType<typeof vi.fn>) {
  const { registerCapability } = await import('@/lib/retrieval/registry')
  const { POST } = await import('../route')
  registerCapability({
    uri,
    type: 'tool',
    layer: 'L0',
    name: 'ayanamsha_probe',
    description: 'ayanamsha contract probe',
    input_schema: schema,
    required_inputs: ['chart_id'],
    scope: 'per_chart',
    archetype: 'flat_fact',
    traversal_level: 'L-ORIENT',
    tool_role: 'leaf',
    emits_references: false,
    lel_capable: false,
    llm_hints: { agentic: { cost_class: 'cheap', cacheable: false } },
    handler,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any)
  return POST
}

describe('capability route ayanamsha contract', () => {
  it('omitted ayanamsha_id stays omitted here (no injection on this route; platform-mcp pins it, handlers keep their default)', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const POST = await setup(AYA_URI, { chart_id: {}, ayanamsha_id: {} }, handler)
    const res = await POST(makeReq({ uri: AYA_URI, args: { chart_id: CHART_ID } }))
    expect(res.status).toBe(200)
    expect((handler.mock.calls[0] as unknown[])[0]).toEqual({ chart_id: CHART_ID })
  })

  it.each([['LAHIRI', 'lahiri_chitrapaksha'], ['kp', 'krishnamurti'], ['true_citra', 'true_chitra'], ['raman', 'raman']])(
    '%j is normalised to %j',
    async (input, stored) => {
      const handler = vi.fn(() => Promise.resolve({ ok: true }))
      const POST = await setup(AYA_URI, { chart_id: {}, ayanamsha_id: {} }, handler)
      await POST(makeReq({ uri: AYA_URI, args: { chart_id: CHART_ID, ayanamsha_id: input } }))
      expect((handler.mock.calls[0] as unknown[])[0]).toMatchObject({ ayanamsha_id: stored })
    },
  )

  it('"all" removes the filter and marks ayanamsha_scope:"all"', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const POST = await setup(AYA_URI, { chart_id: {}, ayanamsha_id: {} }, handler)
    await POST(makeReq({ uri: AYA_URI, args: { chart_id: CHART_ID, ayanamsha_id: 'all' } }))
    const received = (handler.mock.calls[0] as unknown[])[0] as Record<string, unknown>
    expect('ayanamsha_id' in received).toBe(false)
    expect(received['ayanamsha_scope']).toBe('all')
  })

  it('unknown ayanamsha_id -> 400 validation envelope listing the stored ids; handler never runs', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const POST = await setup(AYA_URI, { chart_id: {}, ayanamsha_id: {} }, handler)
    const res = await POST(makeReq({ uri: AYA_URI, args: { chart_id: CHART_ID, ayanamsha_id: 'bogus' } }))
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('validation')
    for (const id of ['lahiri_chitrapaksha', 'true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical']) {
      expect(body.error.message).toContain(id)
    }
    expect(handler).not.toHaveBeenCalled()
  })

  it('a capability with no ayanamsha_id input is not touched (same args, no injection, no validation)', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true }))
    const POST = await setup(NOAYA_URI, { chart_id: {} }, handler)
    await POST(makeReq({ uri: NOAYA_URI, args: { chart_id: CHART_ID, ayanamsha_id: 'whatever' } }))
    expect((handler.mock.calls[0] as unknown[])[0]).toEqual({ chart_id: CHART_ID, ayanamsha_id: 'whatever' })
  })

  it('a real KP-frame capability (get_kp_cusps): explicit kp is normalised, omitted stays omitted', async () => {
    const { POST } = await import('../route')
    const { getCapability } = await import('@/lib/retrieval/registry')
    // Warm-up call: the route bootstraps (registers every real capability) on first dispatch.
    await POST(makeReq({ uri: 'marsys://tool/test/does_not_exist', args: {} }))
    const cap = getCapability(KP_URI as never)!
    expect(cap, 'get_kp_cusps registered by the route bootstrap').toBeDefined()
    const spy = vi.spyOn(cap, 'handler').mockResolvedValue({ content: {} } as never)
    await POST(makeReq({ uri: KP_URI, args: { chart_id: CHART_ID } }))
    expect('ayanamsha_id' in (spy.mock.calls[0]![0] as Record<string, unknown>)).toBe(false)
    await POST(makeReq({ uri: KP_URI, args: { chart_id: CHART_ID, ayanamsha_id: 'KP' } }))
    expect(spy.mock.calls[1]![0]).toMatchObject({ ayanamsha_id: 'krishnamurti' })
  })
})
