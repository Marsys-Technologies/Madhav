/**
 * query_signals (msr_sql) — signal_headline_text internal-tag stripping
 * =======================================================================
 * bodha_signals_get / bodha_chart_digest_get were serving strings like
 * "SAT: saham position: sign = Aquarius [ga_sensitive]" — the bracketed suffix is an
 * internal L1-writer namespace tag stored on the row, echoed verbatim into the
 * user-facing headline field with no gloss or stripping.
 *
 * Fix: query_signals.ts strips /\[ga_\w+\]/-shaped internal tags from
 * signal_headline_text at serve time, response-envelope only — the underlying row
 * and its provenance are untouched.
 *
 * DB is mocked — no live connection required.
 */

import { describe, it, expect, vi } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'

const FAKE_ROW: Record<string, unknown> = {
  signal_id: 'sig-1', signal_type_id: 't1', signal_type_class: 'yoga',
  signal_tradition: 'parashari', signal_summary_text: 's',
  signal_headline_text: 'SAT: saham position: sign = Aquarius [ga_sensitive]',
  computed_salience: 0.9, top_k_salience_rank: 1, domains_affected_array: ['career'],
  constituent_facts_array: ['F-1'], source_subsystem: 'parashara', valence: 'positive',
  verification_pass_status: 'pass', citation_human: 'BPHS', lel_origin: false,
  signature_tier: 'major', configuration_jsonb: {},
}

const FAKE_ROW_STRUCTURAL: Record<string, unknown> = {
  ...FAKE_ROW,
  signal_id: 'sig-2',
  signal_headline_text: 'MOON: nakshatra lord activation [ga_structural]',
}

const FAKE_ROW_NO_TAG: Record<string, unknown> = {
  ...FAKE_ROW,
  signal_id: 'sig-3',
  signal_headline_text: 'MARS: dignity state = exalted',
}

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('COUNT(*)')) return { rows: [{ total: '3' }] }
    if (sql.includes('FROM bodha_msr_signals')) {
      return { rows: [FAKE_ROW, FAKE_ROW_STRUCTURAL, FAKE_ROW_NO_TAG] }
    }
    if (sql.includes('FROM chart_facts')) return { rows: [] }
    return { rows: [] }
  }),
}))

import { querySignalsCapability } from '../query_signals'

function servedSignals(result: Awaited<ReturnType<typeof querySignalsCapability.handler>>) {
  const content = result.content as Record<string, unknown>
  return content.signals as Record<string, unknown>[]
}

describe('query_signals — signal_headline_text internal-tag hygiene', () => {
  it('strips a [ga_sensitive] tag from the served headline', async () => {
    const result = await querySignalsCapability.handler({ chart_id: CHART_A }, {})
    expect(result.is_error).toBe(false)
    const signals = servedSignals(result)
    const row = signals.find(s => s['signal_id'] === 'sig-1')!
    expect(row['signal_headline_text']).toBe('SAT: saham position: sign = Aquarius')
    expect(String(row['signal_headline_text'])).not.toMatch(/\[ga_\w+\]/)
  })

  it('strips a [ga_structural] tag from the served headline', async () => {
    const result = await querySignalsCapability.handler({ chart_id: CHART_A }, {})
    const signals = servedSignals(result)
    const row = signals.find(s => s['signal_id'] === 'sig-2')!
    expect(row['signal_headline_text']).toBe('MOON: nakshatra lord activation')
  })

  it('leaves an untagged headline unchanged', async () => {
    const result = await querySignalsCapability.handler({ chart_id: CHART_A }, {})
    const signals = servedSignals(result)
    const row = signals.find(s => s['signal_id'] === 'sig-3')!
    expect(row['signal_headline_text']).toBe('MARS: dignity state = exalted')
  })

  it('strips the tag even when domain is passed (composite-ranking path)', async () => {
    const result = await querySignalsCapability.handler({ chart_id: CHART_A, domain: 'career' }, {})
    expect(result.is_error).toBe(false)
    const signals = servedSignals(result)
    for (const s of signals) {
      expect(String(s['signal_headline_text'])).not.toMatch(/\[ga_\w+\]/)
    }
  })
})
