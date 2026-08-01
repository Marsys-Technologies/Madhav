/**
 * query_parihara_graph — ṢAḌ-DARŚANA W3 items 36/41 substrate reader.
 * The load-bearing assertions here are the two honesty disclosures the substrate
 * ships and this reader must not soften: the placeholder-vs-real-cited doṣa split
 * (queried LIVE, never a remembered literal) and the scope=natal reality — zero
 * muhūrta-scope cancellation rules exist, and the response has to say so.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryPariharaGraphCapability } from '../query_parihara_graph'

function pariharaRow(over: Record<string, unknown> = {}) {
  return {
    dosha_canonical_id: 'manglik_dosha',
    dosha_name_en: 'Manglik Dosha',
    dosha_category: 'relationship',
    cancellation_index: 1,
    cancellation_condition_text: 'Mars in own sign cancels',
    net_standing: 'cancellable_by_condition',
    scope: 'natal',
    source_text_id: 'bphs',
    source_chapter: 80,
    source_citation: 'Brihat Parasara Hora Sastra (bphs), ch.80',
    ...over,
  }
}

describe('queryPariharaGraphCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('reports the placeholder/real-cited doṣa split from a LIVE query, not a literal', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [pariharaRow()] })                       // rules
      .mockResolvedValueOnce({ rows: [{ real_cited: '26', placeholder_only: '53' }] }) // split
    const result = await queryPariharaGraphCapability.handler({ section: 'parihara_rules' }, undefined)
    const section = (result.content as Record<string, unknown>)['parihara_rules'] as Record<string, unknown>

    expect(section['count']).toBe(1)
    expect(section['real_cited_dosha_count']).toBe(26)
    expect(section['placeholder_only_dosha_count']).toBe(53)
    expect(String(section['placeholder_note'])).toContain('classical_tradition')
    // The split really is computed by SQL against the catalog, not asserted.
    expect(mockQuery.mock.calls[1][0] as string).toContain('FROM brahma_dosha_catalog')
  })

  it('states the scope=natal corpus gap explicitly when zero muhūrta-scope rules exist', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [pariharaRow(), pariharaRow({ dosha_canonical_id: 'kala_sarpa', cancellation_index: 1 })] })
      .mockResolvedValueOnce({ rows: [{ real_cited: '26', placeholder_only: '53' }] })
    const result = await queryPariharaGraphCapability.handler({ section: 'parihara_rules' }, undefined)
    const section = (result.content as Record<string, unknown>)['parihara_rules'] as Record<string, unknown>

    expect(section['muhurta_scope_rule_count']).toBe(0)
    expect(String(section['scope_note'])).toContain('ZERO muhūrta-scope')
  })

  it('counts muhūrta-scope rules honestly when they do exist', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [pariharaRow({ scope: 'muhurta' })] })
      .mockResolvedValueOnce({ rows: [{ real_cited: '26', placeholder_only: '53' }] })
    const result = await queryPariharaGraphCapability.handler({ section: 'parihara_rules' }, undefined)
    const section = (result.content as Record<string, unknown>)['parihara_rules'] as Record<string, unknown>
    expect(section['muhurta_scope_rule_count']).toBe(1)
    expect(String(section['scope_note'])).not.toContain('ZERO')
  })

  it('returns activity rules filtered and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ activity_class: 'vivah', factor_type: 'tithi', factor_id: 2, quality_score: 0.9 }] })
    await queryPariharaGraphCapability.handler({ section: 'activity_rules', activity_class: 'vivah' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM bg_muhurta_activity_rules')
    expect(sql).toContain('activity_class = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual(['vivah'])
  })

  it('summarises census dispositions (item 41 completeness register)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        { factor_family: 'panchangika', factor_name: 'tithi', disposition: 'computed' },
        { factor_family: 'combination_yoga', factor_name: 'mrityu_yoga', disposition: 'not_in_corpus' },
        { factor_family: 'degree_sensitive', factor_name: 'mrityu_bhaga', disposition: 'not_computed' },
      ],
    })
    const result = await queryPariharaGraphCapability.handler({ section: 'factor_census' }, undefined)
    const section = (result.content as Record<string, unknown>)['factor_census'] as Record<string, unknown>
    expect(section['disposition_counts']).toEqual({ computed: 1, not_in_corpus: 1, not_computed: 1 })
  })

  it('returns all three sections when none is requested', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ real_cited: '0', placeholder_only: '0' }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
    const result = await queryPariharaGraphCapability.handler({}, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['sections_returned']).toEqual(['parihara_rules', 'activity_rules', 'factor_census'])
    for (const key of ['parihara_rules', 'activity_rules', 'factor_census']) {
      expect(String((content[key] as Record<string, unknown>)['empty_reason'])).toContain('may not be built')
    }
  })

  it('rejects unknown section / activity_class without touching the DB', async () => {
    expect((await queryPariharaGraphCapability.handler({ section: 'nope' }, undefined)).is_error).toBe(true)
    expect((await queryPariharaGraphCapability.handler({ activity_class: 'nope' }, undefined)).is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryPariharaGraphCapability.handler({ section: 'factor_census' }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id, no native identifiers in the description', () => {
    expect(queryPariharaGraphCapability.scope).toBe('global')
    expect(queryPariharaGraphCapability.required_inputs).not.toContain('chart_id')
    expect(queryPariharaGraphCapability.description).not.toContain('Bhubaneswar')
    expect(queryPariharaGraphCapability.description).not.toMatch(/\b\d{1,3}(?:,\d{3}){1,2}\b/)
  })
})
