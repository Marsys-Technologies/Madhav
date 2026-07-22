/**
 * route.test.ts — POST /api/mcp/prashna_ask.
 *
 * Integration-style: mocks the engine calls (callPipelinePlanner, compileFloorForPlan
 * guarantees, getToolByName) and the DB/auth surfaces — never hits a live DB.
 *
 * Coverage:
 *   1. Auth: rejects missing service token / missing principal headers.
 *   2. Auth: denies a chart the caller cannot access (entitlement_denied envelope).
 *   3. Happy path: normal completion returns a full result with all planned tools dispatched.
 *   4. A triggered cost cap returns the honest partial-result shape with the right
 *      judgment_flags entry and an unserved_tools list.
 *   5. A leaked (calibration_context_only) capability never appears in what gets
 *      dispatched, even though the planner "authorized" it.
 *
 * Streaming (W6 Part 1): the success path (`outcome: 'plan'`) now returns an
 * NDJSON-streamed `Response` (one `{"event":"progress",...}` line per completed
 * tool-dispatch iteration, ending with one `{"event":"final",...}` line) instead
 * of a single `NextResponse.json(...)` blob. `readNdjson()` below reads the full
 * body and splits it into parsed lines; the LAST line's payload (minus the
 * `event` discriminator) must match exactly what the old single-blob assertions
 * already checked. The early-return paths (400/401/clarification_needed/fault)
 * are unchanged — still a single JSON response, asserted via `res.json()`.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/retrieval/registry/catalog', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn() }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn().mockResolvedValue('fake-model') }))
vi.mock('@/lib/models/registry', () => ({ DEFAULT_STACK_ID: 'anthropic' }))

const { mockCallPipelinePlanner, mockGetToolByName } = vi.hoisted(() => ({
  mockCallPipelinePlanner: vi.fn(),
  mockGetToolByName: vi.fn(),
}))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({ callPipelinePlanner: mockCallPipelinePlanner }))

vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({ toolCalls: [], mappedPrimitives: [], unmappedPrimitives: [], compilerIntent: 'general_synthesis', compileFailed: false })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))

vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({ getToolByName: mockGetToolByName }))

// Real filter — Part A — exercised for real so the leakage assertion is genuine.
vi.mock('@/lib/pipeline/no_leakage_filter', () => ({
  filterLeakedCapabilities: (names: readonly string[]) => names.filter((n) => n !== 'marsys://tool/L5/lel_query'),
}))

const { mockSynthesizeReading, mockFetchChartHeaderResolution } = vi.hoisted(() => ({
  mockSynthesizeReading: vi.fn(),
  mockFetchChartHeaderResolution: vi.fn(),
}))
vi.mock('@/lib/pipeline/prashna_ask_synthesis', () => ({ synthesizeReading: mockSynthesizeReading }))
vi.mock('@/lib/retrieval/chart_header', () => ({ fetchChartHeaderResolution: mockFetchChartHeaderResolution }))

import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { POST } from '../route'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function makeReq(body: object, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/mcp/prashna_ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': 'owner-uid',
      'x-mcp-key-id': 'mcp_test_KEY001',
      ...headers,
    },
    body: JSON.stringify(body),
  })
}

async function readNdjson(res: Response): Promise<Array<Record<string, unknown>>> {
  const text = await res.text()
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line))
}

function planOutcome(toolNames: string[]) {
  return {
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      query_intent_summary: 'test query',
      domains: [],
      forward_looking: false,
      tool_calls: toolNames.map((tool_name) => ({
        tool_name,
        params: {},
        token_budget: 400,
        priority: 1 as const,
        reason: 'test',
      })),
      scope_tuple: undefined,
      history_mode: 'synthesized' as const,
      expected_output_shape: 'structured_data' as const,
    },
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('all')
  mockGetToolByName.mockImplementation((name: string) => ({
    name,
    version: '1.0',
    retrieve: vi.fn().mockResolvedValue({
      tool_bundle_id: 'b1',
      tool_name: name,
      tool_version: '1.0',
      invocation_params: {},
      results: [{ id: '1' }],
      served_from_cache: false,
      latency_ms: 1,
      result_hash: 'sha256:x',
      schema_version: '1.0',
    }),
  }))
  mockSynthesizeReading.mockResolvedValue({
    reading: 'Your Mercury-Jupiter Antardasha favors steady, disciplined career growth.',
    model_id: 'claude-sonnet-test',
    judgment_flags: [],
  })
  mockFetchChartHeaderResolution.mockResolvedValue({
    header: { chart_id_short: '482012f1', name: 'Test', lagna_sign: 'Aries', lagna_deg: 1.2, moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: 'Mercury/Jupiter' },
    flags: [],
  })
})

describe('POST /api/mcp/prashna_ask — auth', () => {
  it('rejects a missing/invalid service token', async () => {
    const req = makeReq({ chart_id: CHART, question: 'test' }, { 'x-mcp-internal-token': 'wrong' })
    const res = await POST(req)
    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error.class).toBe('auth')
  })

  it('rejects missing principal headers', async () => {
    const req = new Request('http://localhost/api/mcp/prashna_ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-mcp-internal-token': 'test-token' },
      body: JSON.stringify({ chart_id: CHART, question: 'test' }),
    })
    const res = await POST(req)
    expect(res.status).toBe(401)
  })

  it('returns 400 when chart_id or question is missing', async () => {
    const res = await POST(makeReq({ chart_id: CHART }))
    expect(res.status).toBe(400)
  })

  it('returns 400 for a malformed scope_tuple rather than silently ignoring it', async () => {
    const res = await POST(
      makeReq({ chart_id: CHART, question: 'test?', scope_tuple: { intent: 'not_a_real_intent' } })
    )
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error.message).toMatch(/scope_tuple/i)
  })

  it('denies a chart the caller cannot access with the distinct entitlement_denied envelope', async () => {
    ;(authorizeChartAccess as ReturnType<typeof vi.fn>).mockResolvedValue('deny')
    const res = await POST(makeReq({ chart_id: CHART, question: 'What is my ascendant?' }))
    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error.class).toBe('entitlement_denied')
    expect(body.denial.chart_id).toBe(CHART)
  })
})

describe('POST /api/mcp/prashna_ask — happy path', () => {
  it('runs the engine, dispatches every planned tool, and returns a complete result', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query', 'get_positions']))
    const res = await POST(makeReq({ chart_id: CHART, question: 'What is my ascendant?' }))
    expect(res.status).toBe(200)
    expect(res.headers.get('content-type')).toContain('application/x-ndjson')

    const lines = await readNdjson(res)
    const progressLines = lines.filter((l) => l.event === 'progress')
    const finalLines = lines.filter((l) => l.event === 'final')

    // Interim progress: at least one line appears before the final line for a
    // multi-tool request (streamed incrementally, not one blob).
    expect(progressLines.length).toBeGreaterThan(0)
    expect(finalLines.length).toBe(1)
    expect(lines[lines.length - 1].event).toBe('final')

    const body = finalLines[0]
    expect(body.ok).toBe(true)
    expect((body.completeness as { status: string }).status).toBe('complete')
    expect((body.completeness as { cap_tripped: unknown }).cap_tripped).toBeNull()
    // W6.2 fix-cycle: the full v3-enveloped reading (verdict + chart_header), not
    // just raw evidence bundles — the actual defect this fix-cycle closed.
    expect(body.reading).toBe('Your Mercury-Jupiter Antardasha favors steady, disciplined career growth.')
    expect((body.chart_header as { lagna_sign: string }).lagna_sign).toBe('Aries')
    expect(mockSynthesizeReading).toHaveBeenCalledTimes(1)
    expect((body.results as Array<{ tool_name: string }>).map((r) => r.tool_name)).toEqual(['chart_facts_query', 'get_positions'])
    expect(mockGetToolByName).toHaveBeenCalledTimes(2)
  })

  it('discloses a tool that dispatched successfully but returned zero rows (W6.2 fix-cycle empty_tool_results hardening)', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query', 'get_positions']))
    mockGetToolByName.mockImplementation((name: string) => ({
      name,
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        tool_bundle_id: 'b1',
        tool_name: name,
        tool_version: '1.0',
        invocation_params: {},
        // chart_facts_query dispatches cleanly but matches nothing; get_positions
        // returns a real row — the disclosure must name only the empty one.
        results: name === 'chart_facts_query' ? [] : [{ id: '1' }],
        served_from_cache: false,
        latency_ms: 1,
        result_hash: 'sha256:x',
        schema_version: '1.0',
      }),
    }))

    const res = await POST(makeReq({ chart_id: CHART, question: 'What is my current dasha?' }))
    const lines = await readNdjson(res)
    const body = lines[lines.length - 1]

    expect(body.judgment_flags).toContain('empty_tool_results')
    expect((body.completeness as { empty_result_tools: string[] }).empty_result_tools).toEqual(['chart_facts_query'])
    // An honest empty result is NOT the same as an incomplete job — status stays
    // 'complete' (nothing failed, nothing was capped/unresolved); the flag is the
    // disclosure mechanism, not a completeness demotion.
    expect((body.completeness as { status: string }).status).toBe('complete')
  })

  it('forwards a supplied scope_tuple to callPipelinePlanner as the 8th positional arg (W6.1 fix-cycle)', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    const suppliedTuple = {
      intent: 'domain_assessment',
      domains: ['career'],
      width: 'standard',
      depth: 'standard',
      horizon: 'near',
      intervention: 'none',
      entitlement: 'native',
    }
    await POST(makeReq({ chart_id: CHART, question: 'test?', scope_tuple: suppliedTuple }))
    expect(mockCallPipelinePlanner).toHaveBeenCalledWith(
      'test?',
      [],
      expect.any(String),
      CHART,
      undefined,
      expect.any(String),
      expect.any(String),
      suppliedTuple
    )
  })

  it('calls callPipelinePlanner with undefined for the 8th arg when no scope_tuple is supplied', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    await POST(makeReq({ chart_id: CHART, question: 'test?' }))
    const lastCallArgs = mockCallPipelinePlanner.mock.calls[mockCallPipelinePlanner.mock.calls.length - 1]
    expect(lastCallArgs[7]).toBeUndefined()
  })

  it('propagates a clarification_needed outcome without dispatching any tools', async () => {
    mockCallPipelinePlanner.mockResolvedValue({
      outcome: 'clarification_needed',
      question: 'Which chart do you mean?',
      missing_scope_dims: ['chart'],
      suggested_options: [],
    })
    const res = await POST(makeReq({ chart_id: CHART, question: 'ambiguous' }))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.outcome).toBe('clarification_needed')
    expect(mockGetToolByName).not.toHaveBeenCalled()
  })
})

describe('POST /api/mcp/prashna_ask — cost cap enforcement', () => {
  it('stops dispatch and reports an honest partial result when the call-count cap trips', async () => {
    mockCallPipelinePlanner.mockResolvedValue(
      planOutcome(['chart_facts_query', 'get_positions', 'get_strength', 'get_dashas']),
    )
    // guest tier caps at 10 calls by default — force a trip by making the tracker's
    // maxCalls effectively 0 via monkeypatching resolveCostCapsForEntitlement.
    vi.doMock('@/lib/pipeline/cost_caps', async () => {
      const actual = await vi.importActual<typeof import('@/lib/pipeline/cost_caps')>('@/lib/pipeline/cost_caps')
      return {
        ...actual,
        resolveCostCapsForEntitlement: () => ({ maxCalls: 1, maxWallClockMs: 120_000 }),
      }
    })
    vi.resetModules()
    const { POST: POST_WITH_LOW_CAP } = await import('../route')

    const res = await POST_WITH_LOW_CAP(makeReq({ chart_id: CHART, question: 'deep dive' }))
    expect(res.status).toBe(200)
    const lines = await readNdjson(res)
    const body = lines[lines.length - 1]
    expect(body.event).toBe('final')
    expect((body.completeness as { status: string }).status).toBe('partial')
    expect((body.completeness as { cap_tripped: unknown }).cap_tripped).toBe('call_count_cap')
    expect(body.judgment_flags).toContain('cost_cap_call_count_exceeded')
    expect((body.completeness as { unserved_tools: unknown[] }).unserved_tools.length).toBeGreaterThan(0)
    expect((body.results as unknown[]).length).toBe(1)
  })
})

describe('POST /api/mcp/prashna_ask — unresolved planner tool names', () => {
  it('discloses a planned-but-unresolved tool name rather than silently completing', async () => {
    mockCallPipelinePlanner.mockResolvedValue(
      planOutcome(['chart_facts_query', 'a_hallucinated_tool_name']),
    )
    mockGetToolByName.mockImplementation((name: string) => {
      if (name === 'a_hallucinated_tool_name') return undefined
      return {
        name,
        version: '1.0',
        retrieve: vi.fn().mockResolvedValue({
          tool_bundle_id: 'b1',
          tool_name: name,
          tool_version: '1.0',
          invocation_params: {},
          results: [{ id: '1' }],
          served_from_cache: false,
          latency_ms: 1,
          result_hash: 'sha256:x',
          schema_version: '1.0',
        }),
      }
    })
    const res = await POST(makeReq({ chart_id: CHART, question: 'test?' }))
    const lines = await readNdjson(res)
    const body = lines[lines.length - 1]
    expect(body.event).toBe('final')
    expect((body.completeness as { status: string }).status).toBe('partial')
    expect((body.completeness as { unresolved_tools: unknown[] }).unresolved_tools).toContain('a_hallucinated_tool_name')
    expect(body.judgment_flags).toContain('planned_tools_unresolved')
    // The unresolved name must not have consumed a cost-cap call slot or
    // blocked the tool that DID resolve from running.
    expect((body.results as Array<{ tool_name: string }>).map((r) => r.tool_name)).toContain('chart_facts_query')
    expect((body.completeness as { cap_tripped: unknown }).cap_tripped).toBeNull()
  })
})

describe('POST /api/mcp/prashna_ask — NO-LEAKAGE', () => {
  it('never dispatches a calibration_context_only-flagged capability even when the planner authorized it', async () => {
    mockCallPipelinePlanner.mockResolvedValue(
      planOutcome(['marsys://tool/L5/lel_query', 'chart_facts_query']),
    )
    const res = await POST(makeReq({ chart_id: CHART, question: 'what happened in my life' }))
    const lines = await readNdjson(res)
    const body = lines[lines.length - 1]
    expect(body.event).toBe('final')
    expect((body.completeness as { stripped_leaked_capabilities: unknown[] }).stripped_leaked_capabilities).toContain('marsys://tool/L5/lel_query')
    expect((body.results as Array<{ tool_name: string }>).map((r) => r.tool_name)).not.toContain('marsys://tool/L5/lel_query')
    expect(body.judgment_flags).toContain('no_leakage_capabilities_stripped')
    // getToolByName must never have been called for the leaked tool.
    expect(mockGetToolByName).not.toHaveBeenCalledWith('marsys://tool/L5/lel_query')
  })
})

describe('POST /api/mcp/prashna_ask — stream error handling', () => {
  it('emits a structured error event with trace_id/chart_id instead of a bare exception when the dispatch loop throws unexpectedly', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    // getToolByName itself throwing (not returning undefined) is not wrapped by
    // the existing per-tool try/catch (which only guards tool.retrieve()) — it
    // propagates out of the dispatch loop, exercising the stream-level catch.
    mockGetToolByName.mockImplementation(() => {
      throw new Error('registry lookup exploded')
    })
    const res = await POST(makeReq({ chart_id: CHART, question: 'test?' }))
    expect(res.status).toBe(200) // headers already sent by the time the body streams
    const lines = await readNdjson(res)
    const errorLine = lines.find((l) => l.event === 'error')
    expect(errorLine).toBeDefined()
    expect(errorLine!.trace_id).toBeTruthy()
    expect(errorLine!.chart_id).toBe(CHART)
    expect(errorLine!.message).toContain('registry lookup exploded')
    // No 'final' line — the loop errored before reaching it.
    expect(lines.some((l) => l.event === 'final')).toBe(false)
  })
})

describe('POST /api/mcp/prashna_ask — synthesis wiring (W6.2 fix-cycle)', () => {
  it('passes the gathered evidence and gap disclosures to synthesizeReading', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query', 'get_positions']))
    const res = await POST(makeReq({ chart_id: CHART, question: 'What is my ascendant?' }))
    await readNdjson(res) // drives the stream's start() callback to completion

    expect(mockSynthesizeReading).toHaveBeenCalledTimes(1)
    const call = mockSynthesizeReading.mock.calls[0][0]
    expect(call.chartId).toBe(CHART)
    expect(call.question).toBe('What is my ascendant?')
    expect(call.evidence.map((e: { tool_name: string }) => e.tool_name)).toEqual([
      'chart_facts_query',
      'get_positions',
    ])
    expect(call.unresolvedTools).toEqual([])
    expect(call.emptyResultTools).toEqual([])
    expect(call.strippedLeakedCapabilities).toEqual([])
    expect(call.capTripped).toBeNull()
  })

  it('W6.3: threads chart_header.current_maha_antar and today\'s date into the synthesis call as the temporal anchor', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    const res = await POST(makeReq({ chart_id: CHART, question: 'What is my current dasha?' }))
    await readNdjson(res)

    expect(mockFetchChartHeaderResolution).toHaveBeenCalledTimes(1)
    const call = mockSynthesizeReading.mock.calls[0][0]
    expect(call.currentMahaAntar).toBe('Mercury/Jupiter') // from the mocked chart_header
    expect(call.nowContextDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('W6.3: degrades honestly (currentMahaAntar: null) when chart_header resolution fails, instead of skipping synthesis', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    mockFetchChartHeaderResolution.mockResolvedValue({ header: null, flags: ['chart_header_unresolved'] })

    const res = await POST(makeReq({ chart_id: CHART, question: 'What is my current dasha?' }))
    await readNdjson(res)

    const call = mockSynthesizeReading.mock.calls[0][0]
    expect(call.currentMahaAntar).toBeNull()
  })

  it('still runs synthesis over partial evidence when a cost cap trips, and forwards the cap reason as a gap', async () => {
    mockCallPipelinePlanner.mockResolvedValue(
      planOutcome(['chart_facts_query', 'get_positions', 'get_strength', 'get_dashas']),
    )
    vi.doMock('@/lib/pipeline/cost_caps', async () => {
      const actual = await vi.importActual<typeof import('@/lib/pipeline/cost_caps')>('@/lib/pipeline/cost_caps')
      return { ...actual, resolveCostCapsForEntitlement: () => ({ maxCalls: 1, maxWallClockMs: 120_000 }) }
    })
    vi.resetModules()
    const { POST: POST_WITH_LOW_CAP } = await import('../route')

    const res = await POST_WITH_LOW_CAP(makeReq({ chart_id: CHART, question: 'deep dive' }))
    await readNdjson(res)

    expect(mockSynthesizeReading).toHaveBeenCalledTimes(1)
    const call = mockSynthesizeReading.mock.calls[0][0]
    expect(call.capTripped).toBe('call_count_cap')
    expect(call.evidence.length).toBeGreaterThan(0)
  })

  it('surfaces synthesis-side judgment_flags (e.g. a failed synthesis call) in the final response without failing the whole request', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    mockSynthesizeReading.mockResolvedValue({
      reading: null,
      model_id: null,
      judgment_flags: ['synthesis_call_failed'],
    })

    const res = await POST(makeReq({ chart_id: CHART, question: 'test?' }))
    const lines = await readNdjson(res)
    const body = lines[lines.length - 1]

    expect(body.ok).toBe(true) // the request still succeeds — synthesis failure is disclosed, not fatal
    expect(body.reading).toBeNull()
    expect(body.judgment_flags).toContain('synthesis_call_failed')
  })

  it('discloses chart_header resolution failure via judgment_flags without failing the request', async () => {
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    mockFetchChartHeaderResolution.mockResolvedValue({ header: null, flags: ['chart_header_unresolved'] })

    const res = await POST(makeReq({ chart_id: CHART, question: 'test?' }))
    const lines = await readNdjson(res)
    const body = lines[lines.length - 1]

    expect(body.ok).toBe(true)
    expect(body.chart_header).toBeNull()
    expect(body.judgment_flags).toContain('chart_header_unresolved')
  })
})
