/**
 * primitives.test.ts — Tests for the MCP primitives dispatcher.
 *
 * Tests cover:
 *   1. Auth: missing X-MCP-User header → 401
 *   2. Whitelist enforcement: non-whitelisted tool → {ok: false, error: {class: "validation"}} 400
 *   3. Surgical flag: happy-path call → epistemics.surgical === true
 *   4. Trace step log: happy-path → trace step written with source: "mcp_primitive"
 *   5. All 10 tools reachable: isAllowedSurgicalTool(MCP_TOOL_NAME) returns true for each
 *
 * Approach: unit-tests the registry functions directly (test 5), and uses
 * module mocks for route-level tests (tests 1–4) to avoid DB connections.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Test 5: isAllowedSurgicalTool / MCP_TO_RETRIEVAL_TOOL unit tests ──────────

// D7 Step 4: primitives_registry retired — imports moved to tool_name_bridge
import {
  isAllowedSurgicalTool,
  MCP_TO_RETRIEVAL_TOOL,
  SURGICAL_TOOLS,
} from '@/lib/retrieval/registry/tool_name_bridge'

describe('primitives_registry — isAllowedSurgicalTool', () => {
  it('returns true for all whitelisted tool names', () => {
    const mcpToolNames = Object.keys(MCP_TO_RETRIEVAL_TOOL)
    // 34 post-WP-1.7 + 13 WP-1.3a + 5 WP-1.3j + 1 DOCTRINE-WAVES D-4b Lane B-5
    // (mechanism_retrodiction_get)
    expect(mcpToolNames).toHaveLength(53)
    for (const name of mcpToolNames) {
      expect(isAllowedSurgicalTool(name)).toBe(true)
    }
  })

  it('returns false for non-whitelisted tool names', () => {
    // WP-1.7: pattern_register and resonance_register REMOVED (no backing capability) → rejected
    expect(isAllowedSurgicalTool('pattern_register')).toBe(false)
    expect(isAllowedSurgicalTool('resonance_register')).toBe(false)
    // These remain non-whitelisted
    expect(isAllowedSurgicalTool('ask_madhav')).toBe(false)
    expect(isAllowedSurgicalTool('')).toBe(false)
    expect(isAllowedSurgicalTool('__proto__')).toBe(false)
  })

  it('MCP_TO_RETRIEVAL_TOOL maps all entries to valid SURGICAL_TOOLS members', () => {
    for (const [, retrievalName] of Object.entries(MCP_TO_RETRIEVAL_TOOL)) {
      expect(SURGICAL_TOOLS).toContain(retrievalName)
    }
  })

  it('all 23 expected tool names are present in the whitelist', () => {
    const expected = [
      // Original 11
      'query_chart_facts',
      'query_signals',
      'query_dasha_periods',
      'query_panchanga',
      'query_ephemeris',
      'query_transit_event',
      'lel_query',
      'vector_search',
      'get_cgm_subgraph',
      // WP-1.7: cross_school_lookup removed (no backing capability)
      'read_classical_text',
      // TR Wave Class A — MCP-facing names
      'query_varshphal',
      'query_divisional_chart',
      'query_remedial_mantras',
      'muhurta_finder',
      // TR Wave Class A — retrieval-name aliases (wrappers call with retrieval name)
      'query_varshaphala',
      'divisional_query',
      'remedial_codex_query',
      'query_muhurat',
      // Tara/Chandra bala (now resolve → get_tara_chandra_bala)
      'query_tara_balam',
      'query_chandra_balam',
      // WP-1.7: jaimini_chara_dasha[_full] removed (TR Wave stubs, never built)
    ]
    for (const name of expected) {
      expect(isAllowedSurgicalTool(name)).toBe(true)
    }
  })

  it('MCP_TO_RETRIEVAL_TOOL maps query_chart_facts → chart_facts_query', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['query_chart_facts']).toBe('chart_facts_query')
  })

  it('MCP_TO_RETRIEVAL_TOOL maps query_signals → msr_sql', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['query_signals']).toBe('msr_sql')
  })

  it('MCP_TO_RETRIEVAL_TOOL maps get_cgm_subgraph → cgm_graph_walk', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['get_cgm_subgraph']).toBe('cgm_graph_walk')
  })

  it('WP-1.7: cross_school_lookup removed (multi_school_signal_lookup never bridged to registry)', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['cross_school_lookup']).toBeUndefined()
  })
})

// ── Dispatcher route unit tests (mocked) ──────────────────────────────────────

// We mock the heavy dependencies so we don't need a live DB or retrieval tools.

// D7 Step 4: route now calls getToolByName from tool_name_bridge (lib/retrieve/index RETIRED)
// Prevent catalog side-effect import from populating the capability registry during
// unit tests — otherwise isPerChartPrimitive() returns true for per_chart tools (e.g.
// query_signals) and the route returns 400 CHART_REQUIRED before the trace emit.
vi.mock('@/lib/retrieval/registry/catalog', () => ({}))

vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return {
    ...real,
    getToolByName: vi.fn(),
  }
})

vi.mock('@/lib/trace/emitter', () => ({
  traceEmitter: {
    emitStep: vi.fn(),
  },
}))

vi.mock('@/lib/mcp/epistemics', async (importOriginal) => {
  // Use the real implementations for envelope builders (they don't hit DB).
  const real = await importOriginal<typeof import('@/lib/mcp/epistemics')>()
  return real
})

import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { traceEmitter } from '@/lib/trace/emitter'
import { POST } from '@/app/api/mcp/primitives/[tool]/route'

const mockGetTool = vi.mocked(getToolByName)
const mockTraceEmitter = vi.mocked(traceEmitter)

// Helper to build a request with service-token + principal headers
function buildRequest(
  toolName: string,
  opts: {
    missingUser?: boolean
    missingToken?: boolean
    params?: Record<string, unknown>
    extraHeaders?: Record<string, string>
  } = {}
) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'x-mcp-internal-token': 'test-internal-token',
    'x-mcp-user': 'uid_test_user',
    'x-mcp-audience-tier': 'super_admin',
    'x-mcp-key-id': 'mcp_test_abc12345',
    ...(opts.extraHeaders ?? {}),
  }
  if (opts.missingUser) delete headers['x-mcp-user']
  if (opts.missingToken) delete headers['x-mcp-internal-token']

  return new Request(`http://localhost:3000/api/mcp/primitives/${toolName}`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ params: opts.params ?? {} }),
  })
}

// Mock route params helper
function buildRouteParams(toolName: string) {
  return { params: Promise.resolve({ tool: toolName }) }
}

describe('POST /api/mcp/primitives/[tool] — dispatcher', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // In test env, MCP_INTERNAL_TOKEN is not set → dev mode allows all (NODE_ENV=test ≠ development)
    // Set the env var to our test value
    process.env['MCP_INTERNAL_TOKEN'] = 'test-internal-token'
    // NODE_ENV is read-only in Next.js type definitions; set MCP_INTERNAL_TOKEN to match header
    // so validation passes (dev fallback also works in vitest environment)
  })

  it('Test 1 (auth): missing X-MCP-User header returns 401', async () => {
    const req = buildRequest('query_chart_facts', { missingUser: true })
    const res = await POST(req, buildRouteParams('query_chart_facts'))
    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('auth')
  })

  it('Test 2 (whitelist): non-whitelisted tool returns 400 with class: validation', async () => {
    // ask_madhav is an end-to-end tool, never a surgical primitive → always rejected
    const req = buildRequest('ask_madhav')
    const res = await POST(req, buildRouteParams('ask_madhav'))
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('validation')
    expect(body.error.message).toContain('ask_madhav')
  })

  it('Test 3 (surgical flag): happy-path call returns epistemics.surgical === true', async () => {
    // Mock the tool to return a simple result
    mockGetTool.mockReturnValue({
      name: 'chart_facts_query',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({ rows: [{ planet: 'Saturn', category: 'shadbala' }] }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('query_chart_facts', { params: { category: 'shadbala' } })
    const res = await POST(req, buildRouteParams('query_chart_facts'))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.epistemics.surgical).toBe(true)
  })

  it('Test 4 (trace log): happy-path call logs trace step with source: mcp_primitive', async () => {
    mockGetTool.mockReturnValue({
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({ signals: [] }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('query_signals', { params: { domain: 'career' } })
    await POST(req, buildRouteParams('query_signals'))

    // Verify traceEmitter.emitStep was called with source: mcp_primitive
    expect(mockTraceEmitter.emitStep).toHaveBeenCalledOnce()
    const callArg = mockTraceEmitter.emitStep.mock.calls[0]?.[0]
    expect(callArg).toBeDefined()
    // The step payload items[0].source should be "mcp_primitive"
    const itemSource = callArg?.step?.payload?.items?.[0]?.source ?? ''
    expect(itemSource).toBe('mcp_primitive')
  })

  it('Test 5 (C3a): get_cgm_subgraph with node_id wires graph_seed_hints into queryPlan', async () => {
    // Capture the queryPlan passed to tool.retrieve to verify graph_seed_hints injection.
    let capturedPlan: Record<string, unknown> | null = null
    mockGetTool.mockReturnValue({
      name: 'cgm_graph_walk',
      version: '1.0',
      retrieve: vi.fn().mockImplementation((plan: Record<string, unknown>) => {
        capturedPlan = plan
        return Promise.resolve({ nodes: [], edges: [] })
      }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('get_cgm_subgraph', { params: { node_id: 'MERCURY_10H', hops: 2 } })
    const res = await POST(req, buildRouteParams('get_cgm_subgraph'))
    expect(res.status).toBe(200)

    // graph_seed_hints must be present and contain the node_id value
    expect(capturedPlan).not.toBeNull()
    expect(capturedPlan!['graph_seed_hints']).toEqual(['MERCURY_10H'])
    expect(capturedPlan!['graph_traversal_depth']).toBe(2)
  })

  it('Test 5b (C3a): get_cgm_subgraph without node_id does NOT add graph_seed_hints', async () => {
    let capturedPlan: Record<string, unknown> | null = null
    mockGetTool.mockReturnValue({
      name: 'cgm_graph_walk',
      version: '1.0',
      retrieve: vi.fn().mockImplementation((plan: Record<string, unknown>) => {
        capturedPlan = plan
        return Promise.resolve({ nodes: [], edges: [] })
      }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('get_cgm_subgraph', { params: {} })
    await POST(req, buildRouteParams('get_cgm_subgraph'))

    expect(capturedPlan!['graph_seed_hints']).toBeUndefined()
    expect(capturedPlan!['graph_traversal_depth']).toBeUndefined()
  })

  // ── CR-118 (RC-11) regression — chart_id threaded onto queryPlan ───────────
  //
  // This route resolved `chartId` (params['chart_id'] ?? x-mcp-chart-id header)
  // for the entitlement gate ONLY — the `queryPlan` object handed to
  // `tool.retrieve(queryPlan, toolParams)` carried no `chart_id` field at all.
  // tool_name_bridge.ts's getToolByName().retrieve() reads chart_id off the
  // PLAN (`plan['chart_id']`), not off `params`, to populate the per_chart
  // handler's `args.chart_id` — so a caller supplying chart_id only via the
  // X-MCP-Chart-Id header (never inside `params`) would reach the capability
  // handler with no chart_id and fast-fail immediately, matching CR-118's
  // single-digit-ms error/empty pattern for msr_sql/get_yoga_firings/
  // cgm_graph_walk. See MARSYS_DEFECT_GAP_REGISTER_v2_0.md CR-118.
  const NATIVE_CHART = '482012f1-710e-4a25-994a-93821f5871aa'

  it('CR-118: chart_id supplied in params reaches queryPlan.chart_id', async () => {
    let capturedPlan: Record<string, unknown> | null = null
    mockGetTool.mockReturnValue({
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockImplementation((plan: Record<string, unknown>) => {
        capturedPlan = plan
        return Promise.resolve({ signals: [] })
      }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('query_signals', { params: { chart_id: NATIVE_CHART, domain: 'career' } })
    const res = await POST(req, buildRouteParams('query_signals'))
    expect(res.status).toBe(200)

    expect(capturedPlan).not.toBeNull()
    expect(capturedPlan!['chart_id']).toBe(NATIVE_CHART)
  })

  it('CR-118: chart_id supplied ONLY via X-MCP-Chart-Id header still reaches queryPlan.chart_id', async () => {
    let capturedPlan: Record<string, unknown> | null = null
    mockGetTool.mockReturnValue({
      name: 'cgm_graph_walk',
      version: '1.0',
      retrieve: vi.fn().mockImplementation((plan: Record<string, unknown>) => {
        capturedPlan = plan
        return Promise.resolve({ nodes: [], edges: [] })
      }),
    } as unknown as ReturnType<typeof getToolByName>)

    // chart_id deliberately absent from params — header-only, the path CR-118's
    // fast-fail would have hit pre-fix (queryPlan.chart_id stayed undefined
    // regardless of how chartId was resolved for the entitlement check).
    const req = buildRequest('get_cgm_subgraph', {
      params: {},
      extraHeaders: { 'x-mcp-chart-id': NATIVE_CHART },
    })
    const res = await POST(req, buildRouteParams('get_cgm_subgraph'))
    expect(res.status).toBe(200)

    expect(capturedPlan).not.toBeNull()
    expect(capturedPlan!['chart_id']).toBe(NATIVE_CHART)
  })

  it('CR-118: chart-agnostic tool (vector_search) never has chart_id fabricated onto queryPlan', async () => {
    let capturedPlan: Record<string, unknown> | null = null
    mockGetTool.mockReturnValue({
      name: 'vector_search',
      version: '1.0',
      retrieve: vi.fn().mockImplementation((plan: Record<string, unknown>) => {
        capturedPlan = plan
        return Promise.resolve({ results: [] })
      }),
    } as unknown as ReturnType<typeof getToolByName>)

    const req = buildRequest('vector_search', { params: { query: 'test' } })
    const res = await POST(req, buildRouteParams('vector_search'))
    expect(res.status).toBe(200)

    expect(capturedPlan).not.toBeNull()
    expect(capturedPlan!['chart_id']).toBeUndefined()
  })
})
