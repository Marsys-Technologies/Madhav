/**
 * no_leakage_runtime_canary.test.ts — W6 Part E LIVE/runtime NO-LEAKAGE canary,
 * door 2: /api/mcp/prashna_ask/route.ts.
 *
 * DISTINCT from `projection_compiler_parity.test.ts`'s F-R7 check: that suite is a
 * STATIC, codegen-time assertion over the generated projection artifacts. THIS
 * suite drives the REAL, unmocked `filterLeakedCapabilities` (Part A) against the
 * REAL, fully-registered production capability catalog (`getCatalog()` — no
 * registry/catalog/tool_name_bridge resolver mocking) through the prashna_ask
 * route's actual tool-authorization sequence, for a fixture planner output,
 * asserting the real F-R7-flagged `marsys://tool/L5/lel_query` never appears in
 * what the route actually dispatches — even though the fixture planner output
 * "authorizes" it, simulating a compromised/buggy planner.
 *
 * The companion canary for door 1 (the consult route) lives alongside it at
 * `platform/src/app/api/chat/__tests__/no_leakage_runtime_canary_consult.test.ts`
 * — split into its own file because the two routes need incompatible top-level
 * module mocks (e.g. `@/lib/models/registry`'s STACK_ROUTING) that collide if
 * mixed in one file's hoisted `vi.mock` calls. Both use the same real-registry,
 * real-filter, stubbed-dispatch-only technique.
 *
 * Only the planner LLM call, DB, and auth are mocked (no live DB, no live LLM);
 * the actual dispatch step (`getToolByName(...).retrieve(...)`) is stubbed to a
 * lightweight fake so this stays a fast unit-style test, but resolveToolUri/
 * getCapability/getCatalog and filterLeakedCapabilities itself run for REAL —
 * this is what makes it a runtime canary rather than another mocked-filter unit
 * test (that's what no_leakage_filter.test.ts and the Part C/D suites already
 * cover).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const LEAKED_TOOL = 'marsys://tool/L5/lel_query'
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

// ── Real registry + real filter: NOT mocked ──────────────────────────────────
// '@/lib/retrieval/registry', '@/lib/retrieval/registry/catalog', and
// '@/lib/pipeline/no_leakage_filter' are intentionally absent from this mock
// list — the whole point of this canary is to exercise them for real.

// tool_name_bridge: keep the REAL resolveToolUri (so filterLeakedCapabilities'
// real lookups work), but stub getToolByName's dispatch to avoid a live DB call
// from a real capability handler.
vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return {
    ...actual,
    getToolByName: vi.fn((name: string) => ({
      name,
      version: '1.0',
      retrieve: vi.fn(async () => ({
        tool_bundle_id: 'canary',
        tool_name: name,
        tool_version: '1.0',
        invocation_params: {},
        results: [{ content: `content-for-${name}` }],
        served_from_cache: false,
        latency_ms: 1,
        result_hash: 'sha256:canary',
        schema_version: '1.0' as const,
      })),
    })),
  }
})

vi.mock('@/lib/db/client', () => ({ query: vi.fn(async () => ({ rows: [] })) }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn(async () => 'all') }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn(async () => 'guest') }))
vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: vi.fn(() => true) }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn(async () => 'fake-model') }))

vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({ toolCalls: [], mappedPrimitives: [], unmappedPrimitives: [], compilerIntent: 'general_synthesis', compileFailed: false })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))

const { mockCallPipelinePlanner } = vi.hoisted(() => ({ mockCallPipelinePlanner: vi.fn() }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: mockCallPipelinePlanner,
}))

// Fixture "compromised planner" output: authorizes the real leaked capability
// alongside an ordinary tool.
function fixturePlan() {
  return {
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic' as const,
      query_intent_summary: 'canary fixture query',
      domains: ['career'],
      forward_looking: false,
      tool_calls: [
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'canary fixture — B.11 floor satisfied' },
        { tool_name: LEAKED_TOOL, params: {}, token_budget: 400, priority: 2 as const, reason: 'canary fixture — must be stripped' },
      ],
      scope_tuple: undefined,
      history_mode: 'synthesized' as const,
      expected_output_shape: 'structured_data' as const,
    },
  }
}

import { POST } from '@/app/api/mcp/prashna_ask/route'

beforeEach(() => {
  vi.clearAllMocks()
  mockCallPipelinePlanner.mockResolvedValue(fixturePlan())
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
})

describe('W6 Part E — NO-LEAKAGE runtime canary — door 2 (prashna_ask route, real registry + real filter)', () => {
  it('a real calibration_context_only capability never reaches dispatch', async () => {
    const req = new Request('http://localhost/api/mcp/prashna_ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-mcp-internal-token': 'test-token',
        'x-mcp-user': 'owner-uid',
        'x-mcp-key-id': 'mcp_test_KEY001',
      },
      body: JSON.stringify({ chart_id: CHART, question: 'What has happened in my life recently?' }),
    })

    const resp = await POST(req)
    expect(resp.status).toBe(200)
    // W6 Part 1: the route now streams NDJSON (progress lines + one final
    // line) instead of a single JSON blob — read the full body and take the
    // last line (the `"event":"final"` payload, same shape as before).
    const text = await resp.text()
    const lines = text.trim().split('\n').filter((l) => l.length > 0).map((l) => JSON.parse(l))
    const body = lines[lines.length - 1]
    expect(body.event).toBe('final')

    expect(body.completeness.stripped_leaked_capabilities).toContain(LEAKED_TOOL)
    expect(body.results.map((r: { tool_name: string }) => r.tool_name)).not.toContain(LEAKED_TOOL)
    expect(body.results.map((r: { tool_name: string }) => r.tool_name)).toContain('msr_sql')
  })
})
