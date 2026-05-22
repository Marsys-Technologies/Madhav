/**
 * execute.integration.test.ts — Integration tests for /api/mcp/execute.
 *
 * Tests the envelope shape and key structural contracts of the execute
 * endpoint. Mocks are applied at the module boundary so no real DB,
 * pipeline planner, or synthesis LLM is called.
 *
 * Coverage:
 *   - Service token validation (rejects missing/invalid tokens)
 *   - Principal header validation (rejects missing headers)
 *   - ask_madhav: envelope shape (ok, trace_id, audience_tier, epistemics,
 *     result, synthesis_audit.holistic_read_passed, suggested_followups)
 *   - plan_query: returns plan without execution
 *   - Unknown tool: 400 validation error
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { POST } from '@/app/api/mcp/execute/route'
import { query } from '@/lib/db/client'

// ── Module mocks ───────────────────────────────────────────────────────────────

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [], rowCount: 0, command: '', oid: 0, fields: [] }),
}))

vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  callPipelinePlanner: vi.fn().mockResolvedValue({
    query_class: 'factual',
    query_intent_summary: 'Test factual query',
    asset_bundle: [{ asset_id: 'FORENSIC', priority: 1, reason: 'floor' }],
    tool_calls: [
      { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1, reason: 'B.11 floor' },
      { tool_name: 'cgm_graph_walk', params: {}, token_budget: 400, priority: 2, reason: 'B.11 floor' },
    ],
    domains: ['career'],
    forward_looking: false,
  }),
  PlannerFault: class PlannerFault extends Error {
    constructor(msg: string) { super(msg); this.name = 'PlannerFault' }
  },
}))

// F.7 (MCPT v3.1.0-S1): token-budget allocation mock removed — no longer on MCP path.

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn().mockResolvedValue({
    assets: [],
    floor_enforced: false,
    tool_specs: [],
  }),
}))

vi.mock('@/lib/bundle/manifest_reader', () => ({
  loadManifest: vi.fn().mockResolvedValue({
    fingerprint: 'mock-fingerprint-abc123',
    assets: [],
    tools: [],
  }),
}))

vi.mock('@/lib/retrieve/index', () => ({
  getTool: vi.fn().mockReturnValue({
    tool_name: 'msr_sql',
    execute: vi.fn().mockResolvedValue({ results: [] }),
  }),
}))

vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn().mockReturnValue({}),
  executeWithCache: vi.fn().mockResolvedValue({
    tool_name: 'msr_sql',
    results: [{ signal_id: 'SIG.MSR.001', content: 'Test signal content', source_canonical_id: 'MSR' }],
  }),
}))

vi.mock('@/lib/synthesis/index', () => ({
  createOrchestrator: vi.fn().mockReturnValue({
    synthesize: vi.fn().mockResolvedValue({
      result: {
        text: Promise.resolve('The Atmakaraka in this chart is Saturn (Shani), placed in the 9th house with strong dignity. [^1] SIG.MSR.001'),
      },
      metadata: { synthesis_prompt_version: '1.0', synthesizer_model_id: 'mock', bundle_hash: 'abc', started_at: new Date().toISOString() },
    }),
  }),
}))

vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: vi.fn().mockResolvedValue('claude-sonnet-test'),
}))

vi.mock('@/lib/models/registry', () => ({
  DEFAULT_STACK_ID: 'primary',
  DEFAULT_MODEL_ID: 'claude-sonnet-test',
  getModelMeta: vi.fn().mockReturnValue({ maxInputTokens: 128_000 }),
}))

vi.mock('@/lib/config/index', () => ({
  configService: { getFlag: vi.fn().mockReturnValue(false) },
}))

vi.mock('@/lib/trace/emitter', () => ({
  traceEmitter: { emitStep: vi.fn() },
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeRequest(
  body: unknown,
  headers: Record<string, string> = {},
): Request {
  const internalToken = process.env.MCP_INTERNAL_TOKEN ?? 'test-internal-token'
  return new Request('http://localhost/api/mcp/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': internalToken,
      'x-mcp-user': 'uid_test_123',
      'x-mcp-audience-tier': 'super_admin',
      'x-mcp-key-id': 'mcp_test_testkey1',
      ...headers,
    },
    body: JSON.stringify(body),
  })
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('/api/mcp/execute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Ensure development mode so service token validation passes
    ;(process.env as Record<string, string>).NODE_ENV = 'test'
    // Set internal token for tests
    process.env.MCP_INTERNAL_TOKEN = 'test-internal-token'

    // Reset chart query mock to return a valid chart
    vi.mocked(query).mockImplementation((sql: string) => {
      if (sql.includes('FROM charts')) {
        return Promise.resolve({
          rows: [{ id: 'chart-uuid-123', name: 'Abhisek Mohanty', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar, Odisha, India' }],
          rowCount: 1, command: '', oid: 0, fields: [],
        })
      }
      return Promise.resolve({ rows: [], rowCount: 0, command: '', oid: 0, fields: [] })
    })
  })

  describe('auth guard', () => {
    it('rejects missing service token when MCP_INTERNAL_TOKEN is set', async () => {
      process.env.MCP_INTERNAL_TOKEN = 'required-secret'
      const req = makeRequest(
        { tool: 'ask_madhav', params: { query: 'test' } },
        { 'x-mcp-internal-token': 'wrong-token' }
      )
      const res = await POST(req)
      expect(res.status).toBe(401)
      const body = await res.json()
      expect(body.ok).toBe(false)
      expect(body.error.class).toBe('auth')
    })

    it('rejects missing principal headers', async () => {
      const req = makeRequest(
        { tool: 'ask_madhav', params: { query: 'test' } },
        { 'x-mcp-user': '' }  // empty user header
      )
      const res = await POST(req)
      expect(res.status).toBe(401)
      const body = await res.json()
      expect(body.ok).toBe(false)
    })
  })

  describe('ask_madhav', () => {
    it('returns valid envelope with all required fields', async () => {
      const req = makeRequest({ tool: 'ask_madhav', params: { query: 'What is the current dasha?' } })
      const res = await POST(req)

      const body = await res.json()
      expect(body.ok).toBe(true)
      expect(body.trace_id).toBeTruthy()
      expect(body.audience_tier).toBe('super_admin')
      expect(body.epistemics).toBeDefined()
      expect(body.epistemics.surgical).toBe(false)
      expect(body.result).toBeDefined()
      expect(body.result.answer_markdown).toBeTruthy()
    })

    it('synthesis_audit.holistic_read_passed is true when L2.5 tools fired', async () => {
      const req = makeRequest({ tool: 'ask_madhav', params: { query: 'What is my Atmakaraka?' } })
      const res = await POST(req)
      const body = await res.json()
      // msr_sql fires in our mock, so holistic_read_passed should be true
      expect(body.synthesis_audit).toBeDefined()
      expect(body.synthesis_audit.holistic_read_passed).toBe(true)
    })

    it('suggested_followups is non-empty array', async () => {
      const req = makeRequest({ tool: 'ask_madhav', params: { query: 'How is my career?' } })
      const res = await POST(req)
      const body = await res.json()
      expect(body.suggested_followups).toBeInstanceOf(Array)
      expect(body.suggested_followups.length).toBeGreaterThan(0)
    })

    it('citations array is present', async () => {
      const req = makeRequest({ tool: 'ask_madhav', params: { query: 'What are the key signals?' } })
      const res = await POST(req)
      const body = await res.json()
      expect(body.citations).toBeInstanceOf(Array)
      // SIG.MSR.001 appears in the mocked synthesis text
      expect(body.citations.some((c: {id: string}) => c.id === 'SIG.MSR.001')).toBe(true)
    })

    it('returns 400 when query param is empty', async () => {
      const req = makeRequest({ tool: 'ask_madhav', params: { query: '' } })
      const res = await POST(req)
      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.ok).toBe(false)
    })
  })

  describe('plan_query', () => {
    it('returns plan without executing synthesis', async () => {
      const req = makeRequest({ tool: 'plan_query', params: { query: 'What is my lagna?' } })
      const res = await POST(req)
      const body = await res.json()
      expect(body.ok).toBe(true)
      expect(body.result).toBeDefined()
      expect(body.result.query_class).toBeDefined()
      // synthesis_audit should be null — no synthesis ran
      expect(body.synthesis_audit).toBeNull()
    })
  })

  describe('unknown tool', () => {
    it('returns 400 validation error', async () => {
      const req = makeRequest({ tool: 'unknown_tool_xyz', params: {} })
      const res = await POST(req)
      expect(res.status).toBe(400)
      const body = await res.json()
      expect(body.ok).toBe(false)
      expect(body.error.class).toBe('validation')
    })
  })
})
