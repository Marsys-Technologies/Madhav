/**
 * ref_graha_reference_get — exercise test (W-L0-4)
 * =============================================================================
 * Strategy §4.2 W-L0-4: "ref_graha_reference_get (or equivalent) exists and is
 * exercised". Exercised = the handler runs end-to-end against the db seam
 * (mocked here, same pattern as every other L0 capability test) and the
 * reference_planets row passes through with its citation and honest nulls.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { refGrahaReferenceGetCapability } from '../ref_graha_reference_get'

const venusRow = {
  planet_id: 'venus',
  canonical_name_en: 'Venus',
  canonical_name_sa: 'Shukra',
  exaltation_sign: 12,
  exaltation_degree: '27.00',
  debilitation_sign: 6,
  mooltrikona_sign: 7,
  own_signs: [2, 7],
  natural_benefic: true,
  karak_domains: ['beauty', 'marriage', 'luxury', 'arts', 'vehicles', 'passion'],
  dasha_years: '20.0',
  source_citation: 'BPHS Ch.3 (Grahana-svarupa-adhyaya)',
}

const ascendantRow = {
  planet_id: 'ascendant',
  canonical_name_en: 'Ascendant',
  canonical_name_sa: 'Lagna',
  exaltation_sign: null,
  exaltation_degree: null,
  debilitation_sign: null,
  mooltrikona_sign: null,
  own_signs: [],
  natural_benefic: true,
  karak_domains: ['self', 'body', 'appearance', 'health', 'personality'],
  dasha_years: null,
  source_citation: 'BPHS Ch.7 (Bhava-svarupa-adhyaya)',
}

describe('refGrahaReferenceGetCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries reference_planets unfiltered, ordered by planet_id', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [ascendantRow, venusRow] })
    const result = await refGrahaReferenceGetCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM reference_planets')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
    const content = result.content as { rows: unknown[]; count: number }
    expect(content.count).toBe(2)
  })

  it('serves names in both scripts and the source citation as data (presentation obligation §2.2)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [venusRow] })
    const result = await refGrahaReferenceGetCapability.handler({ planet_id: 'venus' }, undefined)
    const content = result.content as { rows: Array<Record<string, unknown>> }
    const row = content.rows[0]
    expect(row['canonical_name_en']).toBe('Venus')
    expect(row['canonical_name_sa']).toBe('Shukra')
    expect(String(row['source_citation'])).toContain('BPHS')
  })

  it('carries honest nulls through (angles have no dignity — null, never hidden)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [ascendantRow] })
    const result = await refGrahaReferenceGetCapability.handler({ planet_id: 'ascendant' }, undefined)
    const content = result.content as { rows: Array<Record<string, unknown>> }
    expect(content.rows[0]['exaltation_sign']).toBeNull()
    expect(content.rows[0]['dasha_years']).toBeNull()
    expect('exaltation_sign' in content.rows[0]).toBe(true)
  })

  it('planet_id filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await refGrahaReferenceGetCapability.handler({ planet_id: 'VeNuS' }, undefined)
    expect(mockQuery.mock.calls[0][0] as string).toContain('LOWER(planet_id) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['VeNuS'])
  })

  it('unknown planet_id: empty result says why (empty_reason, B.10)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await refGrahaReferenceGetCapability.handler({ planet_id: 'pluto' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as { count: number; empty_reason?: string }
    expect(content.count).toBe(0)
    expect(content.empty_reason).toContain('pluto')
  })

  it('declares the W-L0-4 density_contract explicitly', () => {
    expect(refGrahaReferenceGetCapability.density_contract).toEqual({
      max_verdict_bytes: 1024,
      max_digest_bytes: 4096,
      paginated: false,
      facets: ['planet_id'],
      empty_reason: true,
    })
  })

  it('db error surfaces as is_error, never thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('connection refused'))
    const result = await refGrahaReferenceGetCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })
})
