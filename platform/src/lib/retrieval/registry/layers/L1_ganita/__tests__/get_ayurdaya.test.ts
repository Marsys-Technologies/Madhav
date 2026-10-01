/**
 * get_ayurdaya.test.ts — F-E2/F-E3 (L1_W1_ANALYSIS_BATCH_E.md, NOW) unit tests. No live DB
 * required — `query` is mocked.
 *
 * F-E2: the SELECT omitted fact_value_jsonb, making maraka_grahas, per_graha contributions,
 * lagna_years, and harana_status unreachable at 0 hops despite the writer already storing
 * them. F-E3: harana_status is a real incompleteness disclosure that lived only inside the
 * (previously-omitted) jsonb — no consumer could see it without already knowing to look.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getAyurdayaCapability } from '../get_ayurdaya'
import { isJudgmentFlagCode } from '../../../../envelope'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getAyurdayaCapability (ganita_ayurdaya_get)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('selects fact_value_jsonb (F-E2) and promotes harana_status to a top-level field (F-E3)', async () => {
    const rows = [
      {
        fact_id: 'f1', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_num: 98.75, fact_value_text: 'purnayu',
        fact_value_jsonb: { per_graha: { SU: 10.5 }, lagna_years: 4.2, classification: 'purnayu', method: 'pindayu', harana_status: 'base_only_haranas_deferred_to_w3' },
      },
      {
        fact_id: 'f2', fact_subject: 'CHART', fact_key: 'maraka_grahas', fact_value_num: null, fact_value_text: 'SAT,MAR',
        fact_value_jsonb: { maraka_grahas: ['SAT', 'MAR'] },
      },
    ]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })

    const result = await getAyurdayaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)

    const selectSql = mockQuery.mock.calls[0][0] as string
    expect(selectSql).toMatch(/fact_value_jsonb/)

    const content = result.content as Record<string, unknown>
    expect(content['harana_status']).toBe('base_only_haranas_deferred_to_w3')
    const returnedRows = content['rows'] as Array<Record<string, unknown>>
    expect(returnedRows[1]['fact_value_jsonb']).toEqual({ maraka_grahas: ['SAT', 'MAR'] })
  })

  it('does not fabricate harana_status when no total_years row is on the page', async () => {
    const rows = [
      { fact_id: 'f2', fact_subject: 'CHART', fact_key: 'maraka_grahas', fact_value_num: null, fact_value_text: 'SAT,MAR', fact_value_jsonb: { maraka_grahas: ['SAT', 'MAR'] } },
    ]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })

    const result = await getAyurdayaCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['harana_status']).toBeUndefined()
  })

  it('reports harana_status as an array if the served page ever carries divergent values (honest, not silently collapsed)', async () => {
    const rows = [
      { fact_id: 'f1', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_jsonb: { harana_status: 'status_a' } },
      { fact_id: 'f3', fact_subject: 'AMSAYU', fact_key: 'total_years', fact_value_jsonb: { harana_status: 'status_b' } },
    ]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })

    const result = await getAyurdayaCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['harana_status']).toEqual(['status_a', 'status_b'])
  })
})

// SS N-62 Q10 — display-side: served totals must say they are UNREDUCED BASE figures.
describe('getAyurdayaCapability — unreduced-base disclosure (SS N-62 Q10)', () => {
  const CAVEAT = 'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'
  const baseRows = (): Array<Record<string, unknown>> => [
    {
      fact_id: 'f1', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_num: 98.7521, fact_value_text: 'purnayu',
      fact_value_jsonb: { method: 'pindayu', harana_status: 'base_only_haranas_deferred_to_w3' },
    },
    { fact_id: 'f2', fact_subject: 'SAT', fact_key: 'pindayu_contribution_years', fact_value_num: 19.8649, fact_value_text: 'pindayu', fact_value_jsonb: { graha: 'Saturn', method: 'pindayu' } },
    { fact_id: 'f3', fact_subject: 'CHART', fact_key: 'applicable_method', fact_value_num: null, fact_value_text: 'pindayu', fact_value_jsonb: { totals: { pindayu: 98.7521 } } },
    { fact_id: 'f4', fact_subject: 'CHART', fact_key: 'maraka_grahas', fact_value_num: null, fact_value_text: 'Mars,Saturn,Venus', fact_value_jsonb: { maraka_grahas: ['Mars', 'Saturn', 'Venus'] } },
  ]

  async function serve(rows: Array<Record<string, unknown>>) {
    mockQuery.mockReset()
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: String(rows.length) }] })
    return await getAyurdayaCapability.handler({ chart_id: CHART_ID }, undefined) as {
      content: Record<string, unknown>; is_error: boolean; judgment_flags?: Array<Record<string, unknown>>
    }
  }

  it('serves figure_kind=unreduced_base, reductions_applied=false and the plain-language caveat', async () => {
    const result = await serve(baseRows())
    expect(result.is_error).toBe(false)
    expect(result.content['figure_kind']).toBe('unreduced_base')
    expect(result.content['reductions_applied']).toBe(false)
    expect(result.content['caveat']).toBe(CAVEAT)
    expect(String(result.content['caveat'])).toMatch(/not a prediction of lifespan/)
  })

  it('emits a structured ayurdaya_unreduced_base_figures judgment flag (closed vocabulary)', async () => {
    const result = await serve(baseRows())
    expect(result.judgment_flags).toEqual([{ code: 'ayurdaya_unreduced_base_figures', detail: CAVEAT, severity: 'info' }])
    expect(isJudgmentFlagCode('ayurdaya_unreduced_base_figures')).toBe(true)
  })

  it('annotates every year-bearing row and leaves non-year rows untouched', async () => {
    const result = await serve(baseRows())
    const rows = result.content['rows'] as Array<Record<string, unknown>>
    const byKey = Object.fromEntries(rows.map(r => [`${r['fact_subject']}/${r['fact_key']}`, r]))
    for (const k of ['PINDAYU/total_years', 'SAT/pindayu_contribution_years', 'CHART/applicable_method']) {
      expect(byKey[k]['figure_kind']).toBe('unreduced_base')
      expect(byKey[k]['reductions_applied']).toBe(false)
    }
    expect(byKey['CHART/maraka_grahas']['figure_kind']).toBeUndefined()
    expect(byKey['CHART/maraka_grahas']['reductions_applied']).toBeUndefined()
  })

  it('leaves every stored number/text/jsonb value exactly as stored (display-side only)', async () => {
    const input = baseRows()
    const snapshot = JSON.parse(JSON.stringify(input)) as Array<Record<string, unknown>>
    const result = await serve(input)
    const rows = result.content['rows'] as Array<Record<string, unknown>>
    expect(rows).toHaveLength(snapshot.length)
    rows.forEach((served, i) => {
      for (const field of ['fact_id', 'fact_subject', 'fact_key', 'fact_value_num', 'fact_value_text', 'fact_value_jsonb']) {
        expect(served[field]).toEqual(snapshot[i][field])
      }
    })
    expect(rows[0]['fact_value_num']).toBe(98.7521)
    // the rows handed in by the DB layer are not mutated either
    expect(input).toEqual(snapshot)
    // the pre-existing disclosure surface is unchanged
    expect(result.content['harana_status']).toBe('base_only_haranas_deferred_to_w3')
    expect(String(result.content['disclaimer'])).toMatch(/NOT a death prediction/)
  })

  it('does not fabricate the disclosure for a page with no year-bearing row (honest absence)', async () => {
    const result = await serve([baseRows()[3]])
    expect(result.content['figure_kind']).toBeUndefined()
    expect(result.content['reductions_applied']).toBeUndefined()
    expect(result.content['caveat']).toBeUndefined()
    expect(result.judgment_flags).toBeUndefined()
  })

  it('does not label a total unreduced when its own harana_status cannot confirm it (honest null)', async () => {
    const result = await serve([
      { fact_id: 'f9', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_num: 80.1, fact_value_text: 'madhyayu', fact_value_jsonb: { method: 'pindayu', harana_status: 'haranas_applied_v2' } },
    ])
    expect(result.content['figure_kind']).toBe('reduction_status_unverified')
    expect(result.content['reductions_applied']).toBeNull()
    expect(String(result.content['caveat'])).toMatch(/could not be confirmed/)
    expect(result.judgment_flags?.[0]?.['severity']).toBe('warning')
  })

  it('treats a total_years row with no harana_status at all as unverified, not unreduced', async () => {
    const result = await serve([
      { fact_id: 'f9', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_num: 80.1, fact_value_text: 'madhyayu', fact_value_jsonb: null },
    ])
    expect(result.content['figure_kind']).toBe('reduction_status_unverified')
    expect(result.content['reductions_applied']).toBeNull()
  })
})
