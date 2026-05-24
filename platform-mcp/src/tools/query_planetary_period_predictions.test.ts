/**
 * query_planetary_period_predictions.test.ts — Tests for the
 * query_planetary_period_predictions MCP tool.
 *
 * Session: TR-P7-S3
 *
 * Acceptance criteria:
 *   TC.1 — {maha_dasha_lord:"Rahu", antar_dasha_lord:"Jupiter"} → result_count >= 1 (mock 3 chunks)
 *   TC.2 — {maha_dasha_lord:"Saturn"} works without antar_dasha_lord
 *   TC.3 — Response has `results` array and `sources_searched` array
 *   TC.4 — Deduplication: same chunk_id from vector + classical appears once
 *   TC.5 — School derivation: chunk with text_id "BPHS" gets school "Parashari"
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryPlanetaryPeriodPredictions } from './query_planetary_period_predictions.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/** Build a vector_search envelope with classical chunks. */
function buildVectorEnvelope(
  chunks: Array<{
    chunk_id: string
    text_id: string
    chapter?: number
    verse?: number
    content: string
    score: number
    school?: string
  }>,
) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-vector-001',
      result: {
        chunks,
      },
    },
  }
}

/** Build a read_classical_text envelope with results. */
function buildClassicalEnvelope(
  results: Array<{
    chunk_id: string
    text_id: string
    chapter?: number
    verse?: number
    content: string
    relevance_score?: number
    school?: string
  }>,
) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-classical-001',
      result: {
        results,
      },
    },
  }
}

/** Build an error envelope. */
function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-error-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

/**
 * Registers query_planetary_period_predictions on a stub MCP server,
 * applies Zod validation, and invokes the handler.
 */
async function callQueryPlanetaryPeriodPredictions(
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

  registerQueryPlanetaryPeriodPredictions(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_planetary_period_predictions handler was not registered')

  // Simulate Zod validation as MCP SDK would do
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

/** Parse the MCP content text from the result. */
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_planetary_period_predictions (TR-P7-S3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── TC.1: Rahu/Jupiter MD/AD returns result_count >= 1 ────────────────────

  it('TC.1 — {maha_dasha_lord:"Rahu", antar_dasha_lord:"Jupiter"} returns result_count >= 1', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    // 3 chunks, all containing "Rahu" to pass the content filter
    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'chunk-001',
            text_id: 'BPHS',
            chapter: 49,
            verse: 1,
            content: 'Rahu Mahadasha brings foreign travels and unconventional outcomes.',
            score: 0.92,
          },
          {
            chunk_id: 'chunk-002',
            text_id: 'KP_READER',
            chapter: 12,
            verse: 5,
            content: 'During Rahu dasha Jupiter antardasha, spiritual wisdom dawns.',
            score: 0.85,
          },
        ])
      )
      .mockResolvedValueOnce(
        buildClassicalEnvelope([
          {
            chunk_id: 'chunk-003',
            text_id: 'PHALADEEPIKA',
            chapter: 20,
            verse: 10,
            content: 'Rahu period causes confusion but also Rahu gains from foreign lands.',
            relevance_score: 0.78,
          },
        ])
      )

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Rahu',
      antar_dasha_lord: 'Jupiter',
    })
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    expect(envelope['maha_dasha_lord']).toBe('Rahu')
    expect(envelope['antar_dasha_lord']).toBe('Jupiter')

    const resultCount = envelope['result_count'] as number
    expect(resultCount).toBeGreaterThanOrEqual(1)

    const results = envelope['results'] as unknown[]
    expect(Array.isArray(results)).toBe(true)
    expect(results.length).toBe(resultCount)
  })

  // ── TC.2: Saturn MD works without antar_dasha_lord ────────────────────────

  it('TC.2 — {maha_dasha_lord:"Saturn"} works without antar_dasha_lord', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'saturn-001',
            text_id: 'BPHS',
            chapter: 50,
            verse: 3,
            content: 'Saturn Mahadasha lasts 19 years and brings discipline and hard work.',
            score: 0.88,
          },
        ])
      )
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Saturn',
    })
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    expect(envelope['maha_dasha_lord']).toBe('Saturn')
    expect(envelope['antar_dasha_lord']).toBeNull()

    const results = envelope['results'] as unknown[]
    expect(Array.isArray(results)).toBe(true)
  })

  // ── TC.3: Response has results array and sources_searched array ───────────

  it('TC.3 — response has `results` array and `sources_searched` array', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'jupiter-001',
            text_id: 'JAIMINI_SUTRAM',
            chapter: 5,
            verse: 12,
            content: 'Jupiter as Dara Karaka gives Jupiter strong dasha results in marriage.',
            score: 0.90,
          },
        ])
      )
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Jupiter',
    })
    const envelope = parseResult(result)

    // results must be an array
    expect(Array.isArray(envelope['results'])).toBe(true)
    // sources_searched must be an array
    const sourcesSearched = envelope['sources_searched'] as unknown[]
    expect(Array.isArray(sourcesSearched)).toBe(true)
    expect(sourcesSearched.length).toBeGreaterThan(0)
  })

  // ── TC.4: Deduplication — same chunk_id appears once ─────────────────────

  it('TC.4 — deduplication: if vector and classical return same chunk_id, it appears once', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    const sharedChunkId = 'shared-chunk-001'
    const sharedContent = 'Mercury Mahadasha bestows Mercury intelligence and commerce.'

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: sharedChunkId,
            text_id: 'BPHS',
            chapter: 55,
            verse: 7,
            content: sharedContent,
            score: 0.95,
          },
        ])
      )
      .mockResolvedValueOnce(
        buildClassicalEnvelope([
          {
            chunk_id: sharedChunkId, // Same chunk_id!
            text_id: 'BPHS',
            chapter: 55,
            verse: 7,
            content: sharedContent,
            relevance_score: 0.75,
          },
        ])
      )

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Mercury',
    })
    const envelope = parseResult(result)

    const results = envelope['results'] as Array<{ text_id: string }>
    // Should appear exactly once despite being returned by both sources
    const matchingChunks = results.filter(
      r => (r as unknown as Record<string, unknown>)['text_id'] === 'BPHS',
    )
    // There could be multiple BPHS chunks overall, but specifically verify total result_count
    // is 1 (only the deduplicated chunk matches "Mercury")
    expect(envelope['result_count']).toBe(1)
  })

  // ── TC.5: School derivation — BPHS text_id → Parashari ───────────────────

  it('TC.5 — chunk with text_id "BPHS" gets school "Parashari"', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'bphs-school-001',
            text_id: 'BPHS',
            chapter: 33,
            verse: 1,
            content: 'Venus Mahadasha brings comforts, arts, and Venus pleasures.',
            score: 0.87,
            // No school field — should be derived
          },
        ])
      )
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Venus',
    })
    const envelope = parseResult(result)

    const results = envelope['results'] as Array<Record<string, unknown>>
    expect(results.length).toBeGreaterThanOrEqual(1)

    const bphsResult = results.find(r => r['text_id'] === 'BPHS')
    expect(bphsResult).toBeDefined()
    expect(bphsResult!['school']).toBe('Parashari')
  })

  // ── Additional: school derivation for other text_ids ─────────────────────

  it('school derivation — JAIMINI_SUTRAM → Jaimini, KP_READER → KP', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'jaimini-001',
            text_id: 'JAIMINI_SUTRAM',
            content: 'Sun Mahadasha — Atmakaraka Sun gives Sun kingship and authority.',
            score: 0.80,
          },
          {
            chunk_id: 'kp-001',
            text_id: 'KP_READER',
            content: 'Sun dasha KP sub-lord Sun: significations of Sun dominate the Sun period.',
            score: 0.75,
          },
        ])
      )
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Sun',
    })
    const envelope = parseResult(result)

    const results = envelope['results'] as Array<Record<string, unknown>>
    const jaiminiResult = results.find(r => r['text_id'] === 'JAIMINI_SUTRAM')
    if (jaiminiResult) expect(jaiminiResult['school']).toBe('Jaimini')

    const kpResult = results.find(r => r['text_id'] === 'KP_READER')
    if (kpResult) expect(kpResult['school']).toBe('KP')
  })

  // ── Additional: max_results cap ───────────────────────────────────────────

  it('max_results caps the number of returned results', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    // 5 chunks, all containing "Mars"
    const chunks = Array.from({ length: 5 }, (_, i) => ({
      chunk_id: `mars-chunk-${i}`,
      text_id: 'BPHS',
      chapter: i + 1,
      verse: 1,
      content: `Mars Mahadasha effect ${i + 1}: energy and courage dominate the Mars period.`,
      score: 0.9 - i * 0.05,
    }))

    mockFn
      .mockResolvedValueOnce(buildVectorEnvelope(chunks))
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Mars',
      max_results: 3,
    })
    const envelope = parseResult(result)

    expect(envelope['result_count']).toBe(3)
    const results = envelope['results'] as unknown[]
    expect(results.length).toBe(3)
  })

  // ── Additional: maha_dasha_lord content filter removes non-matching chunks ─

  it('content filter removes chunks that do not mention maha_dasha_lord', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'moon-001',
            text_id: 'BPHS',
            content: 'Moon Mahadasha brings emotional sensitivity and Moon travel.',
            score: 0.90,
          },
          {
            chunk_id: 'irrelevant-001',
            text_id: 'BPHS',
            content: 'This chunk does not mention the requested planet at all.',
            score: 0.85,
          },
        ])
      )
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Moon',
    })
    const envelope = parseResult(result)

    const results = envelope['results'] as Array<Record<string, unknown>>
    // All results must contain "moon" (case-insensitive)
    for (const r of results) {
      const content = (r['content'] as string).toLowerCase()
      expect(content).toContain('moon')
    }
    expect(envelope['result_count']).toBe(1)
  })

  // ── Additional: both calls fail → ok:true, result_count=0 ────────────────

  it('when both primitives fail, returns ok:true with result_count=0', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(buildErrorEnvelope())
      .mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Ketu',
    })
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    expect(envelope['result_count']).toBe(0)
    expect(Array.isArray(envelope['results'])).toBe(true)
  })

  // ── Additional: text_ids filter limits to specified texts ─────────────────

  it('text_ids filter: only specified text_ids appear in results', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'bphs-001',
            text_id: 'BPHS',
            content: 'Saturn Mahadasha gives Saturn discipline per BPHS.',
            score: 0.88,
          },
          {
            chunk_id: 'kp-001',
            text_id: 'KP_READER',
            content: 'Saturn dasha KP sub-lord analysis for Saturn placement.',
            score: 0.82,
          },
        ])
      )
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Saturn',
      text_ids: ['BPHS'],
    })
    const envelope = parseResult(result)

    const results = envelope['results'] as Array<Record<string, unknown>>
    for (const r of results) {
      expect(r['text_id']).toBe('BPHS')
    }

    // sources_searched should reflect the text_ids param
    const sourcesSearched = envelope['sources_searched'] as string[]
    expect(sourcesSearched).toContain('BPHS')
  })

  // ── Additional: results are sorted by relevance_score descending ──────────

  it('results are sorted by relevance_score descending', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(
        buildVectorEnvelope([
          {
            chunk_id: 'low-score',
            text_id: 'BPHS',
            content: 'Jupiter Mahadasha low relevance result.',
            score: 0.60,
          },
          {
            chunk_id: 'high-score',
            text_id: 'BPHS',
            content: 'Jupiter Mahadasha high relevance result for Jupiter.',
            score: 0.95,
          },
        ])
      )
      .mockResolvedValueOnce(buildClassicalEnvelope([]))

    const result = await callQueryPlanetaryPeriodPredictions({
      maha_dasha_lord: 'Jupiter',
    })
    const envelope = parseResult(result)

    const results = envelope['results'] as Array<Record<string, unknown>>
    for (let i = 1; i < results.length; i++) {
      const prev = results[i - 1]['relevance_score'] as number
      const curr = results[i]['relevance_score'] as number
      expect(prev).toBeGreaterThanOrEqual(curr)
    }
  })
})
