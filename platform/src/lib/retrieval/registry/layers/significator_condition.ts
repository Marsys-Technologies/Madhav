/**
 * significator_condition.ts — F-113: the domain-significator D1 (rāśi) condition leg
 * ==================================================================================
 * PARIŚEṢA-V4 · F-113 (CL-20, TIER1-CORRECTNESS).
 *
 * THE DEFECT THIS CLOSES
 * ----------------------
 * `assess_marriage` on the canonical chart (482012f1-…, lahiri) contained the string
 * 'exalted' ZERO times across its entire response, while the chart's single most
 * consequential 7th-house fact is that **Saturn is exalted in Libra in the 7th bhāva**
 * (Vishakha, ṣaḍbala 7.83 rūpa — 2nd-strongest graha of the classical seven), and its
 * 7th lord + marriage kāraka **Venus sits in the bottom ṣaḍbala quartile** (4.64 rūpa).
 * Both facts were surfaced INCIDENTALLY, in ~6KB, by the generic
 * `ganita_dasha_lord_capability_get` — the domain-specialised tool missed what the
 * generic tool found.
 *
 * ROOT CAUSE — a coverage gap, not a ranking bug. `runAssessDomain` (register_d8_assess_
 * domain.ts) assembled MSR signals, yoga firings, the OPERATIVE-VARGA dignity (D9 for
 * relationship), contradictions and dāśā timing — but it never read the **D1 (rāśi)**
 * dignity/house/ṣaḍbala of the domain's own bhāveśa, kāraka(s), or bhāva OCCUPANTS. No
 * ranking could surface a fact the assembler never fetched. (The D9 leg it does fetch,
 * and the graha_shadbala_ranking it does compute, both land in the `evidence` /
 * `verdict_skeleton` layers — which `assembleSaraContent` drops ALL-OR-NOTHING under
 * the 40KB assess_* budget, so neither reaches the caller at default verbosity either.)
 *
 * THE FIX — reuse, not rebuild (§19 single-source mandate). `judgment_query`
 * (register_d9_judgment.ts) already owns a correct, classically-grounded, deterministic
 * D1 grading mechanism: `resolveAddress` for bhāveśa/kāraka/occupant resolution +
 * `gradeGraha` for D1 dignity + ṣaḍbala with real L1 fact_ids + `DIGNITY_WEIGHT` for the
 * uncontested dignity grading. This module wires that EXISTING mechanism into the
 * assess_* assembler. It computes nothing new: every value is a stored L1 fact read by
 * fact_id (§N.5 — L1 is the authority over L2+ derivations; a signal never restates a
 * computed value as its own truth).
 *
 * ONE GAP THIS MODULE ALSO CLOSES ON THE SHARED PATH: judgment_query resolves the bhāva
 * OCCUPANTS but only ever counts them (benefic/malefic ±0.5) — it never grades their
 * dignity. That is exactly how an exalted Saturn in the 7th disappears into "one malefic
 * occupant". Here the occupants are graded like any other significator. This module does
 * NOT change judgment_query's scored verdict composite (that would need its own design
 * review); it only supplies the assess_* narration leg.
 *
 * SELECTION CONTRACT (the "what gets surfaced" rule, deterministic — never an LLM, never
 * a calibrated probability; see selectNotablePlacements below for the code):
 *   A graded significator placement is NOTABLE iff EITHER
 *     (a) its D1 `dignity_state` is a classical EXTREME — |DIGNITY_WEIGHT| >= 1.5, i.e.
 *         exalted(2) / debilitated(-2) / own(1.5) / moolatrikona(1.75) (the tiers no
 *         school disputes; F-153: moolatrikona now sits strictly above own, both still
 *         clear the 1.5 gate); OR
 *     (b) its ṣaḍbala rank sits in the TOP or BOTTOM quartile of the classical-seven
 *         population — the same quartile convention `ganita_dasha_lord_capability_get`
 *         already ships for its warning_tier (shadbala_percentile thresholds).
 *   Notable placements are ordered by |dignity_weight| desc, then ṣaḍbala desc, so a
 *   dignity extreme always outranks a mere strength extreme and the ordering is stable.
 * NEITHER threshold is invented here: both are lifted from mechanisms already shipped
 * and already reviewed in this codebase.
 */

import { query } from '@/lib/db/client'
import {
  resolveAddress,
  GRAHA_CODE_TO_NAME,
  grahaCodeOf,
  type ResolvedGraha,
  type ResolvedOccupants,
  type ResolvedSign,
} from '../../address_resolver'
import {
  SHASTRA_MAP,
  DIGNITY_WEIGHT,
  gradeGraha,
  type GrahaCondition,
} from './register_d9_judgment'
import { rankGrahasByShadbala, type RankedGraha } from '../../ranking/rank_vocabulary'
import { LOW_SHADBALA_PERCENTILE as B8_LOW_SHADBALA_PERCENTILE } from './L1_ganita/get_dasha_lord_capability'
import { ordinalHouse } from '../../ranking/identifier_format'

/** Roles a graded placement can hold relative to the domain being assessed. */
export type SignificatorRole = 'bhavesha' | 'karaka' | 'occupant'

export interface SignificatorPlacement extends GrahaCondition {
  role: SignificatorRole
  /** 1-indexed ṣaḍbala rank within the classical-seven population, when computable. */
  shadbala_rank: number | null
  shadbala_population_size: number | null
  /** rank/population as a fraction: 1.0 = strongest, 0.0 = weakest. Null when unranked. */
  shadbala_percentile: number | null
  rank_statement: string | null
}

export interface NotablePlacement extends SignificatorPlacement {
  /** Why this placement was selected — the selection contract's own reasons, verbatim. */
  notable_reasons: string[]
}

export interface SignificatorCondition {
  domain: string
  bhava: number | null
  bhava_sign: string | null
  bhavesha: SignificatorPlacement | null
  karakas: SignificatorPlacement[]
  occupants: SignificatorPlacement[]
  notable: NotablePlacement[]
  fact_ids: string[]
  selection_contract: string
  note: string
  /** Present ONLY when the leg could not be assembled — an honest null, never a fake fill. */
  empty_reason?: string
}

/** |weight| >= this is a classical dignity EXTREME: exalted(2)/debilitated(-2)/own(1.5)/
 *  moolatrikona(1.75) — F-153: moolatrikona strictly outranks own, both clear this gate.
 *  great_friend(1)/friend(0.5)/neutral(0)/enemy(-0.5) are not. */
export const NOTABLE_DIGNITY_ABS_WEIGHT = 1.5

/** Low-strength boundary — the EXACT constant + percentile definition
 *  `ganita_dasha_lord_capability_get` (B8) already ships for its warning_tier: PERCENT_RANK
 *  over this chart's 9 graha_shadbala_total.rupa rows, ascending (0 = weakest, 1 = strongest).
 *  Imported, not re-declared, so the two surfaces cannot drift apart about which graha is
 *  strength-extreme on a given chart. F-113's own claim cites this scale directly
 *  ("Venus … shadbala_percentile 0.25"). */
export const LOW_SHADBALA_PERCENTILE = B8_LOW_SHADBALA_PERCENTILE
/** Its symmetric mirror at the strong end. */
export const HIGH_SHADBALA_PERCENTILE = 1 - B8_LOW_SHADBALA_PERCENTILE

export const SELECTION_CONTRACT_NOTE =
  'A significator placement is surfaced as NOTABLE iff (a) its D1 dignity_state is a ' +
  `classical extreme (|dignity_weight| >= ${NOTABLE_DIGNITY_ABS_WEIGHT} — exalted / debilitated / own / ` +
  `moolatrikona) OR (b) its ṣaḍbala percentile is <= ${LOW_SHADBALA_PERCENTILE} or >= ` +
  `${HIGH_SHADBALA_PERCENTILE.toFixed(2)} — PERCENT_RANK over this chart's 9 graha_shadbala_total.rupa ` +
  'rows, the identical scale and threshold ganita_dasha_lord_capability_get uses for its ' +
  'warning_tier. Deterministic; never an LLM judgment and never a calibrated probability. ' +
  'Ordered by |dignity_weight| desc, then ṣaḍbala desc.'

/** Does this dignity_state count as a classical extreme under the selection contract? */
export function isDignityExtreme(dignity_state: string | null): boolean {
  if (!dignity_state) return false
  const w = DIGNITY_WEIGHT[dignity_state]
  return typeof w === 'number' && Math.abs(w) >= NOTABLE_DIGNITY_ABS_WEIGHT
}

/**
 * THE SELECTION CONTRACT, as a pure function over already-graded placements. Kept pure and
 * exported so its regression test asserts the RULE, not a mocked DB round-trip.
 */
export function selectNotablePlacements(
  placements: SignificatorPlacement[],
): NotablePlacement[] {
  const notable: NotablePlacement[] = []
  for (const p of placements) {
    const reasons: string[] = []
    if (isDignityExtreme(p.dignity_state)) {
      reasons.push(`dignity_state='${p.dignity_state}' is a classical extreme (|weight| >= ${NOTABLE_DIGNITY_ABS_WEIGHT})`)
    }
    if (p.shadbala_percentile !== null) {
      if (p.shadbala_percentile >= HIGH_SHADBALA_PERCENTILE) {
        reasons.push(
          `shadbala_percentile=${p.shadbala_percentile.toFixed(2)} (>= ${HIGH_SHADBALA_PERCENTILE.toFixed(2)}) ` +
          `— rank ${p.shadbala_rank} of ${p.shadbala_population_size}, top of chart`,
        )
      } else if (p.shadbala_percentile <= LOW_SHADBALA_PERCENTILE) {
        reasons.push(
          `shadbala_percentile=${p.shadbala_percentile.toFixed(2)} (<= ${LOW_SHADBALA_PERCENTILE}) ` +
          `— rank ${p.shadbala_rank} of ${p.shadbala_population_size}, bottom of chart`,
        )
      }
    }
    if (reasons.length > 0) notable.push({ ...p, notable_reasons: reasons })
  }
  notable.sort((a, b) => {
    const aw = Math.abs(a.dignity_weight ?? 0), bw = Math.abs(b.dignity_weight ?? 0)
    if (aw !== bw) return bw - aw
    return (b.shadbala_rupa ?? 0) - (a.shadbala_rupa ?? 0)
  })
  return notable
}

/**
 * One plain-language sentence naming the notable placements, for the deterministic verdict
 * layer. Fixed template over already-graded terms — no generative call (B.10). Returns null
 * when there is nothing notable (the caller emits the honest-absence clause instead).
 *
 * `maxNamed` bounds the sentence because the verdict lands in the ≤2KB Sāra kernel, the one
 * layer no budget pass may drop — the whole point of putting this fact there.
 */
export function describeNotablePlacements(
  notable: NotablePlacement[],
  bhava: number | null,
  maxNamed = 2,
): string | null {
  if (notable.length === 0) return null
  // Deliberately terse: every byte here competes for the ≤2KB kernel ceiling with the
  // drill pointers and flags, so the sentence states the placement and nothing decorative.
  const bhavaOrdinal = bhava !== null ? ordinalHouse(bhava) : null
  const named = notable.slice(0, maxNamed).map(p => {
    const roleLabel = p.role === 'bhavesha'
      ? `${bhavaOrdinal ? `${bhavaOrdinal} ` : ''}lord`
      : p.role === 'karaka' ? 'kāraka'
      : `${bhavaOrdinal ?? 'domain-bhāva'} occupant`
    // The occupant's house IS the domain bhāva by construction — never restate it.
    const showHouse = p.house !== null && !(p.role === 'occupant' && p.house === bhava)
    const where = p.sign
      ? ` in ${p.sign}${showHouse ? ` (${ordinalHouse(p.house!)})` : ''}`
      : showHouse ? ` in the ${ordinalHouse(p.house!)}` : ''
    const dignity = p.dignity_state ?? 'dignity not computed'
    const strength = p.shadbala_rupa !== null
      ? ` — ṣaḍbala ${p.shadbala_rupa}${p.shadbala_rank !== null ? `, rank ${p.shadbala_rank}/${p.shadbala_population_size}` : ''}`
      : ''
    return `${p.graha} (${roleLabel}) is ${dignity}${where}${strength}`
  })
  const more = notable.length > named.length
    ? ` (+${notable.length - named.length} further notable placement(s) in significator_condition.notable)`
    : ''
  return `Significator condition (D1): ${named.join('; ')}${more}.`
}

/** The honest-absence sentence — never substituted for a fabricated positive claim (B.10). */
export const NO_NOTABLE_PLACEMENT_TEXT =
  'No significator placement for this domain (bhāveśa, kāraka(s), or bhāva occupants) sits ' +
  'at a classical D1 dignity extreme or a ṣaḍbala quartile extreme — an honest absence, not ' +
  'an omission; see significator_condition for every graded placement.'

interface ShadbalaRankInfo { ranked: RankedGraha[]; percentileByKey: Map<string, number> }

/**
 * ṣaḍbala rūpa + percentile per graha, straight from L1 chart_facts. The PERCENT_RANK
 * window is COPIED VERBATIM from `ganita_dasha_lord_capability_get`'s own query so the two
 * surfaces compute the identical percentile for the identical chart — cross-surface
 * consistency by construction, not by coincidence (the WP-1.8 discipline). Ranks/statements
 * come from the shared rank_vocabulary so a rank is never served without its population.
 */
async function fetchShadbalaRanking(
  chart_id: string,
  ayanamsha_id: string,
): Promise<ShadbalaRankInfo> {
  const empty: ShadbalaRankInfo = { ranked: [], percentileByKey: new Map() }
  try {
    const res = await query<{ fact_subject: string; rupa: number | null; percentile: number | null }>(
      `SELECT fact_subject, fact_value_num AS rupa,
              PERCENT_RANK() OVER (ORDER BY fact_value_num) AS percentile
       FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2
         AND fact_category = 'graha_shadbala_total' AND fact_key = 'rupa'`,
      [chart_id, ayanamsha_id],
    )
    const inputs: Array<{ graha: string; shadbala_total: number }> = []
    const percentileByKey = new Map<string, number>()
    for (const r of res.rows) {
      if (r.rupa === null) continue
      // chart_facts stores the 3-char subject (VEN/SAT); rank_vocabulary's population is
      // keyed by the 2-char code. grahaCodeOf normalises both to the canonical code.
      const key = normaliseToRankKey(r.fact_subject)
      if (!key) continue
      inputs.push({ graha: key, shadbala_total: Number(r.rupa) })
      if (r.percentile !== null) percentileByKey.set(key, Number(r.percentile))
    }
    return { ranked: rankGrahasByShadbala(inputs, 'all_9'), percentileByKey }
  } catch {
    // Non-fatal: the dignity leg still stands; strength-extreme selection degrades to null.
    return empty
  }
}

const RANK_KEYS = ['SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA', 'RA', 'KE'] as const

/** Map any graha code/name (SAT / RAH_MEAN / "Saturn" / "shani") to the 2-char key
 *  rank_vocabulary's population table uses. Null — never a guess — on an unknown subject. */
function normaliseToRankKey(subject: string): string | null {
  let canonical: string
  try {
    canonical = grahaCodeOf(subject)
  } catch {
    return null
  }
  return RANK_KEYS.find(k => grahaCodeOf(k) === canonical) ?? null
}

function rankDisplayName(code: string): string | null {
  try {
    return GRAHA_CODE_TO_NAME[grahaCodeOf(code)] ?? null
  } catch {
    return null
  }
}

/** Attach ṣaḍbala rank/percentile to a graded GrahaCondition. */
function withRank(
  g: GrahaCondition,
  role: SignificatorRole,
  ranking: ShadbalaRankInfo,
): SignificatorPlacement {
  const hit = ranking.ranked.find(r => rankDisplayName(r.graha) === g.graha)
  const pct = hit ? ranking.percentileByKey.get(hit.graha) : undefined
  return {
    ...g,
    role,
    shadbala_rank: hit ? hit.rank : null,
    shadbala_population_size: hit ? hit.population_size : null,
    shadbala_percentile: pct === undefined ? null : pct,
    rank_statement: hit ? hit.rank_statement : null,
  }
}

/**
 * Assemble the D1 significator-condition leg for one domain. Every value is a stored L1
 * fact read by fact_id — nothing is recomputed here (§N.5). Non-fatal throughout: a leg
 * that cannot resolve reports its absence rather than degrading the whole assessment.
 */
export async function buildSignificatorCondition(
  chart_id: string,
  ayanamsha_id: string,
  domain: string,
): Promise<SignificatorCondition> {
  const spec = SHASTRA_MAP[domain]
  const base: SignificatorCondition = {
    domain,
    bhava: spec ? spec.bhava : null,
    bhava_sign: null,
    bhavesha: null,
    karakas: [],
    occupants: [],
    notable: [],
    fact_ids: [],
    selection_contract: SELECTION_CONTRACT_NOTE,
    note:
      'D1 (rāśi) condition of this domain\'s bhāveśa, kāraka(s) and bhāva occupants — dignity, ' +
      'sign, house and ṣaḍbala, each read from L1 chart_facts by fact_id (§N.5, never recomputed). ' +
      'Shares the exact grading mechanism judgment_query uses (resolveAddress + gradeGraha + ' +
      'DIGNITY_WEIGHT) — reuse, not a parallel implementation. F-113.',
  }
  if (!spec) {
    return {
      ...base,
      empty_reason: `domain "${domain}" has no SHASTRA_MAP entry — no bhāva/kāraka spec to ground a ` +
        'significator condition on. Honest absence, not a fabricated leg.',
    }
  }

  const fact_ids = new Set<string>()
  const ranking = await fetchShadbalaRanking(chart_id, ayanamsha_id)

  // ── bhāva sign + bhāveśa + occupants (lagna frame — the rāśi promise) ──
  let bhava_sign: string | null = null
  let bhavesha: SignificatorPlacement | null = null
  const occupants: SignificatorPlacement[] = []
  try {
    const [bhavaRes, lordRes, occRes] = await Promise.all([
      resolveAddress(chart_id, { type: 'bhava', house: spec.bhava }, { ayanamsha_id }),
      resolveAddress(chart_id, { type: 'lord_of', house: spec.bhava }, { ayanamsha_id }),
      resolveAddress(chart_id, { type: 'occupants_of', house: spec.bhava }, { ayanamsha_id }),
    ])
    const bhavaEntity = bhavaRes.entities[0] as ResolvedSign | undefined
    if (bhavaEntity) {
      bhava_sign = bhavaEntity.sign
      bhavaEntity.fact_ids.forEach(f => fact_ids.add(f))
    }
    const lordEntity = lordRes.entities[0] as ResolvedGraha | undefined
    if (lordEntity) {
      bhavesha = withRank(await gradeGraha(chart_id, ayanamsha_id, lordEntity), 'bhavesha', ranking)
      bhavesha.fact_ids.forEach(f => fact_ids.add(f))
    }
    const occEntity = occRes.entities[0] as ResolvedOccupants | undefined
    if (occEntity) {
      occEntity.fact_ids.forEach(f => fact_ids.add(f))
      // The previously-ungraded leg: an occupant is graded exactly like the bhāveśa, so an
      // exalted graha sitting in the domain's own bhāva can never again reduce to a bare name.
      for (const name of occEntity.grahas) {
        try {
          const res = await resolveAddress(chart_id, { type: 'graha', graha: name }, { ayanamsha_id })
          const graded = withRank(
            await gradeGraha(chart_id, ayanamsha_id, res.entities[0] as ResolvedGraha),
            'occupant',
            ranking,
          )
          graded.fact_ids.forEach(f => fact_ids.add(f))
          occupants.push(graded)
        } catch {
          // Non-fatal: one unresolvable occupant never blanks the whole leg.
        }
      }
    }
  } catch (err) {
    return {
      ...base,
      fact_ids: Array.from(fact_ids),
      empty_reason: `bhāva/bhāveśa/occupant resolution failed for bhāva ${spec.bhava}: ${String(err)} — ` +
        'reported, never silently downgraded to an empty leg.',
    }
  }

  // ── kāraka(s) ──
  const karakas: SignificatorPlacement[] = []
  for (const karakaName of spec.karakas) {
    try {
      const res = await resolveAddress(chart_id, { type: 'graha', graha: karakaName }, { ayanamsha_id })
      const graded = withRank(
        await gradeGraha(chart_id, ayanamsha_id, res.entities[0] as ResolvedGraha),
        'karaka',
        ranking,
      )
      graded.fact_ids.forEach(f => fact_ids.add(f))
      karakas.push(graded)
    } catch {
      // Non-fatal: a single unresolved kāraka is absent, not fatal to the leg.
    }
  }

  // Dedup across roles by graha, keeping the most domain-specific role (bhāveśa > kāraka >
  // occupant) so Venus-as-both-7th-lord-and-kāraka is stated once, not twice.
  const seen = new Set<string>()
  const forSelection: SignificatorPlacement[] = []
  for (const p of [...(bhavesha ? [bhavesha] : []), ...karakas, ...occupants]) {
    if (seen.has(p.graha)) continue
    seen.add(p.graha)
    forSelection.push(p)
  }

  return {
    ...base,
    bhava_sign,
    bhavesha,
    karakas,
    occupants,
    notable: selectNotablePlacements(forSelection),
    fact_ids: Array.from(fact_ids),
  }
}
