/**
 * ayurdaya_unreduced_base.test.ts — direct unit tests for the shared Āyurdāya disclosure helper
 * (SS N-62 Q10, display-side). Pure functions; no DB.
 */
import { describe, it, expect, vi } from 'vitest'
import {
  AYURDAYA_FIGURE_KIND_MIXED,
  AYURDAYA_MIXED_CAVEAT,
  AYURDAYA_STATUS_UNVERIFIED_CAVEAT,
  AYURDAYA_UNREDUCED_BASE_CAVEAT,
  annotateAyurdayaYearRows,
  deriveAyurdayaFigureDisclosure,
  isAyurdayaYearsRow,
  postProcessAyurdayaDisclosure,
  withAyurdayaFigureDisclosure,
  WALK_MAX_DEPTH,
  WALK_MAX_KEYS_PER_OBJECT,
  WALK_MAX_NODES,
  __resetAyurdayaWarningsForTests,
} from '../ayurdaya_unreduced_base'

const BASE = 'base_only_haranas_deferred_to_w3'
type Row = Record<string, unknown>

const total = (subject: string, status: string | null | undefined, extra: Row = {}): Row => ({
  fact_id: `t-${subject}`, fact_category: 'ayurdaya', fact_subject: subject, fact_key: 'total_years',
  fact_value_num: 98.7521, fact_value_text: 'purnayu',
  fact_value_jsonb: status === undefined ? { method: subject.toLowerCase() } : status === null ? null : { method: subject.toLowerCase(), harana_status: status },
  ...extra,
})
const contrib = (method: string, graha = 'SAT', extra: Row = {}): Row => ({
  fact_id: `c-${method}-${graha}`, fact_category: 'ayurdaya', fact_subject: graha, fact_key: `${method}_contribution_years`,
  fact_value_num: 19.8649, fact_value_jsonb: { graha, method }, ...extra,
})
const applicable = (totals: Record<string, number> = { amsayu: 36.3, pindayu: 98.7, nisargayu: 99.1 }, extra: Row = {}): Row => ({
  fact_id: 'a1', fact_category: 'ayurdaya', fact_subject: 'CHART', fact_key: 'applicable_method',
  fact_value_text: 'pindayu', fact_value_jsonb: { totals, applicable_method: 'pindayu' }, ...extra,
})

describe('deriveAyurdayaFigureDisclosure — empty / non-ayurdaya', () => {
  it('returns null for an empty page', () => {
    expect(deriveAyurdayaFigureDisclosure([])).toBeNull()
  })
  it('returns null for rows with no year figure (maraka only) and for other categories', () => {
    expect(deriveAyurdayaFigureDisclosure([
      { fact_category: 'ayurdaya', fact_subject: 'CHART', fact_key: 'maraka_grahas', fact_value_jsonb: {} },
      { fact_category: 'dasha_total', fact_subject: 'VIMSHOTTARI', fact_key: 'total_years', fact_value_num: 120 },
    ])).toBeNull()
  })
  it('only accepts a category-less fact row when assumeAyurdayaCategory is set', () => {
    const r = { fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_jsonb: { method: 'pindayu', harana_status: BASE } }
    expect(isAyurdayaYearsRow(r)).toBe(false)
    expect(isAyurdayaYearsRow(r, { assumeAyurdayaCategory: true })).toBe(true)
  })
})

describe('deriveAyurdayaFigureDisclosure — exact caveat wording', () => {
  it('serves the exact unreduced-base caveat when every row is confirmed', () => {
    const d = deriveAyurdayaFigureDisclosure([total('PINDAYU', BASE)])!
    expect(d.figure_kind).toBe('unreduced_base')
    expect(d.reductions_applied).toBe(false)
    expect(d.caveat).toBe('Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.')
    expect(d.caveat).toBe(AYURDAYA_UNREDUCED_BASE_CAVEAT)
    expect(d.judgment_flag).toEqual({ code: 'ayurdaya_unreduced_base_figures', detail: d.caveat, severity: 'info' })
    expect(d.figure_counts).toEqual({ unreduced_base: 1, reduction_status_unverified: 0 })
  })

  it('serves the exact unverified caveat (null reductions_applied, warning severity) when a total has an unknown status', () => {
    const d = deriveAyurdayaFigureDisclosure([total('PINDAYU', 'haranas_applied_v2')])!
    expect(d.figure_kind).toBe('reduction_status_unverified')
    expect(d.reductions_applied).toBeNull()
    expect(d.caveat).toBe('Classical pinda/amsa/nisarga figure whose harana (reduction) status could not be confirmed from the served row; do not read it as a reduced or final figure; not a prediction of lifespan.')
    expect(d.caveat).toBe(AYURDAYA_STATUS_UNVERIFIED_CAVEAT)
    expect(d.judgment_flag).toEqual({ code: 'ayurdaya_unreduced_base_figures', detail: d.caveat, severity: 'warning' })
    expect(d.figure_counts).toEqual({ unreduced_base: 0, reduction_status_unverified: 1 })
  })

  it('serves the mixed caveat when confirmed and unconfirmed rows coexist', () => {
    const d = deriveAyurdayaFigureDisclosure([total('PINDAYU', BASE), total('AMSAYU', 'other')])!
    expect(d.figure_kind).toBe(AYURDAYA_FIGURE_KIND_MIXED)
    expect(d.reductions_applied).toBeNull()
    expect(d.caveat).toBe(AYURDAYA_MIXED_CAVEAT)
    expect(d.judgment_flag.severity).toBe('warning')
  })
})

describe('deriveAyurdayaFigureDisclosure — missing status is never "unreduced"', () => {
  it('total_years with jsonb present but no harana_status → unverified', () => {
    const d = deriveAyurdayaFigureDisclosure([total('PINDAYU', undefined)])!
    expect(d.figure_kind).toBe('reduction_status_unverified')
    expect(d.reductions_applied).toBeNull()
  })
  it('total_years with null jsonb → unverified', () => {
    expect(deriveAyurdayaFigureDisclosure([total('PINDAYU', null)])!.reductions_applied).toBeNull()
  })
  it('a non-string harana_status is not confirmation', () => {
    const d = deriveAyurdayaFigureDisclosure([{ ...total('PINDAYU', BASE), fact_value_jsonb: { method: 'pindayu', harana_status: true } }])!
    expect(d.reductions_applied).toBeNull()
  })
})

describe('deriveAyurdayaFigureDisclosure — pages with no total_years row (no hardcoded false)', () => {
  it('contribution-only page → unverified / null', () => {
    const rows = [contrib('pindayu'), contrib('amsayu', 'SUN')]
    const d = deriveAyurdayaFigureDisclosure(rows)!
    expect(d.figure_kind).toBe('reduction_status_unverified')
    expect(d.reductions_applied).toBeNull()
    expect(d.figure_counts).toEqual({ unreduced_base: 0, reduction_status_unverified: 2 })
    for (const r of rows) expect(d.row_figures.get(r)).toEqual({ figure_kind: 'reduction_status_unverified', reductions_applied: null })
  })
  it('applicable_method-only page → unverified / null', () => {
    const d = deriveAyurdayaFigureDisclosure([applicable()])!
    expect(d.figure_kind).toBe('reduction_status_unverified')
    expect(d.reductions_applied).toBeNull()
  })
})

describe('deriveAyurdayaFigureDisclosure — per-row status (mixed pages)', () => {
  it('annotates each total from its OWN status', () => {
    const p = total('PINDAYU', BASE)
    const a = total('AMSAYU', 'weird_status')
    const n = total('NISARGAYU', BASE)
    const d = deriveAyurdayaFigureDisclosure([p, a, n])!
    expect(d.row_figures.get(p)).toEqual({ figure_kind: 'unreduced_base', reductions_applied: false })
    expect(d.row_figures.get(a)).toEqual({ figure_kind: 'reduction_status_unverified', reductions_applied: null })
    expect(d.row_figures.get(n)).toEqual({ figure_kind: 'unreduced_base', reductions_applied: false })
    expect(d.figure_counts).toEqual({ unreduced_base: 2, reduction_status_unverified: 1 })
  })

  it('a contribution row follows its own method total (not the whole page)', () => {
    const pT = total('PINDAYU', BASE)
    const aT = total('AMSAYU', 'weird_status')
    const cp = contrib('pindayu')
    const ca = contrib('amsayu')
    const cn = contrib('nisargayu') // no nisargayu total on the page → cannot confirm
    const d = deriveAyurdayaFigureDisclosure([pT, aT, cp, ca, cn])!
    expect(d.row_figures.get(cp)!.figure_kind).toBe('unreduced_base')
    expect(d.row_figures.get(ca)!.figure_kind).toBe('reduction_status_unverified')
    expect(d.row_figures.get(cn)!.figure_kind).toBe('reduction_status_unverified')
  })

  it('contribution rows are matched to totals within the same ayanamsha only', () => {
    const tLahiri = total('PINDAYU', BASE, { ayanamsha_id: 'lahiri_chitrapaksha' })
    const tRaman = total('PINDAYU', 'weird_status', { ayanamsha_id: 'raman' })
    const cLahiri = contrib('pindayu', 'SAT', { ayanamsha_id: 'lahiri_chitrapaksha' })
    const cRaman = contrib('pindayu', 'SAT', { ayanamsha_id: 'raman' })
    const d = deriveAyurdayaFigureDisclosure([tLahiri, tRaman, cLahiri, cRaman])!
    expect(d.row_figures.get(cLahiri)!.figure_kind).toBe('unreduced_base')
    expect(d.row_figures.get(cRaman)!.figure_kind).toBe('reduction_status_unverified')
  })

  it('applicable_method is confirmed only if EVERY method it names has a confirmed total', () => {
    const app = applicable()
    const allThree = deriveAyurdayaFigureDisclosure([app, total('PINDAYU', BASE), total('AMSAYU', BASE), total('NISARGAYU', BASE)])!
    expect(allThree.row_figures.get(app)!.figure_kind).toBe('unreduced_base')
    const missingOne = deriveAyurdayaFigureDisclosure([app, total('PINDAYU', BASE), total('AMSAYU', BASE)])!
    expect(missingOne.row_figures.get(app)!.figure_kind).toBe('reduction_status_unverified')
    const oneUnknown = deriveAyurdayaFigureDisclosure([app, total('PINDAYU', BASE), total('AMSAYU', BASE), total('NISARGAYU', 'x')])!
    expect(oneUnknown.row_figures.get(app)!.figure_kind).toBe('reduction_status_unverified')
  })

  it('page kind is unverified/mixed as soon as ONE total is unconfirmed (some, not every)', () => {
    // one unconfirmed among many confirmed → NOT page-level "unreduced_base"
    const rows = [total('PINDAYU', BASE), total('NISARGAYU', BASE), total('AMSAYU', null)]
    const d = deriveAyurdayaFigureDisclosure(rows)!
    expect(d.figure_kind).not.toBe('unreduced_base')
    expect(d.reductions_applied).toBeNull()
    // one confirmed among many unconfirmed → still not page-level "unverified" only: it is mixed
    const d2 = deriveAyurdayaFigureDisclosure([total('PINDAYU', BASE), total('NISARGAYU', 'x'), total('AMSAYU', 'y')])!
    expect(d2.figure_kind).toBe(AYURDAYA_FIGURE_KIND_MIXED)
  })
})

describe('deriveAyurdayaFigureDisclosure — jsonb as object or JSON string', () => {
  it('accepts jsonb delivered as a JSON string', () => {
    const t = total('PINDAYU', BASE, { fact_value_jsonb: JSON.stringify({ method: 'pindayu', harana_status: BASE }) })
    const d = deriveAyurdayaFigureDisclosure([t])!
    expect(d.row_figures.get(t)!.figure_kind).toBe('unreduced_base')
  })
  it('an unparseable string is treated as no status (unverified), not as a crash', () => {
    const t = total('PINDAYU', BASE, { fact_value_jsonb: '{not json' })
    expect(deriveAyurdayaFigureDisclosure([t])!.reductions_applied).toBeNull()
  })
  it('string and object jsonb produce identical results', () => {
    const obj = { method: 'amsayu', harana_status: BASE }
    const a = deriveAyurdayaFigureDisclosure([total('AMSAYU', BASE, { fact_value_jsonb: obj })])!
    const b = deriveAyurdayaFigureDisclosure([total('AMSAYU', BASE, { fact_value_jsonb: JSON.stringify(obj) })])!
    expect([b.figure_kind, b.reductions_applied, b.figure_counts]).toEqual([a.figure_kind, a.reductions_applied, a.figure_counts])
  })
})

describe('deriveAyurdayaFigureDisclosure — L2 signal-shaped rows', () => {
  const sig = (suffix: string, cfg: Row | string | null, extra: Row = {}): Row => ({
    signal_id: `s-${suffix}`, signal_type_id: `ayurdaya:${suffix}`, signal_headline_text: `ayurdaya: ${suffix}`,
    signal_summary_text: `category=ayurdaya | key=${suffix}`, configuration_jsonb: cfg, ...extra,
  })
  it('reads harana_status from configuration_jsonb (signal_type_id detector)', () => {
    const t = sig('total_years', { fact_key: 'total_years', method: 'pindayu', harana_status: BASE })
    const c = sig('pindayu_contribution_years', { fact_key: 'pindayu_contribution_years', method: 'pindayu' })
    const app = sig('applicable_method', { fact_key: 'applicable_method', totals: { amsayu: 1, pindayu: 2, nisargayu: 3 } })
    const d = deriveAyurdayaFigureDisclosure([t, c, app])!
    expect(d.row_figures.get(t)!.figure_kind).toBe('unreduced_base')
    expect(d.row_figures.get(c)!.figure_kind).toBe('unreduced_base')
    // applicable_method signal has no status of its own and only the pindayu total is on the page
    expect(d.row_figures.get(app)!.figure_kind).toBe('reduction_status_unverified')
  })
  it('a signal row without a status is unverified / null', () => {
    const t = sig('total_years', { fact_key: 'total_years', method: 'amsayu' })
    expect(deriveAyurdayaFigureDisclosure([t])!.reductions_applied).toBeNull()
  })
  it('falls back to the summary text when configuration_jsonb / signal_type_id were projected away', () => {
    const t = { signal_id: 's1', signal_summary_text: 'category=ayurdaya | key=total_years | value_num=98.75 | harana_status=base_only_haranas_deferred_to_w3 | method=pindayu' }
    const d = deriveAyurdayaFigureDisclosure([t])!
    expect(d.row_figures.get(t)!.figure_kind).toBe('unreduced_base')
    const noStatus = { signal_id: 's2', summary: 'category=ayurdaya | key=total_years | value_num=98.75 | method=pindayu' }
    expect(deriveAyurdayaFigureDisclosure([noStatus])!.reductions_applied).toBeNull()
  })
  it('ignores non-year ayurdaya signals (maraka) and other signals', () => {
    expect(deriveAyurdayaFigureDisclosure([
      sig('maraka_grahas', { fact_key: 'maraka_grahas' }),
      { signal_id: 'x', signal_type_id: 'yoga:gajakesari', signal_summary_text: 'category=yoga' },
    ])).toBeNull()
  })
})

describe('annotateAyurdayaYearRows', () => {
  it('adds per-row keys without mutating inputs or stored values', () => {
    const t = total('PINDAYU', BASE)
    const m = { fact_category: 'ayurdaya', fact_subject: 'CHART', fact_key: 'maraka_grahas', fact_value_text: 'Mars' }
    const snapshot = JSON.parse(JSON.stringify([t, m]))
    const d = deriveAyurdayaFigureDisclosure([t, m])
    const out = annotateAyurdayaYearRows([t, m], d)
    expect(out[0]).toMatchObject({ figure_kind: 'unreduced_base', reductions_applied: false, fact_value_num: 98.7521 })
    expect(out[1]).toBe(m)
    expect([t, m]).toEqual(snapshot)
  })
  it('returns a plain copy when there is no disclosure', () => {
    const rows = [{ a: 1 }]
    const out = annotateAyurdayaYearRows(rows, null)
    expect(out).toEqual(rows)
    expect(out).not.toBe(rows)
  })
})

describe('withAyurdayaFigureDisclosure (chart_facts_query adapter)', () => {
  it('puts the disclosure and flag FIRST in content and keeps prior flags', () => {
    const prior = { code: 'time_sensitive_low_confidence' }
    const res = withAyurdayaFigureDisclosure(
      { content: { chart_id: 'c', rows: [1], judgment_flags: [prior] }, is_error: false },
      [total('PINDAYU', BASE)],
    )
    const keys = Object.keys(res.content as Row)
    expect(keys.slice(0, 2)).toEqual(['ayurdaya_figure_disclosure', 'judgment_flags'])
    const flags = (res.content as Row)['judgment_flags'] as Array<Row>
    expect(flags[0]).toBe(prior)
    expect(flags[1]?.['code']).toBe('ayurdaya_unreduced_base_figures')
  })
  it('returns the same reference for a non-ayurdaya page', () => {
    const res = { content: { chart_id: 'c' }, is_error: false }
    expect(withAyurdayaFigureDisclosure(res, [{ fact_category: 'graha_position', fact_key: 'sign' }])).toBe(res)
  })
})

describe('postProcessAyurdayaDisclosure (registry safety net)', () => {
  type Out = { content: Row; judgment_flags: Array<Row> }
  const run = (result: unknown): Out => postProcessAyurdayaDisclosure(result) as unknown as Out

  it('annotates COPIES of nested rows, prepends the disclosure and adds the flag at content AND result level', () => {
    const t = total('PINDAYU', BASE)
    const result = { content: { chart_id: 'c', categories: ['ayurdaya'], rows: [t] }, is_error: false }
    const out = run(result)
    expect(Object.keys(out.content)[0]).toBe('ayurdaya_figure_disclosure')
    expect((out.content['ayurdaya_figure_disclosure'] as Row)['figure_kind']).toBe('unreduced_base')
    const servedRow = (out.content['rows'] as Row[])[0]!
    expect(servedRow).toMatchObject({ figure_kind: 'unreduced_base', reductions_applied: false, fact_value_num: 98.7521 })
    // the handler's own object is untouched (it may be cached/shared)
    expect(t['figure_kind']).toBeUndefined()
    expect(servedRow).not.toBe(t)
    // closed-vocabulary flag at BOTH places MCP-bridged tools / HTTP callers read
    expect(out.judgment_flags.map(f => f['code'])).toEqual(['ayurdaya_unreduced_base_figures'])
    expect((out.content['judgment_flags'] as Row[]).map(f => f['code'])).toEqual(['ayurdaya_unreduced_base_figures'])
  })

  it('appends to (never replaces) pre-existing content and result flags', () => {
    const t = total('PINDAYU', BASE)
    const prior = { code: 'zero_rows_returned' }
    const out = run({ content: { rows: [t], judgment_flags: [prior] }, is_error: false, judgment_flags: [prior] })
    expect((out.content['judgment_flags'] as Row[]).map(f => f['code'])).toEqual(['zero_rows_returned', 'ayurdaya_unreduced_base_figures'])
    expect(out.judgment_flags.map(f => f['code'])).toEqual(['zero_rows_returned', 'ayurdaya_unreduced_base_figures'])
  })

  it('leaves a non-array content.judgment_flags untouched', () => {
    const out = run({ content: { rows: [total('PINDAYU', BASE)], judgment_flags: 'legacy-string' }, is_error: false })
    expect(out.content['judgment_flags']).toBe('legacy-string')
    expect(out.judgment_flags).toHaveLength(1)
  })

  it('shares every untouched subtree by reference (copy-on-write only along the changed path)', () => {
    const other = { big: [1, 2, 3] }
    const result = { content: { other, rows: [total('PINDAYU', BASE)] }, is_error: false }
    expect((run(result).content['other'])).toBe(other)
  })

  it('returns non-ayurdaya, error, already-disclosed and primitive results by reference', () => {
    const plain = { content: { rows: [{ fact_category: 'graha_position', fact_key: 'sign' }] }, is_error: false }
    expect(postProcessAyurdayaDisclosure(plain)).toBe(plain)
    const err = { content: { rows: [total('PINDAYU', BASE)] }, is_error: true }
    expect(postProcessAyurdayaDisclosure(err)).toBe(err)
    const done = { content: { ayurdaya_figure_disclosure: {}, rows: [total('PINDAYU', BASE)] }, is_error: false }
    expect(postProcessAyurdayaDisclosure(done)).toBe(done)
    const flat = { content: { figure_kind: 'unreduced_base', rows: [total('PINDAYU', BASE)] }, is_error: false }
    expect(postProcessAyurdayaDisclosure(flat)).toBe(flat)
    expect(postProcessAyurdayaDisclosure('text')).toBe('text')
    expect(postProcessAyurdayaDisclosure(null)).toBeNull()
  })

  describe('frozen / cached rows (no silent loss)', () => {
    const deepFreeze = <T>(o: T): T => {
      if (o && typeof o === 'object') { Object.values(o as object).forEach(deepFreeze); Object.freeze(o) }
      return o
    }
    it('a deep-frozen result still gets the per-row tags (on copies) AND the page-level disclosure + flags', () => {
      const t = total('PINDAYU', BASE)
      const result = deepFreeze({ content: { rows: [t] }, is_error: false })
      let out: Out | undefined
      expect(() => { out = run(result) }).not.toThrow()
      expect(out!.content['ayurdaya_figure_disclosure']).toMatchObject({ figure_kind: 'unreduced_base', reductions_applied: false })
      expect((out!.content['rows'] as Row[])[0]).toMatchObject({ figure_kind: 'unreduced_base' })
      expect(Object.isFrozen(t)).toBe(true)
      expect(t['figure_kind']).toBeUndefined()
      expect(out!.judgment_flags).toHaveLength(1)
      expect(out!.content['judgment_flags']).toHaveLength(1)
    })

    it('if the row rewrite itself fails, the page-level disclosure + flags STILL attach and a warning is logged', () => {
      __resetAyurdayaWarningsForTests()
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      let reads = 0
      const bomb: Row = {}
      Object.defineProperty(bomb, 'x', { enumerable: true, get() { if (++reads > 1) throw new Error('boom'); return 5 } })
      const t = total('PINDAYU', BASE)
      const out = run({ content: { rows: [t], bomb }, is_error: false })
      expect(out.content['ayurdaya_figure_disclosure']).toMatchObject({ figure_kind: 'unreduced_base' })
      expect(out.judgment_flags.map(f => f['code'])).toEqual(['ayurdaya_unreduced_base_figures'])
      expect((out.content['judgment_flags'] as Row[])).toHaveLength(1)
      expect(warn).toHaveBeenCalledTimes(1)
      expect(String(warn.mock.calls[0]![0])).toMatch(/row annotation failed/)
      warn.mockRestore()
    })

    it('warns only once per distinct loss message', () => {
      __resetAyurdayaWarningsForTests()
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const mk = () => {
        let reads = 0
        const bomb: Row = {}
        Object.defineProperty(bomb, 'x', { enumerable: true, get() { if (++reads > 1) throw new Error('boom'); return 5 } })
        return { content: { rows: [total('PINDAYU', BASE)], bomb }, is_error: false }
      }
      run(mk()); run(mk())
      expect(warn).toHaveBeenCalledTimes(1)
      warn.mockRestore()
    })
  })

  describe('composed tools (an inner tool already tagged the rows)', () => {
    it('never recomputes or overwrites an existing figure_kind, and counts it from its existing value', () => {
      // outer returns a SUBSET of the inner page: only a contribution row the inner page confirmed
      // against its total. Recomputed on the subset alone it would read "unverified" — it must not.
      const inner = run({ content: { rows: [total('PINDAYU', BASE), contrib('pindayu')] }, is_error: false })
      const taggedContribution = (inner.content['rows'] as Row[])[1]!
      expect(taggedContribution['figure_kind']).toBe('unreduced_base')
      const outer = run({ content: { composed: { rows: [taggedContribution] } }, is_error: false })
      // already tagged + no disclosure on the outer content → processed, but the tag is preserved
      const served = ((outer.content['composed'] as Row)['rows'] as Row[])[0]!
      expect(served['figure_kind']).toBe('unreduced_base')
      expect(served['reductions_applied']).toBe(false)
      expect((outer.content['ayurdaya_figure_disclosure'] as Row)['figure_kind']).toBe('unreduced_base')
      expect((outer.content['ayurdaya_figure_disclosure'] as Row)['figure_counts']).toEqual({ unreduced_base: 1, reduction_status_unverified: 0 })
    })

    it('keeps an inner "unverified" tag even if an outer page would now confirm it', () => {
      const tagged = { ...contrib('pindayu'), figure_kind: 'reduction_status_unverified', reductions_applied: null }
      const out = run({ content: { rows: [tagged, total('PINDAYU', BASE)] }, is_error: false })
      const rows = out.content['rows'] as Row[]
      expect(rows[0]!['figure_kind']).toBe('reduction_status_unverified')
      expect(rows[0]!['reductions_applied']).toBeNull()
      expect(rows[1]!['figure_kind']).toBe('unreduced_base')
      expect((out.content['ayurdaya_figure_disclosure'] as Row)['figure_kind']).toBe(AYURDAYA_FIGURE_KIND_MIXED)
    })
  })

  describe('walk bounds', () => {
    const nest = (row: Row, levels: number): Row => {
      let o: Row = { row }
      for (let i = 1; i < levels; i++) o = { child: o }
      return o
    }
    it('exposes the documented bounds', () => {
      expect(WALK_MAX_DEPTH).toBe(8)
      expect(WALK_MAX_NODES).toBe(250_000)
      expect(WALK_MAX_KEYS_PER_OBJECT).toBe(5_000)
    })

    it('discloses a row at exactly the depth bound', () => {
      // content depth 0; row object sits at depth WALK_MAX_DEPTH
      const content = nest(total('PINDAYU', BASE), WALK_MAX_DEPTH)
      const out = run({ content, is_error: false })
      expect(out.content['ayurdaya_figure_disclosure']).toBeDefined()
    })

    it('a row one level too deep is not disclosed and the loss is warned, not silent', () => {
      __resetAyurdayaWarningsForTests()
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const result = { content: nest(total('PINDAYU', BASE), WALK_MAX_DEPTH + 1), is_error: false }
      expect(postProcessAyurdayaDisclosure(result)).toBe(result)
      expect(warn).toHaveBeenCalledTimes(1)
      expect(String(warn.mock.calls[0]![0])).toMatch(/hit its bound/)
      warn.mockRestore()
    })

    it('stops at the object-count bound (rows past it are not found) and warns', () => {
      __resetAyurdayaWarningsForTests()
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const filler = Array.from({ length: WALK_MAX_NODES + 10 }, () => ({}))
      const result = { content: { filler, tail: [total('PINDAYU', BASE)] }, is_error: false }
      expect(postProcessAyurdayaDisclosure(result)).toBe(result)
      expect(warn).toHaveBeenCalledTimes(1)
      warn.mockRestore()
    })

    it('does not descend into an object with more than the key cap, and warns', () => {
      __resetAyurdayaWarningsForTests()
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const wide: Row = {}
      for (let i = 0; i <= WALK_MAX_KEYS_PER_OBJECT; i++) wide[`k${i}`] = i
      wide['rows'] = [total('PINDAYU', BASE)]
      const result = { content: { wide }, is_error: false }
      expect(postProcessAyurdayaDisclosure(result)).toBe(result)
      expect(warn).toHaveBeenCalledTimes(1)
      warn.mockRestore()
    })

    it('skips typed arrays / ArrayBuffers (no descent, no node cost) and passes them through by reference', () => {
      const blob = new Uint8Array(1_000_000)
      const buf = new ArrayBuffer(16)
      const out = run({ content: { blob, buf, rows: [total('PINDAYU', BASE)] }, is_error: false })
      expect(out.content['blob']).toBe(blob)
      expect(out.content['buf']).toBe(buf)
      expect(out.content['ayurdaya_figure_disclosure']).toBeDefined()
    })
  })
})
