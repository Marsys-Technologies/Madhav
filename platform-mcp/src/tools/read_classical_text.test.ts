/**
 * read_classical_text.test.ts — Regression tests for the read_classical_text MCP tool.
 *
 * Tests the C10 bug fix (TR-P2-S3):
 *   - text_id now routes to text_key filter (ct.text_key = 'bphs'), NOT school filter
 *     (ct.school = 'parashari'). Previous wrapper incorrectly passed text_id.toLowerCase()
 *     as `schools`, which mapped to the tradition column.
 *   - citation param added: "BPHS.33.1" splits to text_key=bphs, chapter=33, verse=1
 *     for exact lookup.
 *   - chapter + verse params added for direct numeric exact lookup.
 *   - Graceful handling of unknown texts (e.g. PHALADEEPIKA) — no error on 0 results.
 *
 * AC.1: text_id: "BPHS" → text_key='bphs' in toolParams (not schools=['bphs'])
 * AC.2: citation: "BPHS.33.1" → exact_lookup=true, chapter=33, verse=1
 * AC.3: text_id: "BPHS" routes to text_key='bphs' filter (verified by checking params)
 * AC.4: citation: "BPHS.33.1" triggers exact lookup with chapter=33, verse=1
 * AC.5: test file passes vitest (this file itself)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerReadClassicalText } from './read_classical_text.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildClassicalEnvelope(chunks: unknown[] = []) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-classical-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'classical-bundle-id',
        tool_name: 'classical_text_search',
        tool_version: '1.0.0',
        invocation_params: {},
        results: chunks.map(c => ({
          content: JSON.stringify(c),
          source_canonical_id: 'CLASSICAL_CORPUS',
          source_version: '1.0',
          confidence: 0.9,
          significance: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 15,
        result_hash: 'sha256:classical-test',
        schema_version: '1.0',
      },
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-classical-err',
      error: { class: 'internal', message: 'DB error in classical_text_search' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callReadClassicalText(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null
  let capturedSchema: Record<string, unknown> | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      schema: Record<string, unknown>,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
      capturedSchema = schema
    },
  } as unknown as McpServer

  registerReadClassicalText(stubServer, () => principal)

  if (!capturedHandler) throw new Error('read_classical_text handler was not registered')

  // Simulate Zod validation as the MCP SDK would perform
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)

  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// Helper: parse the text content from an MCP result
function parseResultContent(result: unknown): unknown {
  const r = result as { content?: Array<{ type: string; text: string }>; isError?: boolean }
  if (!r.content?.[0]?.text) return null
  try {
    return JSON.parse(r.content[0].text)
  } catch {
    return r.content[0].text
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('read_classical_text — C10 text_key fix + citation lookup (TR-P2-S3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── AC.1 + AC.3: text_key fix ─────────────────────────────────────────────

  it('AC.1/AC.3 — text_id: BPHS routes to text_key=bphs in toolParams (not schools=["bphs"])', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([
      { text_key: 'bphs', chapter: '7', verse_range: '7.1-7.5', content: 'Jupiter as Karaka...' },
    ]))

    await callReadClassicalText({ query: 'Jupiter', text_id: 'BPHS' })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('read_classical_text')

    const typedParams = params as Record<string, unknown>

    // AC.1: text_key must be 'bphs' (lowercase of BPHS)
    expect(typedParams['text_key']).toBe('bphs')

    // AC.3: must NOT use schools filter at all
    expect(Object.hasOwn(typedParams, 'schools')).toBe(false)
    expect(typedParams['schools']).toBeUndefined()
  })

  it('text_id: KP_READER routes to text_key=kp_reader (not schools=["kp_reader"])', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({ query: 'cuspal sublord', text_id: 'KP_READER' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['text_key']).toBe('kp_reader')
    expect(Object.hasOwn(params, 'schools')).toBe(false)
  })

  it('text_id: JAIMINI routes to text_key=jaimini', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({ query: 'Karakamsha', text_id: 'JAIMINI' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['text_key']).toBe('jaimini')
    expect(Object.hasOwn(params, 'schools')).toBe(false)
  })

  it('text_id: PHALADEEPIKA routes to text_key=phaladeepika without error on 0 results', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    // 0 results — must not error
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    const result = await callReadClassicalText({ query: 'Jupiter exaltation', text_id: 'PHALADEEPIKA' })

    // Must not be an error
    expect((result as { isError?: boolean }).isError).toBeUndefined()

    // text_key must be phaladeepika
    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['text_key']).toBe('phaladeepika')
  })

  it('text_id: BRIHAT_JATAKA routes to text_key=brihat_jataka', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    const result = await callReadClassicalText({ query: 'Saturn affliction', text_id: 'BRIHAT_JATAKA' })

    expect((result as { isError?: boolean }).isError).toBeUndefined()

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['text_key']).toBe('brihat_jataka')
    expect(Object.hasOwn(params, 'schools')).toBe(false)
  })

  it('no text_id → no text_key in toolParams (search across all texts)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({ query: 'Ketu moksha 12th house' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(Object.hasOwn(params, 'text_key')).toBe(false)
    expect(Object.hasOwn(params, 'schools')).toBe(false)
  })

  // ── AC.2 + AC.4: citation lookup ──────────────────────────────────────────

  it('AC.2/AC.4 — citation: "BPHS.33.1" triggers exact lookup with chapter=33, verse=1', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([
      { text_key: 'bphs', chapter: '33', verse_range: '33.1', content: 'Verse 33.1 of BPHS...' },
    ]))

    await callReadClassicalText({ citation: 'BPHS.33.1' })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const params = mockCall.mock.calls[0][1] as Record<string, unknown>

    // AC.4: exact lookup params must be set correctly
    expect(params['text_key']).toBe('bphs')
    expect(params['chapter']).toBe(33)
    expect(params['verse']).toBe(1)
    expect(params['exact_lookup']).toBe(true)
  })

  it('citation: "PHALADEEPIKA.7.12" splits correctly to chapter=7, verse=12', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({ citation: 'PHALADEEPIKA.7.12' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['text_key']).toBe('phaladeepika')
    expect(params['chapter']).toBe(7)
    expect(params['verse']).toBe(12)
    expect(params['exact_lookup']).toBe(true)
  })

  it('citation lookup response includes citation_requested and text_key_filter metadata', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([
      { text_key: 'bphs', chapter: '33', verse_range: '33.1', content: 'BPHS 33.1 content' },
    ]))

    const result = await callReadClassicalText({ citation: 'BPHS.33.1' })

    const parsed = parseResultContent(result) as Record<string, unknown>
    expect(parsed['citation_requested']).toBe('BPHS.33.1')
    expect(parsed['text_key_filter']).toBe('bphs')
    expect(parsed['chapter_filter']).toBe(33)
    expect(parsed['verse_filter']).toBe(1)
    expect(parsed['lookup_mode']).toBe('exact')
  })

  it('exact lookup with 0 results sets fallback: "semantic_search" in response', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([])) // 0 results

    const result = await callReadClassicalText({ citation: 'BPHS.99.99' })

    const parsed = parseResultContent(result) as Record<string, unknown>
    expect(parsed['fallback']).toBe('semantic_search')
    expect(parsed['lookup_mode']).toBe('exact')
  })

  // ── chapter + verse direct params ─────────────────────────────────────────

  it('chapter + verse + text_id triggers exact lookup without citation string', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([
      { text_key: 'bphs', chapter: '12', verse_range: '12.5', content: 'BPHS 12.5 content' },
    ]))

    await callReadClassicalText({ query: 'Ketu 12th', text_id: 'BPHS', chapter: 12, verse: 5 })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['text_key']).toBe('bphs')
    expect(params['chapter']).toBe(12)
    expect(params['verse']).toBe(5)
    expect(params['exact_lookup']).toBe(true)
  })

  it('chapter without verse does not trigger exact lookup', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({ query: 'Ketu 12th', text_id: 'BPHS', chapter: 12 })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    // chapter alone is not enough for exact lookup
    expect(params['exact_lookup']).toBeUndefined()
  })

  // ── citation takes precedence over chapter + verse ────────────────────────

  it('citation takes precedence over chapter + verse params', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({
      query: 'ignored query',
      text_id: 'BPHS',
      citation: 'PHALADEEPIKA.5.3',
      chapter: 99,
      verse: 99,
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    // citation wins: text_key = phaladeepika, chapter = 5, verse = 3
    expect(params['text_key']).toBe('phaladeepika')
    expect(params['chapter']).toBe(5)
    expect(params['verse']).toBe(3)
  })

  // ── Error handling ────────────────────────────────────────────────────────

  it('returns isError=true when platform returns 500 error', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildErrorEnvelope())

    const result = await callReadClassicalText({ query: 'Jupiter moksha' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── Zod schema validation ─────────────────────────────────────────────────

  it('Zod rejects invalid text_id values', async () => {
    const result = await callReadClassicalText({ query: 'test', text_id: 'NOT_A_TEXT' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  it('Zod rejects non-integer chapter', async () => {
    const result = await callReadClassicalText({ query: 'test', chapter: 1.5 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  it('query is optional when citation is supplied (Zod accepts)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    const result = await callReadClassicalText({ citation: 'BPHS.33.1' })
    // Should not be a Zod error
    expect((result as { isZodError?: boolean }).isZodError).toBeUndefined()
    expect(mockCall).toHaveBeenCalledTimes(1)
  })

  // ── Limit param ───────────────────────────────────────────────────────────

  it('limit param is forwarded to toolParams', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({ query: 'Jupiter aspects', limit: 10 })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(10)
  })

  it('limit defaults to 5 when not specified', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    await callReadClassicalText({ query: 'Venus darakaraka' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(5)
  })

  // ── New text IDs in enum ──────────────────────────────────────────────────

  it('SARAVALI is a valid text_id (part of extended enum)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildClassicalEnvelope([]))

    const result = await callReadClassicalText({ query: 'Mars 10th house', text_id: 'SARAVALI' })
    expect((result as { isZodError?: boolean }).isZodError).toBeUndefined()

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['text_key']).toBe('saravali')
  })
})
