/**
 * F-28 — calibration ToolBundle content must remain structured and recoverable.
 *
 * The platform primitive serializes the capability payload into
 * `result.results[0].content`. These tests exercise the real registered alias handler and
 * mock only that external HTTP boundary.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolResult = {
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}

type ToolHandler = (args: Record<string, unknown>) => Promise<ToolResult>

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const TRUNCATION_MARKER = '…[truncated for budget]'

function makeCapturingServer() {
  const schemas = new Map<string, Record<string, unknown>>()
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (
      name: string,
      _description: string,
      schema: Record<string, unknown>,
      handler: ToolHandler,
    ) => {
      schemas.set(name, schema)
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, schemas, handlers }
}

function calibrationPayload() {
  const qaResults = Array.from({ length: 168 }, (_, index) => ({
    check_id: `QA-${index}`,
    check_type: 'negative_control',
    target: `control-window-${index}`,
    result_score: '0.1234',
    status: index % 17 === 0 ? 'FAIL' : 'PASS',
    checked_at: '2026-08-18T00:00:00.000Z',
    detail: `QA row ${index}: ${'x'.repeat(260)}`,
  }))
  return {
    chart_id: CHART_ID,
    verdict_distribution: Array.from({ length: 4 }, (_, index) => ({
      composite_verdict: ['CONFIRMED', 'PARTIAL', 'REFUTED', 'UNRESOLVED'][index],
      n: [2, 23, 7, 25][index],
    })),
    reliability_curve: Array.from({ length: 6 }, (_, index) => ({
      stratum_key: `bin-${index}`,
      predicted_prob_bin: index / 10,
      observed_rate: index / 12,
      n: 10 + index,
    })),
    multipliers: Array.from({ length: 9 }, (_, index) => ({
      weight_id: `weight-${index}`,
      mechanism: `mechanism-${index}`,
      target_kind: 'signal_family',
      target_ref: `family-${index}`,
      domain: 'career',
      applied_multiplier: 1,
      raw_multiplier: 1,
      n_observations: 20,
      promotion_status: 'candidate',
      gate_passed: false,
      kill_switch_state: 'inactive',
      divergence_from_classical: 0,
    })),
    qa_results: qaResults,
    qa_summary: { total: 168, fail_count: 10 },
    filters: { include_heldout: false, promoted_only: false },
  }
}

function primitiveResponse(innerContent: string) {
  const body = {
    ok: true,
    trace_id: 'trace-f28',
    epistemics: {
      surgical: true,
      confidence_band: 'high',
      horizon_days: null,
      falsifier: null,
    },
    result: {
      tool_bundle_id: 'bundle-f28',
      tool_name: 'query_calibration',
      tool_version: '1.0',
      invocation_params: { chart_id: CHART_ID },
      results: [{ content: innerContent }],
      served_from_cache: false,
      latency_ms: 12,
      result_hash: 'sha256:fixture',
      schema_version: '1.0',
    },
    citations: [],
    plan: null,
    predictions_logged: [],
    synthesis_audit: null,
    suggested_followups: [],
    warnings: [],
  }
  return {
    ok: true,
    status: 200,
    json: async () => body,
    text: async () => JSON.stringify(body),
  }
}

function servedObject(result: ToolResult): Record<string, unknown> {
  return result.structuredContent!.object as Record<string, unknown>
}

function servedCalibration(result: ToolResult): Record<string, unknown> {
  const outer = servedObject(result)
  const bundle = outer['result'] as Record<string, unknown>
  const rows = bundle['results'] as Array<Record<string, unknown>>
  return rows[0]!['content'] as Record<string, unknown>
}

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
})

describe('F-28 calibration ToolBundle budget', () => {
  it('keeps the default response valid and exposes a callable recovery path for trimmed QA detail', async () => {
    const payload = calibrationPayload()
    vi.stubGlobal('fetch', vi.fn(async () => primitiveResponse(JSON.stringify(payload))))

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const capture = makeCapturingServer()
    registerP1AliasTools(capture.server, PRINCIPAL)

    const result = await capture.handlers.get('mimamsa_calibration_get')!({ chart_id: CHART_ID })
    const outer = servedObject(result)
    const calibration = servedCalibration(result)
    const trimReport = outer['trim_report'] as Array<Record<string, unknown>>
    const drillPointers = outer['drill_pointers'] as Array<Record<string, unknown>>

    expect(result.isError).toBeFalsy()
    expect(Buffer.byteLength(JSON.stringify(result.structuredContent), 'utf8')).toBeLessThanOrEqual(40 * 1024)
    expect(JSON.stringify(outer)).not.toContain(TRUNCATION_MARKER)
    expect(calibration['verdict_distribution']).toHaveLength(4)
    expect(calibration['reliability_curve']).toHaveLength(6)
    expect(calibration['multipliers']).toHaveLength(9)
    expect((calibration['qa_summary'] as Record<string, unknown>)['total']).toBe(168)
    expect((calibration['qa_results'] as unknown[]).length).toBeGreaterThan(0)
    expect((calibration['qa_results'] as unknown[]).length).toBeLessThan(168)
    expect(outer['budget_kb_applied']).toBe(40)
    expect(trimReport).toEqual(expect.arrayContaining([
      expect.objectContaining({
        path: 'result.results[0].content.qa_results',
        recover_via: expect.objectContaining({ instrument: 'mimamsa_calibration_get' }),
      }),
    ]))
    expect(drillPointers).toEqual(expect.arrayContaining([
      expect.objectContaining({ instrument: 'mimamsa_calibration_get' }),
    ]))
  })

  it('returns the complete structured scorecard when a caller requests a sufficient budget', async () => {
    const payload = calibrationPayload()
    let forwardedParams: Record<string, unknown> | undefined
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init: { body: string }) => {
      forwardedParams = (JSON.parse(init.body) as { params: Record<string, unknown> }).params
      return primitiveResponse(JSON.stringify(payload))
    }))

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const capture = makeCapturingServer()
    registerP1AliasTools(capture.server, PRINCIPAL)

    const result = await capture.handlers.get('mimamsa_calibration_get')!({
      chart_id: CHART_ID,
      budget_kb: 200,
    })
    const outer = servedObject(result)
    const calibration = servedCalibration(result)

    expect(result.isError).toBeFalsy()
    expect(JSON.stringify(outer)).not.toContain(TRUNCATION_MARKER)
    expect(calibration['qa_results']).toHaveLength(168)
    expect(outer['trim_report']).toBeUndefined()
    expect(forwardedParams).toEqual({ chart_id: CHART_ID })
  })

  it('rejects malformed inner ToolBundle content instead of serving a success-shaped non-JSON payload', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => primitiveResponse('{"chart_id":')))

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const capture = makeCapturingServer()
    registerP1AliasTools(capture.server, PRINCIPAL)

    const result = await capture.handlers.get('mimamsa_calibration_get')!({ chart_id: CHART_ID })

    expect(result.isError).toBe(true)
    expect(result.content[0]!.text).toContain('content_not_json')
  })

  // F-27 (PARIŚEṢA V4) retarget: this case used to assert `domain` was absent, on the
  // then-believed premise that no domain filter could be derived from L5's schema.
  // Adversarial review disproved that premise — `mimamsa_calibration.prediction_id`
  // resolves to `mimamsa_predictions.domain` (`text NOT NULL`), and the filter is now
  // implemented and live-verified (57 rows -> 9 for domain='career' on the canonical
  // chart). `include_held_out`/`promoted_only` were likewise real capability filters that
  // no tool name could reach. The invariant this case actually guards is unchanged and
  // still enforced below: every advertised control must be backed by real behaviour —
  // hence `limit`/`offset` stay absent (the capability has no pagination at all) and
  // `budget_kb` stays presentation-only. See f27_calibration_param_contract.test.ts.
  it('advertises only real calibration controls: no no-op pagination params', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => primitiveResponse(JSON.stringify(calibrationPayload()))))

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const capture = makeCapturingServer()
    registerP1AliasTools(capture.server, PRINCIPAL)

    const schema = capture.schemas.get('mimamsa_calibration_get')!
    expect(schema).toHaveProperty('chart_id')
    expect(schema).toHaveProperty('budget_kb')
    // Real, implemented capability filters — each must reach the primitive.
    expect(schema).toHaveProperty('domain')
    expect(schema).toHaveProperty('include_held_out')
    expect(schema).toHaveProperty('promoted_only')
    // Genuinely unimplemented — the capability has no LIMIT/OFFSET path whatsoever.
    expect(schema).not.toHaveProperty('limit')
    expect(schema).not.toHaveProperty('offset')
  })
})
