/**
 * kala_sky_pattern.test.ts — ṢAḌ-DARŚANA W4 Lane R.
 *
 * Two things are proven here, and the second is the one that matters most:
 *   1. the Mode-2 interval arithmetic is EXACT (no sampling interval exists), and
 *   2. §5.4's mortality hard exclusion is NON-VACUOUS — it fires, it fires on the
 *      subtle cases, it does NOT fire on ordinary requests, and it is structurally
 *      incapable of running after a fetch (§N.8: a rail nobody proves can fire is null).
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import {
  MORTALITY_EXCLUSION_PATTERN,
  MORTALITY_FORBIDDEN_IDENTIFIERS,
  PADDHATI_DIVERGENCE_STATES,
  SKY_PATTERN_CONSTRAINT_KINDS,
  TARA_CYCLE,
  buildMortalityExclusionRefusal,
  detectMortalityExclusion,
  intersectIntervals,
  subtractIntervals,
  taraFor,
  type Interval,
} from './kala_sky_pattern.js'

const iv = (start: number, end: number, ...basis: string[]): Interval => ({ start, end, basis })

describe('interval arithmetic — exact set ops over lattice atoms', () => {
  it('intersects overlapping intervals and keeps both bases (the authority_basis trail)', () => {
    const out = intersectIntervals([iv(0, 100, 'a')], [iv(50, 150, 'b')])
    expect(out).toHaveLength(1)
    expect(out[0]!.start).toBe(50)
    expect(out[0]!.end).toBe(100)
    expect(out[0]!.basis.sort()).toEqual(['a', 'b'])
  })

  it('returns nothing for touching endpoints (half-open, matching the engine\'s own overlap rule)', () => {
    expect(intersectIntervals([iv(0, 100)], [iv(100, 200)])).toHaveLength(0)
  })

  it('intersects many-to-many without dropping a satisfying sliver', () => {
    // This is the completeness property: a 1-unit satisfying sliver must survive.
    const a = [iv(0, 10), iv(20, 30), iv(40, 50)]
    const b = [iv(9, 21), iv(29, 41)]
    const out = intersectIntervals(a, b)
    expect(out.map((o) => [o.start, o.end])).toEqual([[9, 10], [20, 21], [29, 30], [40, 41]])
  })

  it('subtracts a cut from the middle, producing two intervals', () => {
    const out = subtractIntervals([iv(0, 100, 'a')], [iv(40, 60)])
    expect(out.map((o) => [o.start, o.end])).toEqual([[0, 40], [60, 100]])
    // Basis survives the split — a candidate must still be able to name its atoms.
    expect(out.every((o) => o.basis.includes('a'))).toBe(true)
  })

  it('subtracting a covering cut leaves nothing (an eliminated horizon is genuinely empty)', () => {
    expect(subtractIntervals([iv(10, 20)], [iv(0, 100)])).toHaveLength(0)
  })

  it('subtracting a non-overlapping cut is a no-op', () => {
    expect(subtractIntervals([iv(10, 20)], [iv(50, 60)]).map((o) => [o.start, o.end])).toEqual([[10, 20]])
  })

  it('intersection is commutative in RESULT (order of operands cannot change which Tuesday survives)', () => {
    const a = [iv(0, 10), iv(15, 25)]
    const b = [iv(5, 20)]
    const ab = intersectIntervals(a, b).map((o) => [o.start, o.end])
    const ba = intersectIntervals(b, a).map((o) => [o.start, o.end])
    expect(ab).toEqual(ba)
  })
})

describe('tārā-bala arithmetic (chart-relative, R-4)', () => {
  it('a nakṣatra equal to the janma nakṣatra is janma-tārā', () => {
    expect(taraFor(1, 1)).toBe('janma')
    expect(taraFor(17, 17)).toBe('janma')
  })

  it('counts forward through the 9-fold cycle and wraps', () => {
    expect(taraFor(1, 2)).toBe('sampat')
    expect(taraFor(1, 3)).toBe('vipat')
    expect(taraFor(1, 10)).toBe('janma')
    expect(taraFor(1, 19)).toBe('janma')
  })

  it('wraps correctly when the current nakṣatra precedes the janma nakṣatra', () => {
    // 27 → 1 is one step forward, not 26 backward.
    expect(taraFor(27, 1)).toBe('sampat')
  })

  it('every (janma, current) pair yields a name from the declared 9-fold cycle', () => {
    for (let j = 1; j <= 27; j++) {
      for (let c = 1; c <= 27; c++) {
        expect(TARA_CYCLE).toContain(taraFor(j, c))
      }
    }
  })

  it('the two canonical charts genuinely DISAGREE on tārā for the same day — the both-charts clause has a real basis', () => {
    // Abhisek = Purva Bhadrapada (id 25); Abhinandan = Ardra (id 6). Ids are the
    // canonical NAKSHATRA_NAMES indices the lattice's own detail.factor_id carries.
    const ABHISEK_JANMA = 25
    const ABHINANDAN_JANMA = 6
    const disagreements = Array.from({ length: 27 }, (_, k) => k + 1).filter(
      (day) => taraFor(ABHISEK_JANMA, day) !== taraFor(ABHINANDAN_JANMA, day),
    )
    // If this were 0 the both-charts detector could only ever pass by accident.
    expect(disagreements.length).toBeGreaterThan(0)
  })
})

describe('sky_pattern_spec v1 — the frozen vocabulary', () => {
  it('carries exactly the nine frozen constraint kinds', () => {
    expect([...SKY_PATTERN_CONSTRAINT_KINDS].sort()).toEqual(
      [
        'chart_relative', 'kalam_not', 'mutual_configuration', 'natal_yoga_activation',
        'panchanga', 'panchanga_not', 'planet_state', 'residence', 'transit_contact',
      ],
    )
  })

  it('the paddhati divergence closed set is exactly ADJUDICATION-8\'s three states', () => {
    expect([...PADDHATI_DIVERGENCE_STATES]).toEqual(['none_computed', 'diverges', 'agrees'])
  })
})

// ══════════════════════════════════════════════════════════════════════════════
// §5.4 — THE MORTALITY HARD EXCLUSION. Non-vacuity is the point of this block.
// ══════════════════════════════════════════════════════════════════════════════

describe('§5.4 mortality hard exclusion — it FIRES', () => {
  it.each(MORTALITY_FORBIDDEN_IDENTIFIERS.map((s) => [s]))('fires on the substrate identifier %s', (id) => {
    const d = detectMortalityExclusion({ question_frame: { entity: id } })
    expect(d.excluded).toBe(true)
    expect(d.test).toBe('substrate')
  })

  it('fires when the identifier is only in an object KEY (the composition case a value scan would miss)', () => {
    expect(detectMortalityExclusion({ longevity_bound: '2050-01-01' }).excluded).toBe(true)
    expect(detectMortalityExclusion({ maraka_dasha: true }).excluded).toBe(true)
  })

  it('fires through arrays and nesting up to the traversal depth', () => {
    expect(
      detectMortalityExclusion({ sky_pattern_spec: { all: [{ chart_relative: { kind: 'ayurdaya' } }] } }).excluded,
    ).toBe(true)
  })

  it('fires on ordinary-language mortality phrasing (test 2, request shape)', () => {
    for (const s of ['when will I die', 'date of death', 'how long will I live', 'my demise', 'is it fatal']) {
      expect(detectMortalityExclusion({ question_frame: { stakes: s } }).excluded, s).toBe(true)
    }
  })
})

describe('§5.4 mortality hard exclusion — it does NOT fire on ordinary work', () => {
  it('an ordinary Mode-1/Mode-2 request passes through', () => {
    for (const req of [
      { chart_id: 'x', horizon: '24m' },
      { chart_id: 'x', sky_pattern_spec: { all: [{ panchanga: { vara: 'guru-vara' } }, { kalam_not: ['rahu_kalam'] }] } },
      { chart_id: 'x', question_frame: { domain: 'marriage', intent_verb: 'when_should_i' } },
      { chart_id: 'x', activity_class: 'sadhana_initiation' },
    ]) {
      const d = detectMortalityExclusion(req)
      expect(d.excluded, JSON.stringify(req)).toBe(false)
      expect(d.test).toBeNull()
      expect(d.matched_on).toBeNull()
    }
  })

  it('the `ayus` word boundary is real (ayusmati is not a mortality request)', () => {
    expect(MORTALITY_EXCLUSION_PATTERN.test('ayusmati')).toBe(false)
    expect(detectMortalityExclusion({ question_frame: { entity: 'ayusmati bhava' } }).excluded).toBe(false)
    expect(detectMortalityExclusion({ question_frame: { entity: 'ayus' } }).excluded).toBe(true)
  })

  it('health-domain language that is NOT mortality still passes (the rail is narrow, not a blanket)', () => {
    // §5.3 governs FILING for health-class interventions; §5.4 governs COMPUTATION
    // for mortality windows. Conflating them would suppress readings §3.5.B grants.
    for (const s of ['chronic onset', 'surgery timing', 'an acute illness window']) {
      expect(detectMortalityExclusion({ question_frame: { stakes: s } }).excluded, s).toBe(false)
    }
  })
})

describe('§5.4 — structural properties a future edit must not weaken', () => {
  it('the detector is SYNCHRONOUS (cannot await I/O, cannot be reordered after a fetch)', () => {
    expect(detectMortalityExclusion.constructor.name).not.toBe('AsyncFunction')
  })

  it('the detector is PURE — the same request yields the same decision, and the input is not mutated', () => {
    const req = { chart_id: 'x', question_frame: { entity: 'ayurdaya' } }
    const snapshot = JSON.stringify(req)
    const a = detectMortalityExclusion(req)
    const b = detectMortalityExclusion(req)
    expect(a).toEqual(b)
    expect(JSON.stringify(req)).toBe(snapshot)
  })

  it('the refusal names §3.5.C, is tier-independent and filing-independent, and carries a NAMED detector', () => {
    const d = detectMortalityExclusion({ question_frame: { entity: 'maraka' } })
    const refusal = buildMortalityExclusionRefusal(d)
    expect(refusal.withheld).toBe(true)
    expect(refusal.clause).toContain('§3.5.C')
    expect(refusal.audience_tier_independent).toBe(true)
    expect(refusal.filing_state_independent).toBe(true)
    expect(refusal.detector.matched_on).toBe('maraka')
    expect(refusal.statement).toContain('ABSOLUTE')
  })

  it('building a refusal from a NON-excluded decision THROWS — no refusal without a detector behind it (§N.8)', () => {
    const notExcluded = detectMortalityExclusion({ chart_id: 'x', horizon: '90d' })
    expect(notExcluded.excluded).toBe(false)
    expect(() => buildMortalityExclusionRefusal(notExcluded)).toThrow(/detector/)
  })

  it('the module never calls the L1 span-of-life capability (the substrate ban applies to its own file too)', () => {
    const src = readFileSync(fileURLToPath(new URL('./kala_sky_pattern.ts', import.meta.url)), 'utf8')
    expect(src).not.toMatch(/ganita_ayurdaya_get/)
  })
})
