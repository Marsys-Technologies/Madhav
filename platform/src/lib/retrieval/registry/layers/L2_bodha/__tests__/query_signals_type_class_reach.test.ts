/**
 * query_signals — signal_type_class serving REACH (Gate B / B2_sudarshana, D-1.5b)
 * ================================================================================
 * Regression test for the Gate B (CR-100) Sudarśana serving gap. The 45
 * `sudarshana_agreement` rows (9 grahas × 5 ayanamshas) are legitimately
 * low-salience tri-frame CORROBORATION signals (computed_salience ~0.31–0.48),
 * ranking ~8,097–9,797 of the ~9,877 signals per ayanamsha. A chart-wide salience
 * page never surfaces them; the reach path is a class-scoped filter applied in the
 * WHERE clause BEFORE the salience LIMIT / candidate-pool cap.
 *
 * These tests assert (DB mocked — no live connection):
 *   1. signal_type_class='sudarshana_agreement' is ACCEPTED (no enum rejection) and
 *      added to the SQL as `m.signal_type_class = $n` bound to that value.
 *   2. The class filter is emitted BEFORE the LIMIT clause — i.e. it constrains the
 *      row set the LIMIT applies to, rather than being a post-cap filter. This is
 *      what makes all 45 (9 per ayanamsha) rows reachable regardless of salience rank.
 *   3. When the mock returns the sudarshana rows, the Sun+Mercury CONTRADICTED
 *      specimen (10th-from-Lagna vs 12th-from-Moon) is served through the handler.
 */

import { describe, it, expect, vi } from 'vitest'

// Distinct chart_id per test so the handler's in-process response cache (keyed on args)
// never masks a fresh DB call between tests.
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const CHART_2 = '482012f1-710e-4a25-994a-93821f5871ab'
const CHART_3 = '482012f1-710e-4a25-994a-93821f5871ac'

// Nine lahiri sudarshana_agreement rows including the Sun + Mercury CONTRADICTED specimen.
const SUDARSHANA_ROWS = [
  { signal_id: 'sud-saturn', signal_type_class: 'sudarshana_agreement', computed_salience: 0.476,
    domains_affected_array: ['character', 'career'], signal_headline_text: 'Saturn: tri-frame partial (kendra 2-of-3)' },
  { signal_id: 'sud-mercury', signal_type_class: 'sudarshana_agreement', computed_salience: 0.397,
    domains_affected_array: ['character', 'career'], signal_headline_text: 'Mercury: tri-frame CONTRADICTED — H10(kendra) from Lagna vs H12 from Moon' },
  { signal_id: 'sud-sun', signal_type_class: 'sudarshana_agreement', computed_salience: 0.397,
    domains_affected_array: ['character', 'career'], signal_headline_text: 'Sun: tri-frame CONTRADICTED — H10(kendra) from Lagna vs H12 from Moon' },
]

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    // Family-size COUNT receipt.
    if (sql.includes('COUNT(*)')) return { rows: [{ total: '9' }] }
    // Main signal fetch — only return the sudarshana rows when the class filter is present.
    if (sql.includes('FROM bodha_msr_signals') && sql.includes('signal_type_class =')) {
      return { rows: SUDARSHANA_ROWS }
    }
    if (sql.includes('FROM bodha_msr_signals')) return { rows: [] }
    if (sql.includes('FROM chart_facts')) return { rows: [] }
    return { rows: [] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'
import { querySignalsCapability } from '../query_signals'

describe('query_signals — signal_type_class serving reach (Gate B B2_sudarshana)', () => {
  it('accepts signal_type_class=sudarshana_agreement and binds it as an SQL filter param', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART, signal_type_class: 'sudarshana_agreement' }, {},
    )
    expect(result.is_error).toBe(false)
    // First DB call is the family COUNT; find the main-fetch call that carries the class filter.
    const fetchCall = vi.mocked(mockQuery).mock.calls.find(
      ([sql]) => (sql as string).includes('FROM bodha_msr_signals') && (sql as string).includes('signal_type_class =') && !(sql as string).includes('COUNT(*)'),
    ) as [string, unknown[]] | undefined
    expect(fetchCall).toBeDefined()
    const [sql, params] = fetchCall!
    expect(sql).toContain('m.signal_type_class = $')
    expect(params).toContain('sudarshana_agreement')

    const content = result.content as Record<string, unknown>
    const filters = content.filters as Record<string, unknown>
    expect(filters.signal_type_class).toBe('sudarshana_agreement')
  })

  it('emits the class filter BEFORE the LIMIT clause (so the cap applies to the class-scoped set)', async () => {
    vi.mocked(mockQuery).mockClear()
    await querySignalsCapability.handler(
      { chart_id: CHART_2, signal_type_class: 'sudarshana_agreement' }, {},
    )
    const fetchCall = vi.mocked(mockQuery).mock.calls.find(
      ([sql]) => (sql as string).includes('FROM bodha_msr_signals') && (sql as string).includes('signal_type_class =') && !(sql as string).includes('COUNT(*)'),
    ) as [string, unknown[]] | undefined
    expect(fetchCall).toBeDefined()
    const sql = fetchCall![0]
    const classIdx = sql.indexOf('signal_type_class =')
    const limitIdx = sql.indexOf('LIMIT')
    expect(classIdx).toBeGreaterThan(-1)
    expect(limitIdx).toBeGreaterThan(-1)
    expect(classIdx).toBeLessThan(limitIdx)
  })

  it('serves the Sun + Mercury tri-frame CONTRADICTED specimen through the handler', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_3, signal_type_class: 'sudarshana_agreement' }, {},
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const signals = content.signals as Record<string, unknown>[]
    const headlines = signals.map(s => String(s.signal_headline_text))
    expect(headlines.some(h => h.startsWith('Sun: tri-frame CONTRADICTED'))).toBe(true)
    expect(headlines.some(h => h.startsWith('Mercury: tri-frame CONTRADICTED'))).toBe(true)
    // All served rows are the requested class — the reach path returns the class cleanly.
    expect(signals.every(s => s.signal_type_class === 'sudarshana_agreement')).toBe(true)
  })
})
