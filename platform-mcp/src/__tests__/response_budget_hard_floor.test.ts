/**
 * response_budget_hard_floor.test.ts — D-1.5a wave gate finding.
 *
 * PASS 2 (hard-cap fallback) floors every declared TrimmableSection to 0, ranked by
 * current byte size, biggest-first, stopping as soon as the response fits. A section
 * that used to be reliably empty (e.g. judgment_query's bearing_yogas before its
 * firings-authoritative fix landed) becomes, once genuinely populated, the biggest
 * remaining candidate purely by no longer being empty — and PASS 2 silently zeroes it,
 * defeating the fix that populated it in the first place. `hardFloor: true` exempts a
 * section's declared minKeep from PASS 2's override.
 */
import { describe, it, expect } from 'vitest'
import { applyResponseBudget, type TrimmableSection } from '../lib/response_budget.js'

function makeContent(bearingYogasCount: number, paddingBytes: number) {
  return {
    padding: 'x'.repeat(paddingBytes), // simulates non-trimmable base content (orientation_context prose etc.)
    checklist: {
      bearing_yogas: Array.from({ length: bearingYogasCount }, (_, i) => ({
        yoga_canonical_id: `dhana_yoga_${i}`,
        strength: 1.02,
        constituent_planets: ['venus', 'jupiter'],
        source: 'ga_yoga_firings',
      })),
    },
  }
}

function bearingYogasSection(hardFloor: boolean): TrimmableSection<ReturnType<typeof makeContent>> {
  return {
    path: 'checklist.bearing_yogas',
    getArray: (c) => c.checklist.bearing_yogas,
    setArray: (c, kept) => { c.checklist.bearing_yogas = kept as typeof c.checklist.bearing_yogas },
    minKeep: 3,
    recover: { instrument: 'bodha_signals_get', hint: 'full set' },
    label: 'checklist.bearing_yogas',
    hardFloor,
  }
}

describe('applyResponseBudget hardFloor (D-1.5a gate finding)', () => {
  it('without hardFloor: PASS 2 zeroes bearing_yogas below its declared minKeep when base content alone is over budget', () => {
    // Large non-trimmable padding forces PASS 1 (respecting minKeep=3) to fail, then PASS 2 fires.
    const content = makeContent(13, 12_000)
    const result = applyResponseBudget(content, 1, [bearingYogasSection(false)])
    expect(result.content.checklist.bearing_yogas.length).toBeLessThan(3)
  })

  it('with hardFloor: PASS 2 respects minKeep=3 even when base content alone exceeds budget', () => {
    const content = makeContent(13, 12_000)
    const result = applyResponseBudget(content, 1, [bearingYogasSection(true)])
    expect(result.content.checklist.bearing_yogas.length).toBeGreaterThanOrEqual(3)
    // Honest reporting: the response is still over budget (base content alone exceeds
    // it) — hardFloor protects the section's data, it does not pretend the ceiling was met.
    // (W3-L5: the dead `still_over_budget` boolean was removed from BudgetResult — GT-45,
    // nobody read it on any real call path; the `(whole response)` trim_report entry below
    // is the one real, already-consumed honesty signal for this condition.)
    expect(result.trim_report?.some(e => e.path === '(whole response)')).toBe(true)
  })

  it('with hardFloor but response fits under budget: no trimming needed at all', () => {
    const content = makeContent(3, 10)
    const result = applyResponseBudget(content, 100, [bearingYogasSection(true)])
    expect(result.trimmed).toBe(false)
    expect(result.content.checklist.bearing_yogas.length).toBe(3)
  })
})
