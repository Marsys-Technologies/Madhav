/**
 * F-144 — query_mantras / ref_mantras_get scaffold_status leak.
 * ================================================================
 * `brahmagyan/l0_remedy_corpus.py::sweep_classical_text_chunks` (F-144's other lane, PR #1408)
 * grades every corpus_sweep row into `scaffold_status` ('live' | 'review' | 'rejected') based on
 * a deterministic OCR-legibility score. But `query_mantras`'s SQL
 * (`register_d7_channel.ts`) matched on `LOWER(remedy_type) = 'mantra' OR LOWER(category) =
 * 'mantras'` with NO `scaffold_status` predicate at all — so a garbled-OCR sweep row graded
 * 'review' (or a hand-rejected 'rejected' row) was served through `ref_mantras_get` exactly like
 * a hand-curated mantra. Independently corroborated at
 * `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` R-19 (named example:
 * `sweep_jupiter_mantra_2ab17171`). `ref_mantras_get` had no behavioural test prior to this file
 * — only registry-presence assertions.
 *
 * This test is DB-free (mocks `@/lib/db/client`), per the `register_d7_remedy_pagination.test.ts`
 * precedent for this same file.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import { query } from '@/lib/db/client'
import { clearRegistry, getCapability } from '../../index'
import { registerD7ChannelCapabilities } from '../register_d7_channel'

const mockQuery = vi.mocked(query)

describe('query_mantras — scaffold_status gate (F-144)', () => {
  beforeEach(() => {
    clearRegistry()
    registerD7ChannelCapabilities()
    mockQuery.mockReset()
  })

  it("SQL WHERE clause requires scaffold_status = 'live'", async () => {
    mockQuery.mockResolvedValue({ rows: [] } as never)
    const cap = getCapability('marsys://tool/L0/query_mantras')!

    await cap.handler({})

    expect(mockQuery).toHaveBeenCalledTimes(1)
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql as string).toContain("scaffold_status = 'live'")
  })

  it('does not serve a corpus_sweep row that is not scaffold_status=live', async () => {
    // The mock stands in for the DB's own WHERE-clause filtering: a 'review'-graded sweep
    // row (like the named sweep_jupiter_mantra_2ab17171 example) is never returned by the
    // (correctly-filtered) query, so the handler must not have to filter it a second time —
    // asserting the row simply never appears in returned_count.
    mockQuery.mockResolvedValue({ rows: [] } as never)
    const cap = getCapability('marsys://tool/L0/query_mantras')!

    const result = await cap.handler({ planet: 'Jupiter' })

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['returned_count']).toBe(0)
    expect(content['mantras']).toEqual([])
  })

  it('still serves a live-graded mantra row (regression guard: filter is not blanket-exclusionary)', async () => {
    const liveRow = {
      remedy_id: 'mars-mantra-1', planet: 'mars', deity: 'Mangal',
      mantra_sanskrit: 'Om Angarakaya Namah', mantra_transliteration: 'Om Angarakaya Namah',
      mantra_text: null, prescription_text: 'Recite daily.', timing_rules_jsonb: null,
      source_canonical_id: 'BPHS', classical_attestation_text: null, classical_ref: null,
    }
    mockQuery.mockResolvedValue({ rows: [liveRow] } as never)
    const cap = getCapability('marsys://tool/L0/query_mantras')!

    const result = await cap.handler({ planet: 'Mars' })

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['returned_count']).toBe(1)
    expect(content['mantras']).toEqual([liveRow])
  })

  it('planet filter and scaffold_status filter compose (planet is still $1)', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as never)
    const cap = getCapability('marsys://tool/L0/query_mantras')!

    await cap.handler({ planet: 'Venus' })

    const [sql, values] = mockQuery.mock.calls[0]!
    expect(sql as string).toContain("scaffold_status = 'live'")
    expect(sql as string).toContain('LOWER(planet) = LOWER($1)')
    expect(values).toEqual(['Venus'])
  })
})
