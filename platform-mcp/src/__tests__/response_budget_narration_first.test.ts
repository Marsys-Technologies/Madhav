/**
 * response_budget_narration_first.test.ts — SS N-345 / CLAUDE.md §N.6.
 *
 * The typed L1 readers serve `citation_human` (graded narration) on every row beside the machine
 * `citation_ref`. Narration is the most disposable field of a row: under a tight budget it must be
 * the FIRST thing dropped (before any row of any section — hardFloor or not — is cut), never the
 * field that pushes confirmed data out.
 */
import { describe, it, expect } from 'vitest'
import { applyResponseBudget, NARRATION_FIELDS, estimateBytes, type TrimmableSection } from '../lib/response_budget.js'

type Row = { fact_id: string; fact_value_text: string; citation_ref: string; citation_human?: string | null }
interface Content { rows: Row[]; padding: string }

function make(rowCount: number, narration: string | null): Content {
  return {
    padding: 'p'.repeat(400),
    rows: Array.from({ length: rowCount }, (_, i) => ({
      fact_id: `f${i}`, fact_value_text: `v${i}`, citation_ref: `ref-${i}`,
      ...(narration === null ? {} : { citation_human: narration }),
    })),
  }
}

const section = (hardFloor: boolean): TrimmableSection<Content> => ({
  path: 'rows', label: 'rows', minKeep: 10, hardFloor,
  getArray: (c) => c.rows, setArray: (c, kept) => { c.rows = kept as Row[] },
  recover: { instrument: 'ganita_nakshatra_get', hint: 'narrow the scope' },
})

describe('narration is shed FIRST under a tight budget', () => {
  it('declares citation_human as a narration field', () => {
    expect(NARRATION_FIELDS).toContain('citation_human')
  })

  it.each([false, true])('hardFloor=%s: dropping the narration alone is enough -> every row (and citation_ref) survives', (hardFloor) => {
    const narration = 'N'.repeat(300)
    const c = make(40, narration)
    const withoutNarration = estimateBytes(make(40, null))
    // budget: fits WITHOUT narration, does not fit WITH it
    const maxKb = (withoutNarration + 600) / 1024
    expect(estimateBytes(c)).toBeGreaterThan(maxKb * 1024)
    const res = applyResponseBudget(c, maxKb, [section(hardFloor)])
    expect(res.content.rows).toHaveLength(40)
    expect(res.content.rows.every((r) => r.citation_ref.startsWith('ref-') && !('citation_human' in r))).toBe(true)
    const entry = res.trim_report?.find((e) => e.path === 'rows[].narration')
    expect(entry?.original_count).toBe(40)
    expect(entry?.kept_count).toBe(0)
    expect(res.trim_report?.some((e) => e.path === 'rows')).toBe(false) // no row was cut
  })

  it('rows are cut only AFTER the narration is gone, and the narration entry is still reported', () => {
    const c = make(60, 'N'.repeat(200))
    const res = applyResponseBudget(c, 1.2, [section(false)])
    expect(res.content.rows.length).toBeLessThan(60)
    expect(res.content.rows.every((r) => !('citation_human' in r))).toBe(true)
    expect(res.trim_report?.some((e) => e.path === 'rows[].narration')).toBe(true)
    expect(res.trim_report?.some((e) => e.path === 'rows')).toBe(true)
  })

  it('an under-budget response keeps its narration untouched', () => {
    const c = make(3, 'short narration')
    const res = applyResponseBudget(c, 40, [section(false)])
    expect(res.trimmed).toBe(false)
    expect(res.content.rows.every((r) => r.citation_human === 'short narration')).toBe(true)
  })

  it('rows with a null narration are left as they are (honest null is not "narration")', () => {
    const c = make(30, null)
    c.rows.forEach((r) => { r.citation_human = null })
    const res = applyResponseBudget(c, (estimateBytes(c) - 200) / 1024, [section(false)])
    expect(res.trim_report?.some((e) => e.path === 'rows[].narration')).toBeFalsy()
  })
})
