/**
 * query_classical_texts_embed_timeout.test.ts — PARISHODHANA B1 regression.
 *
 * Newly-discovered live defect (distinct from the documented CR-42 silent-filter-
 * fallthrough): `ref_dasha_systems_get`, `ref_nakshatra_get`, `ref_rules_search`, and
 * `ref_vector_search` all route through this capability's free-text/hybrid path
 * (query_text/query/topic), which calls `embedText()` (Vertex AI, platform/src/lib/
 * embeddings/embedText.ts). `embedText()` wires no internal timeout/AbortSignal of its
 * own on either the ADC auth handshake or the :predict fetch — so a slow/hung
 * credential or network path there blocked `tryEmbedQuery()` INDEFINITELY, because its
 * try/catch only ever caught a REJECTED promise, never a HUNG one. Every live call
 * through the MCP layer eventually failed with a bare "TimeoutError: The operation was
 * aborted due to timeout" once the MCP tool's own outer 15s AbortSignal.timeout cut the
 * whole HTTP round-trip — an internal error with zero honest degradation, even though
 * this file's own doc comment already promised graceful trigram-only degradation on
 * embedding failure.
 *
 * Fix: EMBED_TIMEOUT_MS (4s) bounds tryEmbedQuery() via Promise.race, so a hung
 * embedText() call now degrades to trigram-only ranking (search_mode:
 * 'keyword_trigram_only') well inside any caller's outer deadline, instead of hanging
 * past it.
 *
 * These tests mock `@/lib/db/client` and `@/lib/embeddings/embedText` — no live DB or
 * Vertex AI call is made. Fake timers simulate the hang without a real 4s wait.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery, mockEmbedText } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockEmbedText: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/embeddings/embedText', () => ({ embedText: mockEmbedText }))

import { queryClassicalTextsCapability } from '../query_classical_texts'

const SAMPLE_ROW = {
  id: 'c1', text_id: 'bphs', chunk_id: 'bphs_pg0001_c01', verse_ref: 'PG1:C1', chapter: 1,
  content_en: 'sample verse text', content_sa: null, content_summary: null,
  source_citation: 'BPHS', tradition_school: 'vedic:parashari', topics: [],
  vector_score: 0.9, keyword_score: 0.5,
}

describe('query_classical_texts — embedText timeout hardening (PARISHODHANA B1)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockEmbedText.mockReset()
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('degrades to keyword_trigram_only (never hangs) when embedText() hangs indefinitely', async () => {
    vi.useFakeTimers()
    // Simulate a hung Vertex AI call — a promise that never resolves or rejects.
    mockEmbedText.mockReturnValue(new Promise(() => {}))
    mockQuery.mockResolvedValue({ rows: [SAMPLE_ROW] })

    const resultPromise = queryClassicalTextsCapability.handler({ query_text: 'dasha system' }, undefined)

    // Advance past EMBED_TIMEOUT_MS (4_000ms) without waiting in real time.
    await vi.advanceTimersByTimeAsync(4_100)
    const result = await resultPromise

    expect(result.is_error).toBe(false)
    const content = result.content as { search_mode: string; total: number }
    // The whole call completed — it did NOT hang past the internal timeout.
    expect(content.search_mode).toBe('keyword_trigram_only')
    expect(content.total).toBeGreaterThan(0)
  })

  it('still returns hybrid_vector_keyword when embedText() resolves normally (no regression)', async () => {
    mockEmbedText.mockResolvedValue(new Array(768).fill(0.1))
    mockQuery.mockResolvedValue({ rows: [SAMPLE_ROW] })

    const result = await queryClassicalTextsCapability.handler({ query_text: 'nakshatra lords' }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as { search_mode: string; total: number }
    expect(content.search_mode).toBe('hybrid_vector_keyword')
    expect(content.total).toBeGreaterThan(0)
  })

  it('still degrades gracefully when embedText() rejects outright (pre-existing behavior preserved)', async () => {
    mockEmbedText.mockRejectedValue(new Error('no GCP credentials'))
    mockQuery.mockResolvedValue({ rows: [SAMPLE_ROW] })

    const result = await queryClassicalTextsCapability.handler({ query_text: 'gajakesari yoga' }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as { search_mode: string; total: number }
    expect(content.search_mode).toBe('keyword_trigram_only')
    expect(content.total).toBeGreaterThan(0)
  })
})
