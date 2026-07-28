/**
 * PARISHODHANA B1 (R-29/EL-51 follow-up) — regression tests.
 *
 * Two serving-layer fixes to `query_remedies` (the capability behind
 * `bodha_remedies_get`), found while investigating the reconciliation register's
 * "3 Saturn prescriptions vs 29 in the global corpus" finding:
 *
 *   1. `tradition` filter (mantra|gemstone|charity|vrata|yantra|ayurvedic per its own
 *      enum) was matching ONLY the `tradition` column — which the bo_upaya writer
 *      always sets to the literal 'parashari' for every row. The category axis this
 *      param actually describes lives in `remedy_category`, a different column. Live
 *      DB confirmed: `bodha_remedies_get(graha:'Moon', tradition:'gemstone')` returned
 *      ZERO prescriptions even though a real gemstone prescription for Moon exists and
 *      is returned when no tradition filter is applied. Fixed by OR-matching both
 *      columns.
 *   2. `maraka_contraindication_verdict` (β.G/EL-51 — a real, BPHS Ch.44-cited,
 *      deterministic verdict the bo_upaya writer computes for gemstone-category rows)
 *      lives inside `prescription_detail_jsonb`, which compact-mode output drops
 *      entirely. It is now extracted and surfaced directly on the compact row.
 *
 * NOTE: the Saturn "3 vs 29" narrowing itself is NOT fixed here — confirmed via
 * `_fetch_remedies_for_graha(conn, graha, limit=3)` in bo_upaya.py (writer-level,
 * out of this serving-layer session's authorized scope; PARKED-HONEST).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryRemediesCapability } from '../query_remedies'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('query_remedies (L2 Bodha) — tradition/remedy_category OR-match (PARISHODHANA B1)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('the prescription-side SQL OR-matches both tradition and remedy_category (never a bare tradition-only exact match)', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    await queryRemediesCapability.handler({ chart_id: CHART_ID, tradition: 'gemstone' }, undefined)

    const prescriptionCall = queryMock.mock.calls.find(
      call => typeof call[0] === 'string' && (call[0] as string).includes('FROM bodha_rm_remedy_prescriptions'),
    )
    expect(prescriptionCall).toBeDefined()
    const [sql, params] = prescriptionCall as [string, unknown[]]
    expect(sql).toMatch(/LOWER\(tradition\)\s*=\s*LOWER\(\$\d+\)\s*OR\s*LOWER\(remedy_category\)\s*=\s*LOWER\(\$\d+\)/i)
    expect(params).toContain('gemstone')
  })

  it('tradition:"gemstone" returns a prescription whose real column value is tradition:"parashari"/remedy_category:"gemstone" (the bo_upaya data shape) — the fix must not require an exact tradition-column match', async () => {
    const gemstoneRow = {
      prescription_id: 'p-moon-gem-1',
      target_graha: 'Moon',
      tradition: 'parashari',
      remedy_category: 'gemstone',
      prescription_detail_jsonb: { maraka_contraindication_verdict: { verdict: 'no_contraindication_found' } },
    }
    queryMock.mockImplementation((sql: string) => {
      if (String(sql).includes('FROM bodha_rm_remedy_prescriptions')) return Promise.resolve({ rows: [gemstoneRow] })
      return Promise.resolve({ rows: [] })
    })

    const result = await queryRemediesCapability.handler(
      { chart_id: CHART_ID, graha: 'Moon', tradition: 'gemstone' },
      undefined,
    ) as { content: { prescriptions: Array<{ remedy_category: unknown }> }; is_error: boolean }

    expect(result.is_error).toBe(false)
    expect(result.content.prescriptions.length).toBe(1)
    expect(result.content.prescriptions[0].remedy_category).toBe('gemstone')
  })
})

describe('query_remedies (L2 Bodha) — maraka_contraindication_verdict surfacing (PARISHODHANA B1 / EL-51)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('a gemstone prescription with a non-null maraka_contraindication_verdict inside prescription_detail_jsonb surfaces it on the compact row', async () => {
    const verdict = {
      verdict: 'contraindicated',
      reason: 'Saturn is the 7th-house lord (a maraka house) from lagna in this chart.',
      citation: 'BPHS Ch.44 "Maraka (Killer) Planets"',
    }
    queryMock.mockImplementation((sql: string) => {
      if (String(sql).includes('FROM bodha_rm_remedy_prescriptions')) {
        return Promise.resolve({
          rows: [{
            prescription_id: 'p-sat-gem-1',
            target_graha: 'Saturn',
            remedy_category: 'gemstone',
            prescription_detail_jsonb: { maraka_contraindication_verdict: verdict },
          }],
        })
      }
      return Promise.resolve({ rows: [] })
    })

    const result = await queryRemediesCapability.handler(
      { chart_id: CHART_ID, graha: 'Saturn' },
      undefined,
    ) as { content: { prescriptions: Array<{ maraka_contraindication_verdict: unknown }> } }

    expect(result.content.prescriptions[0].maraka_contraindication_verdict).toEqual(verdict)
  })

  it('a non-gemstone prescription (no maraka_contraindication_verdict key at all) surfaces null, not undefined/omitted', async () => {
    queryMock.mockImplementation((sql: string) => {
      if (String(sql).includes('FROM bodha_rm_remedy_prescriptions')) {
        return Promise.resolve({
          rows: [{
            prescription_id: 'p-sat-mantra-1',
            target_graha: 'Saturn',
            remedy_category: 'mantra',
            prescription_detail_jsonb: { prescription_text: 'Recite...', mantra_text: null },
          }],
        })
      }
      return Promise.resolve({ rows: [] })
    })

    const result = await queryRemediesCapability.handler(
      { chart_id: CHART_ID, graha: 'Saturn' },
      undefined,
    ) as { content: { prescriptions: Array<{ maraka_contraindication_verdict: unknown }> } }

    expect(result.content.prescriptions[0].maraka_contraindication_verdict).toBeNull()
  })

  it('fields="all" still returns the full raw row (unaffected by the compact-mode extraction fix)', async () => {
    const rawRow = {
      prescription_id: 'p-sat-gem-2',
      target_graha: 'Saturn',
      remedy_category: 'gemstone',
      prescription_detail_jsonb: { maraka_contraindication_verdict: { verdict: 'no_contraindication_found' } },
      associated_doshas_array: null,
    }
    queryMock.mockImplementation((sql: string) => {
      if (String(sql).includes('FROM bodha_rm_remedy_prescriptions')) return Promise.resolve({ rows: [rawRow] })
      return Promise.resolve({ rows: [] })
    })

    const result = await queryRemediesCapability.handler(
      { chart_id: CHART_ID, graha: 'Saturn', fields: 'all' },
      undefined,
    ) as { content: { prescriptions: Array<Record<string, unknown>> } }

    expect(result.content.prescriptions[0]).toEqual(rawRow)
  })
})
