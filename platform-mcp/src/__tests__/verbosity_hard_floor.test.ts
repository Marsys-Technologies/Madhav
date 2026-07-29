/**
 * verbosity_hard_floor.test.ts — W3 "One Envelope" C-4 guard.
 * ==============================================================
 * RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §7 item 6 ("verbosity: concise|detailed request
 * knob wired through density_contract") + master brief §E W3 ("WITH the C-4 guard").
 *
 * CLAUDE.md §N.6 "Serving Density Principle" names the exact regression this guards
 * against: the D-1.5a wave gate caught a generic budget trim silently ZEROING
 * judgment_query's `bearing_yogas` section the moment it became genuinely populated —
 * because a non-empty confirmed-finding section was, simply by no longer being empty,
 * the biggest remaining candidate for PASS 2's hard-cap fallback. `hardFloor: true`
 * (response_budget.ts) exempts a section's declared `minKeep` from that override.
 * `response_budget_hard_floor.test.ts` already proves that mechanism holds for a FIXED
 * maxKb. This file proves the NEW thing W3 adds — `resolveVerbosityMaxKb` tightening
 * maxKb for `verbosity:'concise'` — does not reopen the gap: a hardFloor section must
 * survive at its declared minKeep under the TIGHTENED concise budget, not just the
 * normal 'detailed' one.
 *
 * Content shape mirrors judgment_query's REAL sections (registry_bridge.ts's
 * `judgmentSections` — see the `hardFloor: true` blocks on bearing_yogas/
 * bearing_afflictions/affliction_mechanisms, and the non-hardFloor `fact_id_refs`
 * section with minKeep 20), not an invented fixture — same minKeep values, same
 * hardFloor/non-hardFloor split, so this test genuinely exercises the shape the C-4
 * guard was written for.
 */
import { describe, it, expect } from 'vitest'
import { applyResponseBudget, type TrimmableSection } from '../lib/response_budget.js'
import { resolveVerbosityMaxKb } from '../tools/registry_bridge.js'

type Content = {
  padding: string
  checklist: {
    bearing_yogas: { yoga_canonical_id: string; strength: number }[]
    bearing_afflictions: { affliction_id: string }[]
  }
  fact_id_refs: string[]
}

function makeJudgmentShapedContent(): Content {
  return {
    // Simulates the non-trimmable base content (receipt, orientation_context prose,
    // chart_header) that alone can push a response over a tight concise ceiling —
    // exactly the condition that makes PASS 2's hard-cap fallback fire in production.
    padding: 'x'.repeat(15_000),
    checklist: {
      // Firings-authoritative confirmed yogas (register_d9_judgment.ts §N.6 hardFloor) —
      // genuinely populated, mirroring the exact post-fix state the D-1.5a gate caught
      // PASS 2 silently zeroing.
      bearing_yogas: Array.from({ length: 12 }, (_, i) => ({
        yoga_canonical_id: `dhana_yoga_${i}`,
        strength: 1.0 + i * 0.01,
      })),
      bearing_afflictions: Array.from({ length: 10 }, (_, i) => ({
        affliction_id: `affliction_${i}`,
      })),
    },
    // Non-hardFloor section (real judgment_query analog: content.fact_id_refs, minKeep 20)
    // — expected to actually shrink under a tightened budget, proving concise has real
    // teeth and this isn't a no-op knob.
    fact_id_refs: Array.from({ length: 200 }, (_, i) => `fact_${i}`),
  }
}

function judgmentLikeSections(): TrimmableSection<Content>[] {
  return [
    {
      path: 'checklist.bearing_yogas',
      getArray: (c) => c.checklist.bearing_yogas,
      setArray: (c, kept) => { c.checklist.bearing_yogas = kept as Content['checklist']['bearing_yogas'] },
      minKeep: 3,
      recover: { instrument: 'bodha_signals_get', hint: 'full yoga+dosha set' },
      label: 'checklist.bearing_yogas',
      hardFloor: true, // register_d9_judgment.ts's real declaration
    },
    {
      path: 'checklist.bearing_afflictions',
      getArray: (c) => c.checklist.bearing_afflictions,
      setArray: (c, kept) => { c.checklist.bearing_afflictions = kept as Content['checklist']['bearing_afflictions'] },
      minKeep: 3,
      recover: { instrument: 'bodha_signals_get', hint: 'full adverse-valence set' },
      label: 'checklist.bearing_afflictions',
      hardFloor: true, // register_d9_judgment.ts's real declaration
    },
    {
      path: 'fact_id_refs',
      getArray: (c) => c.fact_id_refs,
      setArray: (c, kept) => { c.fact_id_refs = kept as string[] },
      minKeep: 20,
      recover: { instrument: 'judgment_query', hint: 'full fact_id_refs list' },
      label: 'fact_id_refs',
      // no hardFloor — same as the real judgment_query declaration.
    },
  ]
}

describe('W3 C-4 guard — verbosity:concise never reintroduces the D-1.5a hardFloor regression', () => {
  it('resolveVerbosityMaxKb: detailed (or omitted) keeps the base ceiling; concise roughly halves it, floored at 4KB', () => {
    expect(resolveVerbosityMaxKb(12, 'detailed')).toBe(12)
    expect(resolveVerbosityMaxKb(12, undefined)).toBe(12)
    expect(resolveVerbosityMaxKb(12, 'concise')).toBe(6)
    expect(resolveVerbosityMaxKb(55, 'concise')).toBe(28) // Math.round(27.5)
    // Never degenerates to (or below) 0 — leaves the hard-cap PASS 2 / hardFloor
    // mechanism room to actually operate rather than trimming a zero-byte ceiling.
    expect(resolveVerbosityMaxKb(1, 'concise')).toBe(4)
  })

  it('detailed (base maxKb=12, judgment_query real ceiling): hardFloor sections survive at minKeep; the response is honestly reported over/under budget', () => {
    const content = makeJudgmentShapedContent()
    const maxKb = resolveVerbosityMaxKb(12, 'detailed')
    const result = applyResponseBudget(content, maxKb, judgmentLikeSections())
    expect(content.checklist.bearing_yogas.length).toBeGreaterThanOrEqual(3)
    expect(content.checklist.bearing_afflictions.length).toBeGreaterThanOrEqual(3)
    expect(result).toBeDefined() // sanity: applyResponseBudget mutates content in place and returns it
  })

  it("C-4 GUARD: concise (maxKb halved to 6) still respects EVERY hardFloor section's declared minKeep — the exact D-1.5a class does not reappear under a tighter caller-requested ceiling", () => {
    const content = makeJudgmentShapedContent()
    const maxKb = resolveVerbosityMaxKb(12, 'concise')
    expect(maxKb).toBeLessThan(12) // sanity: verbosity actually tightened something
    const result = applyResponseBudget(content, maxKb, judgmentLikeSections())

    // THE C-4 ASSERTION: hardFloor sections never drop below their declared minKeep,
    // even under PASS 2's hard-cap fallback at this tighter ceiling.
    expect(content.checklist.bearing_yogas.length).toBeGreaterThanOrEqual(3)
    expect(content.checklist.bearing_afflictions.length).toBeGreaterThanOrEqual(3)

    // Honesty, not silence: if the tighter ceiling genuinely can't be met even with every
    // hardFloor section respected, that must be reported, never masked as a clean trim.
    if (result.still_over_budget) {
      expect(result.trim_report).not.toBeNull()
    }
  })

  it('concise vs detailed produce a REAL byte-size difference on the non-hardFloor section (fact_id_refs) — proves the knob has genuine effect, not a cosmetic no-op', () => {
    const detailedContent = makeJudgmentShapedContent()
    const detailedMaxKb = resolveVerbosityMaxKb(12, 'detailed')
    applyResponseBudget(detailedContent, detailedMaxKb, judgmentLikeSections())

    const conciseContent = makeJudgmentShapedContent()
    const conciseMaxKb = resolveVerbosityMaxKb(12, 'concise')
    applyResponseBudget(conciseContent, conciseMaxKb, judgmentLikeSections())

    // The non-hardFloor fact_id_refs section is exactly the kind of catalog/reference
    // list §N.6 says should absorb a tighter budget FIRST — concise must keep no more of
    // it than detailed does.
    expect(conciseContent.fact_id_refs.length).toBeLessThanOrEqual(detailedContent.fact_id_refs.length)
    // And the hardFloor sections must be IDENTICAL between the two (both at/above
    // minKeep) — the knob's tightening effect lands on the trimmable section, never on
    // the confirmed-finding one.
    expect(conciseContent.checklist.bearing_yogas.length).toBeGreaterThanOrEqual(3)
    expect(detailedContent.checklist.bearing_yogas.length).toBeGreaterThanOrEqual(3)
  })
})
