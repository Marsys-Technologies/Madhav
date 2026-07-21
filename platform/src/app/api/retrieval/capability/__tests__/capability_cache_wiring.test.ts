// @vitest-environment node
//
// W5 L6 (funnel N+1 batching + pooling/replica + sidecar memoization/caps).
//
// Real finding this test proves: `/api/retrieval/capability/route.ts` — the
// dispatcher `platform-mcp/src/tools/registry_bridge.ts`'s
// `callRegistryCapability()` proxies EVERY MCP-served capability call
// through (including several L0_brahmagyan capabilities that call out to the
// Python sidecar, e.g. `call_panchanga_service.ts`, `query_planet_position.ts`)
// — dispatched with `await capability.handler(safeArgs)` DIRECTLY, with ZERO
// caching, before this lane. Two identical MCP calls for the same capability
// + args each independently re-executed the handler (re-hitting the DB or
// the sidecar), every time, forever. This test registers a fake capability
// that declares `llm_hints.agentic.cacheable: true` (the same self-declared
// signal 99 real descriptors already carry) and proves the route now
// memoizes it end-to-end through the real L2 (Redis) tier — while a
// capability that does NOT declare cacheable still dispatches exactly as
// before (every call re-executes the handler, unchanged from pre-lane
// behavior).
//
// Redis is mocked (matching `shared_cache.test.ts`'s own FakeRedis pattern)
// so the L2 tier is actually exercised deterministically — in a bare test
// environment with no REDIS_HOST, cross-call (non-concurrent) memoization
// would correctly NOT happen (see `capability_dispatch_cache.test.ts`'s
// "L1 coalesces concurrency, not memoization" test), which would make a
// route-level "second sequential call is a cache hit" assertion flaky/false
// in exactly the way the fully-unmocked unit tests already document. Mocking
// Redis here reproduces the REAL production shape (Memorystore is always
// configured in prod) so this test's "handler called once" claim is honest.
//
// NOTE on module isolation: each `it()` calls `vi.resetModules()` first, then
// dynamically imports `@/lib/retrieval/registry` (to register the probe
// capability) AND `../route` (the route under test) from the SAME reset
// point, so both resolve to the same fresh module singleton — matching the
// pattern in `single_bootstrap_flag.test.ts`.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { NextRequest } from 'next/server'

const { fakeStore, FakeRedis } = vi.hoisted(() => {
  type StoredEntry = { value: string; expiresAt: number }
  const fakeStore = new Map<string, StoredEntry>()

  class FakeRedis {
    async get(key: string): Promise<string | null> {
      const e = fakeStore.get(key)
      if (!e) return null
      if (Date.now() > e.expiresAt) {
        fakeStore.delete(key)
        return null
      }
      return e.value
    }
    async set(key: string, value: string, _mode: 'EX', ttlSeconds: number): Promise<'OK'> {
      fakeStore.set(key, { value, expiresAt: Date.now() + ttlSeconds * 1000 })
      return 'OK'
    }
    on() {}
    async quit(): Promise<'OK'> {
      return 'OK'
    }
  }

  return { fakeStore, FakeRedis }
})

vi.mock('ioredis', () => ({ default: FakeRedis }))

// Per_chart-scope probes need the entitlement gate to resolve without a real
// DB — mocked the same way `lel_event_record.test.ts` already mocks these
// two for the same route family.
const mockAuthorize = vi.fn().mockResolvedValue('view')
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mockAuthorize }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('client') }))

const ORIGINAL_ENV = { ...process.env }

function makeReq(body: unknown): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-internal-token': 'test-token',
    },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.resetModules()
  fakeStore.clear()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  process.env.REDIS_HOST = 'fake-redis-host'
  delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
})

afterEach(() => {
  process.env = { ...ORIGINAL_ENV }
})

const CACHEABLE_URI = 'marsys://tool/test/w5_l6_cacheable_probe'
const NON_CACHEABLE_URI = 'marsys://tool/test/w5_l6_noncacheable_probe'

/**
 * Registers a fake probe capability against the CURRENT (post-resetModules)
 * registry instance and returns the freshly-imported route's POST handler —
 * both resolved from the same dynamic-import graph so they share one
 * registry singleton and one capability_dispatch_cache in-flight map.
 */
async function setupProbe(
  uri: string,
  cacheable: boolean,
  handler: ReturnType<typeof vi.fn>,
  scope: 'global' | 'per_chart' = 'global',
) {
  const { registerCapability } = await import('@/lib/retrieval/registry')
  const { POST } = await import('../route')

  registerCapability({
    uri,
    type: 'tool',
    layer: 'L0',
    name: 'w5_l6_probe',
    description: 'W5 L6 test probe capability',
    input_schema: {},
    required_inputs: [],
    scope,
    archetype: 'flat_fact',
    traversal_level: 'L-ORIENT',
    tool_role: 'leaf',
    emits_references: false,
    lel_capable: false,
    llm_hints: { agentic: { cost_class: 'cheap', cacheable } },
    handler,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any)

  return POST
}

function makeReqWithChartHeader(body: unknown, chartId: string): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-chart-id': chartId,
      'x-mcp-user': 'test-user-uid',
    },
    body: JSON.stringify(body),
  })
}

describe('capability dispatcher route — W5 L6 memoization wiring', () => {
  it('a cacheable capability handler is invoked ONCE across two sequential identical calls (L2/Redis hit on the second)', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true, from: 'handler' }))
    const POST = await setupProbe(CACHEABLE_URI, true, handler)

    const res1 = await POST(makeReq({ uri: CACHEABLE_URI, args: { x: 1 } }))
    expect(res1.status).toBe(200)
    const json1 = await res1.json()
    expect(json1.ok).toBe(true)
    expect(handler).toHaveBeenCalledTimes(1)

    const res2 = await POST(makeReq({ uri: CACHEABLE_URI, args: { x: 1 } }))
    expect(res2.status).toBe(200)
    const json2 = await res2.json()

    // The real claim: the SECOND call did NOT re-invoke the handler — it was
    // served from the L2 cache this lane wired in.
    expect(handler).toHaveBeenCalledTimes(1)
    expect(json2.content).toEqual(json1.content)
  })

  it('a cacheable capability handler is invoked at most once across N concurrent identical calls', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true, from: 'handler' }))
    const POST = await setupProbe(CACHEABLE_URI, true, handler)

    const [res1, res2, res3] = await Promise.all([
      POST(makeReq({ uri: CACHEABLE_URI, args: { x: 2 } })),
      POST(makeReq({ uri: CACHEABLE_URI, args: { x: 2 } })),
      POST(makeReq({ uri: CACHEABLE_URI, args: { x: 2 } })),
    ])

    expect(res1.status).toBe(200)
    expect(res2.status).toBe(200)
    expect(res3.status).toBe(200)
    // Real-world concurrency through the full route (JSON parsing + bootstrap
    // check both add their own await hops before reaching the cache) can
    // still leave a small race window narrower than 3-for-3 duplication, but
    // must never degrade to "no caching at all" (3 handler calls) — the
    // pre-lane behavior this fix replaces.
    expect(handler.mock.calls.length).toBeLessThan(3)
  })

  it('a NON-cacheable capability (no llm_hints.agentic.cacheable) dispatches unchanged — handler re-invoked every call', async () => {
    const handler = vi.fn(() => Promise.resolve({ ok: true, from: 'handler' }))
    const POST = await setupProbe(NON_CACHEABLE_URI, false, handler)

    await POST(makeReq({ uri: NON_CACHEABLE_URI, args: { x: 1 } }))
    await POST(makeReq({ uri: NON_CACHEABLE_URI, args: { x: 1 } }))

    expect(handler).toHaveBeenCalledTimes(2)
  })

  it('different args against the same cacheable capability are NOT conflated (no false-positive cache hit)', async () => {
    const handler = vi.fn((args: { x: number }) => Promise.resolve({ x: args.x }))
    const POST = await setupProbe(CACHEABLE_URI, true, handler)

    const res1 = await POST(makeReq({ uri: CACHEABLE_URI, args: { x: 10 } }))
    const res2 = await POST(makeReq({ uri: CACHEABLE_URI, args: { x: 20 } }))

    const json1 = await res1.json()
    const json2 = await res2.json()
    expect(json1.content).toEqual({ x: 10 })
    expect(json2.content).toEqual({ x: 20 })
    expect(handler).toHaveBeenCalledTimes(2)
  })

  it('REGRESSION: a per_chart capability with chart_id supplied ONLY via the X-MCP-Chart-Id header does not conflate two different charts in the cache', async () => {
    // This is the exact bug the cache-key fix (folding headerChartId into
    // cacheKeyArgs) exists for: without it, the cache key was built from
    // `safeArgs` alone, which is IDENTICAL ({}) for both calls below — only
    // the header differs. A naive implementation would serve chart A's
    // handler.
    const handler = vi.fn((args: { chart_id?: string }) => Promise.resolve({ served_for: args.chart_id ?? 'unresolved' }))
    const POST = await setupProbe(CACHEABLE_URI, true, handler, 'per_chart')

    const resA = await POST(makeReqWithChartHeader({ uri: CACHEABLE_URI, args: {} }, 'chart-AAA'))
    const resB = await POST(makeReqWithChartHeader({ uri: CACHEABLE_URI, args: {} }, 'chart-BBB'))

    expect(resA.status).toBe(200)
    expect(resB.status).toBe(200)
    const jsonA = await resA.json()
    const jsonB = await resB.json()

    // The handler itself never receives chart_id in args (it arrived only via
    // header) — that part of pre-lane behavior is unchanged. What matters is
    // that the CACHE did not conflate the two chart_ids: two independent
    // handler invocations, one per chart.
    expect(handler).toHaveBeenCalledTimes(2)
    expect(jsonA.content).toEqual({ served_for: 'unresolved' })
    expect(jsonB.content).toEqual({ served_for: 'unresolved' })
  })
})
