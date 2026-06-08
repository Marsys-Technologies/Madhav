/**
 * classical_texts_smoke.test.ts
 * Acceptance gate smoke test for brahmagyan.texts (delta build 2026-06-03).
 *
 * Assertions:
 * 1. classical_texts table has >= 4 rows
 * 2. classical_chunks table has >= 4000 rows
 * 3. BPHS text present (native birthdate 1984-02-05 ground-truth: BPHS is the
 *    primary Parashara source used for L1 chart analysis of this chart)
 * 4. At least one chunk has a non-null embedding vector
 * 5. classical_text_search returns results for a FORENSIC-grounded query:
 *    "Sun in Leo 10th house Parashara" (native Sun is Leo 10H per FORENSIC v8.0 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md))
 * 6. Verse-ref citation lookup: query containing "BPHS" returns a BPHS-tradition result
 * 7. classical_attributions has >= 1 row (attribution pipeline ran)
 *
 * Skip automatically when DATABASE_URL not set (CI without live DB).
 */

import { describe, it, expect, beforeAll } from 'vitest'
import { query } from '../../src/lib/db/client'
import { classical_text_search } from '../../src/lib/tools/classical_text_search'

const HAS_DB = Boolean(process.env.DATABASE_URL)
const itDb = HAS_DB ? it : it.skip

describe('brahmagyan.texts smoke — classical corpus', () => {
  beforeAll(async () => {
    if (!HAS_DB) return
  })

  itDb('classical_texts: >= 4 rows present', async () => {
    const res = await query<{ count: string }>('SELECT count(*)::text AS count FROM classical_texts')
    const count = parseInt(res.rows[0]?.count ?? '0', 10)
    expect(count).toBeGreaterThanOrEqual(4)
  })

  itDb('classical_chunks: >= 4000 rows present', async () => {
    const res = await query<{ count: string }>('SELECT count(*)::text AS count FROM classical_chunks')
    const count = parseInt(res.rows[0]?.count ?? '0', 10)
    expect(count).toBeGreaterThanOrEqual(4000)
  })

  itDb('BPHS present (FORENSIC ground-truth: primary Parashara source)', async () => {
    const res = await query<{ text_key: string; chunk_count: number }>(
      `SELECT text_key, chunk_count FROM classical_texts WHERE text_key = 'bphs'`
    )
    expect(res.rows.length).toBe(1)
    expect(res.rows[0]?.chunk_count).toBeGreaterThan(0)
  })

  itDb('at least one chunk has a non-null embedding', async () => {
    const res = await query<{ has_embedding: boolean }>(
      `SELECT (embedding IS NOT NULL) AS has_embedding
       FROM classical_chunks WHERE embedding IS NOT NULL LIMIT 1`
    )
    expect(res.rows.length).toBeGreaterThan(0)
    expect(res.rows[0]?.has_embedding).toBe(true)
  })

  itDb('classical_text_search: FORENSIC query returns results (native Sun Leo 10H)', async () => {
    // Native (1984-02-05): Sun is in Leo, 10th house per FORENSIC v8.0 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
    const result = await classical_text_search({
      query: 'Sun exalted Leo tenth house raja yoga Parashara',
      limit: 3,
    })
    expect(result.results.length).toBeGreaterThan(0)
    expect(result.results[0]).toMatchObject({
      chunk_id: expect.any(String),
      text_key: expect.any(String),
      content: expect.any(String),
      similarity: expect.any(Number),
    })
  })

  itDb('classical_text_search: school filter (parashari) returns only parashari results', async () => {
    const result = await classical_text_search({
      query: 'ascendant lord dasha period results',
      schools: ['parashari'],
      limit: 5,
    })
    for (const r of result.results) {
      expect(r.school).toBe('parashari')
    }
  })

  itDb('classical_text_search: verse-citation style query resolves BPHS result', async () => {
    const result = await classical_text_search({
      query: 'BPHS chapter 1 Parashara sage sages',
      limit: 3,
    })
    expect(result.results.length).toBeGreaterThan(0)
    const bphsHit = result.results.find(r => r.text_key === 'bphs')
    expect(bphsHit).toBeDefined()
  })

  itDb('classical_attributions: >= 1 attribution row exists', async () => {
    const res = await query<{ count: string }>(
      'SELECT count(*)::text AS count FROM classical_attributions'
    )
    const count = parseInt(res.rows[0]?.count ?? '0', 10)
    expect(count).toBeGreaterThanOrEqual(1)
  })
})
