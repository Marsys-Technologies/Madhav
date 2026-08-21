/**
 * F-27 — the calibration tool pair must advertise and forward the filters that are REAL,
 * and advertise nothing that isn't.
 *
 * Original finding: `mimamsa_calibration_get({chart_id})` and the same call with
 * `domain: 'career'` added returned an identical `result_hash` — `domain` was a complete
 * no-op, as were `limit` and `offset`, on both names of the CR-51/CR-30 strict-alias pair
 * (`mimamsa_calibration_get` / `query_calibration`).
 *
 * The first repair attempt deleted all three parameters, claiming no honest domain filter
 * could be derived. Adversarial review proved that claim false: `mimamsa_calibration`
 * carries `prediction_id` (348_mimamsa_pramana.sql:9) and `mimamsa_predictions` declares
 * `domain text NOT NULL` (347_mimamsa_bhavisya.sql:10), with the composite index for the
 * join already shipped (348:31). Live on the canonical chart, `domain: 'career'` narrows
 * 57 calibration rows to 9. The narrowing itself is asserted at the capability layer
 * (platform/.../L5_mimamsa/__tests__/f27_calibration_domain_filter.test.ts); THIS file
 * asserts the MCP contract on top of it:
 *
 *   - `domain` is declared and forwarded on BOTH tool names (it was a no-op on one and
 *     absent on the other);
 *   - `include_held_out` / `promoted_only` — two GENUINE capability filters that no tool
 *     name could reach — are declared and forwarded on both;
 *   - `limit` / `offset` stay REMOVED: the capability has no pagination whatsoever, and
 *     response size is governed by the alias's presentation-only `budget_kb`. Re-declaring
 *     them would be the exact defect this repair closes (§N.8 Earned-Signal Principle);
 *   - `budget_kb` remains presentation-only and never reaches the primitive.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

function makeCapturingServer() {
  const schemas = new Map<string, Record<string, unknown>>()
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, _description: string, schema: Record<string, unknown>, handler: ToolHandler) => {
      schemas.set(name, schema)
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, schemas, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const CALIBRATION_TOOLS = ['mimamsa_calibration_get', 'query_calibration'] as const

/**
 * The capability handler's `content` object, in the post-fix shape: verdict counts mirror
 * the real canonical-chart distribution (57 rows across 4 verdict classes) and `filters`
 * carries the domain-scope disclosure the capability now emits.
 */
const CAPABILITY_CONTENT = {
  chart_id: TEST_CHART_ID,
  verdict_distribution: [
    { composite_verdict: 'UNRESOLVED', n: 25 },
    { composite_verdict: 'PARTIAL', n: 23 },
    { composite_verdict: 'REFUTED', n: 7 },
    { composite_verdict: 'CONFIRMED', n: 2 },
  ],
  verdict_row_count: 57,
  reliability_curve: [],
  multipliers: [],
  qa_results: [],
  qa_summary: { total: 0, fail_count: 0 },
  filters: {
    include_heldout: false,
    promoted_only: false,
    domain: null,
    domain_filtered_sections: [],
    domain_unfiltered_sections: [],
    multipliers_total: 0,
    multipliers_with_domain: 0,
  },
}

/**
 * Faithful production wire shape: `/api/mcp/primitives/<tool>` returns the legacy
 * ToolBundle built by tool_name_bridge.ts, with the real payload at
 * `result.results[0].content` as a JSON string (see src/lib/primitive_unwrap.ts).
 */
const CAPABILITY_PAYLOAD = {
  ok: true,
  result: {
    tool_bundle_id: 'tb-f27-test',
    results: [{ content: JSON.stringify(CAPABILITY_CONTENT) }],
  },
}

/** Captures every params object forwarded to the platform primitive. */
function stubPrimitiveFetch(sink: Record<string, unknown>[]) {
  vi.stubGlobal('fetch', vi.fn(async (url: string, opts?: { body?: string }) => {
    if (String(url).includes('/api/mcp/primitives/')) {
      sink.push((JSON.parse(opts?.body ?? '{}') as { params: Record<string, unknown> }).params)
    }
    return {
      ok: true,
      json: async () => CAPABILITY_PAYLOAD,
      text: async () => '',
    }
  }))
}

async function registerBoth() {
  const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
  const { registerMimamsaOutcomeTool } = await import('../tools/mimamsa_outcome.js')
  const capture = makeCapturingServer()
  registerP1AliasTools(capture.server, PRINCIPAL)
  registerMimamsaOutcomeTool(capture.server, PRINCIPAL)
  return capture
}

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
  process.env['SERVICE_TOKEN'] = 'test-service-token'
})

describe('F-27 calibration parameter contract', () => {
  it('both tool names declare the three real filters and neither declares the removed pagination', async () => {
    stubPrimitiveFetch([])
    const capture = await registerBoth()

    for (const name of CALIBRATION_TOOLS) {
      const schema = capture.schemas.get(name)
      expect(schema, `${name} must be registered`).toBeDefined()
      expect(schema).toHaveProperty('chart_id')
      // The repair: a real, derived domain filter, reachable from both names.
      expect(schema, `${name} must advertise the real domain filter`).toHaveProperty('domain')
      // The reviewer's non-blocking half: genuine filters that no tool name could reach.
      expect(schema, `${name} must advertise include_held_out`).toHaveProperty('include_held_out')
      expect(schema, `${name} must advertise promoted_only`).toHaveProperty('promoted_only')
      // Still genuinely unimplemented — the capability has no pagination at all.
      expect(schema, `${name} must not advertise a no-op limit`).not.toHaveProperty('limit')
      expect(schema, `${name} must not advertise a no-op offset`).not.toHaveProperty('offset')
    }
  })

  it('both tool names forward domain / include_held_out / promoted_only to the primitive', async () => {
    const forwarded: Record<string, unknown>[] = []
    stubPrimitiveFetch(forwarded)
    const capture = await registerBoth()

    for (const name of CALIBRATION_TOOLS) {
      const result = await capture.handlers.get(name)!({
        chart_id: TEST_CHART_ID,
        domain: 'career',
        include_held_out: true,
        promoted_only: true,
      })
      expect(result.isError, `${name} should succeed`).toBeFalsy()
    }

    expect(forwarded).toHaveLength(CALIBRATION_TOOLS.length)
    for (const [i, params] of forwarded.entries()) {
      const name = CALIBRATION_TOOLS[i]
      expect(params['chart_id'], `${name} chart_id`).toBe(TEST_CHART_ID)
      // The defect was that this value was accepted and then thrown away.
      expect(params['domain'], `${name} must forward domain`).toBe('career')
      expect(params['include_held_out'], `${name} must forward include_held_out`).toBe(true)
      expect(params['promoted_only'], `${name} must forward promoted_only`).toBe(true)
      expect(params, `${name} must not invent pagination`).not.toHaveProperty('limit')
      expect(params, `${name} must not invent pagination`).not.toHaveProperty('offset')
    }
  })

  it('omitting the optional filters forwards chart_id alone (no undefined keys on the wire)', async () => {
    const forwarded: Record<string, unknown>[] = []
    stubPrimitiveFetch(forwarded)
    const capture = await registerBoth()

    for (const name of CALIBRATION_TOOLS) {
      await capture.handlers.get(name)!({ chart_id: TEST_CHART_ID })
    }

    expect(forwarded).toEqual([{ chart_id: TEST_CHART_ID }, { chart_id: TEST_CHART_ID }])
  })

  it('the alias does not forward its presentation-only budget_kb to the primitive', async () => {
    const forwarded: Record<string, unknown>[] = []
    stubPrimitiveFetch(forwarded)

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const capture = makeCapturingServer()
    registerP1AliasTools(capture.server, PRINCIPAL)

    await capture.handlers.get('mimamsa_calibration_get')!({
      chart_id: TEST_CHART_ID,
      budget_kb: 200,
    })

    expect(forwarded).toEqual([{ chart_id: TEST_CHART_ID }])
  })
})
