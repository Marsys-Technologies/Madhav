/**
 * address_resolver.ts — THE ADDRESS RESOLVER (R5 W1, design §27.2 — "the one genuinely new
 * architectural piece")
 * ======================================================================================
 * Resolves an astrological ADDRESS ("10th lord", "dispositor of Venus", "from Moon", "Venus
 * in D9", "Atmakaraka") into concrete chart_facts / chart_divisionals rows — WITHOUT the
 * caller (or the LLM) needing to know the underlying table/EAV structure. Design quote:
 * "the resolver is a thin, cacheable, per-chart PURE function... this single component is
 * what lets the LLM ask questions the way the shastra phrases them."
 *
 * SCOPE OF THIS MODULE (per the W1 lane brief): the resolver itself — solid, tested,
 * cleanly exported. It is NOT wired into chart_query / dasha_query here; that is each
 * consuming lane's own job against the `about` facet (design §27.1).
 *
 * PURITY: every exported resolution function only ever READS chart_facts / chart_divisionals
 * (via the shared `query` helper) and returns a value — no writes, no caching side effects,
 * no mutation of shared state. (A thin caller-side cache is a legitimate future addition but
 * is deliberately NOT added here — see design §18 cache-locality caveat; adding one here would
 * duplicate that already-flagged risk.)
 *
 * REFERENCE FRAMES (design §27.3): lagna (default) | chandra | surya | arudha | karakamsha.
 * `varnada` is NOT supported — no varnada-lagna fact exists anywhere in chart_facts /
 * chart_divisionals as of this build (verified against both canonical charts); a caller
 * requesting it gets a clear, typed error rather than a fabricated frame (B.10).
 *
 * DISPOSITOR RESOLUTION — JUDGMENT CALL (recorded at R5_JUDGMENT_LEDGER JL-011): sign
 * rulership is resolved from the CLASSICAL FIXED RULERSHIP TABLE (SIGN_LORDS below), not
 * from the L2 Bodha `bodha_cgm_edges` 'dispositor' edge_type the design also mentions as a
 * backing option. Reasons: (1) the classical table is a citable constant (BPHS rulership),
 * true for EVERY chart with no build dependency, whereas CGM edges are an L2 Bodha campaign
 * artifact that may not exist for charts where L2 hasn't run; (2) B.1 (facts/interpretation
 * separation) — an L1-adjacent primitive utility should not depend on L2 derivations for its
 * basic correctness; (3) cross-checked against chart_facts.sign_lord (written by L1 ga_*
 * writers) on both canonical charts — the classical table matches every observed sign_lord
 * fact exactly. CGM dispositor edges remain a valid corroboration source for a future
 * caller that wants graph-context (betweenness, cross-subsystem mapping) on TOP of this.
 *
 * HOUSE SYSTEM: whole-sign (rāśi) houses, confirmed against chart_facts.house_d1 on both
 * canonical charts — e.g. native LAGNA sign=Aries (house 1), MAR sign=Libra (house 7):
 * Libra is exactly the 7th sign counted from Aries. This is the standard Parashari system
 * and the only one chart_facts/chart_divisionals materialize a house number for.
 *
 * THE PARADIGM FACET (design §27.4, R5 W2; ruling recorded at R5_JUDGMENT_LEDGER JL-011):
 * `paradigm: parashari (default) | jaimini | kp | tajika`. Most address types (graha, sign,
 * bhava, lord_of, dispositor_of, bhava_from, occupants_of) are PARADIGM-NEUTRAL substrate —
 * sign placement and classical fixed rulership are true under every school, so they resolve
 * identically no matter which paradigm a caller names. Three address types are genuinely
 * PARADIGM-SPECIFIC, matching design §27.4's own list of what each paradigm "activates":
 *   - `karaka`      → jaimini (chāra karaka addressing; backed by karaka_chara_position)
 *   - `sub_lord_of` → kp      (sub-lord/cusp addressing; backed by cusp_kp_lords)
 *   - `saham`       → tajika  (sāham addressing; backed by saham_position)
 * `assertParadigmCoherent` is the COHERENCE GUARD `resolveAddress` runs on every call: it
 * walks an expression tree and throws `ParadigmMixError` if (a) two DIFFERENT paradigm-specific
 * address types appear in the SAME expression (e.g. a jaimini `karaka` chained under a kp
 * `sub_lord_of`) — the "subtle sin of mixing paradigms mid-answer" design §27.4 names — or
 * (b) a caller declares an explicit `paradigm` that conflicts with a paradigm-specific address
 * type actually used. No caller can silently produce a paradigm-mixed answer through this
 * resolver.
 */

import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from './registry/constants'
// Graha code/name/alias vocabulary + grahaCodeOf() + AddressResolutionError live in
// graha_labels.ts — the CLIENT-SAFE pure subset of this module (no `@/lib/db/client`
// import, so no `server-only` poisoning of a client bundle that only needs graha
// labels). Re-exported below so every existing address_resolver.{GRAHA_CODE_TO_NAME,
// grahaCodeOf, AddressResolutionError} call site is unaffected — moved, not copied.
// A CLIENT COMPONENT must import from './graha_labels' directly, never from this file.
import { AddressResolutionError, GRAHA_CODE_TO_NAME, grahaCodeOf } from './graha_labels'
export { AddressResolutionError, GRAHA_CODE_TO_NAME, grahaCodeOf } from './graha_labels'

// ─────────────────────────────────────────────────────────────────────────────
// § Vocabulary — coordinates with design §27.1 `about` facet + §27.3 `frame` facet
// (graha code/name/alias vocabulary + grahaCodeOf() moved to graha_labels.ts —
// see the import/re-export block above)
// ─────────────────────────────────────────────────────────────────────────────

/** The 12 rāśi in zodiacal order — index 0 = Aries. Fixed; never re-derived per chart. */
export const ZODIAC_SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

export type ZodiacSign = (typeof ZODIAC_SIGNS)[number]

/** Classical fixed sign rulership (BPHS) — the dispositor of every sign. Never Rahu/Ketu. */
export const SIGN_LORDS: Record<ZodiacSign, string> = {
  Aries: 'Mars',
  Taurus: 'Venus',
  Gemini: 'Mercury',
  Cancer: 'Moon',
  Leo: 'Sun',
  Virgo: 'Mercury',
  Libra: 'Venus',
  Scorpio: 'Mars',
  Sagittarius: 'Jupiter',
  Capricorn: 'Saturn',
  Aquarius: 'Saturn',
  Pisces: 'Jupiter',
}

/** Reference frames — design §27.3. `varnada` intentionally omitted (no backing data, see header). */
export type ReferenceFrame = 'lagna' | 'chandra' | 'surya' | 'arudha' | 'karakamsha'

/** Jaimini chāra karaka short codes ↔ chart_facts.karaka_chara_position fact_subject. */
export const KARAKA_CODE_TO_SUBJECT: Record<string, string> = {
  AK: 'ATMAKARAKA',
  AMK: 'AMATYAKARAKA',
  BK: 'BHRATRIKARAKA',
  MK: 'MATRIKARAKA',
  PK: 'PUTRAKARAKA',
  GK: 'GNATIKARAKA',
  DK: 'DARAKARAKA',
  SK: 'STRIKARAKA', // 8th karaka — only populated under the kn_rao_rahu_included school
}

export type KarakaSchool = 'parashari_rahu_excluded' | 'kn_rao_rahu_included'

/** The PARADIGM facet (design §27.4) — the coherent classical interpretive frame. */
export type Paradigm = 'parashari' | 'jaimini' | 'kp' | 'tajika'

export const PARADIGMS: readonly Paradigm[] = ['parashari', 'jaimini', 'kp', 'tajika']

/** Named sāham (tajika) short codes ↔ chart_facts.saham_position fact_subject suffix.
 *  Small curated set of the most commonly consulted sāhams; any other code is passed through
 *  uppercased (`saham('X')` → fact_subject `SAHAM_X`) so newly-populated sāhams need no code change. */
export const SAHAM_CODE_TO_SUBJECT: Record<string, string> = {
  PUNYA: 'SAHAM_PUNYA',
  VIDYA: 'SAHAM_VIDYA',
  YASHAS: 'SAHAM_YASHAS',
  MITRA: 'SAHAM_MITRA',
  MAHATMYA: 'SAHAM_MAHATMYA',
  ASHA: 'SAHAM_AASTHA',
  AKSA: 'SAHAM_AKSA',
  AMRTA: 'SAHAM_AMRTA',
}

// ─────────────────────────────────────────────────────────────────────────────
// § AddressExpression — the structured (primary) address contract
// ─────────────────────────────────────────────────────────────────────────────

export type HouseNumber = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12

/** A resolvable astrological address. Recursive — chains like `dispositor_of(lord_of(10))`
 *  are just nested AddressExpression values. */
export type AddressExpression =
  | { type: 'graha'; graha: string; varga?: string }
  | { type: 'sign'; sign: ZodiacSign }
  | { type: 'bhava'; house: HouseNumber; frame?: ReferenceFrame }
  | { type: 'lord_of'; house: HouseNumber; frame?: ReferenceFrame }
  | { type: 'dispositor_of'; of: AddressExpression; varga?: string }
  | { type: 'bhava_from'; from: ReferenceFrame | AddressExpression; house: HouseNumber; varga?: string }
  | { type: 'karaka'; code: string; school?: KarakaSchool }
  | { type: 'occupants_of'; house: HouseNumber; varga?: string; frame?: ReferenceFrame }
  // ── Paradigm-specific address types (design §27.4, R5 W2) ──
  | { type: 'sub_lord_of'; cusp: HouseNumber } // kp
  | { type: 'saham'; code: string } // tajika

/** Thrown specifically by the paradigm coherence guard — a subtype of AddressResolutionError
 *  so existing `catch (AddressResolutionError)` call sites keep working unchanged, while a
 *  caller that cares specifically about paradigm-mixing can `instanceof` narrow on it. */
export class ParadigmMixError extends AddressResolutionError {}

// ─────────────────────────────────────────────────────────────────────────────
// § Resolved output — concrete rows + human-readable resolution chain
// ─────────────────────────────────────────────────────────────────────────────

export interface ResolvedGraha {
  kind: 'graha'
  graha: string
  graha_code: string
  sign: string | null
  house: number | null
  varga: string
  fact_ids: string[]
}

export interface ResolvedSign {
  kind: 'sign'
  sign: ZodiacSign
  house_number: number
  frame: ReferenceFrame
  fact_ids: string[]
}

export interface ResolvedKaraka {
  kind: 'karaka'
  code: string
  fact_subject: string
  graha: string
  house: number | null
  sign: string | null
  school: KarakaSchool
  fact_ids: string[]
}

export interface ResolvedOccupants {
  kind: 'occupants'
  house: number
  sign: ZodiacSign | null
  varga: string
  frame: ReferenceFrame
  grahas: string[]
  fact_ids: string[]
}

/** kp paradigm — the 4-tier significator chain for one cusp (design §27.4 "sub-lord/cusp
 *  addressing"). `sub_lord` is the primary KP-doctrine determinant; the others are carried
 *  for completeness of the resolution chain. */
export interface ResolvedSubLord {
  kind: 'sub_lord'
  cusp: number
  prana_lord: string | null
  star_lord: string | null
  sub_lord: string
  sub_sub_lord: string | null
  fact_ids: string[]
}

/** tajika paradigm — a sāham (sensitive point), by whole-sign house + sign + dispositor. */
export interface ResolvedSaham {
  kind: 'saham'
  code: string
  fact_subject: string
  sign: string | null
  house: number | null
  sign_lord: string | null
  fact_ids: string[]
}

export type ResolvedEntity =
  | ResolvedGraha
  | ResolvedSign
  | ResolvedKaraka
  | ResolvedOccupants
  | ResolvedSubLord
  | ResolvedSaham

export interface ResolvedAddress {
  expression: AddressExpression
  entities: ResolvedEntity[]
  /** Human-readable resolution steps, in order — "the 7th lord is Venus, placed in the 9th…" */
  chain: string[]
  epistemic_note?: string
  /** The effective paradigm this resolution ran under (design §27.4) — the caller's explicit
   *  `paradigm` option if given, else the paradigm implied by a paradigm-specific address type
   *  actually used (karaka→jaimini, sub_lord_of→kp, saham→tajika), else 'parashari' (default;
   *  every paradigm-neutral address type — graha/sign/bhava/lord_of/dispositor_of/bhava_from/
   *  occupants_of — resolves identically under 'parashari' with no paradigm-specific behavior). */
  paradigm: Paradigm
}

interface ResolveCtx {
  chart_id: string
  ayanamsha_id: string
}

// ─────────────────────────────────────────────────────────────────────────────
// § Core arithmetic — pure, no I/O
// ─────────────────────────────────────────────────────────────────────────────

/** The Nth house counted (whole-sign) from a reference sign. N=1 returns the reference sign itself. */
export function signAtHouseOffset(referenceSign: ZodiacSign, house: number): ZodiacSign {
  const idx = ZODIAC_SIGNS.indexOf(referenceSign)
  if (idx === -1) throw new AddressResolutionError(`"${referenceSign}" is not a recognized zodiac sign.`)
  if (!Number.isInteger(house) || house < 1 || house > 12) {
    throw new AddressResolutionError(`House number must be an integer 1..12, got ${house}.`)
  }
  return ZODIAC_SIGNS[(idx + house - 1) % 12]
}

function assertZodiacSign(sign: string): asserts sign is ZodiacSign {
  if (!(ZODIAC_SIGNS as readonly string[]).includes(sign)) {
    throw new AddressResolutionError(`"${sign}" is not a recognized zodiac sign.`)
  }
}

/** Inverse of `signAtHouseOffset` — given a reference sign and a target sign, which house
 *  (1..12, whole-sign) is the target counted-from-reference in? Pure arithmetic, no I/O.
 *  This is the exact math R5 W2 (frame facet, design §27.3) needs to re-base a graha's
 *  lagna-relative `house_d1` into a `frame`-relative house WITHOUT a parallel resolver —
 *  it is the one new primitive this lane adds, everything else reuses `resolveFrameSign`
 *  (exported below as `resolveFrameReferenceSign`) for frame → reference-sign resolution. */
export function houseCountedFrom(referenceSign: ZodiacSign, targetSign: ZodiacSign): number {
  const refIdx = ZODIAC_SIGNS.indexOf(referenceSign)
  const targetIdx = ZODIAC_SIGNS.indexOf(targetSign)
  if (refIdx === -1) throw new AddressResolutionError(`"${referenceSign}" is not a recognized zodiac sign.`)
  if (targetIdx === -1) throw new AddressResolutionError(`"${targetSign}" is not a recognized zodiac sign.`)
  return ((targetIdx - refIdx + 12) % 12) + 1
}

// ─────────────────────────────────────────────────────────────────────────────
// § DB reads
// ─────────────────────────────────────────────────────────────────────────────

interface FactRow {
  fact_id: string
  fact_value_text: string | null
  fact_value_num: string | null
}

/** A single graha's D1 (chart_facts) placement — sign + whole-sign house + the backing fact_ids. */
async function fetchD1GrahaPlacement(
  ctx: ResolveCtx,
  grahaCode: string,
): Promise<{ sign: string | null; house: number | null; fact_ids: string[] }> {
  const res = await query<FactRow & { fact_key: string }>(
    `SELECT fact_id, fact_key, fact_value_text, fact_value_num
     FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_position'
       AND fact_subject = $3 AND fact_key IN ('sign', 'house_d1')`,
    [ctx.chart_id, ctx.ayanamsha_id, grahaCode],
  )
  let sign: string | null = null
  let house: number | null = null
  const fact_ids: string[] = []
  for (const r of res.rows) {
    fact_ids.push(r.fact_id)
    if (r.fact_key === 'sign') sign = r.fact_value_text
    if (r.fact_key === 'house_d1') house = r.fact_value_num !== null ? Number(r.fact_value_num) : null
  }
  return { sign, house, fact_ids }
}

/** A graha's placement in a named divisional chart (varga != D1), via chart_divisionals.
 *  Canonical row per (chart, ayanamsha, varga, graha) is the one tagged `formula_provenance_text
 *  = 'whole_sign'` — verified to be the only row in that table carrying BOTH sign and house
 *  populated consistently (other rows are per-formula annotations: dignity tables, saptavargaja
 *  weights, Jaimini karaka labels, etc. that share the varga/graha key but not house). */
async function fetchVargaGrahaPlacement(
  ctx: ResolveCtx,
  grahaFullName: string,
  varga: string,
): Promise<{ sign: string | null; house: number | null; fact_ids: string[] }> {
  const res = await query<{ id: string; sign: string | null; house: number | null }>(
    `SELECT id, sign, house
     FROM chart_divisionals
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND varga = $3 AND graha = $4
       AND formula_provenance_text = 'whole_sign'
     LIMIT 1`,
    [ctx.chart_id, ctx.ayanamsha_id, varga, grahaFullName],
  )
  const row = res.rows[0]
  if (!row) return { sign: null, house: null, fact_ids: [] }
  return { sign: row.sign, house: row.house, fact_ids: [row.id] }
}

async function resolveGrahaEntity(
  ctx: ResolveCtx,
  grahaInput: string,
  varga: string,
): Promise<ResolvedGraha> {
  const grahaCode = grahaCodeOf(grahaInput)
  const grahaName = GRAHA_CODE_TO_NAME[grahaCode]
  const placement =
    varga === 'D1'
      ? await fetchD1GrahaPlacement(ctx, grahaCode)
      : await fetchVargaGrahaPlacement(ctx, grahaName, varga)
  return {
    kind: 'graha',
    graha: grahaName,
    graha_code: grahaCode,
    sign: placement.sign,
    house: placement.house,
    varga,
    fact_ids: placement.fact_ids,
  }
}

/** Frame → its reference sign + backing fact_ids. */
async function resolveFrameSign(
  ctx: ResolveCtx,
  frame: ReferenceFrame,
): Promise<{ sign: ZodiacSign; fact_ids: string[] }> {
  let category: string
  let subject: string
  switch (frame) {
    case 'lagna': category = 'graha_position'; subject = 'LAGNA'; break
    case 'chandra': category = 'graha_position'; subject = 'MOON'; break
    case 'surya': category = 'graha_position'; subject = 'SUN'; break
    case 'arudha': category = 'bhava_arudha'; subject = 'BHAVA_ARUDHA_AL'; break
    case 'karakamsha': category = 'karakamsa_position'; subject = 'KARAKAMSA'; break
    default:
      throw new AddressResolutionError(
        `Frame "${frame}" is not supported. Supported frames: lagna, chandra, surya, arudha, karakamsha ` +
          `(design §27.3; varnada omitted — no backing fact exists in chart_facts/chart_divisionals).`,
      )
  }
  const res = await query<{ fact_id: string; fact_value_text: string | null }>(
    `SELECT fact_id, fact_value_text FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = $3
       AND fact_subject = $4 AND fact_key = 'sign'`,
    [ctx.chart_id, ctx.ayanamsha_id, category, subject],
  )
  const row = res.rows[0]
  if (!row || !row.fact_value_text) {
    throw new AddressResolutionError(
      `Could not resolve frame "${frame}" for chart ${ctx.chart_id}: no ${category}/${subject} sign fact found.`,
    )
  }
  assertZodiacSign(row.fact_value_text)
  return { sign: row.fact_value_text, fact_ids: [row.fact_id] }
}

/**
 * PUBLIC wrapper over `resolveFrameSign` — R5 W2 (frame facet, design §27.3) consuming
 * surfaces (get_positions, get_strength, query_signals) call this to re-base
 * positional/strength/signal facts onto a non-lagna reference frame, rather than
 * re-deriving frame → reference-sign resolution themselves (single-source mandate,
 * design §19 — the resolver already solved this in W1; don't build a parallel one).
 */
export async function resolveFrameReferenceSign(
  chart_id: string,
  frame: ReferenceFrame,
  opts?: { ayanamsha_id?: string },
): Promise<{ sign: ZodiacSign; fact_ids: string[] }> {
  const ctx: ResolveCtx = { chart_id, ayanamsha_id: opts?.ayanamsha_id ?? DEFAULT_AYANAMSHA }
  return resolveFrameSign(ctx, frame)
}

async function fetchD1OccupantsOfHouse(ctx: ResolveCtx, house: number): Promise<{ grahas: string[]; fact_ids: string[] }> {
  const res = await query<{ fact_id: string; fact_subject: string }>(
    `SELECT fact_id, fact_subject FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_position'
       AND fact_key = 'house_d1' AND fact_value_num = $3`,
    [ctx.chart_id, ctx.ayanamsha_id, house],
  )
  const grahas = res.rows
    .map(r => r.fact_subject)
    .filter(subj => subj !== 'LAGNA')
    .map(subj => GRAHA_CODE_TO_NAME[subj] ?? subj)
  return { grahas, fact_ids: res.rows.map(r => r.fact_id) }
}

async function fetchVargaOccupantsOfHouse(
  ctx: ResolveCtx,
  varga: string,
  house: number,
): Promise<{ grahas: string[]; fact_ids: string[] }> {
  const res = await query<{ id: string; graha: string }>(
    `SELECT id, graha FROM chart_divisionals
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND varga = $3 AND house = $4
       AND formula_provenance_text = 'whole_sign' AND graha NOT IN ('ALL', 'karya', 'Lagna')`,
    [ctx.chart_id, ctx.ayanamsha_id, varga, house],
  )
  return { grahas: res.rows.map(r => r.graha), fact_ids: res.rows.map(r => r.id) }
}

async function fetchKarakaRow(
  ctx: ResolveCtx,
  factSubject: string,
): Promise<{ graha: string | null; house: number | null; sign: string | null; fact_ids: string[] }> {
  // karaka_chara_position value-rows in chart_facts do not carry a per-row school tag
  // (only 'karaka_school' rows do, with no shared row id to join on). Both canonical charts
  // were verified to have the parashari/kn_rao schools agree on assigned_graha/house/sign for
  // every karaka the two schemes share (only STRIKARAKA, the 8th karaka, is kn_rao-only) — so
  // reading the value rows directly is safe regardless of which school the caller asked for.
  // Documented here rather than silently assumed; a future chart where the schools diverge
  // would need a real per-row school column upstream (the `school` param on the `karaka`
  // AddressExpression is preserved on the RESULT for the caller's audit trail either way).
  const res = await query<{ fact_id: string; fact_key: string; fact_value_text: string | null; fact_value_num: string | null }>(
    `SELECT fact_id, fact_key, fact_value_text, fact_value_num
     FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'karaka_chara_position'
       AND fact_subject = $3 AND fact_key IN ('assigned_graha', 'house_d1', 'sign')`,
    [ctx.chart_id, ctx.ayanamsha_id, factSubject],
  )
  let graha: string | null = null
  let house: number | null = null
  let sign: string | null = null
  const fact_ids: string[] = []
  for (const r of res.rows) {
    fact_ids.push(r.fact_id)
    if (r.fact_key === 'assigned_graha' && graha === null) graha = r.fact_value_text
    if (r.fact_key === 'house_d1' && house === null) house = r.fact_value_num !== null ? Number(r.fact_value_num) : null
    if (r.fact_key === 'sign' && sign === null) sign = r.fact_value_text
  }
  return { graha, house, sign, fact_ids: [...new Set(fact_ids)] }
}

/** kp paradigm — cusp_kp_lords value-rows for one whole-sign house-as-cusp (design §27.4
 *  "sub-lord/cusp addressing"). fact_subject convention verified against the canonical chart:
 *  CUSP_01..CUSP_12 (zero-padded two-digit), fact_key in {prana_lord, star_lord, sub_lord,
 *  sub_sub_lord}. */
async function fetchCuspKpLords(
  ctx: ResolveCtx,
  cusp: number,
): Promise<{ prana_lord: string | null; star_lord: string | null; sub_lord: string | null; sub_sub_lord: string | null; fact_ids: string[] }> {
  const factSubject = `CUSP_${String(cusp).padStart(2, '0')}`
  const res = await query<{ fact_id: string; fact_key: string; fact_value_text: string | null }>(
    `SELECT fact_id, fact_key, fact_value_text
     FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'cusp_kp_lords'
       AND fact_subject = $3 AND fact_key IN ('prana_lord', 'star_lord', 'sub_lord', 'sub_sub_lord')`,
    [ctx.chart_id, ctx.ayanamsha_id, factSubject],
  )
  let prana_lord: string | null = null
  let star_lord: string | null = null
  let sub_lord: string | null = null
  let sub_sub_lord: string | null = null
  const fact_ids: string[] = []
  for (const r of res.rows) {
    fact_ids.push(r.fact_id)
    if (r.fact_key === 'prana_lord') prana_lord = r.fact_value_text
    if (r.fact_key === 'star_lord') star_lord = r.fact_value_text
    if (r.fact_key === 'sub_lord') sub_lord = r.fact_value_text
    if (r.fact_key === 'sub_sub_lord') sub_sub_lord = r.fact_value_text
  }
  return { prana_lord, star_lord, sub_lord, sub_sub_lord, fact_ids }
}

/** tajika paradigm — saham_position value-row for one named sāham (design §27.4 "varshaphala/
 *  saham" addressing). Unknown codes are passed through uppercased under the `SAHAM_<CODE>`
 *  naming convention observed on both canonical charts (e.g. SAHAM_AASTHA, SAHAM_AKSA). */
async function fetchSaham(
  ctx: ResolveCtx,
  factSubject: string,
): Promise<{ sign: string | null; house: number | null; sign_lord: string | null; fact_ids: string[] }> {
  const res = await query<{ fact_id: string; fact_key: string; fact_value_text: string | null; fact_value_num: string | null }>(
    `SELECT fact_id, fact_key, fact_value_text, fact_value_num
     FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'saham_position'
       AND fact_subject = $3 AND fact_key IN ('sign', 'house_d1', 'sign_lord')`,
    [ctx.chart_id, ctx.ayanamsha_id, factSubject],
  )
  let sign: string | null = null
  let house: number | null = null
  let sign_lord: string | null = null
  const fact_ids: string[] = []
  for (const r of res.rows) {
    fact_ids.push(r.fact_id)
    if (r.fact_key === 'sign') sign = r.fact_value_text
    if (r.fact_key === 'house_d1') house = r.fact_value_num !== null ? Number(r.fact_value_num) : null
    if (r.fact_key === 'sign_lord') sign_lord = r.fact_value_text
  }
  return { sign, house, sign_lord, fact_ids }
}

// ─────────────────────────────────────────────────────────────────────────────
// § PARADIGM coherence guard (design §27.4, R5 W2)
// ─────────────────────────────────────────────────────────────────────────────

/** Which paradigm an address TYPE is specific to; absent from this map = paradigm-neutral
 *  (resolves identically under every paradigm — see module header). */
const PARADIGM_SPECIFIC_TYPE: Partial<Record<AddressExpression['type'], Paradigm>> = {
  karaka: 'jaimini',
  sub_lord_of: 'kp',
  saham: 'tajika',
}

/** Recursively collect every address-expression `type` appearing in an expression tree
 *  (including nested `of`/`from` sub-expressions) so the coherence guard can inspect the
 *  WHOLE call, not just its top node. */
function collectExpressionTypes(
  expr: AddressExpression,
  acc: Set<AddressExpression['type']> = new Set(),
): Set<AddressExpression['type']> {
  acc.add(expr.type)
  if (expr.type === 'dispositor_of') collectExpressionTypes(expr.of, acc)
  if (expr.type === 'bhava_from' && typeof expr.from !== 'string') collectExpressionTypes(expr.from, acc)
  return acc
}

/**
 * THE PARADIGM COHERENCE GUARD (design §27.4). Called by `resolveAddress` on every
 * resolution — never opt-in, so no caller can bypass it. Throws `ParadigmMixError` when:
 *   (a) the expression tree itself contains address types specific to TWO DIFFERENT
 *       paradigms (e.g. a jaimini `karaka` nested under a kp construct) — this is the
 *       "subtle sin of mixing paradigms mid-answer" regardless of what the caller asked for;
 *   (b) the caller passed an explicit `paradigm` that conflicts with a paradigm-specific
 *       address type actually present in the expression.
 * Paradigm-neutral types (graha/sign/bhava/lord_of/dispositor_of/bhava_from/occupants_of)
 * never trigger either check — they are valid substrate under any paradigm (JL-006).
 */
export function assertParadigmCoherent(expr: AddressExpression, paradigm?: Paradigm): void {
  const types = collectExpressionTypes(expr)
  const specificParadigmsUsed = new Set<Paradigm>()
  for (const t of types) {
    const p = PARADIGM_SPECIFIC_TYPE[t]
    if (p) specificParadigmsUsed.add(p)
  }
  if (specificParadigmsUsed.size > 1) {
    throw new ParadigmMixError(
      `Address expression mixes paradigm-specific addressing from ${[...specificParadigmsUsed].sort().join(' + ')} ` +
        `within a single resolution. Design §27.4 requires a COHERENT interpretive frame per response — ` +
        `resolve each paradigm's address in a separate call, not chained together in one.`,
    )
  }
  if (paradigm) {
    for (const t of types) {
      const p = PARADIGM_SPECIFIC_TYPE[t]
      if (p && p !== paradigm) {
        throw new ParadigmMixError(
          `Address type "${t}" is specific to the ${p} paradigm, but paradigm:"${paradigm}" was requested. ` +
            `Design §27.4: paradigm switches the COHERENT interpretive frame — a "${paradigm}"-paradigm call ` +
            `cannot resolve a ${p}-specific address type.`,
        )
      }
    }
  }
}

/** The effective paradigm a resolved expression ran under: the caller's explicit choice if
 *  given, else the paradigm implied by whichever paradigm-specific type the expression used
 *  (guaranteed unique by `assertParadigmCoherent` having already run), else the 'parashari'
 *  default for an all-paradigm-neutral expression. */
function effectiveParadigm(expr: AddressExpression, explicit?: Paradigm): Paradigm {
  if (explicit) return explicit
  for (const t of collectExpressionTypes(expr)) {
    const p = PARADIGM_SPECIFIC_TYPE[t]
    if (p) return p
  }
  return 'parashari'
}

// ─────────────────────────────────────────────────────────────────────────────
// § Evaluator — recursive over AddressExpression
// ─────────────────────────────────────────────────────────────────────────────

interface EvalResult {
  entities: ResolvedEntity[]
  chain: string[]
}

async function evaluate(ctx: ResolveCtx, expr: AddressExpression): Promise<EvalResult> {
  switch (expr.type) {
    case 'graha': {
      const varga = expr.varga ?? 'D1'
      const g = await resolveGrahaEntity(ctx, expr.graha, varga)
      const chain = [
        g.house !== null
          ? `${g.graha} is placed in house ${g.house}${g.sign ? ` (${g.sign})` : ''} in ${varga}.`
          : `${g.graha}'s placement in ${varga} could not be resolved (no matching row).`,
      ]
      return { entities: [g], chain }
    }

    case 'sign': {
      assertZodiacSign(expr.sign)
      const entity: ResolvedSign = { kind: 'sign', sign: expr.sign, house_number: 0, frame: 'lagna', fact_ids: [] }
      return { entities: [entity], chain: [`Address resolves to the sign ${expr.sign} directly.`] }
    }

    case 'bhava': {
      const frame = expr.frame ?? 'lagna'
      const { sign: refSign, fact_ids } = await resolveFrameSign(ctx, frame)
      const targetSign = signAtHouseOffset(refSign, expr.house)
      const entity: ResolvedSign = { kind: 'sign', sign: targetSign, house_number: expr.house, frame, fact_ids }
      return {
        entities: [entity],
        chain: [`House ${expr.house} counted from ${frame} (${refSign}) = ${targetSign}.`],
      }
    }

    case 'lord_of': {
      const frame = expr.frame ?? 'lagna'
      const bhavaResult = await evaluate(ctx, { type: 'bhava', house: expr.house, frame })
      const bhavaEntity = bhavaResult.entities[0] as ResolvedSign
      const lordName = SIGN_LORDS[bhavaEntity.sign]
      const lordEntity = await resolveGrahaEntity(ctx, lordName, 'D1')
      const chain = [
        ...bhavaResult.chain,
        `${bhavaEntity.sign} is ruled by ${lordName} (classical rulership).`,
        lordEntity.house !== null
          ? `The ${ordinal(expr.house)} lord is ${lordName}, placed in the ${ordinal(lordEntity.house)}${lordEntity.sign ? ` (${lordEntity.sign})` : ''}.`
          : `${lordName}'s own placement could not be resolved.`,
      ]
      return { entities: [lordEntity], chain }
    }

    case 'dispositor_of': {
      const ofResult = await evaluate(ctx, expr.of)
      const ofEntity = ofResult.entities[0]
      let sourceSign: ZodiacSign | null = null
      let sourceLabel: string
      if (ofEntity.kind === 'graha') {
        if (!ofEntity.sign) {
          throw new AddressResolutionError(
            `dispositor_of: could not resolve a sign for ${ofEntity.graha} (varga ${ofEntity.varga}) — cannot chain further.`,
          )
        }
        assertZodiacSign(ofEntity.sign)
        sourceSign = ofEntity.sign
        sourceLabel = ofEntity.graha
      } else if (ofEntity.kind === 'sign') {
        sourceSign = ofEntity.sign
        sourceLabel = ofEntity.sign
      } else {
        throw new AddressResolutionError(`dispositor_of: cannot take the dispositor of a "${ofEntity.kind}" address.`)
      }
      const varga = expr.varga ?? 'D1'
      const dispositorName = SIGN_LORDS[sourceSign]
      const dispositorEntity = await resolveGrahaEntity(ctx, dispositorName, varga)
      const chain = [
        ...ofResult.chain,
        `The dispositor of ${sourceLabel} (${sourceSign}) is ${dispositorName}.`,
        dispositorEntity.house !== null
          ? `${dispositorName} is placed in house ${dispositorEntity.house}${dispositorEntity.sign ? ` (${dispositorEntity.sign})` : ''} in ${varga}.`
          : `${dispositorName}'s placement in ${varga} could not be resolved.`,
      ]
      return { entities: [dispositorEntity], chain }
    }

    case 'bhava_from': {
      let refSign: ZodiacSign
      let fromFactIds: string[] = []
      let fromLabel: string
      if (typeof expr.from === 'string') {
        const r = await resolveFrameSign(ctx, expr.from)
        refSign = r.sign
        fromFactIds = r.fact_ids
        fromLabel = expr.from
      } else {
        const r = await evaluate(ctx, expr.from)
        const e = r.entities[0]
        if (e.kind === 'graha') {
          if (!e.sign) throw new AddressResolutionError(`bhava_from: could not resolve a sign for the "from" graha.`)
          assertZodiacSign(e.sign)
          refSign = e.sign
          fromFactIds = e.fact_ids
          fromLabel = e.graha
        } else if (e.kind === 'sign') {
          refSign = e.sign
          fromFactIds = e.fact_ids
          fromLabel = e.sign
        } else {
          throw new AddressResolutionError(`bhava_from: "from" must resolve to a graha or a sign, got "${e.kind}".`)
        }
      }
      const targetSign = signAtHouseOffset(refSign, expr.house)
      const entity: ResolvedSign = {
        kind: 'sign',
        sign: targetSign,
        house_number: expr.house,
        frame: (typeof expr.from === 'string' ? expr.from : 'lagna') as ReferenceFrame,
        fact_ids: fromFactIds,
      }
      return {
        entities: [entity],
        chain: [`House ${expr.house} counted from ${fromLabel} (${refSign}) = ${targetSign}.`],
      }
    }

    case 'karaka': {
      const upperCode = expr.code.trim().toUpperCase()
      const factSubject = KARAKA_CODE_TO_SUBJECT[upperCode] ?? upperCode.toUpperCase()
      if (!Object.values(KARAKA_CODE_TO_SUBJECT).includes(factSubject)) {
        throw new AddressResolutionError(
          `Unknown karaka code "${expr.code}". Supported: ${Object.keys(KARAKA_CODE_TO_SUBJECT).join(', ')}.`,
        )
      }
      // SK (Strikaraka, the 8th karaka) exists only under the kn_rao_rahu_included 8-karaka
      // scheme; the classical 7-karaka Parashari scheme has no SK row. Default the school
      // accordingly unless the caller overrides.
      const school: KarakaSchool = expr.school ?? (factSubject === 'STRIKARAKA' ? 'kn_rao_rahu_included' : 'parashari_rahu_excluded')
      const row = await fetchKarakaRow(ctx, factSubject)
      if (!row.graha) {
        throw new AddressResolutionError(
          `Could not resolve karaka "${expr.code}" (${factSubject}) under school "${school}" for chart ${ctx.chart_id}.`,
        )
      }
      const entity: ResolvedKaraka = {
        kind: 'karaka',
        code: upperCode,
        fact_subject: factSubject,
        graha: row.graha,
        house: row.house,
        sign: row.sign,
        school,
        fact_ids: row.fact_ids,
      }
      return {
        entities: [entity],
        chain: [
          `${factSubject} (${school}) = ${row.graha}` +
            (row.house !== null ? `, placed in house ${row.house}${row.sign ? ` (${row.sign})` : ''}.` : '.'),
        ],
      }
    }

    case 'occupants_of': {
      const frame = expr.frame ?? 'lagna'
      const varga = expr.varga ?? 'D1'
      const { sign: refSign, fact_ids: frameFactIds } = await resolveFrameSign(ctx, frame)
      const targetSign = signAtHouseOffset(refSign, expr.house)
      const { grahas, fact_ids } =
        varga === 'D1'
          ? await fetchD1OccupantsOfHouse(ctx, expr.house)
          : await fetchVargaOccupantsOfHouse(ctx, varga, expr.house)
      const entity: ResolvedOccupants = {
        kind: 'occupants',
        house: expr.house,
        sign: targetSign,
        varga,
        frame,
        grahas,
        fact_ids: [...frameFactIds, ...fact_ids],
      }
      return {
        entities: [entity],
        chain: [
          `House ${expr.house} from ${frame} = ${targetSign} in ${varga}; occupants: ${
            grahas.length ? grahas.join(', ') : '(none)'
          }.`,
        ],
      }
    }

    case 'sub_lord_of': {
      const { prana_lord, star_lord, sub_lord, sub_sub_lord, fact_ids } = await fetchCuspKpLords(ctx, expr.cusp)
      if (!sub_lord) {
        throw new AddressResolutionError(
          `Could not resolve the kp sub-lord of cusp ${expr.cusp} for chart ${ctx.chart_id}: no cusp_kp_lords row found.`,
        )
      }
      const entity: ResolvedSubLord = {
        kind: 'sub_lord',
        cusp: expr.cusp,
        prana_lord,
        star_lord,
        sub_lord,
        sub_sub_lord,
        fact_ids,
      }
      return {
        entities: [entity],
        chain: [
          `kp cusp ${expr.cusp} significator chain: prāṇa-lord ${prana_lord ?? '?'} → star-lord ${star_lord ?? '?'} → ` +
            `sub-lord ${sub_lord} → sub-sub-lord ${sub_sub_lord ?? '?'}. kp doctrine reads the sub-lord as the ` +
            `final determinant.`,
        ],
      }
    }

    case 'saham': {
      const codeRaw = expr.code.trim().toUpperCase()
      const factSubject = SAHAM_CODE_TO_SUBJECT[codeRaw] ?? `SAHAM_${codeRaw}`
      const { sign, house, sign_lord, fact_ids } = await fetchSaham(ctx, factSubject)
      if (!sign) {
        throw new AddressResolutionError(
          `Could not resolve sāham "${expr.code}" (${factSubject}) for chart ${ctx.chart_id}: no saham_position row found.`,
        )
      }
      const entity: ResolvedSaham = {
        kind: 'saham',
        code: codeRaw,
        fact_subject: factSubject,
        sign,
        house,
        sign_lord,
        fact_ids,
      }
      return {
        entities: [entity],
        chain: [
          `${factSubject} falls in ${sign}` +
            (house !== null ? ` (house ${house})` : '') +
            (sign_lord ? `, ruled by ${sign_lord}.` : '.'),
        ],
      }
    }

    default: {
      const _exhaustive: never = expr
      throw new AddressResolutionError(`Unknown address expression type: ${JSON.stringify(_exhaustive)}`)
    }
  }
}

function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`
}

// ─────────────────────────────────────────────────────────────────────────────
// § Public entry point
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Resolve an astrological address expression against one chart. Pure read — no writes,
 * no shared-state caching. Accepts either a structured AddressExpression (recommended for
 * programmatic callers) or a design-§27.2-style DSL string (see parseAddressExpression).
 *
 * `opts.paradigm` (design §27.4): the caller's declared coherent interpretive frame. Every
 * call runs `assertParadigmCoherent` FIRST (before any DB read) — a paradigm-mixed expression
 * throws `ParadigmMixError` and never touches the database. See module header + design §27.4.
 */
export async function resolveAddress(
  chart_id: string,
  expression: AddressExpression | string,
  opts?: { ayanamsha_id?: string; paradigm?: Paradigm },
): Promise<ResolvedAddress> {
  const expr = typeof expression === 'string' ? parseAddressExpression(expression) : expression
  assertParadigmCoherent(expr, opts?.paradigm)
  const ctx: ResolveCtx = { chart_id, ayanamsha_id: opts?.ayanamsha_id ?? DEFAULT_AYANAMSHA }
  const { entities, chain } = await evaluate(ctx, expr)
  return { expression: expr, entities, chain, paradigm: effectiveParadigm(expr, opts?.paradigm) }
}

// ─────────────────────────────────────────────────────────────────────────────
// § DSL parser — the exact forms design §27.2 cites as examples, plus their compositions.
// Anything outside this grammar throws AddressResolutionError rather than guessing (B.10).
// ─────────────────────────────────────────────────────────────────────────────

const FRAME_WORDS = new Set<ReferenceFrame>(['lagna', 'chandra', 'surya', 'arudha', 'karakamsha'])
const FRAME_ALIASES: Record<string, ReferenceFrame> = {
  moon: 'chandra', sun: 'surya', al: 'arudha',
}

function isVargaToken(tok: string): boolean {
  return /^D\d+$/i.test(tok)
}

function normalizeVarga(tok: string): string {
  return tok.toUpperCase()
}

function parseFrameToken(tok: string): ReferenceFrame {
  const lower = tok.trim().toLowerCase()
  if (FRAME_WORDS.has(lower as ReferenceFrame)) return lower as ReferenceFrame
  if (FRAME_ALIASES[lower]) return FRAME_ALIASES[lower]
  throw new AddressResolutionError(`"${tok}" is not a recognized reference frame.`)
}

/** Split top-level comma-separated arguments, respecting nested parens. */
function splitArgs(inner: string): string[] {
  const args: string[] = []
  let depth = 0
  let cur = ''
  for (const ch of inner) {
    if (ch === '(') depth++
    if (ch === ')') depth--
    if (ch === ',' && depth === 0) {
      args.push(cur.trim())
      cur = ''
    } else {
      cur += ch
    }
  }
  if (cur.trim()) args.push(cur.trim())
  return args
}

function parseHouseArg(arg: string): HouseNumber {
  const cleaned = arg.trim()
  const m = cleaned.match(/^(?:bhava|cusp)[\s:]+(\d{1,2})$/i) ?? cleaned.match(/^(\d{1,2})$/)
  if (!m) throw new AddressResolutionError(`Could not parse a house number from "${arg}".`)
  const n = Number(m[1])
  if (n < 1 || n > 12) throw new AddressResolutionError(`House number out of range 1..12: ${n}`)
  return n as HouseNumber
}

function parseSubExpr(arg: string): AddressExpression {
  const trimmed = arg.trim()
  const call = trimmed.match(/^([a-zA-Z_]+)\((.*)\)$/s)
  if (call) return parseAddressExpression(trimmed)
  // Bare token — could be a bhava reference or a graha name used as a nested "of"/"from" argument.
  if (/^bhava[\s:]+\d{1,2}$/i.test(trimmed)) {
    return { type: 'bhava', house: parseHouseArg(trimmed) }
  }
  return { type: 'graha', graha: trimmed } // throws downstream (grahaCodeOf) if not a known graha
}

/**
 * Parse the exact DSL forms cited in design §27.2:
 *   lord_of(bhava 7)            dispositor_of(Venus)          bhava_from(Moon, 10)
 *   karaka('AK')                occupants_of(bhava 4, D9)      dispositor_of(lord_of(10))
 * Case-insensitive on function names and frame words. Anything else throws.
 */
export function parseAddressExpression(input: string): AddressExpression {
  const src = input.trim()
  const m = src.match(/^([a-zA-Z_]+)\s*\((.*)\)$/s)
  if (!m) throw new AddressResolutionError(`Could not parse address expression: "${input}"`)
  const fn = m[1].toLowerCase()
  const args = splitArgs(m[2])

  switch (fn) {
    case 'lord_of': {
      if (args.length < 1) throw new AddressResolutionError(`lord_of(...) requires a house argument.`)
      const house = parseHouseArg(args[0])
      const frame = args[1] ? parseFrameToken(args[1]) : undefined
      return { type: 'lord_of', house, frame }
    }
    case 'dispositor_of': {
      if (args.length < 1) throw new AddressResolutionError(`dispositor_of(...) requires one argument.`)
      const of = parseSubExpr(args[0])
      const varga = args[1] ? normalizeVarga(args[1]) : undefined
      return { type: 'dispositor_of', of, varga }
    }
    case 'bhava_from': {
      if (args.length < 2) throw new AddressResolutionError(`bhava_from(from, house[, varga]) requires 2 args.`)
      const fromArg = args[0].trim()
      let from: ReferenceFrame | AddressExpression
      try {
        from = parseFrameToken(fromArg)
      } catch {
        from = parseSubExpr(fromArg)
      }
      const house = parseHouseArg(args[1])
      const varga = args[2] ? normalizeVarga(args[2]) : undefined
      return { type: 'bhava_from', from, house, varga }
    }
    case 'karaka': {
      if (args.length < 1) throw new AddressResolutionError(`karaka(...) requires a code argument.`)
      const codeRaw = args[0].trim().replace(/^['"]|['"]$/g, '')
      const school = args[1] ? (args[1].trim().replace(/^['"]|['"]$/g, '') as KarakaSchool) : undefined
      return { type: 'karaka', code: codeRaw, school }
    }
    case 'occupants_of': {
      if (args.length < 1) throw new AddressResolutionError(`occupants_of(...) requires a house argument.`)
      const house = parseHouseArg(args[0])
      let varga: string | undefined
      let frame: ReferenceFrame | undefined
      for (const rest of args.slice(1)) {
        if (isVargaToken(rest)) varga = normalizeVarga(rest)
        else frame = parseFrameToken(rest)
      }
      return { type: 'occupants_of', house, varga, frame }
    }
    case 'bhava': {
      if (args.length < 1) throw new AddressResolutionError(`bhava(...) requires a house argument.`)
      const house = parseHouseArg(args[0])
      const frame = args[1] ? parseFrameToken(args[1]) : undefined
      return { type: 'bhava', house, frame }
    }
    case 'graha': {
      if (args.length < 1) throw new AddressResolutionError(`graha(...) requires a graha name.`)
      const varga = args[1] ? normalizeVarga(args[1]) : undefined
      return { type: 'graha', graha: args[0].trim(), varga }
    }
    case 'sub_lord_of': {
      if (args.length < 1) throw new AddressResolutionError(`sub_lord_of(...) requires a cusp argument.`)
      const cusp = parseHouseArg(args[0])
      return { type: 'sub_lord_of', cusp }
    }
    case 'saham': {
      if (args.length < 1) throw new AddressResolutionError(`saham(...) requires a code argument.`)
      const codeRaw = args[0].trim().replace(/^['"]|['"]$/g, '')
      return { type: 'saham', code: codeRaw }
    }
    default:
      throw new AddressResolutionError(
        `Unknown address function "${fn}". Supported: lord_of, dispositor_of, bhava_from, karaka, occupants_of, bhava, graha, sub_lord_of, saham.`,
      )
  }
}
