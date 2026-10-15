/**
 * response_budget_cross_check_first.test.ts — SS N-342 / CLAUDE.md §N.6 (Lahiri-primary PR-3).
 *
 * The labelled ayanamsha cross-check is secondary corroboration. It is registered TRIMMABLE (never
 * hardFloor, never immune) and is shed BEFORE any row of any section — hardFloor or not — so it can
 * never push confirmed/primary data out of a tight budget.
 */
import { describe, it, expect } from 'vitest'
import { applyResponseBudget, CROSS_CHECK_FIELDS, IMMUNE_HONESTY_FIELDS, estimateBytes, type TrimmableSection } from '../lib/response_budget.js'

type Row = { fact_id: string; v: string; ayanamsha_cross_check?: unknown }
interface Content { rows: Row[]; ayanamsha_cross_check?: unknown; padding: string }

const bigCrossCheck = () => ({ heading: 'Cross-check, not the reading', summary: 'x'.repeat(900) })

function make(rowCount: number, withCrossCheck: boolean): Content {
  return {
    padding: 'p'.repeat(300),
    rows: Array.from({ length: rowCount }, (_, i) => ({ fact_id: `f${i}`, v: `v${i}` })),
    ...(withCrossCheck ? { ayanamsha_cross_check: bigCrossCheck() } : {}),
  }
}

const section = (hardFloor: boolean): TrimmableSection<Content> => ({
  path: 'rows', label: 'rows', minKeep: 10, hardFloor,
  getArray: (c) => c.rows, setArray: (c, kept) => { c.rows = kept as Row[] },
  recover: { instrument: 'ganita_positions_get', hint: 'narrow the scope' },
})

describe('ayanamsha_cross_check is trimmed BEFORE confirmed data', () => {
  it('is a registered, non-immune field (so it is trimmable, never hardFloor)', () => {
    expect(CROSS_CHECK_FIELDS).toEqual(['ayanamsha_cross_check', 'identity_cross_check'])
    expect(IMMUNE_HONESTY_FIELDS.has('ayanamsha_cross_check')).toBe(false)
  })

  it.each([false, true])('hardFloor=%s: dropping the cross-check alone is enough -> every row survives', (hardFloor) => {
    const without = estimateBytes(make(40, false))
    const c = make(40, true)
    const maxKb = (without + 200) / 1024
    expect(estimateBytes(c)).toBeGreaterThan(maxKb * 1024)
    const res = applyResponseBudget(c, maxKb, [section(hardFloor)])
    expect(res.content.rows).toHaveLength(40)
    expect(res.content.ayanamsha_cross_check).toBeUndefined()
    const entry = res.trim_report?.find((e) => e.path === 'ayanamsha_cross_check')
    expect(entry?.kept_count).toBe(0)
    expect(res.trim_report?.some((e) => e.path === 'rows')).toBe(false)
  })

  it('rows are cut only AFTER the cross-check is gone, and the shed is still reported', () => {
    const c = make(80, true)
    const res = applyResponseBudget(c, 1.0, [section(false)])
    expect(res.content.rows.length).toBeLessThan(80)
    expect(res.content.ayanamsha_cross_check).toBeUndefined()
    expect(res.trim_report?.some((e) => e.path === 'ayanamsha_cross_check')).toBe(true)
    expect(res.trim_report?.some((e) => e.path === 'rows')).toBe(true)
  })

  it('also sheds a per-row cross-check (families / event rows) and the envelope-nested one', () => {
    const rows: Row[] = Array.from({ length: 30 }, (_, i) => ({ fact_id: `f${i}`, v: 'v', ayanamsha_cross_check: bigCrossCheck() }))
    const env = { content: { rows, ayanamsha_cross_check: bigCrossCheck() } as unknown as Content }
    const sec: TrimmableSection<typeof env> = {
      path: 'content.rows', label: 'rows', minKeep: 10, hardFloor: true,
      getArray: (e) => e.content.rows, setArray: (e, kept) => { e.content.rows = kept as Row[] },
      recover: { instrument: 'bodha_signals_get', hint: 'h' },
    }
    const res = applyResponseBudget(env, 0.5, [sec])
    expect(res.content.content.rows.every((r) => r.ayanamsha_cross_check === undefined)).toBe(true)
    expect(res.content.content.ayanamsha_cross_check).toBeUndefined()
  })

  it('an under-budget response keeps its cross-check untouched', () => {
    const c = make(3, false)
    c.ayanamsha_cross_check = { heading: 'Cross-check, not the reading', summary: 'Agrees across all five ayanamshas' }
    const res = applyResponseBudget(c, 40, [section(false)])
    expect(res.trimmed).toBe(false)
    expect(res.content.ayanamsha_cross_check).toBeDefined()
  })
})
