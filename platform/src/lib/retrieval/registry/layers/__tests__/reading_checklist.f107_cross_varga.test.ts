/**
 * F-107 (PARIŚEṢA-V4, CL-20) — the domain→varga registry and the cross-varga gap it exposes.
 * ==========================================================================================
 * `judgment_query` weights exactly ONE operative varga per domain (SHASTRA_MAP.varga is a
 * `string`, not `string[]`). Wealth classically carries two — D2 Horā for dhana (accumulated
 * wealth) and D11 Rudrāṃśa/Ekādaśāṃśa for lābha (gains/income) — plus Indu Lagna, the Jaimini
 * wealth-strength lagna, which is computed two_pass_verified for every built chart.
 *
 * That narrower scope is defensible. Shipping it WITHOUT disclosure was the defect: a caller
 * asking for D1+D2+D11+Indu convergence got a D1+D2 verdict with no field naming the missing
 * legs. These tests lock the registry that drives the disclosure.
 *
 * They deliberately do NOT assert that any cross-varga convergence is computed — it is not,
 * anywhere, and per CLAUDE.md §N.8 the honest state is a stated gap, not a green flag.
 */
import { describe, it, expect } from 'vitest'
import {
  DOMAIN_DIRECT_VARGAS,
  DOMAIN_INDU_LAGNA,
  corroboratingVargasNotWeighted,
} from '../reading_checklist'
import { SHASTRA_MAP } from '../register_d9_judgment'

describe('F-107 — domain→classical-varga registry', () => {
  it('is a SINGLE definition: register_d8 re-exports it rather than keeping a second copy', async () => {
    // GA.1 / CLAUDE.md §B.8 — two registries that can disagree is the failure mode.
    const d8 = await import('../register_d8_assess_domain')
    expect(d8.DOMAIN_DIRECT_VARGAS).toBe(DOMAIN_DIRECT_VARGAS)
    expect(d8.DOMAIN_INDU_LAGNA).toBe(DOMAIN_INDU_LAGNA)
  })

  it('wealth carries BOTH classical wealth vargas — D2 (dhana) and D11 (lābha)', () => {
    expect(DOMAIN_DIRECT_VARGAS['wealth']).toEqual(['D2', 'D11'])
  })

  it('wealth is the domain with a dedicated special-lagna (Indu) leg', () => {
    expect(DOMAIN_INDU_LAGNA.has('wealth')).toBe(true)
    expect(DOMAIN_INDU_LAGNA.has('career')).toBe(false)
  })

  it("judgment_query's operative varga for wealth is D2 — so D11 is the unweighted remainder", () => {
    // The asymmetry F-107 is about, asserted directly rather than described in a comment.
    expect(SHASTRA_MAP['wealth']?.varga).toBe('D2')
    expect(corroboratingVargasNotWeighted('wealth', 'D2')).toEqual(['D11'])
  })

  it('reports NO remainder for domains whose operative varga already covers their whole set', () => {
    expect(corroboratingVargasNotWeighted('career', 'D10')).toEqual([])
    expect(corroboratingVargasNotWeighted('relationship', 'D9')).toEqual([])
    expect(corroboratingVargasNotWeighted('health', 'D6')).toEqual([])
  })

  it('reports no remainder for an unmapped domain rather than throwing', () => {
    expect(corroboratingVargasNotWeighted('spirituality', 'D20')).toEqual([])
    expect(corroboratingVargasNotWeighted('nonexistent-domain', 'D1')).toEqual([])
  })

  it('every registry key is a real SHASTRA_MAP signal_domain (no orphaned entry)', () => {
    const signalDomains = new Set(Object.values(SHASTRA_MAP).map(s => s.signal_domain))
    for (const domain of Object.keys(DOMAIN_DIRECT_VARGAS)) {
      expect(signalDomains.has(domain), `${domain} is not any SHASTRA_MAP signal_domain`).toBe(true)
    }
    for (const domain of DOMAIN_INDU_LAGNA) {
      expect(signalDomains.has(domain), `${domain} is not any SHASTRA_MAP signal_domain`).toBe(true)
    }
  })

  it('the wealth aliases resolve to the same signal_domain, so `finance` gets the disclosure too', () => {
    // Keying the disclosure off signal_domain (not the raw domain arg) is what makes
    // judgment_query(domain='finance') disclose the D11 gap as well as domain='wealth'.
    expect(SHASTRA_MAP['finance']?.signal_domain).toBe('wealth')
    expect(corroboratingVargasNotWeighted(SHASTRA_MAP['finance']!.signal_domain, SHASTRA_MAP['finance']!.varga))
      .toEqual(['D11'])
  })
})

describe('F-107 — the flag code is registered in the closed envelope vocabulary', () => {
  it('cross_varga_convergence_not_computed is emittable', async () => {
    const { judgmentFlag } = await import('../../../envelope')
    const flag = judgmentFlag('cross_varga_convergence_not_computed', 'detail')
    expect(flag).toBeDefined()
  })
})
