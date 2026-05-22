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

import {
  isAllowedSurgicalTool,
  MCP_TO_RETRIEVAL_TOOL,
  SURGICAL_TOOLS,
} from '@/lib/mcp/primitives_registry'

describe('primitives_registry — isAllowedSurgicalTool', () => {
  it('returns true for all 11 MCP-facing tool names', () => {
    const mcpToolNames = Object.keys(MCP_TO_RETRIEVAL_TOOL)
    expect(mcpToolNames).toHaveLength(11)
    for (const name of mcpToolNames) {
      expect(isAllowedSurgicalTool(name)).toBe(true)
    }
  })

  it('returns false for non-whitelisted tool names', () => {
    expect(isAllowedSurgicalTool('pattern_register')).toBe(false)
    expect(isAllowedSurgicalTool('resonance_register')).toBe(false)
    expect(isAllowedSurgicalTool('ask_madhav')).toBe(false)
    expect(isAllowedSurgicalTool('')).toBe(false)
    expect(isAllowedSurgicalTool('__proto__')).toBe(false)
  })

  it('MCP_TO_RETRIEVAL_TOOL maps all 11 entries to valid SURGICAL_TOOLS members', () => {
    for (const [, retrievalName] of Object.entries(MCP_TO_RETRIEVAL_TOOL)) {
      expect(SURGICAL_TOOLS).toContain(retrievalName)
    }
  })

  it('all 11 expected MCP tool names are present in the whitelist', () => {
    const expected = [
      'query_chart_facts',
      'query_signals',
      'query_dasha_periods',
      'query_panchanga',
      'query_ephemeris',
      'query_transit_event',
      'lel_query',
      'vector_search',
      'get_cgm_subgraph',
      'cross_school_lookup',
      'read_classical_text',
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

  it('MCP_TO_RETRIEVAL_TOOL maps cross_school_lookup → multi_school_signal_lookup', () => {
    expect(MCP_TO_RETRIEVAL_TOOL['cross_school_lookup']).toBe('multi_school_signal_lookup')
  })
})

// ── Dispatcher route unit tests (mocked) ──────────────────────────────────────

// We mock the heavy dependencies so we don't need a live DB or retrieval tools.

vi.mock('@/lib/retrieve/index', () => ({
  getTool: vi.fn(),
}))

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

import { getTool } from '@/lib/retrieve/index'
import { traceEmitter } from '@/lib/trace/emitter'
import { POST } from '@/app/api/mcp/primitives/[tool]/route'

const mockGetTool = vi.mocked(getTool)
const mockTraceEmitter = vi.mocked(traceEmitter)

// Helper to build a request with service-token + principal headers
function buildRequest(
  toolName: string,
  opts: {
    missingUser?: boolean
    missingToken?: boolean
    params?: Record<string, unknown>
  } = {}
) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'x-mcp-internal-token': 'test-internal-token',
    'x-mcp-user': 'uid_test_user',
    'x-mcp-audience-tier': 'super_admin',
    'x-mcp-key-id': 'mcp_test_abc12345',
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
    const req = buildRequest('pattern_register')
    const res = await POST(req, buildRouteParams('pattern_register'))
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('validation')
    expect(body.error.message).toContain('pattern_register')
  })

  it('Test 3 (surgical flag): happy-path call returns epistemics.surgical === true', async () => {
    // Mock the tool to return a simple result
    mockGetTool.mockReturnValue({
      name: 'chart_facts_query',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({ rows: [{ planet: 'Saturn', category: 'shadbala' }] }),
    } as unknown as ReturnType<typeof getTool>)

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
    } as unknown as ReturnType<typeof getTool>)

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
})
