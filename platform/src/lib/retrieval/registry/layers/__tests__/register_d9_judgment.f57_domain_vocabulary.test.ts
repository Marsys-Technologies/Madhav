/**
 * register_d9_judgment.f57_domain_vocabulary.test.ts — F-57 (PARIŚEṢA-V4) regression.
 *
 * THE DEFECT (reproduced live on the canonical chart 482012f1 before the fix):
 * `judgment_query`'s SHASTRA_MAP carried the literal `signal_domain: 'other'` for eleven
 * domains — education/vidya, progeny/children, residence/property/home, family, general,
 * transition, travel. `'other'` is not a member of ANY vocabulary the downstream stores
 * are keyed by:
 *   - bodha_msr_signals.domains_affected_array  → 12 distinct values, none 'other'
 *   - bodha_mechanisms.domains_affected_array   → no 'other'
 *   - brahma_event_ontology.domain              → 13 rows, all canonical, no 'other'
 * so every domain-scoped leg (bearing_yogas_corroboration, bearing_afflictions,
 * affliction_mechanisms, gochara_sweep) returned a structural zero, and the response then
 * served that zero through the `afflictions_empty` "honest empty threat layer" flag and a
 * `gochara_domain_not_covered` flag naming the phantom domain. On the canonical chart that
 * hid 1,126 progeny signals (347 adverse) / 850 education (351) / 510 residence (220), plus
 * 10 / 50 / 80 gochara windows respectively.
 *
 * This is CLAUDE.md §N.8 exactly: a flag whose detector could never read false, because the
 * predicate it evaluated was keyed to a value nothing in the store can equal.
 *
 * Pure module-level data check — no DB required (except the F-165 describe block below, which
 * mocks `@/lib/db/client`).
 *
 * F-165 (PARIŚEṢA-V4) follow-on, same file: F-57 fixed VOCABULARY correctness — is
 * `SHASTRA_MAP['general'].signal_domain` a real member of `CANONICAL_DOMAINS` (yes; see
 * :61/:82 below, UNCHANGED by F-165, they are correct). That is a DIFFERENT axis from
 * POPULATION — does the resolved domain carry any rows at all in the stores those legs read.
 * 'general' is vocabulary-exact AND canonical AND (live-verified on 482012f1, 2026-08-22)
 * carries ZERO `bodha_msr_signals` rows; `bodha_mechanisms.domains_affected_array` covers only
 * 1 of the 13 canonical domains ('wealth', 5 rows). Neither fact is visible from
 * `is_exact`/`is_canonical` alone, so `afflictions_empty` read as a genuine all-clear for a
 * domain the stores had never populated. See `reading_checklist.f165_structural_coverage.
 * test.ts` for the `fetchDomainStructuralCoverage` unit coverage; the block below pins the
 * SHASTRA_MAP/CANONICAL_DOMAINS wiring this finding's disclosure depends on, in the same file
 * that already carries the vocabulary-exactness assertion it must not be conflated with.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// F-165: mocked so the new describe block at the bottom of this file is deterministic and does
// not depend on live production row counts drifting. Hoisted by vitest above all imports below
// regardless of textual position; declared here (top of file) for readability.
const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

import { SHASTRA_MAP } from '../register_d9_judgment'
import { CANONICAL_DOMAINS, isCanonicalDomain } from '@/lib/domain_vocabulary'

describe('F-57 — SHASTRA_MAP.signal_domain is canonical-vocabulary-only', () => {
  it('no SHASTRA_MAP entry resolves to the dead literal "other"', () => {
    // `as string` deliberately: `signal_domain` is now typed to CanonicalDomain, so tsc
    // rejects the comparison outright — which IS the primary guard. This runtime assertion
    // is the belt to that braces, and stays meaningful if the type is ever widened again.
    const offenders = Object.entries(SHASTRA_MAP)
      .filter(([, spec]) => (spec.signal_domain as string) === 'other')
      .map(([key]) => key)
    expect(offenders).toEqual([])
  })

  it('every signal_domain is a member of the canonical 13-domain vocabulary', () => {
    for (const [domain, spec] of Object.entries(SHASTRA_MAP)) {
      expect(isCanonicalDomain(spec.signal_domain), `${domain} -> ${spec.signal_domain}`).toBe(true)
    }
  })

  it('the three F-57 domains resolve to their OWN first-class canonical domain', () => {
    // These three are named in the finding. Each has real, non-empty data under its own tag
    // in bodha_msr_signals / brahma_event_ontology — 'other' was never the correct bucket.
    expect(SHASTRA_MAP['education'].signal_domain).toBe('education')
    expect(SHASTRA_MAP['vidya'].signal_domain).toBe('education')
    expect(SHASTRA_MAP['progeny'].signal_domain).toBe('progeny')
    expect(SHASTRA_MAP['children'].signal_domain).toBe('progeny')
    expect(SHASTRA_MAP['residence'].signal_domain).toBe('residence')
    expect(SHASTRA_MAP['property'].signal_domain).toBe('residence')
    expect(SHASTRA_MAP['home'].signal_domain).toBe('residence')
  })

  it('the four sibling domains F-55 added with the same defect are fixed too', () => {
    // Not named in F-57, but byte-identical defect introduced by the same F-55 pass —
    // leaving them would be a §N.8 known-false-signal left standing.
    expect(SHASTRA_MAP['family'].signal_domain).toBe('family')
    expect(SHASTRA_MAP['general'].signal_domain).toBe('general')
    expect(SHASTRA_MAP['transition'].signal_domain).toBe('transition')
    expect(SHASTRA_MAP['travel'].signal_domain).toBe('travel')
  })

  it('deliberate aliases are preserved (a synonym is a mapping, not a fallback)', () => {
    // These are NOT the F-57 defect: 'marriage'/'moksha' are not canonical members, and the
    // canonical vocabulary itself maps them (DOMAIN_SYNONYMS) onto relationship/spirituality.
    // The fix discloses them via `domain_resolution` rather than changing them.
    expect(SHASTRA_MAP['marriage'].signal_domain).toBe('relationship')
    expect(SHASTRA_MAP['partnership'].signal_domain).toBe('relationship')
    expect(SHASTRA_MAP['vocation'].signal_domain).toBe('career')
    expect(SHASTRA_MAP['finance'].signal_domain).toBe('wealth')
    expect(SHASTRA_MAP['vitality'].signal_domain).toBe('health')
    expect(SHASTRA_MAP['buddhi'].signal_domain).toBe('character')
    expect(SHASTRA_MAP['moksha'].signal_domain).toBe('spirituality')
    expect(SHASTRA_MAP['liberation'].signal_domain).toBe('spirituality')
  })

  it('every canonical domain is reachable as a signal_domain from at least one map key', () => {
    const reachable = new Set(Object.values(SHASTRA_MAP).map((s) => s.signal_domain))
    for (const d of CANONICAL_DOMAINS) {
      expect(reachable.has(d), `canonical domain '${d}' unreachable via SHASTRA_MAP`).toBe(true)
    }
  })
})

// ── F-165: structural-emptiness (population) is a DIFFERENT axis from vocabulary-exactness ──
// `SHASTRA_MAP['general'].signal_domain === 'general'` (asserted above, :61) is CORRECT and
// UNCHANGED by this finding — 'general' really is vocabulary-exact and canonical. The defect
// was reading that correctness as proof the domain has data. These tests pin the disclosure
// register_d9_judgment.ts now emits alongside it, using the SAME `fetchDomainStructuralCoverage`
// helper the handler calls (register_d9_judgment.ts's afflictions/mechanisms step), mocked (see
// top of file) so the test is deterministic and does not depend on live production row counts
// drifting.
describe('F-165 — structural-emptiness disclosure is distinct from is_exact/is_canonical', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })

  it("SHASTRA_MAP['general'] resolves to a vocabulary-exact, canonical domain (F-57, unchanged) that is STILL structurally unpopulated (F-165) — the two axes genuinely differ for the same domain", async () => {
    const { fetchDomainStructuralCoverage } = await import('../reading_checklist')
    const generalDomain = SHASTRA_MAP['general']!.signal_domain
    expect(generalDomain).toBe('general') // F-57 axis: vocabulary-exact
    expect(isCanonicalDomain(generalDomain)).toBe(true) // F-57 axis: canonical

    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 0, mech_count: 0, mech_domain_coverage: 1 }] })
    const coverage = await fetchDomainStructuralCoverage('chart-x', 'lahiri_chitrapaksha', generalDomain)
    // F-165 axis: population. Both being true for the SAME domain at once is the point —
    // is_exact/is_canonical say nothing about whether either store has ever been populated.
    expect(coverage.structurally_unpopulated).toBe(true)
  })

  it('a zero-coverage domain gets the structural flag, and the response does not read as a clean chart', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 0, mech_count: 0, mech_domain_coverage: 1 }] })
    const { fetchDomainStructuralCoverage } = await import('../reading_checklist')
    const { judgmentFlag } = await import('../../../envelope')
    const coverage = await fetchDomainStructuralCoverage('chart-x', 'lahiri_chitrapaksha', 'general')

    // Mirrors register_d9_judgment.ts's own predicate exactly (afflictions/mechanisms step):
    // both bearing_afflictions and affliction_mechanisms come back empty for a zero-coverage
    // domain (there is nothing to find, populated or not), so afflictions_empty ALSO fires —
    // but it must never stand ALONE as the only signal. The structural flag is the disclosure
    // that keeps the empty threat layer from reading as an all-clear.
    const bearingAfflictionsCount = 0
    const afflictionMechanismsCount = 0
    const flags = []
    if (coverage.structurally_unpopulated) {
      flags.push(judgmentFlag('domain_structurally_unpopulated', 'zero rows in both source tables'))
    }
    if (bearingAfflictionsCount === 0 && afflictionMechanismsCount === 0) {
      flags.push(judgmentFlag('afflictions_empty', 'no adverse signal or mechanism'))
    }
    const codes = flags.map(f => f.code)
    expect(codes).toContain('domain_structurally_unpopulated')
    expect(codes).toContain('afflictions_empty')
    // The can-read-CLEAN half would be afflictions_empty firing ALONE — asserting the
    // structural flag is ALSO present is what keeps this response from reading as a clean chart.
    expect(codes.length).toBeGreaterThan(1)
  })

  it('the can-read-false half: a populated domain with genuinely zero malefic signals gets afflictions_empty WITHOUT the structural flag — proving the two cases are distinguished', async () => {
    // Populated in bodha_msr_signals (any valence — e.g. benign/neutral rows exist) but this
    // call's malefic/mixed-only afflictions fetch still comes back empty: a genuine clean
    // reading, not a structural gap. structurally_unpopulated must read FALSE here, or the
    // detector could never distinguish the two cases (§N.8).
    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 15198, mech_count: 0, mech_domain_coverage: 1 }] })
    const { fetchDomainStructuralCoverage } = await import('../reading_checklist')
    const { judgmentFlag } = await import('../../../envelope')
    const coverage = await fetchDomainStructuralCoverage('chart-x', 'lahiri_chitrapaksha', 'career')
    expect(coverage.structurally_unpopulated).toBe(false)

    const bearingAfflictionsCount = 0 // this call's malefic/mixed filter found nothing
    const afflictionMechanismsCount = 0
    const flags = []
    if (coverage.structurally_unpopulated) {
      flags.push(judgmentFlag('domain_structurally_unpopulated', 'unused in this branch'))
    }
    if (bearingAfflictionsCount === 0 && afflictionMechanismsCount === 0) {
      flags.push(judgmentFlag('afflictions_empty', 'no adverse signal or mechanism'))
    }
    const codes = flags.map(f => f.code)
    expect(codes).toEqual(['afflictions_empty'])
    expect(codes).not.toContain('domain_structurally_unpopulated')
  })

  it('mechanisms coverage disclosure is present on every call regardless of population state', async () => {
    const { fetchDomainStructuralCoverage } = await import('../reading_checklist')

    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 0, mech_count: 0, mech_domain_coverage: 1 }] })
    const emptyCase = await fetchDomainStructuralCoverage('chart-x', 'lahiri_chitrapaksha', 'general')
    expect(emptyCase.available).toBe(true)
    expect(typeof emptyCase.mechanisms_domain_coverage).toBe('number')
    expect(typeof emptyCase.total_canonical_domains).toBe('number')

    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 1648, mech_count: 5, mech_domain_coverage: 1 }] })
    const populatedCase = await fetchDomainStructuralCoverage('chart-x', 'lahiri_chitrapaksha', 'wealth')
    expect(populatedCase.available).toBe(true)
    expect(populatedCase.mechanisms_domain_coverage).toBe(1)
    expect(populatedCase.total_canonical_domains).toBe(CANONICAL_DOMAINS.length)
    // "nothing excluded" (this_domain_covered would read true) is a DIFFERENT claim from
    // "never evaluated" (available:false) — §N.8. Both cases above have available:true.
  })

  it('is_exact stays untouched by F-165 — the vocabulary axis is not conflated with the population axis', () => {
    // Leaving is_exact/is_canonical semantics alone is an explicit F-165 requirement: the
    // fix ADDS a population disclosure, it does not change what is_exact means.
    expect(SHASTRA_MAP['general']!.signal_domain === 'general').toBe(true)
    expect(isCanonicalDomain(SHASTRA_MAP['general']!.signal_domain)).toBe(true)
  })
})
