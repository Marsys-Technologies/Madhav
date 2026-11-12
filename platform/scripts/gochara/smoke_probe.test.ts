// @vitest-environment node
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

// Runs in the CLI subprocess before the probe. The fixture has no real endpoint,
// credential, chart payload or network path.
function mockFetch(scenario: string) {
  let calls = 0
  let primaryChart: string
  let crossCheckChart: string
  const expectedTools = [
    'gochara_forecast_get', 'gochara_forecast_get',
    'gochara_activation_get', 'gochara_activation_get',
    'gochara_election_avoidance_get', 'gochara_election_avoidance_get',
    'kala_now_get', 'judgment_query',
  ]
  globalThis.fetch = async (input, options) => {
    if (scenario === 'plan') throw new Error('unexpected plan fetch')
    if (input !== 'https://fixture.invalid/mcp' || options?.method !== 'POST') {
      throw new Error('unexpected fixture request')
    }
    const request = JSON.parse(String(options.body))
    if (request.method !== 'tools/call' || request.jsonrpc !== '2.0' || !options.signal) {
      throw new Error('unexpected fixture protocol')
    }
    const tool = request.params.name
    const args = request.params.arguments
    const chart = args.chart_id
    const gochara = tool.startsWith('gochara_')
    calls++
    if (tool !== expectedTools[calls - 1] || typeof chart !== 'string' || !chart) {
      throw new Error('unexpected fixture call order')
    }
    if (calls === 1) primaryChart = chart
    if (calls === 2) crossCheckChart = chart
    const usesCrossCheck = calls === 2 || calls === 4 || calls === 6
    if ((calls > 1 && primaryChart === crossCheckChart) || chart !== (usesCrossCheck ? crossCheckChart : primaryChart)) {
      throw new Error('unexpected fixture chart binding')
    }
    const needsDateRange = tool === 'gochara_forecast_get' || tool === 'gochara_election_avoidance_get'
    const isDate = (value: unknown) => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
    if ((needsDateRange && (!isDate(args.date_range?.start) || !isDate(args.date_range?.end)))
      || (!needsDateRange && 'date_range' in args)
      || (!gochara && args.ayanamsha_id !== 'lahiri_chitrapaksha')
      || (tool === 'judgment_query' && args.domain !== 'career')) {
      throw new Error('unexpected fixture arguments')
    }
    const selected = calls === (scenario.startsWith('judgment_') ? 8 : scenario === 'baseline_non_2xx' ? 7 : 1)
    const refusal = selected && scenario.startsWith('not_covered')
    const withheld = selected && scenario === 'withheld'
    const unpublished = withheld || (selected && scenario === 'unpublished')
    const provenance: Record<string, unknown> = {
      source: tool,
      chart_id: chart,
      window_count: 0,
      backing_data_reachable: !(selected && (scenario === 'nested_false' || scenario === 'not_covered_false')),
      empty_reason: refusal ? null : withheld ? 'fixture generation withheld' : 'fixture honest empty',
    }
    if (selected && scenario === 'missing_reachability') delete provenance.backing_data_reachable
    const gocharaPayload = {
      windows: [],
      coverage: {
        event_classes_covered: [],
        domains_not_covered: refusal ? ['fixture'] : [],
        sweep_completeness: { substeps_committed: 0 },
        ...(unpublished ? { status: 'unpublished' } : {}),
        ...(withheld ? { withheld_reason: 'fixture generation withheld' } : {}),
      },
      provenance_envelope: provenance,
      ...(refusal ? { not_covered: { domain: 'fixture', cross_pointer: { instrument: 'kala_windows_get', hint: 'fixture' } } } : {}),
    }
    // register_d9_judgment returns { content, is_error }. The capability route
    // wraps it in { ok: true, content }, then registry_bridge unwraps its content
    // into a retrieval envelope, losing is_error. dualOutputBudgeted keeps that
    // envelope in structuredContent.object and suppresses the JSON text duplicate.
    const judgmentErrors: Record<string, Record<string, unknown>> = {
      judgment_resolution_error: { error: 'fixture-private-decoy', code: 'served_generation_resolution_failed', chart_id: chart },
      judgment_no_generation: { error: 'fixture-private-decoy', code: 'no_served_generation', chart_id: chart, unresolved_assets: [] },
      judgment_handler_error: { error: 'fixture-private-decoy', chart_id: chart },
    }
    const judgmentDisclosure = selected && scenario === 'judgment_disclosures'
    const judgmentPayload = {
      envelope_version: 'v3', response_format: 'v3', tool,
      orientation_context: judgmentDisclosure
        ? { content: { error: 'fixture-private-decoy' }, is_error: true }
        : { content: {}, is_error: false },
      orientation_ok: !judgmentDisclosure,
      verdict: { receipt: { timing_anchored: false, varga_confirmed: null } },
      grounding: { fact_ids: [], citations: [], grounding_score: null },
      judgment_flags: judgmentDisclosure
        ? [{ code: 'served_generation_unresolved_assets', detail: 'synthetic unresolved leg disclosed' }]
        : [],
      drill_pointers: [],
      content: judgmentErrors[scenario] ?? {
        chart_id: chart, build_id: 'synthetic-build', about: { domain: 'career' },
        checklist: { bearing_yogas: [], varga_confirmation: { rows: [] } },
        receipt: { timing_anchored: false, varga_confirmed: null },
        fact_id_refs: [],
      },
    }
    const payload = gochara ? gocharaPayload : tool === 'judgment_query'
      ? judgmentPayload : { tool, chart_id: chart, evidence: 'synthetic' }
    const result = gochara
      ? { content: [{ type: 'text', text: JSON.stringify(payload) }] }
      : {
        content: [{ type: 'text', text: tool === 'judgment_query'
          ? '[budget-capped response — see structuredContent; text duplicate suppressed for this instrument per R5.1 C1]'
          : JSON.stringify(payload) }],
        structuredContent: { type: 'object', object: payload },
      }
    const reply = { jsonrpc: '2.0', id: request.id, result }

    if (selected) {
      if (scenario === 'judgment_bridge_error') {
        const error = { ok: false, error: { class: 'internal_error', message: 'fixture-private-decoy' }, tool, chart_id: chart }
        return Response.json({ ...reply, result: {
          isError: true,
          structuredContent: { type: 'object', object: error },
          content: [{ type: 'text', text: JSON.stringify(error) }],
        } })
      }
      if (scenario === 'non_2xx' || scenario === 'baseline_non_2xx') {
        return new Response('fixture-private-decoy', { status: 401 })
      }
      if (scenario === 'invalid_json') {
        return new Response('fixture-private-decoy', { headers: { 'content-type': 'application/json' } })
      }
      if (scenario === 'wrong_version') return Response.json({ ...reply, jsonrpc: '1.0' })
      if (scenario === 'rpc_result_and_error') {
        return Response.json({ ...reply, error: { code: -32603, message: 'fixture-private-decoy' } })
      }
      if (scenario === 'wrong_id') return Response.json({ ...reply, id: request.id + 1 })
      if (scenario === 'missing_result') return Response.json({ jsonrpc: '2.0', id: request.id })
      if (scenario === 'empty_payload') return Response.json({ ...reply, result: { content: [{ type: 'text', text: '{}' }] } })
      if (scenario === 'rpc_error') {
        return Response.json({ jsonrpc: '2.0', id: request.id, error: { code: -32603, message: 'fixture-private-decoy' } })
      }
      if (scenario === 'tool_error') {
        return Response.json({ ...reply, result: { isError: true, content: [{ type: 'text', text: 'fixture-private-decoy' }] } })
      }
      if (scenario === 'timeout') throw new DOMException('fixture-private-decoy', 'TimeoutError')
      if (['sse', 'duplicate_sse', 'unterminated_sse'].includes(scenario)) {
        const unrelated = JSON.stringify({ jsonrpc: '2.0', id: request.id + 1, error: { code: -32603 } })
        const matching = JSON.stringify(reply, null, 2).split('\n').map((line) => 'data: ' + line).join('\r\n')
        const separator = scenario === 'unterminated_sse' ? '\r\n' : '\r\n\r\n'
        const body = ': fixture\r\n\r\n' + 'data: ' + unrelated + '\r\n\r\n' + matching + separator
        return new Response(body + (scenario === 'duplicate_sse' ? matching + '\r\n\r\n' : ''), {
          headers: { 'content-type': 'text/event-stream; charset=utf-8' },
        })
      }
    }
    return Response.json(reply)
  }
}

type Report = {
  summary: { pass: number; fail: number; skipped: number; total: number }
  results: { id: string; status: string; detail: string }[]
}

function runProbe(scenario: string) {
  const preload = Buffer.from(`(${mockFetch.toString()})(${JSON.stringify(scenario)})`).toString('base64')
  const probe = fileURLToPath(new URL('./smoke_probe.ts', import.meta.url))
  const result = spawnSync(process.execPath, [
    '--import', 'tsx', '--import', `data:text/javascript;base64,${preload}`, probe,
  ], {
    encoding: 'utf8',
    timeout: 8_000,
    env: {
      PATH: '/usr/bin:/bin',
      ...(process.env.TMPDIR ? { TMPDIR: process.env.TMPDIR } : {}),
      TSX_DISABLE_CACHE: '1',
      ...(scenario === 'plan' ? {} : { MCP_SERVER_URL: 'https://fixture.invalid/mcp' }),
    },
  })
  expect(result.error).toBeUndefined()
  return result
}

function report(scenario: string) {
  const result = runProbe(scenario)
  expect((result.stdout + result.stderr).includes('fixture-private-decoy')).toBe(false)
  return { exit: result.status, data: JSON.parse(result.stdout) as Report }
}

describe('MR-35 CLI probe', () => {
  it('keeps plan mode free of calls', () => {
    const result = runProbe('plan')
    expect(result.status).toBe(0)
    expect(result.stdout).toContain('PLAN MODE')
  })

  it('runs the eight-call matrix on matching JSON results', () => {
    const { exit, data } = report('healthy')
    expect(exit).toBe(0)
    expect(data.summary).toEqual({ pass: 8, fail: 0, skipped: 0, total: 8 })
    expect(data.results.map(({ id }) => id)).toEqual([
      'gochara:gochara_forecast_get:primary',
      'gochara:gochara_forecast_get:cross-check',
      'gochara:gochara_activation_get:primary',
      'gochara:gochara_activation_get:cross-check',
      'gochara:gochara_election_avoidance_get:primary',
      'gochara:gochara_election_avoidance_get:cross-check',
      'baseline:kala_now_get',
      'baseline:judgment_query',
    ])
  })

  it('uses the matching complete SSE event after an unrelated event', () => {
    const { exit, data } = report('sse')
    expect(exit).toBe(0)
    expect(data.summary.pass).toBe(8)
  })

  it.each([
    ['nested_false', 'backing_data_unreachable'],
    ['not_covered_false', 'backing_data_unreachable'],
    ['missing_reachability', 'missing_gochara_evidence'],
    ['non_2xx', 'http_failure'],
    ['baseline_non_2xx', 'http_failure'],
    ['invalid_json', 'invalid_rpc'],
    ['wrong_id', 'invalid_rpc'],
    ['wrong_version', 'invalid_rpc'],
    ['rpc_result_and_error', 'invalid_rpc'],
    ['missing_result', 'invalid_rpc'],
    ['empty_payload', 'missing_payload'],
    ['rpc_error', 'rpc_error'],
    ['tool_error', 'tool_error'],
    ['timeout', 'timeout'],
    ['duplicate_sse', 'invalid_rpc'],
    ['unterminated_sse', 'invalid_rpc'],
  ])('fails %s with a safe reason', (scenario, detail) => {
    const { exit, data } = report(scenario)
    expect(exit).toBe(1)
    expect(data.summary.fail).toBe(1)
    expect(data.results.find((item) => item.status === 'FAIL')?.detail).toBe(detail)
  })

  it.each([
    'judgment_resolution_error',
    'judgment_no_generation',
    'judgment_handler_error',
  ])('fails the actual budgeted judgment envelope for %s', (scenario) => {
    const { exit, data } = report(scenario)
    expect(exit).toBe(1)
    expect(data.summary).toEqual({ pass: 7, fail: 1, skipped: 0, total: 8 })
    expect(data.results[7]).toMatchObject({ status: 'FAIL', detail: 'judgment_error' })
  })

  it('retains the existing MCP bridge error rejection for the judgment baseline', () => {
    const { exit, data } = report('judgment_bridge_error')
    expect(exit).toBe(1)
    expect(data.summary).toEqual({ pass: 7, fail: 1, skipped: 0, total: 8 })
    expect(data.results[7]).toMatchObject({ status: 'FAIL', detail: 'tool_error' })
  })

  it('accepts successful judgment content with honest empty legs and overlay disclosures', () => {
    const { exit, data } = report('judgment_disclosures')
    expect(exit).toBe(0)
    expect(data.summary).toEqual({ pass: 8, fail: 0, skipped: 0, total: 8 })
    expect(data.results[7]).toMatchObject({ status: 'PASS', detail: 'baseline_response' })
  })

  it('reports an honest not_covered refusal separately from completed scans', () => {
    const { exit, data } = report('not_covered')
    expect(exit).toBe(0)
    expect(data.summary).toEqual({ pass: 7, fail: 0, skipped: 1, total: 8 })
    expect(data.results[0]).toMatchObject({ status: 'SKIPPED', detail: 'not_covered' })
  })

  it.each([
    ['withheld', 'generation_withheld'],
    ['unpublished', 'generation_unpublished'],
  ])('reports %s generation evidence separately from a completed scan', (scenario, detail) => {
    const { exit, data } = report(scenario)
    expect(exit).toBe(0)
    expect(data.summary).toEqual({ pass: 7, fail: 0, skipped: 1, total: 8 })
    expect(data.results[0]).toMatchObject({ status: 'SKIPPED', detail })
  })
})
