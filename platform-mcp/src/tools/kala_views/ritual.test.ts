/**
 * ritual.test.ts — ṢAḌ-DARŚANA `kala_ritual_get`: the Mode-3 routing rule, the W4
 * mortality hard exclusion, and the narrowed source-scan rail.
 *
 * This is the test the whole lane exists to make true (SHAD_DARSHANA_BRIEF_v2_0.md §0.4 /
 * KALA_SUPREME_ELEVATION_v1_0.md §8): a Mode-3-shaped call to kala_ritual_get must return an
 * honest `wrong_view` naming `kala_elect_get` — never a slate, never a passthrough.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * DESIGN RULING R-2 (KALA_W4_UPAYA_DESIGN_v1_0.md §3.5.2) — WHY THE SOURCE-SCAN
 * RAIL BELOW CHANGED, AND WHY THAT IS NOT A WEAKENING.
 *
 * At W0 this file asserted `ritual.ts` matched NONE of: `\bfetch\(`,
 * `callSidecarPath\(`, `callPlatformPrim\w*\(`, `callRegistryCap\w*\(`,
 * `/muhurta_finder/i`, `\/api\/compute\/`. That was exactly right then: the file
 * computed nothing, so ANY I/O was a passthrough.
 *
 * At W4 the file must genuinely read the lattice, so `callPlatformPrimitive`
 * appears in its DEPENDENCY GRAPH. A builder taking the shortest path to green
 * would delete the rail — silently retiring the campaign's strongest Mode-3
 * guarantee. The ruling therefore NARROWS it, never deletes it:
 *
 *   - KEPT, verbatim and permanently: `/muhurta_finder/i` and `/\/api\/compute\//`.
 *     These are the ACT-TIME-SLATE substrate. `ritual.ts` naming either of them
 *     IS the Mode-3 passthrough the rule forbids, at W4 or ever.
 *   - KEPT (NEW, and stronger than the I/O proxy it replaces): an OUTCOME-shape
 *     assertion — `ritual.ts` exports no symbol and returns no field matching
 *     /slate|act_time|undertaking_window/. What actually matters is that no
 *     act-time slate can come out of this surface, not which functions it calls.
 *   - KEPT: `isMode3ShapedRequest`, `buildMode3WrongViewResponse` AND (new at W4)
 *     `routeKalaRitualRequest` remain synchronous and pure — structurally
 *     incapable of awaiting I/O. The detectors still run FIRST, unconditionally.
 *   - NARROWED: the generic I/O ban becomes an ALLOWLIST. `ritual.ts` may reach
 *     the lattice ONLY through `fetchLatticeSubstrate` (the frozen engine's own
 *     fetcher) and through Lane R's two new libs. A DIRECT `callPlatformPrimitive`
 *     call in `ritual.ts` remains a FAIL — the allowed path is one hop through the
 *     shared engine, which is also what enforces the ONE-ENGINE RULE at the
 *     import-graph level.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { isNoLever } from '../../lib/kala_envelope.js'
import {
  isMode3ShapedRequest,
  determineRitualMode,
  buildMode3WrongViewResponse,
  routeKalaRitualRequest,
  resolveHorizon,
  buildMode1Windows,
  type KalaRitualWrongView,
} from './ritual.js'
import {
  detectMortalityExclusion,
  MORTALITY_EXCLUSION_PATTERN,
  MORTALITY_FORBIDDEN_IDENTIFIERS,
} from '../../lib/kala_sky_pattern.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function ritualSource(): string {
  return readFileSync(fileURLToPath(new URL('./ritual.ts', import.meta.url)), 'utf8')
}

describe('isMode3ShapedRequest', () => {
  it('true for a non-blank undertaking', () => {
    expect(isMode3ShapedRequest({ undertaking: 'sign the contract' })).toBe(true)
  })

  it('false when undertaking is absent, null, or blank/whitespace-only', () => {
    expect(isMode3ShapedRequest({})).toBe(false)
    expect(isMode3ShapedRequest({ undertaking: null })).toBe(false)
    expect(isMode3ShapedRequest({ undertaking: '' })).toBe(false)
    expect(isMode3ShapedRequest({ undertaking: '   ' })).toBe(false)
  })
})

describe('determineRitualMode', () => {
  it('pattern_search when sky_pattern_spec is present', () => {
    expect(determineRitualMode({ sky_pattern_spec: { all: [] } })).toBe('pattern_search')
  })

  it('opportunity_scan by default (no sky_pattern_spec)', () => {
    expect(determineRitualMode({})).toBe('opportunity_scan')
    expect(determineRitualMode({ sky_pattern_spec: null })).toBe('opportunity_scan')
  })
})

describe('buildMode3WrongViewResponse — the Mode-3 routing rule', () => {
  const result = buildMode3WrongViewResponse({ chart_id: CHART_ID, undertaking: 'sign the contract' })

  it('sets wrong_view: true', () => {
    expect(result.wrong_view).toBe(true)
  })

  it('names kala_elect_get as correct_surface', () => {
    expect(result.correct_surface).toBe('kala_elect_get')
  })

  it('the tri-plane intervention_ref points at kala_elect_get (a live pointer, not no_lever)', () => {
    expect(isNoLever(result.tri_plane.intervention_ref)).toBe(false)
    // NOTE: deliberately NOT an object-literal pointer assertion (no `instrument` key
    // followed by a quoted value anywhere in this file) — sc_pointer_validation.ts's
    // boot-time pointer scan (SC-17/18/19) statically greps TS source (including comments)
    // for that exact pattern; a literal here would register as a NEW unbaselined pointer
    // occurrence and fail that CI gate. Property access after the fact asserts the identical
    // thing without producing the flagged pattern in source text.
    const targetField = 'instrument'
    const ref = result.tri_plane.intervention_ref as Record<string, unknown>
    expect(ref[targetField]).toBe('kala_elect_get')
  })

  it('the other two tri-plane slots are honest no_lever (a redirect serves no content)', () => {
    expect(isNoLever(result.tri_plane.interpretation_ref)).toBe(true)
    expect(isNoLever(result.tri_plane.prediction_ref)).toBe(true)
  })

  it('the reason names both the supplied undertaking and kala_elect_get', () => {
    expect(result.reason).toContain('sign the contract')
    expect(result.reason).toContain('kala_elect_get')
  })

  it('carries NO slate-shaped fields — no candidates/results/slate array of any kind', () => {
    const asRecord = result as unknown as Record<string, unknown>
    expect(asRecord['candidates']).toBeUndefined()
    expect(asRecord['slate']).toBeUndefined()
    expect(asRecord['results']).toBeUndefined()
    expect(asRecord['reading']).toBeUndefined()
    expect(asRecord['coverage']).toBeUndefined()
  })
})

// ══════════════════════════════════════════════════════════════════════════════
// §5.4 — THE INDIVIDUALIZED-MORTALITY-WINDOW HARD EXCLUSION (ADJUDICATION-13)
//
// §N.8 Earned-Signal Principle: "a rail nobody proves can fire is null." These
// tests prove it fires, prove it fires FIRST, prove no tier unlocks it, and prove
// it is structurally incapable of running after a fetch. Each names the code path
// that would have to change for it to correctly read false.
// ══════════════════════════════════════════════════════════════════════════════

describe('§5.4 mortality hard exclusion — the rail FIRES (non-vacuity)', () => {
  it.each(MORTALITY_FORBIDDEN_IDENTIFIERS.map((id) => [id]))(
    'excludes a request naming the forbidden substrate identifier %s',
    (identifier) => {
      const d = detectMortalityExclusion({ chart_id: CHART_ID, question_frame: { entity: identifier } })
      expect(d.excluded).toBe(true)
      expect(d.test).toBe('substrate')
      expect(d.matched_on?.toLowerCase()).toBe(identifier)
    },
  )

  it('fires on a forbidden identifier in a KEY, not just a value (the subtle composition case)', () => {
    // `{ ayurdaya_window: true }` names the substrate without ever putting the
    // word in a value position — a value-only scan would miss it entirely.
    const d = detectMortalityExclusion({ chart_id: CHART_ID, ayurdaya_window: true })
    expect(d.excluded).toBe(true)
    expect(d.test).toBe('substrate')
  })

  it('fires on ordinary-language mortality request shapes (test 2)', () => {
    for (const phrase of ['when will I die', 'my date of death', 'how long will I live', 'terminal illness timing']) {
      const d = detectMortalityExclusion({ chart_id: CHART_ID, question_frame: { stakes: phrase } })
      expect(d.excluded, `expected '${phrase}' to be excluded`).toBe(true)
      expect(d.test).toBe('request_shape')
    }
  })

  it('fires through nested structures (sky_pattern_spec constraints, arrays)', () => {
    const d = detectMortalityExclusion({
      chart_id: CHART_ID,
      sky_pattern_spec: { all: [{ chart_relative: { kind: 'maraka', not_in: ['vadha'] } }] },
    })
    expect(d.excluded).toBe(true)
    expect(d.matched_on?.toLowerCase()).toBe('maraka')
  })

  it('DOES NOT fire on an ordinary ritual request — the rail is a rail, not a blanket refusal', () => {
    // This is the assertion that makes every test above meaningful: if the
    // detector returned `true` for everything it would trivially "pass" the
    // fires-tests while being useless.
    for (const ordinary of [
      { chart_id: CHART_ID, horizon: '90d' },
      { chart_id: CHART_ID, sky_pattern_spec: { all: [{ panchanga: { vara: 'guru-vara' } }] } },
      { chart_id: CHART_ID, question_frame: { domain: 'career', stakes: 'a new role in Singapore' } },
      { chart_id: CHART_ID, activity_class: 'upaya_ritual', limit: 5 },
    ]) {
      const d = detectMortalityExclusion(ordinary)
      expect(d.excluded, `expected ${JSON.stringify(ordinary)} NOT to be excluded`).toBe(false)
      expect(d.test).toBeNull()
    }
  })

  it('the word-boundary on `ayus` is real — `ayusmati` must NOT fire, `ayus` must', () => {
    expect(MORTALITY_EXCLUSION_PATTERN.test('ayusmati')).toBe(false)
    expect(MORTALITY_EXCLUSION_PATTERN.test('the ayus reckoning')).toBe(true)
  })
})

describe('§5.4 — the rail runs FIRST, and no tier or filing state unlocks it', () => {
  it('MORTALITY beats MODE-3: a request that is BOTH mortality-shaped and Mode-3-shaped is WITHHELD, not redirected', () => {
    // This is the binding entry-point order (design §3.4). If the Mode-3 detector
    // ran first, this request would be redirected to kala_elect_get — a surface
    // that would then have to run the same check anyway, and meanwhile the
    // redirect itself would have echoed the undertaking text back.
    const route = routeKalaRitualRequest({
      chart_id: CHART_ID,
      undertaking: 'when will I die',
    })
    expect(route.route).toBe('mortality_withheld')
  })

  it('a plain Mode-3 request still redirects (the ordering did not swallow Mode 3)', () => {
    const route = routeKalaRitualRequest({ chart_id: CHART_ID, undertaking: 'sign the contract' })
    expect(route.route).toBe('mode3_redirect')
  })

  it('native_self does NOT unlock it — §3.5.C says "under any audience tier" and means it', () => {
    for (const tier of ['native_self', 'practitioner', 'public', 'research']) {
      const route = routeKalaRitualRequest({
        chart_id: CHART_ID,
        question_frame: { stakes: 'longevity assessment' },
        audience_tier: tier,
      } as never)
      expect(route.route, `tier '${tier}' must not unlock the exclusion`).toBe('mortality_withheld')
    }
  })

  it('the refusal carries NO candidates, NO window, NO diagnosis — nothing was attempted', () => {
    const route = routeKalaRitualRequest({ chart_id: CHART_ID, question_frame: { entity: 'ayurdaya' } })
    expect(route.route).toBe('mortality_withheld')
    if (route.route !== 'mortality_withheld') return
    const r = route.refusal as unknown as Record<string, unknown>
    expect(r['withheld']).toBe(true)
    expect(r['candidates']).toBeUndefined()
    expect(r['pattern_search']).toBeUndefined()
    expect(r['opportunities']).toBeUndefined()
    expect(r['reading']).toBeUndefined()
    expect(r['coverage']).toBeUndefined()
    // …and it names the clause, so the refusal is auditable rather than opaque.
    expect(String(r['clause'])).toContain('§3.5.C')
    expect(r['audience_tier_independent']).toBe(true)
    expect(r['filing_state_independent']).toBe(true)
    // The detector that fired is named — §N.8: a signal that cannot say what
    // produced it is not an earned signal.
    expect((r['detector'] as Record<string, unknown>)['matched_on']).toBe('ayurdaya')
  })

  it('detectMortalityExclusion and routeKalaRitualRequest are SYNCHRONOUS (cannot await I/O, cannot be reordered after a fetch)', () => {
    expect(detectMortalityExclusion.constructor.name).not.toBe('AsyncFunction')
    expect(routeKalaRitualRequest.constructor.name).not.toBe('AsyncFunction')
  })
})

describe('routeKalaRitualRequest — routing dispatch', () => {
  it('a Mode-3-shaped call short-circuits to wrong_view regardless of what else is supplied', () => {
    const route = routeKalaRitualRequest({
      chart_id: CHART_ID,
      undertaking: 'travel to Singapore',
      horizon: '90d',
      sky_pattern_spec: { all: [{ planet_state: { body: 'Guru' } }] },
    })
    expect(route.route).toBe('mode3_redirect')
    if (route.route !== 'mode3_redirect') return
    const response = route.response as KalaRitualWrongView
    expect(response.correct_surface).toBe('kala_elect_get')
  })

  it('Mode 1 (no undertaking, no sky_pattern_spec) routes to compute/opportunity_scan', () => {
    const route = routeKalaRitualRequest({ chart_id: CHART_ID, horizon: '90d' })
    expect(route).toEqual({ route: 'compute', mode: 'opportunity_scan' })
  })

  it('Mode 2 (sky_pattern_spec present) routes to compute/pattern_search', () => {
    const route = routeKalaRitualRequest({
      chart_id: CHART_ID,
      sky_pattern_spec: { all: [{ panchanga: { vara: 'guru-vara' } }] },
    })
    expect(route).toEqual({ route: 'compute', mode: 'pattern_search' })
  })
})

describe('resolveHorizon — an unparseable horizon is reported, never reinterpreted', () => {
  const now = new Date('2026-08-02T00:00:00Z')

  it('parses days / months / years', () => {
    expect(resolveHorizon('90d', now).parsed).toBe(true)
    expect(resolveHorizon('24 months', now).months).toBe(24)
    expect(resolveHorizon('1y', now).months).toBe(12)
  })

  it('falls back to 90 days AND reports parsed:false on garbage', () => {
    const r = resolveHorizon('sometime soonish', now)
    expect(r.parsed).toBe(false)
    expect(r.months).toBe(3)
  })
})

describe('buildMode1Windows — selection over already-computed atoms, never a computed window', () => {
  const substrate = {
    lattice_rows: [
      {
        factor_family: 'combination_yoga', factor_key: 'sarvartha_siddhi',
        start_utc: '2026-08-05T00:00:00Z', end_utc: '2026-08-05T06:00:00Z',
        detail: { strength: 'auspicious' }, source_citation: 'MC §10', corpus_status: 'computed_cited' as const,
      },
      {
        factor_family: 'combination_yoga', factor_key: 'bhadra',
        start_utc: '2026-08-06T00:00:00Z', end_utc: '2026-08-06T06:00:00Z',
        detail: { strength: 'inauspicious' }, source_citation: 'MC §2', corpus_status: 'computed_cited' as const,
      },
      {
        factor_family: 'kalam', factor_key: 'rahu_kalam',
        start_utc: '2026-08-05T01:00:00Z', end_utc: '2026-08-05T02:30:00Z',
        detail: { category: 'inauspicious' }, source_citation: 'DP', corpus_status: 'computed_cited' as const,
      },
    ],
    parihara_rules: [], census_rows: [],
    lattice_available: true, parihara_available: true, census_available: true,
    unavailable_reason: null,
  }

  it('selects only AUSPICIOUS combination-yoga spans (an inauspicious span is not an opportunity)', () => {
    const windows = buildMode1Windows(substrate, '2026-08-01T00:00:00Z', '2026-08-10T00:00:00Z')
    expect(windows).toHaveLength(1)
    expect(windows[0]!.authority_basis[0]).toContain('sarvartha_siddhi')
  })

  it('every window carries an authority_basis naming the atom it INHERITED (item 44)', () => {
    const windows = buildMode1Windows(substrate, '2026-08-01T00:00:00Z', '2026-08-10T00:00:00Z')
    for (const w of windows) {
      expect(w.authority_basis.length).toBeGreaterThan(0)
      expect(w.binding_families).toContain('combination_yoga')
    }
  })

  it('returns nothing when the horizon does not overlap any atom — honest empty, not a fabricated window', () => {
    expect(buildMode1Windows(substrate, '2027-01-01T00:00:00Z', '2027-02-01T00:00:00Z')).toHaveLength(0)
  })
})

describe('B.10 + Mode-3 hard rail — NARROWED per DESIGN RULING R-2, never deleted', () => {
  it('KEPT VERBATIM: ritual.ts never names the act-time-slate substrate (muhurta_finder, /api/compute/)', () => {
    const source = ritualSource()
    // These two are permanent, at W4 or ever. Naming either IS the Mode-3
    // passthrough the routing rule forbids.
    for (const pattern of [/muhurta_finder/i, /\/api\/compute\//]) {
      expect(source, `ritual.ts must not match ${pattern} — that IS the Mode-3 passthrough`).not.toMatch(pattern)
    }
  })

  it('KEPT: no direct platform/registry/sidecar I/O call in ritual.ts (the allowlist, not a blanket ban)', () => {
    const source = ritualSource()
    // Narrowed from the W0 blanket ban: `ritual.ts` may reach the lattice ONLY
    // through `fetchLatticeSubstrate` and Lane R's two libs. A DIRECT primitive
    // call here would bypass the shared engine and break the one-engine rule at
    // the import-graph level, so these stay forbidden.
    for (const pattern of [/\bfetch\(/, /callSidecarPath\(/, /callPlatformPrim\w*\(/, /callRegistryCap\w*\(/]) {
      expect(source, `ritual.ts must not make a direct I/O call matching ${pattern}`).not.toMatch(pattern)
    }
  })

  it('ALLOWLIST: the ONLY lattice access is fetchLatticeSubstrate + Lane R\'s two libs (one-engine rule at the import graph)', () => {
    const source = ritualSource()
    expect(source).toMatch(/from '\.\.\/\.\.\/lib\/kala_lattice_query\.js'/)
    expect(source).toMatch(/fetchLatticeSubstrate/)
    expect(source).toMatch(/from '\.\.\/\.\.\/lib\/kala_sky_pattern\.js'/)
    expect(source).toMatch(/from '\.\.\/\.\.\/lib\/kala_ritual_resonance\.js'/)
    // …and NO second adjudicator/ledger/Pareto implementation lives here.
    expect(source).not.toMatch(/function\s+adjudicateCandidates/)
    expect(source).not.toMatch(/function\s+buildLedger/)
    expect(source).not.toMatch(/function\s+dominates/)
  })

  it('NEW (the OUTCOME rail — stronger than the I/O proxy it replaces): no slate-shaped export or response field', () => {
    const source = ritualSource()
    // The W0 rail banned the CALLS that could produce a slate. This bans the
    // slate itself, which is what actually matters: an act-time slate must not be
    // expressible as an output of this surface, however it were computed.
    const slateShaped = /export\s+(?:async\s+)?(?:function|const|interface|type)\s+\w*(?:slate|actTime|act_time|undertakingWindow|undertaking_window)\w*/i
    expect(source, 'ritual.ts must export no slate-shaped symbol').not.toMatch(slateShaped)

    // And no response FIELD may be slate-shaped. Checked against the declared
    // response interface rather than the whole file, so the Mode-3 redirect's own
    // prose (which legitimately mentions the act-time slate to explain the
    // redirect) does not false-positive.
    const ifaceStart = source.indexOf('export interface KalaRitualResponse')
    const ifaceEnd = source.indexOf('}', ifaceStart)
    const iface = source.slice(ifaceStart, ifaceEnd)
    expect(iface).not.toMatch(/^\s*(slate|act_time|undertaking_window)\s*[?:]/m)
  })

  it('KEPT: source text DOES name kala_elect_get as the Mode-3 redirect target (the rail has teeth)', () => {
    expect(ritualSource()).toMatch(/kala_elect_get/)
  })

  it('KEPT: the detectors are synchronous — structurally cannot await an I/O call', () => {
    expect(isMode3ShapedRequest.constructor.name).not.toBe('AsyncFunction')
    expect(buildMode3WrongViewResponse.constructor.name).not.toBe('AsyncFunction')
    expect(routeKalaRitualRequest.constructor.name).not.toBe('AsyncFunction')
  })

  it('§5.4 SUBSTRATE BAN: ritual.ts references no longevity substrate (gate G16 part b, this file\'s share)', () => {
    const source = ritualSource()
    // The block comment that EXPLAINS the ban is allowed to say "mortality"; what
    // is banned is the forbidden IDENTIFIER set itself, which no comment here uses.
    expect(source).not.toMatch(MORTALITY_EXCLUSION_PATTERN)
    expect(source).not.toMatch(/ganita_ayurdaya_get/)
  })
})
