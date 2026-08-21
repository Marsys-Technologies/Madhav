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
 * Pure module-level data check — no DB required.
 */
import { describe, it, expect } from 'vitest'
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
