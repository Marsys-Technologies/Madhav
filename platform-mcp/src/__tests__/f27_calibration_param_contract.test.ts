/**
 * F-27 — the calibration tool pair must not advertise or forward no-op slice fields.
 *
 * Original finding: `mimamsa_calibration_get({chart_id})` and the same call with
 * `domain: 'career'` added returned an identical `result_hash` — the `domain` parameter
 * was a complete no-op. The same was true of `limit` and `offset`, on both names of the
 * CR-51/CR-30 strict-alias pair (`mimamsa_calibration_get` / `query_calibration`).
 *
 * Why the fields are REMOVED rather than implemented: the underlying capability
 * `marsys://tool/L5/query_calibration` declares `required_inputs: ['chart_id']` and its
 * handler reads only chart_id / include_held_out / promoted_only. There is no honest
 * domain filter to implement — the scorecard's verdict rows come from
 * `mimamsa_calibration`, which has no `domain` column at all (only `score_domain`, a
 * numeric match-quality score), and `mimamsa_multipliers.domain` is NULL for every row
 * on the canonical chart. Per CLAUDE.md §N.7 item 6 / §N.8, a parameter with no code
 * path behind it is removed, not left advertising a capability that does not exist.
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

/**
 * The capability handler's `content` object — verdict counts mirror the real
 * canonical-chart distribution (57 rows across 4 verdict classes), the exact data the
 * finding said a domain filter ought to be able to narrow. It cannot: `mimamsa_calibration`
 * has no domain column.
 */
const CAPABILITY_CONTENT = {
  chart_id: TEST_CHART_ID,
  verdict_distribution: [
    { composite_verdict: 'UNRESOLVED', n: 25 },
    { composite_verdict: 'PARTIAL', n: 23 },
    { composite_verdict: 'REFUTED', n: 7 },
    { composite_verdict: 'CONFIRMED', n: 2 },
  ],
  reliability_curve: [],
  multipliers: [],
  qa_results: [],
  qa_summary: { total: 0, fail_count: 0 },
  filters: { include_heldout: false, promoted_only: false },
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

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
  process.env['SERVICE_TOKEN'] = 'test-service-token'
})

describe('F-27 calibration parameter contract', () => {
  it('neither calibration tool name declares the no-op domain/limit/offset fields', async () => {
    stubPrimitiveFetch([])

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const { registerMimamsaOutcomeTool } = await import('../tools/mimamsa_outcome.js')
    const capture = makeCapturingServer()
    registerP1AliasTools(capture.server, PRINCIPAL)
    registerMimamsaOutcomeTool(capture.server, PRINCIPAL)

    for (const name of ['mimamsa_calibration_get', 'query_calibration']) {
      const schema = capture.schemas.get(name)
      expect(schema, `${name} must be registered`).toBeDefined()
      expect(schema).toHaveProperty('chart_id')
      // The defect: these advertised a filter/pagination contract nothing implements.
      expect(schema, `${name} must not advertise a no-op domain filter`).not.toHaveProperty('domain')
      expect(schema, `${name} must not advertise a no-op limit`).not.toHaveProperty('limit')
      expect(schema, `${name} must not advertise a no-op offset`).not.toHaveProperty('offset')
    }
  })

  it('neither tool forwards domain/limit/offset to the primitive even when passed them', async () => {
    const forwarded: Record<string, unknown>[] = []
    stubPrimitiveFetch(forwarded)

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const { registerMimamsaOutcomeTool } = await import('../tools/mimamsa_outcome.js')
    const capture = makeCapturingServer()
    registerP1AliasTools(capture.server, PRINCIPAL)
    registerMimamsaOutcomeTool(capture.server, PRINCIPAL)

    for (const name of ['mimamsa_calibration_get', 'query_calibration']) {
      const result = await capture.handlers.get(name)!({
        chart_id: TEST_CHART_ID,
        domain: 'career',
        limit: 1,
        offset: 3,
      })
      expect(result.isError, `${name} should still succeed`).toBeFalsy()
    }

    // Exactly chart_id reaches the capability — no discarded-at-the-far-end fields.
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
