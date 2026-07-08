/**
 * chart_query_about.ts — minimal inline `about` facet resolver for chart_facts_query
 * ====================================================================================
 * R5 W1 (lane: chart_query). Design mandate: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md
 * §27.1 (universal `about` facet) + §27.2 (the address resolver — "astrological indirection
 * resolved server-side ... lord_of(bhava 7) ... served with the resolution chain").
 *
 * SCOPE NOTE (per W1 brief): the full shared address resolver is the r5/w1-address-resolver
 * lane's deliverable (`platform/src/lib/retrieval/address_resolver.ts` or similar). That module
 * did not exist on this lane's base branch at the time this file was written (parallel-lane
 * wave — see W1 report). This is therefore a MINIMAL INLINE resolver scoped to exactly what
 * chart_query needs (graha addressing, bhava occupants, bhava-lord indirection) — NOT a
 * general-purpose address grammar (no dispositor_of(), no karaka(), no chained addresses).
 * RECONCILE AT RING-1: if the sibling lane's resolver lands, this module's functions should be
 * re-pointed to call it (or be deleted in favor of it) rather than maintained twice.
 *
 * All lordship assignments below are the standard Parashari classical rulerships (BPHS ch.3,
 * "Rashi Adhipatis") — undisputed across every Vedic paradigm, so hardcoding here (rather than
 * treating it as a computed/contested value) is safe per CLAUDE.md B.10.
 */

export type GrahaCode = 'SUN' | 'MOON' | 'MAR' | 'MER' | 'JUP' | 'VEN' | 'SAT' | 'RAH_MEAN' | 'KET_MEAN'

/** Canonical zodiac order, index 0 = Aries, matching the whole-sign house convention chart_facts uses. */
const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

/** BPHS ch.3 classical rashi lordships (Rahu/Ketu have no rashi lordship in Parashari — omitted). */
const SIGN_LORD: Record<string, GrahaCode> = {
  Aries: 'MAR', Scorpio: 'MAR',
  Taurus: 'VEN', Libra: 'VEN',
  Gemini: 'MER', Virgo: 'MER',
  Cancer: 'MOON',
  Leo: 'SUN',
  Sagittarius: 'JUP', Pisces: 'JUP',
  Capricorn: 'SAT', Aquarius: 'SAT',
}

const GRAHA_ALIASES: Record<string, GrahaCode> = {
  sun: 'SUN', surya: 'SUN',
  moon: 'MOON', chandra: 'MOON',
  mars: 'MAR', mangala: 'MAR', kuja: 'MAR',
  mercury: 'MER', budha: 'MER',
  jupiter: 'JUP', guru: 'JUP', brihaspati: 'JUP',
  venus: 'VEN', shukra: 'VEN',
  saturn: 'SAT', shani: 'SAT',
  rahu: 'RAH_MEAN',
  ketu: 'KET_MEAN',
}

export function normalizeGrahaName(name: string): GrahaCode | null {
  const key = name.trim().toLowerCase()
  if (GRAHA_ALIASES[key]) return GRAHA_ALIASES[key]
  const upper = name.trim().toUpperCase().replace(/\s+/g, '_')
  const known: GrahaCode[] = ['SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN']
  return (known as string[]).includes(upper) ? (upper as GrahaCode) : null
}

/** One resolution step, served back to the caller so it can show its reasoning (§27.2). */
export interface ResolutionStep {
  step: string
  input: unknown
  output: unknown
  basis: string
}

export interface AboutResolution {
  /** fact_subject values the resolved address maps to (e.g. ['LAGNA'], ['SAT'], ['HOUSE_10']) */
  subjects: string[]
  /** fact_category hint, if the address implies one (e.g. house-lord implies graha_position) */
  category_hint?: string
  chain: ResolutionStep[]
  error?: string
}

/**
 * Resolve the Nth house's rashi (whole-sign) from the lagna's rashi, given the lagna's
 * `sign` fact already fetched from chart_facts (graha_position/LAGNA/sign).
 */
export function houseSignFromLagna(lagnaSign: string, houseNumber: number): string | null {
  const idx = SIGNS.indexOf(lagnaSign as (typeof SIGNS)[number])
  if (idx === -1 || houseNumber < 1 || houseNumber > 12) return null
  return SIGNS[(idx + houseNumber - 1) % 12]
}

/**
 * Resolve an `about` facet value into concrete chart_facts fact_subject targets + a served
 * resolution chain. `lagnaSign` must be pre-fetched by the caller (one cheap row read) when
 * the address needs bhava-lord indirection.
 *
 * Supported forms:
 *   'lagna'                      → subjects: ['LAGNA']
 *   { graha: 'Saturn' }          → subjects: ['SAT']
 *   { bhava: 10 }                → subjects: ['HOUSE_10']  (occupants/strength rows for the house itself)
 *   { house_lord: 10 }           → resolves lagna-sign + offset → rashi → classical lord → subjects: [lordCode]
 */
export function resolveAboutFacet(
  about: unknown,
  lagnaSign: string | null,
): AboutResolution {
  if (about == null) return { subjects: [], chain: [] }

  if (typeof about === 'string') {
    const key = about.trim().toLowerCase()
    if (key === 'lagna' || key === 'ascendant') {
      return {
        subjects: ['LAGNA'],
        category_hint: 'graha_position',
        chain: [{ step: 'about:string', input: about, output: 'LAGNA', basis: 'direct alias' }],
      }
    }
    const graha = normalizeGrahaName(about)
    if (graha) {
      return {
        subjects: [graha],
        category_hint: 'graha_position',
        chain: [{ step: 'about:string', input: about, output: graha, basis: 'graha name normalization' }],
      }
    }
    return { subjects: [], chain: [], error: `about: unrecognized address string "${about}"` }
  }

  if (typeof about === 'object') {
    const obj = about as Record<string, unknown>

    if (obj['graha'] != null) {
      const raw = String(obj['graha'])
      const graha = normalizeGrahaName(raw)
      if (!graha) return { subjects: [], chain: [], error: `about.graha: unrecognized graha "${raw}"` }
      return {
        subjects: [graha],
        category_hint: 'graha_position',
        chain: [{ step: 'about.graha', input: raw, output: graha, basis: 'graha name normalization' }],
      }
    }

    if (obj['bhava'] != null || obj['house'] != null) {
      const n = Number(obj['bhava'] ?? obj['house'])
      if (!Number.isInteger(n) || n < 1 || n > 12) {
        return { subjects: [], chain: [], error: 'about.bhava/house must be an integer 1-12' }
      }
      const subject = `HOUSE_${n}`
      return {
        subjects: [subject],
        chain: [{ step: 'about.bhava', input: n, output: subject, basis: 'direct bhava subject addressing' }],
      }
    }

    if (obj['house_lord'] != null || obj['bhava_lord'] != null) {
      const n = Number(obj['house_lord'] ?? obj['bhava_lord'])
      if (!Number.isInteger(n) || n < 1 || n > 12) {
        return { subjects: [], chain: [], error: 'about.house_lord must be an integer 1-12' }
      }
      if (!lagnaSign) {
        return {
          subjects: [], chain: [],
          error: 'about.house_lord requires the lagna sign, which could not be resolved for this chart/ayanamsha',
        }
      }
      const rashi = houseSignFromLagna(lagnaSign, n)
      if (!rashi) return { subjects: [], chain: [], error: `about.house_lord: could not compute rashi for house ${n}` }
      const lord = SIGN_LORD[rashi]
      const chain: ResolutionStep[] = [
        { step: 'lagna_sign', input: null, output: lagnaSign, basis: 'chart_facts graha_position/LAGNA/sign' },
        {
          step: 'house_sign', input: { lagnaSign, house: n }, output: rashi,
          basis: 'whole-sign houses: sign(N) = sign(lagna) + (N-1), classical Parashari bhava reckoning',
        },
        { step: 'sign_lord', input: rashi, output: lord, basis: 'BPHS ch.3 classical rashi lordship (Parashari, undisputed)' },
      ]
      return { subjects: [lord], category_hint: 'graha_position', chain }
    }

    return { subjects: [], chain: [], error: 'about: unrecognized address object shape' }
  }

  return { subjects: [], chain: [], error: 'about: must be a string or an address object' }
}
