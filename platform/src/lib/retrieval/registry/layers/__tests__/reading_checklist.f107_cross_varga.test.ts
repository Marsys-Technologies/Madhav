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
 *
 * F-164 (GA-5 follow-up on #1419) update: DOMAIN_DIRECT_VARGAS is no longer a hand-copied
 * literal — it is a live read of brahma_vichara_constants.operative_vargas, minus D1. That
 * live read ALSO surfaced that the OLD literal had drifted for all three OTHER domains, not
 * just wealth: career was missing D9, health was missing D9, relationship was missing D7.
 * The "reports NO remainder" test below is therefore rewritten — it was asserting the drift,
 * not the fix.
 */
import { describe, it, expect, vi, beforeAll } from 'vitest'

// F-164: mock the live constants read this registry now performs. Mirrors migration
// 435_ga_vichara.sql's brahma_vichara_constants seed exactly.
const OPERATIVE_VARGAS_FIXTURE = {
  wealth:   { vargas: ['D1', 'D2', 'D9', 'D11'], provisional: false, houses: [2, 11], karaka: 'Jupiter' },
  career:   { vargas: ['D1', 'D10', 'D9'], provisional: true, houses: [10], karaka: 'Saturn' },
  marriage: { vargas: ['D1', 'D9', 'D7'], provisional: true, houses: [7], karaka: 'Venus' },
  health:   { vargas: ['D1', 'D6', 'D9'], provisional: true, houses: [6], karaka: 'Saturn' },
  general:  { vargas: ['D1', 'D9'], provisional: true, houses: [1], karaka: 'Sun' },
}

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import {
  DOMAIN_DIRECT_VARGAS,
  DOMAIN_INDU_LAGNA,
  corroboratingVargasNotWeighted,
  ensureDomainDirectVargasLoaded,
  getOperativeVargaConstants,
} from '../reading_checklist'
import { SHASTRA_MAP } from '../register_d9_judgment'

describe('F-107/F-164 — domain→classical-varga registry (live-read)', () => {
  beforeAll(async () => {
    queryMock.mockImplementation((sql: string) => {
      if (/brahma_vichara_constants/i.test(sql)) {
        return Promise.resolve({ rows: [{ value_jsonb: OPERATIVE_VARGAS_FIXTURE }] })
      }
      return Promise.resolve({ rows: [] })
    })
    await ensureDomainDirectVargasLoaded()
  })

  it('is a SINGLE definition: register_d8 re-exports it rather than keeping a second copy', async () => {
    // GA.1 / CLAUDE.md §B.8 — two registries that can disagree is the failure mode.
    const d8 = await import('../register_d8_assess_domain')
    expect(d8.DOMAIN_DIRECT_VARGAS).toBe(DOMAIN_DIRECT_VARGAS)
    expect(d8.DOMAIN_INDU_LAGNA).toBe(DOMAIN_INDU_LAGNA)
  })

  it('wealth carries its FULL classical varga set minus D1 — D2 (dhana), D9 (rāśi-promise cross-check), D11 (lābha)', () => {
    // F-164: the old literal (['D2','D11']) omitted D9 — the live read closes that gap.
    expect(DOMAIN_DIRECT_VARGAS['wealth']).toEqual(['D2', 'D9', 'D11'])
  })

  it('wealth is the domain with a dedicated special-lagna (Indu) leg', () => {
    expect(DOMAIN_INDU_LAGNA.has('wealth')).toBe(true)
    expect(DOMAIN_INDU_LAGNA.has('career')).toBe(false)
  })

  it("judgment_query's operative varga for wealth is D2 — so D9+D11 are the unweighted remainder", () => {
    // The asymmetry F-107 is about, asserted directly rather than described in a comment.
    expect(SHASTRA_MAP['wealth']?.varga).toBe('D2')
    expect(corroboratingVargasNotWeighted('wealth', 'D2')).toEqual(['D9', 'D11'])
  })

  it('F-164: career/relationship/health ALSO have a real corroborating-varga remainder (D9) — the pre-fix literal silently hid it', () => {
    // Pre-F-164 these all asserted `[]` — that was the drift, not a correct empty set.
    // Live source (minus D1): career=[D10,D9], marriage/relationship=[D9,D7], health=[D6,D9].
    expect(DOMAIN_DIRECT_VARGAS['career']).toEqual(['D10', 'D9'])
    expect(corroboratingVargasNotWeighted('career', 'D10')).toEqual(['D9'])

    expect(DOMAIN_DIRECT_VARGAS['relationship']).toEqual(['D9', 'D7'])
    expect(corroboratingVargasNotWeighted('relationship', 'D9')).toEqual(['D7'])

    expect(DOMAIN_DIRECT_VARGAS['health']).toEqual(['D6', 'D9'])
    expect(corroboratingVargasNotWeighted('health', 'D6')).toEqual(['D9'])
  })

  it('reports no remainder for an unmapped domain rather than throwing', () => {
    expect(corroboratingVargasNotWeighted('spirituality', 'D20')).toEqual([])
    expect(corroboratingVargasNotWeighted('nonexistent-domain', 'D1')).toEqual([])
  })

  it('every registry key is a real SHASTRA_MAP signal_domain (no orphaned entry)', () => {
    // Set<string>, not Set<CanonicalDomain>: this is a runtime membership check against
    // DOMAIN_DIRECT_VARGAS/DOMAIN_INDU_LAGNA's own plain-string keys (F-107's registry
    // predates and is independent of F-57's CanonicalDomain narrowing of
    // SHASTRA_MAP.signal_domain) -- narrowing here would just move the same assertion from
    // a runtime .toBe(true) to a compile-time cast, not make it more honest.
    const signalDomains = new Set<string>(Object.values(SHASTRA_MAP).map(s => s.signal_domain))
    for (const domain of Object.keys(DOMAIN_DIRECT_VARGAS)) {
      expect(signalDomains.has(domain), `${domain} is not any SHASTRA_MAP signal_domain`).toBe(true)
    }
    for (const domain of DOMAIN_INDU_LAGNA) {
      expect(signalDomains.has(domain), `${domain} is not any SHASTRA_MAP signal_domain`).toBe(true)
    }
  })

  it('the wealth aliases resolve to the same signal_domain, so `finance` gets the disclosure too', () => {
    // Keying the disclosure off signal_domain (not the raw domain arg) is what makes
    // judgment_query(domain='finance') disclose the D9/D11 gap as well as domain='wealth'.
    expect(SHASTRA_MAP['finance']?.signal_domain).toBe('wealth')
    expect(corroboratingVargasNotWeighted(SHASTRA_MAP['finance']!.signal_domain, SHASTRA_MAP['finance']!.varga))
      .toEqual(['D9', 'D11'])
  })

  it('domain-key translation: signal_domain "relationship" reads the constants row keyed "marriage"', async () => {
    // The one place SHASTRA_MAP's signal_domain vocabulary and
    // brahma_vichara_constants.operative_vargas' own vocabulary disagree (F-164).
    const constants = await getOperativeVargaConstants()
    expect(constants['marriage']?.vargas).toEqual(['D1', 'D9', 'D7'])
    expect(DOMAIN_DIRECT_VARGAS['relationship']).toEqual(
      constants['marriage']!.vargas.filter(v => v !== 'D1'),
    )
  })
})

describe('F-164 — the ruled parity test: registry-vs-ratification, for every signal_domain the registry serves', () => {
  it.each(['wealth', 'career', 'relationship', 'health'] as const)(
    'DOMAIN_DIRECT_VARGAS[%s] == brahma_vichara_constants.operative_vargas[translated domain].vargas minus D1',
    async (signalDomain) => {
      const constants = await getOperativeVargaConstants()
      const vicharaDomain = signalDomain === 'relationship' ? 'marriage' : signalDomain
      const entry = constants[vicharaDomain]
      expect(entry, `no operative_vargas entry for '${vicharaDomain}'`).toBeDefined()
      expect(DOMAIN_DIRECT_VARGAS[signalDomain]).toEqual(entry!.vargas.filter(v => v !== 'D1'))
    },
  )
})

describe('F-164 — fails loudly when brahma_vichara_constants has no operative_vargas row', () => {
  it('ensureDomainDirectVargasLoaded throws rather than silently falling back to a stale literal', async () => {
    vi.resetModules()
    const freshQueryMock = vi.fn().mockResolvedValue({ rows: [] })
    vi.doMock('@/lib/db/client', () => ({ query: freshQueryMock }))
    const fresh = await import('../reading_checklist')
    await expect(fresh.ensureDomainDirectVargasLoaded()).rejects.toThrow(/operative_vargas.*missing/i)
    vi.doUnmock('@/lib/db/client')
    vi.resetModules()
  })
})

describe('F-107 — the flag code is registered in the closed envelope vocabulary', () => {
  it('cross_varga_convergence_not_computed is emittable', async () => {
    const { judgmentFlag } = await import('../../../envelope')
    const flag = judgmentFlag('cross_varga_convergence_not_computed', 'detail')
    expect(flag).toBeDefined()
  })
})
