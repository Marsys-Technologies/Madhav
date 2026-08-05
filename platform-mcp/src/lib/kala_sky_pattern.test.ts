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
  PADDHATI_CENSUS_UNCONFIRMED,
  PADDHATI_DIVERGENCE_STATES,
  SKY_PATTERN_CONSTRAINT_KINDS,
  TARA_CYCLE,
  buildAgnivasaConventionBVoices,
  buildMortalityExclusionRefusal,
  detectMortalityExclusion,
  intersectIntervals,
  paddhatiCensusStatement,
  subtractIntervals,
  taraFor,
  type Interval,
  type PaddhatiConventionRow,
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

describe('paddhati census statement — derived from the profile, never a static claim (§N.7/§N.8)', () => {
  const row = (over: Partial<PaddhatiConventionRow> = {}): PaddhatiConventionRow => ({
    factor_family: 'agnivasa',
    convention_id: 'agnivasa_tithi_element_prithvi',
    school_tag: 'corpus_default',
    constraint_role: 'hard',
    convention_status: 'computed',
    provenance: 'L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)',
    corpus_gap_ref: null,
    native_confirmed: false,
    awaiting_native_confirmation: true,
    version: 'paddhati_v01',
    ...over,
  })

  it('native_confirmed=TRUE (migration 534 applied) → cites the row\'s own confirmation_provenance', () => {
    const s = paddhatiCensusStatement({
      available: true,
      unavailable_reason: null,
      operative: [
        row({
          native_confirmed: true,
          awaiting_native_confirmation: false,
          confirmation_provenance:
            'native statement 2026-08-02; recorded in SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS',
        }),
      ],
    })
    expect(s).toContain('natively CONFIRMED')
    expect(s).toContain('agnivasa_tithi_element_prithvi')
    expect(s).toContain('§NATIVE CONFIRMATIONS')
    // The superseded static claim must NOT survive into the confirmed state.
    expect(s).not.toContain('not on record')
  })

  it('confirmed but the wire dropped confirmation_provenance → names the data gap instead of inventing a citation', () => {
    const s = paddhatiCensusStatement({
      available: true,
      unavailable_reason: null,
      operative: [row({ native_confirmed: true, awaiting_native_confirmation: false })],
    })
    expect(s).toContain('natively CONFIRMED')
    expect(s).toContain('no confirmation_provenance')
    expect(s).not.toContain('not on record')
  })

  it('profile read, no confirmed row → the original honest "not on record" text, with the awaiting note the row itself carries', () => {
    const s = paddhatiCensusStatement({ available: true, unavailable_reason: null, operative: [row()] })
    expect(s).toContain(PADDHATI_CENSUS_UNCONFIRMED)
    expect(s).toContain('awaiting native confirmation')
  })

  it('profile read, empty profile → exactly the original ADJUDICATION-8 rail 1 statement', () => {
    expect(paddhatiCensusStatement({ available: true, unavailable_reason: null, operative: [] })).toBe(
      PADDHATI_CENSUS_UNCONFIRMED,
    )
  })

  it('fetch FAILED → reported as unreachable with the reason, never restated as "not on record"', () => {
    const s = paddhatiCensusStatement({
      available: false,
      unavailable_reason: 'query_kala_paddhati_profile returned status 404',
      operative: [],
    })
    expect(s).toContain('could NOT be determined')
    expect(s).toContain('status 404')
    // A `declared_not_computed`-style honest absence and an unreachable record are
    // DIFFERENT claims; the unreachable state must not assert absence.
    expect(s.startsWith('agnivāsa convention = corpus default')).toBe(true)
    expect(s.includes('lineage convention is not on record')).toBe(false)
  })
})

// ══════════════════════════════════════════════════════════════════════════════
// ADJUDICATION-17 — Agnivāsa Convention (B), a SECOND served voice.
//
// The ruling (`SHAD_DARSHANA_ADJUDICATION_17_AGNIVASA_MULTI_CONVENTION_GRADING_v1_0.md`):
// Convention B never enters `compileConstraint`'s `residence` hard-gate match (that stays
// hardcoded to Convention A's `favourableElements = ['prithvi']`, deliberately, per the
// ruling's own reversibility note). It becomes a second, informational, per-date voice —
// `buildAgnivasaConventionBVoices` is the pure function the `residence` branch calls to
// build that voice for exactly the atoms Convention A already matched, never changing what
// Convention A matched.
// ══════════════════════════════════════════════════════════════════════════════

describe('ADJUDICATION-17 — buildAgnivasaConventionBVoices (second, non-gating voice)', () => {
  const paddhatiRow = (over: Partial<PaddhatiConventionRow> = {}): PaddhatiConventionRow => ({
    factor_family: 'agnivasa',
    convention_id: 'agnivasa_tithi_element_prithvi',
    school_tag: 'corpus_default',
    constraint_role: 'hard',
    convention_status: 'computed',
    provenance: 'L1 ga_panchanga / panchang_engine AGNI_VASA_TABLE (shipped)',
    corpus_gap_ref: null,
    native_confirmed: false,
    awaiting_native_confirmation: true,
    version: 'paddhati_v02',
    ...over,
  })

  const conventionBRow = (over: Partial<PaddhatiConventionRow> = {}): PaddhatiConventionRow =>
    paddhatiRow({
      convention_id: 'agnivasa_muhurta_chintamani_arithmetic',
      school_tag: 'muhurta_chintamani',
      native_confirmed: false,
      awaiting_native_confirmation: false,
      ...over,
    })

  const latticeRow = (detail: Record<string, unknown>) => ({
    factor_family: 'agnivasa',
    factor_key: 'agnivasa_prithvi',
    start_utc: '2026-08-05T00:00:00.000Z',
    end_utc: '2026-08-06T00:00:00.000Z',
    detail,
    source_citation: 'bg_muhurta_lattice',
    corpus_status: 'computed_cited' as const,
  })

  it('Convention B NOT operative (only Convention A row present) → returns [] (honest, chart-level gap already carried elsewhere)', () => {
    const voices = buildAgnivasaConventionBVoices(
      [latticeRow({ tithi_id: 1, vara_id: 3, element: 'prithvi' })],
      [paddhatiRow()],
    )
    expect(voices).toEqual([])
  })

  it('Convention B declared_not_computed never even reaches this function (rail 2) — fetchPaddhatiProfile\'s own `operative` filter excludes it upstream, so passing only the surviving rows still yields []', () => {
    // `PaddhatiResolution.operative` is documented as "ONLY convention_status='computed'
    // rows" (fetchPaddhatiProfile filters `scoped.filter((r) => r.convention_status ===
    // 'computed')` before this function ever sees it) — a declared_not_computed Convention
    // (B) row is structurally absent from `paddhatiOperative` by the time it gets here.
    const voices = buildAgnivasaConventionBVoices(
      [latticeRow({ tithi_id: 1, vara_id: 3, element: 'prithvi' })],
      [paddhatiRow()], // Convention B's row was declared_not_computed and so never made it into `operative`
    )
    expect(voices).toEqual([])
  })

  it('no matched atoms → [] regardless of Convention B operative status (nothing to voice an opinion about)', () => {
    expect(buildAgnivasaConventionBVoices([], [paddhatiRow(), conventionBRow()])).toEqual([])
  })

  it('Convention B operative, one matched atom → one voice, computed live from the SAME atom, never overriding Convention A', () => {
    // ADJUDICATION-17's own checkable counter-example: tithi_id=1, vara_id=3 (Tuesday).
    // Convention A: tithi 1-7 band = Pṛthvī/favourable. Convention B: (1+1+3) mod 4 = 1 = Ākāśa/unfavourable.
    const voices = buildAgnivasaConventionBVoices(
      [latticeRow({ tithi_id: 1, vara_id: 3, element: 'prithvi' })],
      [paddhatiRow(), conventionBRow()],
    )
    expect(voices).toHaveLength(1)
    expect(voices[0]!.state).toBe('computed')
    expect(voices[0]!.tithi_id).toBe(1)
    expect(voices[0]!.vara_id).toBe(3)
    expect(voices[0]!.element).toBe('akasha')
    expect(voices[0]!.favourable).toBe(false)
    expect(voices[0]!.convention_a_element).toBe('prithvi')
    expect(voices[0]!.convention_a_favourable).toBe(true)
    // The decisive assertion: Convention B DIVERGES but this is disclosure, not override.
    expect(voices[0]!.agreement).toBe('diverges')
    expect(voices[0]!.claim).toContain('DIVERGING')
    expect(voices[0]!.claim).toContain('Convention (A) remains the native-confirmed, operative reading')
  })

  it('Convention B operative, an agreeing atom → agreement: "agrees", disclosed the same way', () => {
    // tithi_id=1, vara_id=2 (Monday): (1+1+2) mod 4 = 0 = Pṛthvī/favourable — agrees with A.
    const voices = buildAgnivasaConventionBVoices(
      [latticeRow({ tithi_id: 1, vara_id: 2, element: 'prithvi' })],
      [paddhatiRow(), conventionBRow()],
    )
    expect(voices).toHaveLength(1)
    expect(voices[0]!.agreement).toBe('agrees')
    expect(voices[0]!.favourable).toBe(true)
  })

  it('multiple matched atoms → one voice PER atom, in the same order, each independently comparable', () => {
    const voices = buildAgnivasaConventionBVoices(
      [
        latticeRow({ tithi_id: 1, vara_id: 3, element: 'prithvi' }), // diverges
        latticeRow({ tithi_id: 1, vara_id: 2, element: 'prithvi' }), // agrees
      ],
      [paddhatiRow(), conventionBRow()],
    )
    expect(voices).toHaveLength(2)
    expect(voices[0]!.agreement).toBe('diverges')
    expect(voices[1]!.agreement).toBe('agrees')
  })

  it('a matched atom missing tithi_id/vara_id → honest_empty for THAT atom, never a fabricated verdict (B.10)', () => {
    const voices = buildAgnivasaConventionBVoices(
      [latticeRow({ element: 'prithvi' })],
      [paddhatiRow(), conventionBRow()],
    )
    expect(voices).toHaveLength(1)
    expect(voices[0]!.state).toBe('honest_empty')
    expect(voices[0]!.empty_reason).toContain('tithi_id/vara_id')
  })

  it('the residence branch NEVER changes its own hard-gate hardcode — source-level proof this stays a second voice, not a replacement', () => {
    const src = readFileSync(fileURLToPath(new URL('./kala_sky_pattern.ts', import.meta.url)), 'utf8')
    // Convention A's hard-gate match is UNCHANGED — ADJUDICATION-17 forbids touching it.
    expect(src).toMatch(/const favourableElements = \['prithvi'\]/)
    // The new voice IS wired into the residence branch (this is the actual live-flip).
    expect(src).toMatch(/buildAgnivasaConventionBVoices\(/)
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
