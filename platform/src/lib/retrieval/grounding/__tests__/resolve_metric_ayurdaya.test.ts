/**
 * resolveMetric(fact_value_num) — Āyurdāya figures carry their reduction status (SS N-62 Q10).
 * A bare `fact_value_num` for an ayurdaya total is the exact "98.75 with no caveat" defect; the
 * resolved metric must carry figure_kind / reductions_applied / caveat, with the value unchanged.
 */
import { describe, it, expect } from 'vitest'
import { makeStubDbProxy } from '../db_proxy'
import { resolveMetric } from '../resolver'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const CAVEAT = 'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'

const fact = (over: Record<string, unknown>) => ({
  fact_id: 'f-ayu', chart_id: CHART, ayanamsha_id: 'lahiri_chitrapaksha', fact_category: 'ayurdaya',
  fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_num: 98.7521, fact_value_text: 'purnayu',
  fact_value_jsonb: { method: 'pindayu', harana_status: 'base_only_haranas_deferred_to_w3' },
  citation_human: 'Pindayu total (apply_haranas=False)', ...over,
})

async function resolve(row: Record<string, unknown>) {
  const db = makeStubDbProxy({ chart_facts: [row], bodha_msr_signals: [] })
  const out = await resolveMetric(db, CHART, 'fact_value_num', String(row['fact_id']))
  if (!out.ok) throw new Error(`unexpected error ${out.error.error_code}`)
  return out.metric
}

describe('resolveMetric — ayurdaya disclosure', () => {
  it('a confirmed total resolves with figure_kind=unreduced_base + caveat; value unchanged', async () => {
    const m = await resolve(fact({}))
    expect(m.value).toBe(98.7521)
    expect(m.figure_kind).toBe('unreduced_base')
    expect(m.reductions_applied).toBe(false)
    expect(m.caveat).toBe(CAVEAT)
  })

  it('a total whose status is not base-only resolves unverified / null', async () => {
    const m = await resolve(fact({ fact_value_jsonb: { method: 'pindayu', harana_status: 'something_else' } }))
    expect(m.value).toBe(98.7521)
    expect(m.figure_kind).toBe('reduction_status_unverified')
    expect(m.reductions_applied).toBeNull()
  })

  it('a lone contribution fact has no total to confirm against → unverified / null', async () => {
    const m = await resolve(fact({ fact_key: 'pindayu_contribution_years', fact_subject: 'SAT', fact_value_num: 19.8649, fact_value_jsonb: { graha: 'Saturn', method: 'pindayu' } }))
    expect(m.value).toBe(19.8649)
    expect(m.figure_kind).toBe('reduction_status_unverified')
    expect(m.reductions_applied).toBeNull()
  })

  it('non-ayurdaya facts resolve exactly as before (no new keys)', async () => {
    const m = await resolve(fact({ fact_category: 'graha_position', fact_key: 'longitude_deg', fact_value_num: 103.25, fact_value_jsonb: null }))
    expect(m).toEqual({ metric: 'fact_value_num', value: 103.25, source_id: 'f-ayu', source_table: 'chart_facts', citation: expect.any(String) })
    expect('figure_kind' in m).toBe(false)
    expect('caveat' in m).toBe(false)
  })
})
