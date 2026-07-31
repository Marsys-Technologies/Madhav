/**
 * SAMĀPTI · lane B-N8-F19-COVERAGE · finding F-19 (CRITICAL).
 *
 * `assembleDomainCompleteness` (registry_bridge.ts) pages the dossier engine to exhaustion and
 * then reports `fully_accounted`. The pre-fix implementation computed that as
 *
 *     fully_accounted: cov.accounted === cov.slice_size          // cov = LAST page's tally
 *
 * with no term for *whether the walk actually finished*. That measures "did pagination stop",
 * not "is this domain slice accounted for" — CLAUDE.md §N.8: a signal whose detector does not
 * measure the claim it asserts is null, not green.
 *
 * The sharp edge is the mid-walk `!page.ok` branch: `runDossier`'s error shape carries a ZEROED
 * `coverage_so_far` (`accounted: 0`, `slice_size: 0`). The old loop assigned that page to `page`
 * *before* testing `ok`, so the accounting compared `0 === 0` and a FAILED walk reported
 * `fully_accounted: true` — a live false-green on assess_wealth / assess_career / judgment_query.
 *
 * These tests force each early-termination path and assert the honest signal. They are written
 * to FAIL against the pre-fix code (documented in the lane's FINAL_SUMMARY) and pass after.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import type { DossierPage } from '../tools/dossier.js'

// `handler`, when set, intercepts runDossier; otherwise the real implementation runs.
const hoisted = vi.hoisted(() => ({
  handler: null as null | ((args: Record<string, unknown>, real: (a: never) => unknown) => unknown),
}))

vi.mock('../tools/dossier.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../tools/dossier.js')>()
  return {
    ...actual,
    runDossier: (args: never) =>
      hoisted.handler
        ? hoisted.handler(args as unknown as Record<string, unknown>, actual.runDossier as unknown as (a: never) => unknown)
        : actual.runDossier(args),
  }
})

const { assembleDomainCompleteness, attachDomainCompleteness, buildDomainCompletenessPointer } =
  await import('../tools/registry_bridge.js')
const { runDossier: realRunDossier } = await vi.importActual<typeof import('../tools/dossier.js')>('../tools/dossier.js')

const CANON = '482012f1-710e-4a25-994a-93821f5871aa'

/** The genuine first page of the flagship wealth slice — real data, more_available: true. */
function realFirstPage(): DossierPage {
  const p = realRunDossier({ domain: 'wealth', chart_id: CANON, budget_kb: 64 })
  expect(p.ok).toBe(true)
  expect(p.more_available).toBe(true)
  expect(p.cursor).toBeTruthy()
  return p
}

/** runDossier's own not-ok shape: note the ZEROED coverage_so_far — the 0 === 0 trap. */
function notOkPage(): DossierPage {
  const p = realRunDossier({ domain: 'wealth', chart_id: CANON, budget_kb: 64, cursor: 'not-a-real-cursor' })
  expect(p.ok).toBe(false)
  expect(p.coverage_so_far.accounted).toBe(0)
  expect(p.coverage_so_far.slice_size).toBe(0)
  return p
}

afterEach(() => {
  hoisted.handler = null
})

describe('F-19 — fully_accounted must measure accounting, not "pagination stopped"', () => {
  it('TRUE POSITIVE PRESERVED: an unmocked, genuinely complete walk still reports full accounting', () => {
    const b = assembleDomainCompleteness('wealth', CANON) as Record<string, unknown>
    expect(b).not.toBeNull()
    expect(b['fully_accounted']).toBe(true)
    expect(b['coverage_walk']).toBe('complete')
    expect(b['accounted']).toBe(b['slice_size'])
    expect(b['pct']).toBe(100)
    expect(b['synthesis_gate']).toBe('OPEN')
    // No truncation apparatus on a clean walk.
    expect(b['coverage_walk_reason']).toBeUndefined()
  })

  it('career (the second flagship slice) is likewise unaffected', () => {
    const b = assembleDomainCompleteness('career', CANON) as Record<string, unknown>
    expect(b['fully_accounted']).toBe(true)
    expect(b['coverage_walk']).toBe('complete')
  })

  it('EARLY TERMINATION · mid-walk not-ok page: never true (pre-fix this read TRUE via 0 === 0)', () => {
    let n = 0
    hoisted.handler = () => {
      n += 1
      return n === 1 ? realFirstPage() : notOkPage()
    }
    const b = assembleDomainCompleteness('wealth', CANON) as Record<string, unknown>
    expect(b).not.toBeNull()
    expect(b['fully_accounted']).not.toBe(true)
    expect(b['fully_accounted']).toBeNull()
    expect(b['coverage_walk']).toBe('truncated')
    expect(b['coverage_walk_reason']).toBe('page_fetch_not_ok')
    // The zeroed error page must NOT have been adopted as the coverage source.
    expect(b['slice_size'] as number).toBeGreaterThan(1000)
    expect(b['accounted'] as number).toBeGreaterThan(0)
    expect(b['pct'] as number).toBeLessThan(100)
    // No interpretive surface may be handed out on a truncated walk.
    expect(b['composition_scaffold']).toBeUndefined()
    expect(b['synthesis_gate']).toBe('BLOCKED')
  })

  it('EARLY TERMINATION · mid-walk throw: reported as unknown, not as a plain false', () => {
    let n = 0
    hoisted.handler = () => {
      n += 1
      if (n === 1) return realFirstPage()
      throw new Error('simulated slice read failure')
    }
    const b = assembleDomainCompleteness('wealth', CANON) as Record<string, unknown>
    expect(b['fully_accounted']).toBeNull()
    expect(b['coverage_walk']).toBe('truncated')
    expect(b['coverage_walk_reason']).toBe('page_fetch_threw')
    expect(b['slice_size'] as number).toBeGreaterThan(1000)
  })

  it('EARLY TERMINATION · guard limit reached: reported as unknown + guard reason', () => {
    // Always hand back a page that claims more is available — the walk can never finish, so the
    // guard is the only thing that stops it. That is a TRUNCATED measurement by definition.
    hoisted.handler = () => realFirstPage()
    const b = assembleDomainCompleteness('wealth', CANON) as Record<string, unknown>
    expect(b['fully_accounted']).toBeNull()
    expect(b['coverage_walk']).toBe('truncated')
    expect(b['coverage_walk_reason']).toBe('page_guard_limit_reached')
    expect(b['pages_walked']).toBe(65)
  })

  it('the truncated block carries an explicit, readable incompleteness note', () => {
    let n = 0
    hoisted.handler = () => { n += 1; return n === 1 ? realFirstPage() : notOkPage() }
    const b = assembleDomainCompleteness('wealth', CANON) as Record<string, unknown>
    expect(String(b['coverage_walk_note'])).toContain('INCOMPLETE MEASUREMENT')
    // The two prose sinks that used to hardcode "100%" must not claim it here.
    expect(JSON.stringify(b['full_hydration'])).not.toContain('100%')
    expect(String(b['note'])).not.toContain('100%')
  })

  it('attachDomainCompleteness surfaces truncation in judgment_flags + the directive', () => {
    let n = 0
    hoisted.handler = () => { n += 1; return n === 1 ? realFirstPage() : notOkPage() }
    const response: Record<string, unknown> = { domain: 'wealth', judgment_flags: ['pre_existing'] }
    attachDomainCompleteness(response, 'wealth', CANON)
    const flags = response['judgment_flags'] as string[]
    expect(flags.some((f) => String(f).includes('domain_accounting_incomplete'))).toBe(true)
    expect(flags).toContain('pre_existing')
    expect(String(response['completeness_directive'])).toContain('INCOMPLETE')
  })

  it('attachDomainCompleteness on a clean walk keeps the un-missable complete-accounting steer', () => {
    const response: Record<string, unknown> = { domain: 'wealth', judgment_flags: ['pre_existing'] }
    attachDomainCompleteness(response, 'wealth', CANON)
    const flags = response['judgment_flags'] as string[]
    expect(String(flags[0])).toContain('complete_domain_accounting_attached')
    expect(flags.some((f) => String(f).includes('domain_accounting_incomplete'))).toBe(false)
    expect(String(response['completeness_directive'])).toContain('COMPLETE ACCOUNTING ATTACHED')
  })

  it('buildDomainCompletenessPointer (judgment_query) propagates the honest signal, not a bare bool', () => {
    let n = 0
    hoisted.handler = () => { n += 1; return n === 1 ? realFirstPage() : notOkPage() }
    const p = buildDomainCompletenessPointer('wealth', CANON) as Record<string, unknown>
    expect(p).not.toBeNull()
    expect(p['fully_accounted']).toBeNull()
    expect(p['coverage_walk']).toBe('truncated')
    expect(p['coverage_walk_reason']).toBe('page_fetch_not_ok')
    expect(String(p['note'])).not.toContain('100%')
    expect(String(p['note'])).toContain('INCOMPLETE')
  })

  it('buildDomainCompletenessPointer on a clean walk still reports the 100% pointer', () => {
    const p = buildDomainCompletenessPointer('wealth', CANON) as Record<string, unknown>
    expect(p['fully_accounted']).toBe(true)
    expect(p['coverage_walk']).toBe('complete')
    expect(p['pct']).toBe(100)
    expect(String(p['note'])).toContain('100%')
  })
})
