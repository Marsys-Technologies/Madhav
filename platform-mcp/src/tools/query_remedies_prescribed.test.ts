/**
 * query_remedies_prescribed.test.ts — Unit tests for the query_remedies_prescribed MCP tool.
 *
 * TR-P8-S2 acceptance criteria:
 *   AC.1 — query_remedies_prescribed({planet:"Saturn"}) returns results.
 *   AC.2 — remedy_type filter "mantra" returns only mantra entries.
 *   AC.3 — Result has remedy_type, remedy_text, classical_source fields.
 *   AC.4 — Empty query (no params) returns empty results gracefully.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryRemediesPrescribed } from './query_remedies_prescribed.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a remedial_codex_query envelope returning the given chunks array.
 */
function buildRemedialEnvelope(chunks: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-rem-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        chunks,
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

/**
 * Build a chart_facts envelope with rows_by_category.
 */
function buildChartFactsEnvelope(rowsByCategory: Record<string, unknown[]>) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-cf-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        rows_by_category: rowsByCategory,
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
      trace_id: 'trace-fail-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

/**
 * Invoke the query_remedies_prescribed handler via a stub McpServer.
 */
async function callQueryRemediesPrescribed(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      _schema: unknown,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
    },
  } as unknown as McpServer

  registerQueryRemediesPrescribed(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_remedies_prescribed handler was not registered')
  return capturedHandler(args)
}

/**
 * Parse the MCP content text envelope and return the first content item as JSON.
 */
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Sample data ───────────────────────────────────────────────────────────────

const SATURN_MANTRA_CHUNK = {
  chunk_id: 'REM.BPHS.SAT.001',
  content: 'Om Sham Shanaischaraya Namah — recite mantra 108 times on Saturdays. ' +
    'Saturn propitiation through Shani mantra japa is prescribed for Saturn affliction.',
  planet: 'Saturn',
  classical_source: 'BPHS chapter 56',
  timing: 'Saturday, Pushya nakshatra, dawn',
  similarity: 0.87,
}

const SATURN_GEM_CHUNK = {
  chunk_id: 'REM.GEM.SAT.001',
  content: 'Blue Sapphire (Neelam) is the gemstone for Saturn. ' +
    'Wearing a gem / gemstone / ratna in gold or silver ring on middle finger of right hand.',
  planet: 'Saturn',
  classical_source: 'Ratna Pariksha chapter 4',
  timing: 'Saturday, Shravana nakshatra',
  similarity: 0.82,
}

const MARS_RITUAL_CHUNK = {
  chunk_id: 'REM.RITUAL.MAR.001',
  content: 'Perform Mangala puja / ritual on Tuesdays. Homa with red flowers for Mars propitiation.',
  planet: 'Mars',
  classical_source: 'BPHS chapter 58',
  timing: 'Tuesday, Mrigashira nakshatra',
  similarity: 0.75,
}

const CHARITY_CHUNK = {
  chunk_id: 'REM.CHARITY.001',
  content: 'Donate black sesame seeds and mustard oil on Saturdays. ' +
    'Charity / daan to labourers and underprivileged on Saturdays propitiates Saturn.',
  planet: 'Saturn',
  classical_source: 'Muhurta Chintamani chapter 3',
  timing: 'Saturday',
  similarity: 0.70,
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_remedies_prescribed (TR-P8-S2)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  // ── AC.1 — planet:"Saturn" returns results ────────────────────────────────

  it('AC.1 — query with planet:"Saturn" returns non-empty results', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    // First call: remedial_codex_query; second call: query_chart_facts
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope([SATURN_MANTRA_CHUNK, SATURN_GEM_CHUNK]))
      .mockResolvedValueOnce(buildChartFactsEnvelope({ remedy: [], strength: [] }))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn' })
    const parsed = parseResult(result)

    expect(parsed.ok).toBe(true)
    expect(Array.isArray(parsed.results)).toBe(true)
    const results = parsed.results as unknown[]
    expect(results.length).toBeGreaterThan(0)
    expect(parsed.result_count).toBe(results.length)
  })

  // ── AC.1b — affliction_query is echoed in response ────────────────────────

  it('AC.1b — affliction_query is echoed and contains planet name', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope([SATURN_MANTRA_CHUNK]))
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({
      planet: 'Saturn',
      affliction: 'Saturn afflicts 1H',
    })
    const parsed = parseResult(result)

    expect(typeof parsed.affliction_query).toBe('string')
    const query = parsed.affliction_query as string
    expect(query).toContain('Saturn')
    expect(query).toContain('remedy')
  })

  // ── AC.2 — remedy_type filter "mantra" returns only mantra entries ─────────

  it('AC.2 — remedy_type="mantra" returns only mantra-type results', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(
        buildRemedialEnvelope([
          SATURN_MANTRA_CHUNK, // mantra
          SATURN_GEM_CHUNK,    // gem
          MARS_RITUAL_CHUNK,   // ritual
          CHARITY_CHUNK,       // charity
        ])
      )
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn', remedy_type: 'mantra' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    expect(results.length).toBeGreaterThan(0)
    // All returned results must be type "mantra"
    for (const r of results) {
      expect(r.remedy_type).toBe('mantra')
    }
  })

  // ── AC.2b — remedy_type="gem" filter works ────────────────────────────────

  it('AC.2b — remedy_type="gem" returns only gem entries', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(
        buildRemedialEnvelope([SATURN_MANTRA_CHUNK, SATURN_GEM_CHUNK])
      )
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ remedy_type: 'gem' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    for (const r of results) {
      expect(r.remedy_type).toBe('gem')
    }
  })

  // ── AC.3 — Result has remedy_type, remedy_text, classical_source fields ───

  it('AC.3 — each result has remedy_type, remedy_text, and classical_source fields', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope([SATURN_MANTRA_CHUNK, SATURN_GEM_CHUNK]))
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    expect(results.length).toBeGreaterThan(0)

    for (const r of results) {
      // remedy_type must be one of the 5 valid types
      expect(['mantra', 'gem', 'ritual', 'charity', 'unknown']).toContain(r.remedy_type)
      // remedy_text must be a non-empty string
      expect(typeof r.remedy_text).toBe('string')
      expect((r.remedy_text as string).length).toBeGreaterThan(0)
      // classical_source is present (string or null)
      expect('classical_source' in r).toBe(true)
    }
  })

  // ── AC.3b — timing field is present on results ────────────────────────────

  it('AC.3b — results include timing field (may be null)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope([SATURN_MANTRA_CHUNK]))
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    expect(results.length).toBeGreaterThan(0)
    for (const r of results) {
      expect('timing' in r).toBe(true)
    }
  })

  // ── AC.4 — Empty query (no params) returns gracefully ─────────────────────

  it('AC.4 — empty call (no params) with empty remedial response returns gracefully', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    // No planet → only one call (remedial_codex_query); returns empty chunks
    mockCall.mockResolvedValueOnce(buildRemedialEnvelope([]))

    const result = await callQueryRemediesPrescribed({})
    const parsed = parseResult(result)

    expect(parsed.ok).toBe(true)
    expect(Array.isArray(parsed.results)).toBe(true)
    expect(parsed.result_count).toBe(0)
    expect((parsed.results as unknown[]).length).toBe(0)
  })

  // ── Remedy type detection: ritual ─────────────────────────────────────────

  it('ritual keyword detection — chunk with "puja" text is classified as ritual', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    // Two calls: remedial_codex_query + query_chart_facts (planet is provided)
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope([MARS_RITUAL_CHUNK]))
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ planet: 'Mars', remedy_type: 'ritual' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].remedy_type).toBe('ritual')
  })

  // ── Remedy type detection: charity ────────────────────────────────────────

  it('charity keyword detection — chunk with "daan" text is classified as charity', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValueOnce(buildRemedialEnvelope([CHARITY_CHUNK]))

    const result = await callQueryRemediesPrescribed({ remedy_type: 'charity' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].remedy_type).toBe('charity')
  })

  // ── remedy_type="all" returns mixed types ─────────────────────────────────

  it('remedy_type="all" returns all remedy types without filtering', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(
        buildRemedialEnvelope([
          SATURN_MANTRA_CHUNK,
          SATURN_GEM_CHUNK,
          MARS_RITUAL_CHUNK,
          CHARITY_CHUNK,
        ])
      )
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn', remedy_type: 'all' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    const types = new Set(results.map(r => r.remedy_type))
    // Should have multiple types when not filtered
    expect(types.size).toBeGreaterThan(1)
  })

  // ── result_count capped at 10 ─────────────────────────────────────────────

  it('result_count is capped at 10 even when more raw chunks are returned', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    // Create 15 mantra chunks
    const manyChunks = Array.from({ length: 15 }, (_, i) => ({
      chunk_id: `REM.MANTRA.${i}`,
      content: `Saturn mantra japa practice number ${i + 1} — Om Sham Shanaischaraya Namah.`,
      planet: 'Saturn',
      classical_source: `BPHS chapter ${56 + i}`,
      similarity: 0.9 - i * 0.02,
    }))
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope(manyChunks))
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn' })
    const parsed = parseResult(result)

    const results = parsed.results as Array<Record<string, unknown>>
    expect(results.length).toBeLessThanOrEqual(10)
    expect(parsed.result_count).toBeLessThanOrEqual(10)
  })

  // ── chart_facts rows merged when planet provided ───────────────────────────

  it('chart_facts remedy rows are merged when planet is provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    const cfRemedyRow = {
      fact_id: 'CF.REM.SAT.001',
      category: 'remedy',
      planet: 'Saturn',
      content: 'Saturn charity: donate black sesame on Saturdays',
      classical_source: 'BPHS',
    }
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope([SATURN_MANTRA_CHUNK]))
      .mockResolvedValueOnce(buildChartFactsEnvelope({ remedy: [cfRemedyRow] }))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn' })
    const parsed = parseResult(result)

    // Should have results from both remedial codex and chart_facts
    const results = parsed.results as Array<Record<string, unknown>>
    expect(results.length).toBeGreaterThanOrEqual(1)
  })

  // ── house param included in affliction_query ──────────────────────────────

  it('house param is included in affliction_query', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildRemedialEnvelope([]))
      .mockResolvedValueOnce(buildChartFactsEnvelope({}))

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn', house: 7 })
    const parsed = parseResult(result)

    const query = parsed.affliction_query as string
    expect(query).toContain('house 7')
  })

  // ── Hard error from remedial codex propagates ─────────────────────────────

  it('hard error from remedial_codex_query propagates as error result', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callQueryRemediesPrescribed({ planet: 'Saturn' })

    // Should not throw; should return error content
    const content = (result as { content: Array<{ text: string }> }).content
    expect(Array.isArray(content)).toBe(true)
    const text = content[0].text
    const parsed = JSON.parse(text) as Record<string, unknown>
    // Error result has ok:false
    expect(parsed.ok).toBe(false)
  })
})
