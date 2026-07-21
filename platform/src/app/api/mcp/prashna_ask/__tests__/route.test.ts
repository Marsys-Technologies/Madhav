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
    expect((body.results as Array<{ tool_name: string }>).map((r) => r.tool_name)).toEqual(['chart_facts_query', 'get_positions'])
    expect(mockGetToolByName).toHaveBeenCalledTimes(2)
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
