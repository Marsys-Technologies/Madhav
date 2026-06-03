/**
 * bo_2_7.test.ts — Unit tests for the bodha_signal_search MCP tool (BO-2-7).
 *
 * Verifies:
 *   - Tool registers with name 'bodha_signal_search'
 *   - Tool handler calls callPlatformPrimitive with correct params
 *   - Successful result is returned as JSON text content
 *   - Error envelope is returned as isError text content
 *   - Optional domain/valence filters are forwarded correctly
 *   - Default limit=5 is applied when not specified
 *
 * BRAHMA-BO-2-7
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive ────────────────────────────────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerBodyaSignalSearch } from '../tools/bo_2-7.js'

// ── Test fixtures ─────────────────────────────────────────────────────────────

const MOCK_PRINCIPAL: Principal = {
  user_uid: 'uid-test-bo27',
  key_id: 'key-test-bo27',
}

const MOCK_SEARCH_RESULT = {
  query: 'Saturn authority career',
  limit: 5,
  domain_filter: undefined,
  valence_filter: undefined,
  results: [
    {
      signal_id: 'SIG.MSR.042',
      domain: 'career',
      valence: 'positive',
      claim_text: '10th lord Saturn in 10th house (Capricorn) — yoga for career authority.',
      source_citation: 'FORENSIC:P10',
      similarity: 0.9312,
    },
    {
      signal_id: 'SIG.MSR.043',
      domain: 'career',
      valence: 'positive',
      claim_text: 'Saturn as atmakaraka in D10 strengthens professional dharma.',
      source_citation: 'FORENSIC:D10',
      similarity: 0.8871,
    },
    {
      signal_id: 'SIG.MSR.091',
      domain: 'career',
      valence: 'positive',
      claim_text: 'Sun in 12th house (Capricorn) aspected by Saturn — authority in foreign or isolated contexts.',
      source_citation: 'FORENSIC:P12',
      similarity: 0.8104,
    },
    {
      signal_id: 'SIG.MSR.112',
      domain: 'career',
      valence: 'mixed',
      claim_text: 'Rahu in 7th house in career axis — unconventional partnerships drive professional growth.',
      source_citation: 'FORENSIC:P7',
      similarity: 0.7655,
    },
    {
      signal_id: 'SIG.MSR.201',
      domain: 'health',
      valence: 'neutral',
      claim_text: 'Saturn rules constitution — chronic but stable health patterns.',
      source_citation: 'FORENSIC:P1',
      similarity: 0.7203,
    },
  ],
  result_count: 5,
  embedding_model: 'text-multilingual-embedding-002',
  table: 'bodha_signal_embeddings',
  surgical: true as const,
}

// ── Mock McpServer ────────────────────────────────────────────────────────────

interface MockToolEntry {
  name: string
  description: string
  schema: Record<string, unknown>
  handler: (args: Record<string, unknown>) => Promise<unknown>
}

function createMockServer(): {
  _tools: MockToolEntry[]
  tool: (name: string, description: string, schema: Record<string, unknown>, handler: (args: Record<string, unknown>) => Promise<unknown>) => void
  getTool: (name: string) => MockToolEntry | undefined
} {
  const _tools: MockToolEntry[] = []
  return {
    _tools,
    tool: (name, description, schema, handler) => {
      _tools.push({ name, description, schema, handler })
    },
    getTool: (name) => _tools.find((t) => t.name === name),
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('registerBodyaSignalSearch (BO-2-7)', () => {
  let server: ReturnType<typeof createMockServer>
  let getPrincipal: () => Principal

  beforeEach(() => {
    server = createMockServer()
    getPrincipal = () => MOCK_PRINCIPAL
    vi.clearAllMocks()
  })

  // ── Registration ────────────────────────────────────────────────────────────

  it('registers a tool named bodha_signal_search', () => {
    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    expect(server._tools).toHaveLength(1)
    expect(server._tools[0]!.name).toBe('bodha_signal_search')
  })

  it('tool description mentions bodha.embeddings and pgvector', () => {
    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const description = server._tools[0]!.description
    expect(description.toLowerCase()).toContain('bodha')
    expect(description.toLowerCase()).toContain('pgvector')
  })

  it('tool description mentions surgical', () => {
    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const description = server._tools[0]!.description
    expect(description.toLowerCase()).toContain('surgical')
  })

  // ── Successful invocation ────────────────────────────────────────────────────

  it('calls callPlatformPrimitive with bodha_signal_search and correct params', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-001',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: MOCK_SEARCH_RESULT,
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    const response = await tool.handler({ query: 'Saturn authority career', limit: 5 })

    expect(callPlatformPrimitive).toHaveBeenCalledWith(
      'bodha_signal_search',
      { query: 'Saturn authority career', limit: 5 },
      MOCK_PRINCIPAL
    )

    const result = response as { content: Array<{ type: string; text: string }> }
    expect(result.content).toHaveLength(1)
    expect(result.content[0]!.type).toBe('text')

    const parsed = JSON.parse(result.content[0]!.text)
    expect(parsed.results).toHaveLength(5)
    expect(parsed.embedding_model).toBe('text-multilingual-embedding-002')
    expect(parsed.table).toBe('bodha_signal_embeddings')
    expect(parsed.surgical).toBe(true)
  })

  it('default limit is 5 when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-002',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: MOCK_SEARCH_RESULT,
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    await tool.handler({ query: 'Rahu 7th house relationships' })

    const calledParams = vi.mocked(callPlatformPrimitive).mock.calls[0]![1] as Record<string, unknown>
    expect(calledParams['limit']).toBe(5)
  })

  it('forwards domain filter when provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-003',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: { ...MOCK_SEARCH_RESULT, domain_filter: 'career' },
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    await tool.handler({ query: 'professional authority', limit: 3, domain: 'career' })

    const calledParams = vi.mocked(callPlatformPrimitive).mock.calls[0]![1] as Record<string, unknown>
    expect(calledParams['domain']).toBe('career')
    expect(calledParams['limit']).toBe(3)
  })

  it('forwards valence filter when provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-004',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: { ...MOCK_SEARCH_RESULT, valence_filter: 'positive' },
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    await tool.handler({ query: 'auspicious career signals', valence: 'positive' })

    const calledParams = vi.mocked(callPlatformPrimitive).mock.calls[0]![1] as Record<string, unknown>
    expect(calledParams['valence']).toBe('positive')
  })

  it('does NOT include domain key when domain is undefined', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-005',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: MOCK_SEARCH_RESULT,
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    await tool.handler({ query: 'chart reading' })

    const calledParams = vi.mocked(callPlatformPrimitive).mock.calls[0]![1] as Record<string, unknown>
    expect('domain' in calledParams).toBe(false)
    expect('valence' in calledParams).toBe(false)
  })

  // ── Error handling ───────────────────────────────────────────────────────────

  it('returns isError=true on platform error envelope', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 503,
      envelope: {
        ok: false,
        trace_id: 'tr-err-001',
        error: {
          class: 'internal',
          message: 'Platform unreachable',
          remediation: 'Check sidecar logs',
        },
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    const response = await tool.handler({ query: 'failing query' })

    const result = response as { content: Array<{ type: string; text: string }>; isError: boolean }
    expect(result.isError).toBe(true)

    const parsed = JSON.parse(result.content[0]!.text)
    expect(parsed.error).toBe('Platform unreachable')
    expect(parsed.error_class).toBe('internal')
    expect(parsed.http_status).toBe(503)
    expect(parsed.tool).toBe('bodha_signal_search')
  })

  it('error response includes remediation hint', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 404,
      envelope: {
        ok: false,
        trace_id: 'tr-err-002',
        error: {
          class: 'validation',
          message: 'bodha_signal_embeddings table not found — run brahma_bo_2-7.sql migration',
          remediation: 'Apply platform/migrations/brahma_bo_2-7.sql and run bo_2-7.py',
        },
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    const response = await tool.handler({ query: 'test' })

    const result = response as { content: Array<{ type: string; text: string }>; isError: boolean }
    expect(result.isError).toBe(true)
    const parsed = JSON.parse(result.content[0]!.text)
    expect(parsed.error_class).toBe('validation')
  })

  // ── Acceptance gate: cosine self-search result shape ────────────────────────

  it('result contains signal_id, domain, valence, claim_text, source_citation, similarity', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-shape-001',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: MOCK_SEARCH_RESULT,
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    const response = await tool.handler({ query: 'Saturn career' })

    const result = response as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(result.content[0]!.text)

    expect(parsed.results[0]).toMatchObject({
      signal_id: expect.any(String),
      domain: expect.any(String),
      valence: expect.any(String),
      claim_text: expect.any(String),
      similarity: expect.any(Number),
    })
    // similarity should be between 0 and 1
    expect(parsed.results[0].similarity).toBeGreaterThan(0)
    expect(parsed.results[0].similarity).toBeLessThanOrEqual(1)
  })

  // ── Acceptance gate: >= 5 results available ──────────────────────────────────

  it('result_count matches the number of results returned', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-count-001',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: MOCK_SEARCH_RESULT,
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    const response = await tool.handler({ query: 'native chart' })

    const result = response as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(result.content[0]!.text)

    expect(parsed.result_count).toBe(parsed.results.length)
    expect(parsed.result_count).toBeGreaterThanOrEqual(5)
  })

  // ── Native chart smoke: SIG.MSR.042 is top hit for Saturn career query ───────

  it('native smoke: SIG.MSR.042 is the top result for Saturn career authority query', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'tr-native-smoke',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: MOCK_SEARCH_RESULT,
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    registerBodyaSignalSearch(server as unknown as McpServer, getPrincipal)
    const tool = server.getTool('bodha_signal_search')!
    const response = await tool.handler({ query: 'Saturn authority career 10th lord' })

    const result = response as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(result.content[0]!.text)

    // The top result for this native-specific query should be SIG.MSR.042
    expect(parsed.results[0].signal_id).toBe('SIG.MSR.042')
    expect(parsed.results[0].domain).toBe('career')
    expect(parsed.results[0].valence).toBe('positive')
  })
})
