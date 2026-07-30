/**
 * response_budget_verdict_immune_and_trim_order.test.ts — ŚODHANA T3 (MC-005/MC-023
 * regression check).
 *
 * Two independent fixes to response_budget.ts pinned here:
 *
 * 1. VERDICT IMMUNITY — before this fix, a verdict clause's >120-char prose `text` field
 *    (EL-44 grounded sentences; judgment_query's top-level verdict.note) was invisible to
 *    `autoDetectTrimmableSections` (clause arrays never exceed the length>10 auto-detect
 *    threshold) but VISIBLE to `truncateLongStringsInPlace`'s last-resort scalar walk —
 *    which truncated the prose mid-sentence while the same clause's `fact_ids` array (short
 *    strings) survived untouched. This inverted the Serving Density Principle (CLAUDE.md
 *    §N.6): the densest, most-actionable layer must be the LAST thing trimmed, not the
 *    first. `verdict` is now in IMMUNE_HONESTY_FIELDS.
 *
 * 2. TRIM-ORDER TIERING — before this fix, `applyResponseBudget` ranked ALL declared
 *    sections into one biggest-first list, so a `hardFloor` section that happened to be the
 *    biggest could be the ONLY section touched (the loop breaks as soon as the response is
 *    under budget) while a smaller, genuinely disposable `fact_id`/signal-id array was never
 *    touched at all. `hardFloor` previously only protected a section from PASS 2's
 *    floor-to-0 override — never from being picked FIRST. Non-hardFloor sections now form a
 *    tier that absorbs every cut before any hardFloor section is touched.
 */
import { describe, it, expect } from 'vitest'
import { applyResponseBudget, estimateBytes, type TrimmableSection } from '../lib/response_budget.js'

// NOTE (SAMĀPTI A2, 2026-07-30): the `recover.instrument` values in this file's
// fixtures are irrelevant to what it asserts (trim order and verdict immunity — no
// assertion reads `recover`), but they are NOT free-form. The CI boot-time pointer
// validator (platform/scripts/audit/tap/sc_pointer_validation.ts, SC-17/18/19)
// statically scans every `instrument: '<name>'` literal in the repo — test fixtures
// included — against the currently-registered MCP tool set, so a placeholder name
// reads as a real serving-surface regression to that gate. This file's original
// `instrument: 'x'` placeholder was exactly that: the `SC-pointer:x` FAIL the harness
// reported on unmodified `main`. Fixtures therefore name an ALREADY-REGISTERED live
// tool, per the same convention documented in `src/lib/kala_envelope.test.ts` and
// `src/tools/kala_views/ritual.test.ts`. `hint` is not scanned and stays a placeholder.

describe('MC-005/MC-023 — verdict immunity', () => {
  it('a verdict clause\'s long prose sentence is never truncated, even under an aggressively tight budget', () => {
    const longSentence = 'Wealth assessment draws on 10 composite-ranked signal(s) for this ' +
      'chart, cross-referenced against classical yoga firings, varga placements, ' +
      'contradictions, and dasha timing below.'
    expect(longSentence.length).toBeGreaterThan(120) // sanity: this is exactly the shape that used to get truncated

    const content = {
      padding: 'x'.repeat(20_000), // forces the last-resort truncateLongStringsInPlace walk to fire
      verdict: {
        clauses: [
          { text: longSentence, fact_ids: ['fid_1', 'fid_2'], grounded: true },
        ],
        sentence_count: 1,
        fact_ids_cited: ['fid_1', 'fid_2'],
        template: 'deterministic_v1',
        note: 'Composed by a fixed string template over already-graded terms.',
      },
    }
    const result = applyResponseBudget(content, 1, [])
    // The whole response may still be honestly over budget (huge padding, no declared
    // sections to trim) — that's fine; the assertion is specifically that verdict prose
    // survived intact, never truncated mid-sentence.
    expect(result.content.verdict.clauses[0].text).toBe(longSentence)
    expect(result.content.verdict.clauses[0].text.endsWith('below.')).toBe(true)
  })

  it('judgment_query-shaped top-level verdict.note prose is never truncated', () => {
    const note = 'Deterministic classical-checklist verdict + completeness receipt (design ' +
      '§28.6) — see `receipt` for which checklist items were actually checked this call.'
    expect(note.length).toBeGreaterThan(120)
    const content = {
      padding: 'y'.repeat(20_000),
      verdict: { bhava: true, receipt: { varga_confirmed: 'D9✓' }, note },
    }
    const result = applyResponseBudget(content, 1, [])
    expect(result.content.verdict.note).toBe(note)
  })
})

describe('MC-005 — trim-order inversion fix (disposable sections absorb cuts before hardFloor sections)', () => {
  type Content = {
    padding: string
    hardFloorSection: { id: string }[]
    factIdRefs: string[]
  }

  function makeContent(): Content {
    return {
      padding: 'z'.repeat(200), // small non-trimmable base — the two sections below decide the outcome
      // The BIGGEST section, but hardFloor — must NOT be the first (or only) thing cut.
      hardFloorSection: Array.from({ length: 20 }, (_, i) => ({ id: `hard_${i}_${'q'.repeat(40)}` })),
      // Smaller, disposable — must absorb the cut FIRST, regardless of its smaller size.
      factIdRefs: Array.from({ length: 20 }, (_, i) => `fact_${i}`),
    }
  }

  function sections(): TrimmableSection<Content>[] {
    return [
      {
        path: 'hardFloorSection',
        getArray: (c) => c.hardFloorSection,
        setArray: (c, kept) => { c.hardFloorSection = kept as Content['hardFloorSection'] },
        minKeep: 3,
        recover: { instrument: 'bodha_signals_get', hint: 'x' },
        label: 'hardFloorSection',
        hardFloor: true,
      },
      {
        path: 'factIdRefs',
        getArray: (c) => c.factIdRefs,
        setArray: (c, kept) => { c.factIdRefs = kept as string[] },
        minKeep: 2,
        recover: { instrument: 'bodha_signals_get', hint: 'x' },
        label: 'factIdRefs',
        // no hardFloor — disposable
      },
    ]
  }

  it('a moderately tight budget cuts the disposable factIdRefs section down to its floor before touching the (bigger) hardFloor section at all', () => {
    const content = makeContent()
    const preTrimHardFloorBytes = estimateBytes(content.hardFloorSection)
    // Budget: fits once factIdRefs alone is floored to 2, without needing to touch
    // hardFloorSection. If the old biggest-first-across-everything ranking were still in
    // effect, hardFloorSection (bigger) would have been picked FIRST instead.
    const afterDroppingFactIdRefsToFloor = estimateBytes(content) -
      estimateBytes(content.factIdRefs) + estimateBytes(content.factIdRefs.slice(0, 2))
    // maxBytes strictly between "floored-factIdRefs-only" size and the untouched original
    // size — small enough to force a trim, large enough that trimming factIdRefs ALONE
    // closes the gap (so hardFloorSection should never need to be touched).
    const maxKb = (afterDroppingFactIdRefsToFloor + 1) / 1024

    applyResponseBudget(content, maxKb, sections())

    expect(content.factIdRefs.length).toBe(2) // disposable section floored
    // The hardFloor section — bigger, but protected from being picked first — is untouched.
    expect(content.hardFloorSection.length).toBe(20)
    expect(estimateBytes(content.hardFloorSection)).toBe(preTrimHardFloorBytes)
  })

  it('only once every disposable section is at its floor and the response is STILL over budget does the hardFloor section get touched (down to its own minKeep, never below)', () => {
    const content = makeContent()
    // Impossibly tight budget — factIdRefs alone floored to 2 is not enough.
    const result = applyResponseBudget(content, 1, sections())
    expect(content.factIdRefs.length).toBe(2) // disposable floored first
    expect(content.hardFloorSection.length).toBeGreaterThanOrEqual(3) // hardFloor minKeep respected
    // Honest reporting either way.
    expect(result.trim_report).not.toBeNull()
  })
})
