/**
 * query_signals — Āyurdāya MSR signals carry the unreduced-base disclosure (SS N-62 Q10).
 *
 * 130 `ayurdaya:*` signals (source_l1_asset=ga_structural) carry bare totals ("98.75", "purnayu") in
 * signal_summary_text / configuration_jsonb. query_signals must tag each with its own figure_kind
 * and add the nested disclosure + closed-vocabulary flag, from configuration_jsonb.harana_status;
 * rows without a status are reduction_status_unverified / null. DB is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const BASE = 'base_only_haranas_deferred_to_w3'
const CAVEAT = 'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'

const sigRow = (id: string, suffix: string, cfg: Record<string, unknown>, summary: string): Record<string, unknown> => ({
  signal_id: id, signal_type_id: `ayurdaya:${suffix}`, signal_type_class: 'composite_state', signal_tradition: 'parashari',
  signal_summary_text: summary, signal_headline_text: `ayurdaya: ${suffix} [ga_structural]`,
  computed_salience: 0.46, top_k_salience_rank: 12495, domains_affected_array: ['character', 'career', 'family'],
  constituent_facts_array: ['F-1'], source_subsystem: 'structural', valence: 'neutral', verification_pass_status: 'pass',
  citation_human: 'x', lel_origin: false, signature_tier: 'minor', configuration_jsonb: cfg,
})

let ROWS: Record<string, unknown>[] = []

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('COUNT(*)')) return { rows: [{ total: String(ROWS.length) }] }
    if (sql.includes('FROM bodha_msr_signals')) return { rows: ROWS }
    return { rows: [] }
  }),
}))

import { querySignalsCapability } from '../query_signals'
import { isJudgmentFlagCode } from '../../../../envelope'

type Resp = { content: Record<string, unknown>; is_error: boolean; judgment_flags?: Array<Record<string, unknown>> }
let seq = 100
async function serve(rows: Record<string, unknown>[], extra: Record<string, unknown> = {}): Promise<Resp> {
  ROWS = rows
  // distinct top_k per call → distinct cache key (query_signals memoises)
  return await querySignalsCapability.handler({ chart_id: CHART, top_k: seq++, ...extra }, {}) as Resp
}

beforeEach(() => { ROWS = [] })

describe('query_signals — ayurdaya unreduced-base disclosure (SS N-62 Q10)', () => {
  const total = () => sigRow('s-total', 'total_years',
    { fact_key: 'total_years', method: 'pindayu', harana_status: BASE },
    'category=ayurdaya | key=total_years | value_text=purnayu | value_num=98.75 | harana_status=base_only_haranas_deferred_to_w3 | method=pindayu')
  const contrib = () => sigRow('s-contrib', 'pindayu_contribution_years',
    { fact_key: 'pindayu_contribution_years', method: 'pindayu', graha: 'Saturn' },
    'category=ayurdaya | key=pindayu_contribution_years | value_num=19.86 | graha=Saturn | method=pindayu')
  const applicable = () => sigRow('s-app', 'applicable_method',
    { fact_key: 'applicable_method', totals: { amsayu: 36.3, pindayu: 98.7, nisargayu: 99.1 } },
    "category=ayurdaya | key=applicable_method | totals={'amsayu': 36.3448, 'pindayu': 98.7521}")
  const other = () => ({ ...sigRow('s-yoga', 'x', {}, 'category=yoga'), signal_type_id: 'yoga:gajakesari' })

  it('tags the total with figure_kind=unreduced_base and serves the nested disclosure + flag', async () => {
    const r = await serve([total()])
    expect(r.is_error).toBe(false)
    const signals = r.content['signals'] as Array<Record<string, unknown>>
    expect(signals[0]).toMatchObject({ figure_kind: 'unreduced_base', reductions_applied: false })
    expect(r.content['ayurdaya_figure_disclosure']).toMatchObject({ figure_kind: 'unreduced_base', reductions_applied: false, caveat: CAVEAT })
    expect(r.judgment_flags).toEqual([{ code: 'ayurdaya_unreduced_base_figures', detail: CAVEAT, severity: 'info' }])
    expect(isJudgmentFlagCode(r.judgment_flags![0]!['code'])).toBe(true)
    // MCP-bridged tools (get_signals) read only `content` — the flag must live there too
    expect(r.content['judgment_flags']).toEqual(r.judgment_flags)
  })

  it('puts the disclosure before the signals in content (tail-clipping bundlers keep it)', async () => {
    const r = await serve([total()])
    const keys = Object.keys(r.content)
    expect(keys.indexOf('ayurdaya_figure_disclosure')).toBeGreaterThanOrEqual(0)
    expect(keys.indexOf('ayurdaya_figure_disclosure')).toBeLessThan(keys.indexOf('signals'))
  })

  it('leaves the stored headline/summary/number text exactly as stored', async () => {
    const t = total()
    const r = await serve([t])
    const s = (r.content['signals'] as Array<Record<string, unknown>>)[0]!
    expect(s['signal_summary_text']).toBe(t['signal_summary_text'])
    expect(s['configuration_jsonb']).toEqual(t['configuration_jsonb'])
    expect(String(s['signal_summary_text'])).toContain('value_num=98.75')
  })

  it('contribution-only page → reduction_status_unverified / null (no total to read a status from)', async () => {
    const r = await serve([contrib()])
    const s = (r.content['signals'] as Array<Record<string, unknown>>)[0]!
    expect(s).toMatchObject({ figure_kind: 'reduction_status_unverified', reductions_applied: null })
    expect((r.content['ayurdaya_figure_disclosure'] as Record<string, unknown>)['reductions_applied']).toBeNull()
    expect(r.judgment_flags![0]!['severity']).toBe('warning')
  })

  it('applicable_method signal (no status of its own) is unverified unless all three totals are on the page', async () => {
    const r = await serve([applicable()])
    expect((r.content['signals'] as Array<Record<string, unknown>>)[0]).toMatchObject({ figure_kind: 'reduction_status_unverified', reductions_applied: null })
  })

  it('a signal with no harana_status is unverified / null', async () => {
    const r = await serve([sigRow('s-nostatus', 'total_years', { fact_key: 'total_years', method: 'amsayu' }, 'category=ayurdaya | key=total_years')])
    expect((r.content['signals'] as Array<Record<string, unknown>>)[0]).toMatchObject({ figure_kind: 'reduction_status_unverified', reductions_applied: null })
  })

  it('annotates per row on a mixed page and leaves non-ayurdaya signals untouched', async () => {
    const r = await serve([total(), contrib(), applicable(), other()])
    const byId = Object.fromEntries((r.content['signals'] as Array<Record<string, unknown>>).map(s => [String(s['signal_id']), s]))
    expect(byId['s-total']).toMatchObject({ figure_kind: 'unreduced_base' })
    expect(byId['s-contrib']).toMatchObject({ figure_kind: 'unreduced_base' }) // pindayu total confirmed on page
    expect(byId['s-app']).toMatchObject({ figure_kind: 'reduction_status_unverified' })
    expect(byId['s-yoga']!['figure_kind']).toBeUndefined()
    expect((r.content['ayurdaya_figure_disclosure'] as Record<string, unknown>)['figure_kind']).toBe('mixed_reduction_status')
  })

  it('a page with no ayurdaya signal is unchanged: no disclosure, no flags', async () => {
    const r = await serve([other()])
    expect(r.content['ayurdaya_figure_disclosure']).toBeUndefined()
    expect(r.judgment_flags).toBeUndefined()
    expect((r.content['signals'] as Array<Record<string, unknown>>)[0]!['figure_kind']).toBeUndefined()
  })

  it('survives a narrow projection that drops signal_type_id/configuration_jsonb (disclosed from the full fetched row)', async () => {
    const r = await serve([total()], { projection: ['signal_id', 'computed_salience'] })
    const s = (r.content['signals'] as Array<Record<string, unknown>>)[0]!
    expect(Object.keys(s).sort()).toEqual(['computed_salience', 'figure_kind', 'reductions_applied', 'signal_id'])
    expect(s['figure_kind']).toBe('unreduced_base')
    expect(r.content['ayurdaya_figure_disclosure']).toBeDefined()
  })
})
