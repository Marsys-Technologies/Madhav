/**
 * wp18_cross_path_fidelity.integration.test.ts — WP-1.8 live-DB gate.
 *
 * Pins the four WP-1.8 serving-side fixes against BOTH canonical charts:
 *   R-43  dasha-lord natal dignity + shadbala re-derived from chart_facts (== chart_facts,
 *         never the NULL/wrong denormalized chart_dashas columns; §N.5 authority).
 *   R-46  operative-varga (amsha) term ACTUALLY moves a verdict where the varga contradicts D1
 *         (native marriage: Venus debilitated in D9 → mixed → contested).
 *   #3    multi-formula esoteric points (AVAYOGI Virgo-vs-Libra) served as BOTH rows + formula_id
 *         disclosure — never collapsed.
 *   #4    assess_* top-10 == get_signals(domain) top-10 (surfaces agree; no silent divergence).
 *
 * Run with: INTEGRATION=true npx vitest run src/lib/retrieval/registry/layers/wp18_cross_path_fidelity.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getDashasCapability } from './L1_ganita/get_dashas'
import { getSensitivePointsCapability } from './L1_ganita/get_sensitive_points'
import { judgmentQueryCapability } from './register_d9_judgment'
import { getCapability } from '../index'
import './register_d8_assess_domain'
import './L2_bodha/index'
import { query } from '@/lib/db/client'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH = [NATIVE, ABHINANDAN]
const AYA = 'lahiri_chitrapaksha'

const NAME2SUBJ: Record<string, string> = {
  Sun: 'SUN', Moon: 'MOON', Mars: 'MAR', Mercury: 'MER', Jupiter: 'JUP',
  Venus: 'VEN', Saturn: 'SAT', Rahu: 'RAH_MEAN', Ketu: 'KET_MEAN',
}

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('WP-1.8 cross-path fidelity — live DB', () => {
  // ── R-43: served dasha-lord dignity/shadbala == chart_facts, per row, both charts ──
  for (const chartId of BOTH) {
    it(`[${chartId}] R-43 — get_dashas served dignity + shadbala equal chart_facts on every row`, async () => {
      const dig = await query<{ fact_subject: string; v: string }>(
        `SELECT fact_subject, fact_value_text v FROM chart_facts
         WHERE chart_id=$1 AND ayanamsha_id=$2 AND fact_category='graha_dignity_per_varga'
           AND fact_key='dignity_state' AND fact_subject LIKE 'D1\\_%'`, [chartId, AYA])
      const sha = await query<{ fact_subject: string; v: number }>(
        `SELECT fact_subject, fact_value_num v FROM chart_facts
         WHERE chart_id=$1 AND ayanamsha_id=$2 AND fact_category='graha_shadbala_total' AND fact_key='rupa'`, [chartId, AYA])
      const digMap: Record<string, string> = {}
      for (const r of dig.rows) digMap[r.fact_subject.slice(3)] = r.v
      const shaMap: Record<string, number> = {}
      for (const r of sha.rows) shaMap[r.fact_subject] = Number(r.v)

      const res = await getDashasCapability.handler(
        { chart_id: chartId, ayanamsha_id: AYA, system: 'vimshottari', all_levels: true,
          window_start: '1980-01-01', window_end: '2100-01-01', limit: 50 }, undefined)
      expect(res.is_error).toBe(false)
      const content = res.content as Record<string, unknown>
      const rows = content['rows'] as Record<string, unknown>[]
      expect(rows.length).toBeGreaterThan(0)

      let checked = 0
      for (const row of rows) {
        const subj = NAME2SUBJ[row['lord_graha'] as string]
        if (!subj) continue
        checked++
        // Served dignity MUST equal chart_facts (authoritative), NOT the stale/NULL column.
        expect(String(row['lord_natal_dignity_d1']), `dignity for ${row['lord_graha']}`).toBe(String(digMap[subj] ?? null))
        expect(row['lord_natal_dignity_d1'], `dignity populated for ${row['lord_graha']}`).not.toBeNull()
        expect(Number(row['lord_natal_shadbala_total']), `shadbala for ${row['lord_graha']}`).toBe(Number(shaMap[subj] ?? NaN))
      }
      expect(checked).toBeGreaterThan(0)
      // Always-on provenance marker documents the re-derivation on the wire.
      expect(content['natal_condition_provenance']).toContain('chart_facts:re-derived@serve')
    }, 30000)
  }

  // ── R-46: varga term demonstrably moves a verdict where D9 contradicts D1 ──
  it(`[${NATIVE}] R-46 — native marriage: Venus debilitated in D9 moves verdict mixed → contested`, async () => {
    const res = await judgmentQueryCapability.handler({ chart_id: NATIVE, domain: 'marriage' }, undefined)
    expect(res.is_error).toBe(false)
    const verdict = (res.content as Record<string, unknown>)['verdict'] as Record<string, unknown>
    // D1-only leg is 'mixed'; the operative-varga term pulls it to 'contested'.
    expect(verdict['d1_only_grade']).toBe('mixed')
    expect(verdict['verdict_grade']).toBe('contested')
    expect(verdict['varga_moved_verdict']).toBe(true)
    expect(verdict['varga_term'] as number).toBeLessThan(0)
    const subs = verdict['varga_subscores'] as Record<string, Record<string, unknown>>
    expect(subs['bhavesha']['dignity_state']).toBe('debilitated') // Venus in D9
    // composite = d1 + varga
    expect(verdict['composite_score']).toBeCloseTo((verdict['d1_score'] as number) + (verdict['varga_term'] as number), 5)
  }, 30000)

  it(`[${NATIVE}] R-46 — character domain (operative varga D1) skips the varga term (no double-count)`, async () => {
    const res = await judgmentQueryCapability.handler({ chart_id: NATIVE, domain: 'character' }, undefined)
    expect(res.is_error).toBe(false)
    const verdict = (res.content as Record<string, unknown>)['verdict'] as Record<string, unknown>
    expect(verdict['operative_varga']).toBe('D1')
    expect(verdict['varga_term']).toBe(0)
    expect(verdict['composite_score']).toBe(verdict['d1_score'])
  }, 30000)

  // ── #3: multi-formula esoteric points served as BOTH rows + formula_id, never collapsed ──
  it(`[${NATIVE}] #3 — AVAYOGI serves BOTH formulas (BPHS Virgo + alt Libra) with formula_id disclosure`, async () => {
    const res = await getSensitivePointsCapability.handler(
      { chart_id: NATIVE, ayanamsha_id: AYA, categories: ['esoteric_point_avayogi'] }, undefined)
    expect(res.is_error).toBe(false)
    const content = res.content as Record<string, unknown>
    const rows = content['rows'] as Record<string, unknown>[]
    // Both formula rows present for the `sign` fact_key (Virgo + Libra) — not collapsed to one.
    const signRows = rows.filter(r => r['fact_key'] === 'sign')
    const signVals = signRows.map(r => r['fact_value_text']).sort()
    expect(signVals).toEqual(['Libra', 'Virgo'])
    const signFormulas = new Set(signRows.map(r => r['formula_id']))
    expect(signFormulas.has('bphs_93_20')).toBe(true)
    expect(signFormulas.has('alt_96_40')).toBe(true)
    // Disclosure block names the divergence.
    const mf = content['multi_formula'] as Array<Record<string, unknown>>
    const signGroup = mf.find(g => g['fact_key'] === 'sign')
    expect(signGroup).toBeTruthy()
    expect(signGroup!['formula_count']).toBe(2)
    expect(content['multi_formula_note']).toBeTruthy()
  }, 30000)

  // ── #4: assess_* top-10 agrees with get_signals(domain) top-10 ──
  const DOMAINS: Array<{ tool: string; domain: string }> = [
    { tool: 'marsys://tool/L-DOMAIN/assess_marriage', domain: 'relationship' },
    { tool: 'marsys://tool/L-DOMAIN/assess_career', domain: 'career' },
    { tool: 'marsys://tool/L-DOMAIN/assess_health', domain: 'health' },
    { tool: 'marsys://tool/L-DOMAIN/assess_wealth', domain: 'wealth' },
  ]
  for (const chartId of BOTH) {
    for (const { tool, domain } of DOMAINS) {
      it(`[${chartId}] #4 — ${tool.split('/').pop()} top-10 == get_signals(domain:${domain}) top-10`, async () => {
        const assessCap = getCapability(tool)!
        const signalsCap = getCapability('marsys://tool/L2/query_signals')!
        const a = await assessCap.handler({ chart_id: chartId }, undefined)
        const top10 = ((a.content as Record<string, unknown>)['verdict_skeleton'] as Record<string, unknown>)['top_10_composite'] as Array<Record<string, unknown>>
        const s = await signalsCap.handler({ chart_id: chartId, domain, top_k: 10 }, undefined)
        const sig10 = (s.content as Record<string, unknown>)['signals'] as Array<Record<string, unknown>>
        expect(top10.map(x => x['signal_id'])).toEqual(sig10.map(x => x['signal_id']))
        // Cross-surface disclosure is present + names the reproducing domain.
        const cs = ((a.content as Record<string, unknown>)['verdict_skeleton'] as Record<string, unknown>)['cross_surface'] as Record<string, unknown>
        expect(cs['agrees_with']).toBe('get_signals')
        expect((cs['reproducing_call'] as Record<string, Record<string, unknown>>)['args']['domain']).toBe(domain)
      }, 30000)
    }
  }
})
