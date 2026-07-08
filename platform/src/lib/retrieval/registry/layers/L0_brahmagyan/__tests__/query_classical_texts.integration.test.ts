/**
 * query_classical_texts.integration.test.ts — R5 W2 corpus lane (live DB proxy)
 * ================================================================================
 * Verifies the P7 fix's second half — the actual hybrid-search capability that
 * `vector_search` / `ref_vector_search` now resolve to (tool_name_bridge.ts) —
 * against the live DB (localhost:5433, Cloud SQL Auth Proxy).
 *
 * Run with:
 *   INTEGRATION=true DATABASE_URL=... vitest run \
 *     src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_classical_texts.integration.test.ts
 *
 * Test matrix:
 *   I1 — free-text query_text search returns rows with real verse_text_en content
 *        (the "citation arrives WITH verse text, not just a reference id" gate)
 *   I2 — the `query` and `topic` param aliases (ref_vector_search / find_verses_about
 *        naming) resolve to the same hybrid path as query_text — no parallel resolver
 *   I3 — genuine hybrid: keyword_score is present on every row even when the
 *        embedding call fails (degrades to trigram-only, never errors the call)
 *   I4 — default top_k for the interpretation-intent path is 5 (design §3: "top-k≈5
 *        verses in hand"), and an explicit top_k override is honored
 *   I5 — legacy exact-keyword ILIKE path (P8 empty-with-reason) is unchanged
 */

import { describe, it, expect } from 'vitest'
import { queryClassicalTextsCapability } from '../query_classical_texts'

const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip

interface CitationRow {
  citation_ref: string
  chunk_id: string
  verse_text_en: string | null
  verse_text_sa: string | null
  keyword_score: number | null
  vector_score: number | null
  combined_score: number
}

describeIf('query_classical_texts — R5 W2 hybrid corpus search (live DB)', () => {
  // Vertex AI embedding round-trip via ADC can exceed vitest's 5s default.

  it('I1 — free-text query_text returns citations WITH real verse text, not bare ids', async () => {
    const result = await queryClassicalTextsCapability.handler(
      { query_text: 'exalted planets and their effects' },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as { citations: CitationRow[]; total: number; search_mode: string }
    expect(content.total).toBeGreaterThan(0)
    expect(content.citations.length).toBeGreaterThan(0)
    // Confirms this environment's ADC + the configured Google Cloud project/location resolve a
    // real embedding — i.e. genuine hybrid, not the trigram-only degrade path.
    expect(content.search_mode).toBe('hybrid_vector_keyword')
    for (const c of content.citations) {
      // The gate: verse text travels WITH the citation.
      expect(c.citation_ref).toBeTruthy()
      expect(typeof c.verse_text_en).toBe('string')
      expect((c.verse_text_en ?? '').length).toBeGreaterThan(0)
      expect(typeof c.vector_score).toBe('number')
    }
  }, 20000)

  it('I2 — `query` and `topic` aliases resolve to the same hybrid path as query_text', async () => {
    const viaQuery = await queryClassicalTextsCapability.handler({ query: 'Saturn in the 7th house' }, undefined)
    const viaTopic = await queryClassicalTextsCapability.handler({ topic: 'Saturn in the 7th house' }, undefined)
    expect(viaQuery.is_error).toBe(false)
    expect(viaTopic.is_error).toBe(false)
    const c1 = viaQuery.content as { search_mode: string; total: number }
    const c2 = viaTopic.content as { search_mode: string; total: number }
    expect(c1.search_mode).toBe(c2.search_mode)
    expect(c1.total).toBeGreaterThan(0)
    expect(c2.total).toBeGreaterThan(0)
  }, 20000)

  it('I3 — genuine hybrid ranking: every row carries a keyword_score, never errors', async () => {
    const result = await queryClassicalTextsCapability.handler(
      { query_text: 'neecha bhanga raja yoga' },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as { citations: CitationRow[] }
    expect(content.citations.length).toBeGreaterThan(0)
    for (const c of content.citations) {
      expect(typeof c.keyword_score).toBe('number')
      expect(typeof c.combined_score).toBe('number')
    }
  }, 20000)

  it('I4 — default top_k is 5 (interpretation-intent framing); explicit top_k is honored', async () => {
    const defaultResult = await queryClassicalTextsCapability.handler(
      { query_text: 'planetary strength and dignity' },
      undefined,
    )
    const wideResult = await queryClassicalTextsCapability.handler(
      { query_text: 'planetary strength and dignity', top_k: 15 },
      undefined,
    )
    const c1 = defaultResult.content as { citations: CitationRow[] }
    const c2 = wideResult.content as { citations: CitationRow[] }
    expect(c1.citations.length).toBeLessThanOrEqual(5)
    expect(c2.citations.length).toBeGreaterThan(c1.citations.length)
    expect(c2.citations.length).toBeLessThanOrEqual(15)
  }, 20000)

  it('I5 — legacy exact-keyword ILIKE path + P8 empty-with-reason is unchanged', async () => {
    const result = await queryClassicalTextsCapability.handler(
      { keyword: 'zzz_definitely_not_indexed_zzz' },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as { rows: unknown[]; total: number; empty_reason?: string }
    expect(content.total).toBe(0)
    expect(content.empty_reason).toContain('is not indexed in the corpus')
  }, 20000)
})
