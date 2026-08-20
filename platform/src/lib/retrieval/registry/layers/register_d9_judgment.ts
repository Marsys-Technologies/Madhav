/**
 * D9 — judgment_query: THE BHAVA-ADHYAYA RECIPE AS ONE INSTRUMENT
 * ===================================================================
 * GATE A compliance: per-wave registration file. Does NOT edit registry/index.ts or
 * registry/types.ts.
 *
 * R5 W3 (design §28.1, brief §3 "W3 — THE ASTROLOGICAL SURFACE"). Implements the
 * classical judgment protocol for ANY bhava-question in ONE call — general enough for
 * "how is the marriage?" (bhava 7) as well as career/wealth/health/progeny or a bare
 * house number — not hardcoded to marriage.
 *
 * THE CHECKLIST (design §28.1, cited per step below):
 *   1. bhava condition                          — §28.1 "bhava condition"
 *   2. bhavesha (lord) condition + placement     — §28.1 "bhavesha condition + placement"
 *   3. karaka condition                          — §28.1 "karaka condition"
 *   4. occupants + aspecting grahas               — §28.1 "occupants + aspecting grahas"
 *   5. from-lagna AND from-chandra (Sudarshana)   — §28.1 "from-lagna AND from-chandra"
 *   6. operative-varga confirmation status         — §28.1 "operative-varga confirmation status"
 *   7. bearing yogas (formed AND notably-absent)   — §28.1 "bearing yogas (formed AND notably-absent)"
 *   8. promise-register verdict                    — §28.1 "promise-register verdict"
 *   9. timing hooks                                — §28.1 "timing hooks"
 * Each element is GRADED (epistemic + strength) with its resolution chain, assembled into
 * a `receipt` in the classical units design §28.6 specifies:
 *   {bhava, bhavesha, karaka, from_moon, varga_confirmed, yogas_checked, bhanga_checked, timing_anchored}
 *
 * REUSE, NOT REBUILD (design §19 single-source mandate): every bhava/lord/karaka/occupant/
 * from-Moon resolution goes through the SAME `resolveAddress`/address_resolver.ts the W1/W2
 * waves built and tested — this file adds NO parallel resolver logic. Varga confirmation
 * reuses `getDivisionalsCapability`; yoga/dosha signals reuse `querySignalsCapability`;
 * timing reuses `getDashasCapability`; the frame-safety header reuses `getChartHeaderCapability`.
 *
 * THE SHASTRA MAP (design §28.5): domain → {bhava, karaka(s), operative varga}. Ratified per
 * design's own worked examples (marriage→7th/Venus/D9; career→10th/Sun-Mercury-Saturn/D10)
 * and — for domains the design doesn't spell out (wealth/health/progeny) — the SAME mapping
 * `register_d8_assess_domain.ts`'s `assess_*` tools already use in production (2nd+11th/
 * Jupiter/wealth; 1st+6th+8th/Sun/health), so this instrument never contradicts the existing
 * apex_* tools it is designed to fold. See R5_JUDGMENT_LEDGER JL-015 for the full ruling
 * (karaka-gender-neutrality, bhanga-unbuilt honesty, verdict-is-not-a-calibrated-posterior).
 *
 * WHAT THIS INSTRUMENT DOES NOT DO (honest gaps, not silently invented — B.10):
 *   - "notably-absent" yogas / bhanga (cancellation) checking needs the D3 "near-miss band"
 *     design §12 names as a FUTURE data-plane addition (a small stored column at L2 regen).
 *     That column does not exist yet on any canonical chart. `bhanga_checked` in the receipt
 *     is honestly `false` with a note, never fabricated.
 *   - The `verdict` is a DETERMINISTIC weighted aggregation of already-computed dignity/
 *     strength/aspect/vargottama signals — never an LLM synthesis, never a probability. Its
 *     epistemic grade is capped at `structural_prior`; `calibrated_posterior` is reserved for
 *     L5 Mimamsa's own calibration loop (this instrument reads L1/L2 data, not L5).
 *
 * Tool: marsys://tool/L-JUDGMENT/judgment_query
 */
import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'
import { query } from '@/lib/db/client'
import {
  resolveAddress,
  GRAHA_CODE_TO_NAME,
  AddressResolutionError,
  type HouseNumber,
  type ResolvedGraha,
  type ResolvedSign,
  type ResolvedOccupants,
} from '../../address_resolver'
import { DEFAULT_AYANAMSHA } from '../constants'
import type { DrillPointerType, JudgmentFlagEntry } from '../../envelope'
import { judgmentFlag } from '../../envelope'
import { derivedHouses } from '@/lib/jyotish/bhavat_bhavam_map'
// ŚODHANA T5 (PŪRTI) — the three computed-but-never-joined classical legs + the
// served reading_checklist receipt (MC-030/031/033 + the Offer-Law completeness fix).
import {
  fetchSensitiveDegreeFirings,
  fetchKpCuspChain,
  fetchGocharaSweep,
  checklistExhaustiveness,
  DOMAIN_KP_CUSPS,
  type ChecklistUnit,
  type GocharaSweepWindow,
} from './reading_checklist'

// F-119 (EKAVĀKYATĀ A-06): attach resolution_disclosure to gochara_sweep rows.
// Mirrors the same helper in register_d8_assess_domain.ts — see that file for the
// full rationale. GocharaSweepWindow has only temporal_shape + peak_date to work
// from; the full deriveResolutionDisclosure() (register_gochara_windows.ts) is not
// reachable from this package.
interface SweepWindowDisclosure {
  is_timing_window: boolean
  timing_window_blocked_reason: 'era_scale_context' | 'bare_point_no_date' | null
}

function withSweepDisclosure(
  rows: GocharaSweepWindow[]
): Array<GocharaSweepWindow & { resolution_disclosure: SweepWindowDisclosure }> {
  const retained = rows.filter(
    (r) => !(r.temporal_shape === 'point' && r.peak_date == null)
  )
  return retained.map((row) => {
    const isPoint = row.temporal_shape === 'point'
    return {
      ...row,
      resolution_disclosure: isPoint
        ? { is_timing_window: true, timing_window_blocked_reason: null }
        : { is_timing_window: false, timing_window_blocked_reason: 'era_scale_context' },
    }
  })
}

// ── The Shastra Map (design §28.5) ───────────────────────────────────────────────

interface DomainSpec {
  bhava: HouseNumber
  /** Classical significator(s). Gender-neutral per design §28.5's own worked example
   *  (marriage→7th/Venus/D9) — no jaimini chara-karaka (DK) substitution here; that
   *  remains available separately via `karaka('DK')` on the address resolver. */
  karakas: string[]
  /** Operative varga for confirmation (design §28.1 "operative-varga confirmation"). */
  varga: string
  label: string
  /** Maps onto bodha_msr_signals.domain (query_signals.ts) — 'other' where no exact
   *  domain tag exists yet in the signal store. */
  signal_domain: string
  /** D-1.5b Lane B-4 (CR-97) — Bhavat-Bhavam "house of the house" derivation, backfilled
   *  from the shared registry (`bhavat_bhavam_map.ts`) right after SHASTRA_MAP below is
   *  declared. Optional in the type only because it is populated post-construction, not
   *  hand-authored per entry; every SHASTRA_MAP value has it set by the time this module
   *  finishes loading. Odd primary `bhava` -> real derived bhāvas; EVEN primary `bhava` ->
   *  always [] (the doctrine: even houses receive nothing — never fabricate a derivation
   *  for career/wealth/health/education/moksha/character/residence's even primaries). */
  derived_bhavas?: readonly number[]
}

export const SHASTRA_MAP: Record<string, DomainSpec> = {
  marriage:     { bhava: 7,  karakas: ['Venus'],                     varga: 'D9',  label: 'Marriage / Partnership', signal_domain: 'relationship' },
  relationship: { bhava: 7,  karakas: ['Venus'],                     varga: 'D9',  label: 'Marriage / Partnership', signal_domain: 'relationship' },
  partnership:  { bhava: 7,  karakas: ['Venus'],                     varga: 'D9',  label: 'Marriage / Partnership', signal_domain: 'relationship' },
  career:       { bhava: 10, karakas: ['Sun', 'Mercury', 'Saturn'],  varga: 'D10', label: 'Career / Vocation',      signal_domain: 'career' },
  vocation:     { bhava: 10, karakas: ['Sun', 'Mercury', 'Saturn'],  varga: 'D10', label: 'Career / Vocation',      signal_domain: 'career' },
  wealth:       { bhava: 2,  karakas: ['Jupiter'],                   varga: 'D2',  label: 'Wealth / Prosperity',    signal_domain: 'wealth' },
  finance:      { bhava: 2,  karakas: ['Jupiter'],                   varga: 'D2',  label: 'Wealth / Prosperity',    signal_domain: 'wealth' },
  health:       { bhava: 1,  karakas: ['Sun'],                       varga: 'D6',  label: 'Health / Vitality',      signal_domain: 'health' },
  vitality:     { bhava: 1,  karakas: ['Sun'],                       varga: 'D6',  label: 'Health / Vitality',      signal_domain: 'health' },
  progeny:      { bhava: 5,  karakas: ['Jupiter'],                   varga: 'D7',  label: 'Progeny / Children',     signal_domain: 'other' },
  children:     { bhava: 5,  karakas: ['Jupiter'],                   varga: 'D7',  label: 'Progeny / Children',     signal_domain: 'other' },
  // F-0756 fix: bhāva-4 is NOT "education" — its primary significations are mother/home/
  // property/happiness. Vidyā's operative bhāva for the recipe is the 4th vidyā-sthāna (BPHS)
  // but it is judged as ONE leg of a 2/4/5/9 set; karakas are Mercury (learning), Jupiter
  // (jñāna), Ketu (deep insight/research). D24 (siddhāṃśa) is the education varga.
  education:    { bhava: 4,  karakas: ['Mercury', 'Jupiter', 'Ketu'], varga: 'D24', label: 'Education / Vidyā',      signal_domain: 'other' },
  vidya:        { bhava: 4,  karakas: ['Mercury', 'Jupiter', 'Ketu'], varga: 'D24', label: 'Education / Vidyā',      signal_domain: 'other' },
  // Spirituality = DHARMA (9th house) — Jupiter/Ketu, D20. Distinct from moksha below.
  spirituality: { bhava: 9,  karakas: ['Jupiter', 'Ketu'],           varga: 'D20', label: 'Spirituality / Dharma',  signal_domain: 'spirituality' },
  // Moksha = the 4-8-12 mokṣa-trikoṇa + Ketu axis (F-0973/0974) — NOT a 9th-house/dharma alias.
  // Operative bhāva 12 (mokṣa-sthāna/vyaya); karakas Ketu (mokṣa-kāraka), Saturn (vairāgya),
  // Jupiter (guru/jñāna); D20 (vimśāṃśa, upāsanā). signal_domain uses the 'spirituality' tag
  // (there is no stored 'moksha' domain tag) — the recipe's bhāva/karaka legs carry the mokṣa
  // specificity.
  moksha:       { bhava: 12, karakas: ['Ketu', 'Saturn', 'Jupiter'], varga: 'D20', label: 'Moksha / Liberation',    signal_domain: 'spirituality' },
  liberation:   { bhava: 12, karakas: ['Ketu', 'Saturn', 'Jupiter'], varga: 'D20', label: 'Moksha / Liberation',    signal_domain: 'spirituality' },
  // Character / buddhi — 1st (prakṛti/temperament) is primary; Moon (manas) + Mercury (buddhi)
  // are the karakas. D1 lagna is the operative frame for temperament.
  character:    { bhava: 1,  karakas: ['Moon', 'Mercury'],           varga: 'D1',  label: 'Character / Buddhi',     signal_domain: 'character' },
  buddhi:       { bhava: 1,  karakas: ['Moon', 'Mercury'],           varga: 'D1',  label: 'Character / Buddhi',     signal_domain: 'character' },
  // Home / residence / immovable property — 4th sukha-bhāva; Moon (home/mother), Mars
  // (land/immovables); D4 (caturthāṃśa). This is bhāva-4's REAL domain (F-0756), not education.
  residence:    { bhava: 4,  karakas: ['Moon', 'Mars'],              varga: 'D4',  label: 'Home / Residence / Property', signal_domain: 'other' },
  property:     { bhava: 4,  karakas: ['Moon', 'Mars'],              varga: 'D4',  label: 'Home / Residence / Property', signal_domain: 'other' },
  home:         { bhava: 4,  karakas: ['Moon', 'Mars'],              varga: 'D4',  label: 'Home / Residence / Property', signal_domain: 'other' },
  // F-55: 4 canonical domains absent from SHASTRA_MAP — reconcile CANONICAL_DOMAINS 1:1.
  // Family / kutumba — 2nd house (kutumba-sthāna, family lineage, speech); karakas Jupiter
  // (family prosperity, sons) + Moon (nurturing/maternal bond); D12 (dvādaśāṃśa, lineage/ancestry).
  // Bhavat-Bhavam: bhava 2 is EVEN → derived_bhavas: [] (even houses receive nothing — doctrine).
  family:     { bhava: 2,  karakas: ['Jupiter', 'Moon'],              varga: 'D12', label: 'Family / Kutumba',            signal_domain: 'other' },
  // General / overall life pattern — lagna (1st house) as the catch-all life lens; karakas Sun
  // (ātmakāraka/soul) + Moon (manas/mind); D1 (natal chart, full-chart read).
  general:    { bhava: 1,  karakas: ['Sun', 'Moon'],                  varga: 'D1',  label: 'General / Life Pattern',      signal_domain: 'other' },
  // Transition / transformation — 8th house (āyu-sthāna, sudden change, parivartan, hidden matters);
  // karakas Saturn (delay/vairāgya), Rahu (unexpected upheaval/foreign), Mars (acute crisis);
  // D8 (ashtamsha, transformative varga). Bhavat-Bhavam: bhava 8 EVEN → derived_bhavas: [].
  transition: { bhava: 8,  karakas: ['Saturn', 'Rahu', 'Mars'],       varga: 'D8',  label: 'Transition / Transformation', signal_domain: 'other' },
  // Travel / foreign — 9th house (dharma-sthāna, long journeys, fortune, foreign connections);
  // karakas Jupiter (long-distance dharma travel) + Rahu (foreign settlement, ativāsa);
  // D9 (navamsha, dharma/fortune varga). Bhavat-Bhavam: bhava 9 ODD → derived_bhavas: [5, 11].
  travel:     { bhava: 9,  karakas: ['Jupiter', 'Rahu'],              varga: 'D9',  label: 'Travel / Foreign',            signal_domain: 'other' },
}

// D-1.5b Lane B-4 (CR-97): extend every SHASTRA_MAP domain with its Bhavat-Bhavam derived
// bhāvas — {primary} ∪ {derived}, derived-part data-sourced from bhavat_bhavam_map.ts's
// registry (never hardcoded here). Pure append: does not modify any existing SHASTRA_MAP
// entry above. Per the hard doctrinal rule (even houses receive nothing), only domains whose
// primary `bhava` is ODD get a non-empty derived_bhavas:
//   marriage/relationship/partnership (bhava 7 -> [4, 10])
//   progeny/children                 (bhava 5 -> [3, 9])
//   spirituality                     (bhava 9 -> [5, 11])
//   health/vitality, character/buddhi (both bhava 1 -> [1, 7])
// Every EVEN-primary domain resolves to [] — career/vocation (10), wealth/finance (2),
// education/vidya (4), moksha/liberation (12), residence/property/home (4) — intentional,
// not a gap (BRIEF_D1_5B.md Lane B-4: "even houses receive nothing").
for (const spec of Object.values(SHASTRA_MAP)) {
  spec.derived_bhavas = derivedHouses(spec.bhava)
}

/** Reverse map — used only when the caller gives a bare bhava number with no domain. EXPLICIT
 *  (WP-1.2β, F-0756): un-collapses the previous auto-built first-hit map that mis-mapped bhāva-4
 *  to "education". Each house maps to its DOMINANT classical single-word signification so a bare
 *  bhāva number still assembles a sensible karaka/varga leg; houses with no dedicated domain
 *  spec (3rd) intentionally fall through to the bare bhāva/bhāveśa recipe. */
const BHAVA_TO_DOMAIN: Record<number, string> = {
  1:  'character',    // tanu — self / temperament / constitution
  2:  'wealth',       // dhana — accumulated wealth (also vāk/family)
  // 3 (parākrama/siblings): no dedicated domain — bare recipe
  4:  'residence',    // sukha — home / mother / property (NOT education; F-0756)
  5:  'progeny',      // santāna — children (also buddhi/pūrva-puṇya)
  6:  'health',       // roga — disease / debts / enemies
  7:  'relationship', // kalatra — spouse / partnership
  8:  'moksha',       // randhra — transformation / longevity (mokṣa-trikoṇa leg)
  9:  'spirituality', // dharma — fortune / higher wisdom
  10: 'career',       // karma — profession
  11: 'wealth',       // lābha — gains / income
  12: 'moksha',       // vyaya — mokṣa-sthāna / liberation / loss
}

// Simple, deterministic, classically-uncontested dignity/benefic weighting — never an LLM
// judgment, never a fabricated probability. Design §28.1 "graded (epistemic + strength)".
const DIGNITY_WEIGHT: Record<string, number> = {
  exalted: 2, own: 1.5, moolatrikona: 1.5, great_friend: 1, friend: 0.5,
  neutral: 0, enemy: -0.5, great_enemy: -1, debilitated: -2,
}
const NATURAL_BENEFICS = new Set(['Jupiter', 'Venus', 'Mercury', 'Moon'])
const NATURAL_MALEFICS = new Set(['Saturn', 'Mars', 'Rahu', 'Ketu', 'Sun'])

interface GrahaCondition {
  graha: string
  graha_code: string
  house: number | null
  sign: string | null
  dignity_state: string | null
  dignity_weight: number | null
  shadbala_rupa: number | null
  fact_ids: string[]
}

// ── R-46: operative-varga dignity (WP-1.8) ────────────────────────────────────
// Classical grounding (B.3): Parashara holds the divisional (amsha) chart as the
// *ripening* of the rasi promise — "what is shown in the rasi is confirmed (or denied)
// in the amsha." BPHS Ch.6-7 (Shadvarga/Vargas) and the Parashari dictum that the D9
// (navamsha) is the "fruit" (phala) of the D1 promise for marriage/dharma make the
// operative-varga dignity of the bhāveśa and kāraka a first-class verdict term, not a
// decoration. Before WP-1.8 the composite weighted ONLY D1 (R-46: "varga evidence
// structurally cannot move a verdict"). This term reads the SAME frozen build-time
// dignity facts (graha_dignity_per_varga, subject `<VARGA>_<CODE>`) the D1 leg reads —
// it never recomputes dignity (§N.5: L1 is the authority).
//
// Weights are deliberately SUB-D1 (a varga refines, it does not overrule the rasi):
// bhāveśa operative-varga dignity ×0.75, kāraka(s) averaged ×0.5. When the operative
// varga IS D1 (character/buddhi domains) the term is SKIPPED to avoid double-counting
// the D1 dignity already in the composite.
const VARGA_BHAVESHA_WEIGHT = 0.75
const VARGA_KARAKA_WEIGHT = 0.5

// ── A3 (CR-92 residue, R-3): bearing-yoga term (ga_yoga_firings-authoritative) ─────────────────
// Before this pass, `bearing_yogas` read bodha_msr_signals via querySignalsCapability — an MSR
// projection that, live, returned `[]` for wealth on 482012f1 even though ga_yoga_firings shows
// 13 fired yogas (incl. dhana_yoga_2_5_9_11, Venus+Jupiter, strength 1.0218). The composite
// verdict formula (below) never had a yoga term at all — 13 fired yogas could not move it
// (the standing bug: composite stuck at 1.15/convergent_moderate regardless of yoga evidence).
// Fix: bearing_yogas now reads ga_yoga_firings directly (firings-authoritative — real strength +
// bhaṅga/cancellation state, not a single-pass catalog label); MSR yoga signals are demoted to a
// `bearing_yogas_corroboration` annotation (still surfaced, never discarded — B.10). The yoga
// term below is SUB-D1 like the varga term (a bearing yoga corroborates, it does not overrule the
// rasi dignity): each DOMAIN-BEARING fired yoga (constituent_planets ⊆ {this domain's bhāveśa,
// kāraka(s)} — the SAME actors the D1 leg already grades, so a fired classical yoga naming them is
// genuine corroboration, not a new independent claim) contributes its strength × this weight,
// discounted to a quarter when bhaṅga (cancellation) is active on that firing — consuming
// bhaṅga state, not just strength, per R-3. Capped so no single conjunction detected under many
// overlapping classical names (Dhana + Raja Yoga family firing from the same Venus-Jupiter
// placement, e.g.) can run away the composite.
const YOGA_MATCH_WEIGHT = 0.4
const YOGA_BHANGA_DISCOUNT = 0.25
const YOGA_TERM_CAP = 2.0

interface VargaDignity {
  graha: string
  graha_code: string
  role: 'bhavesha' | 'karaka'
  varga: string
  dignity_state: string | null
  dignity_weight: number | null
  fact_id: string | null
}

/** Operative-varga dignity for one graha, re-derived from chart_facts (never recomputed).
 *  Returns a null-dignity record (weight 0 contribution) when the varga row is absent or
 *  when varga==='D1' (already counted by the D1 dignity leg). */
async function vargaDignity(
  chartId: string, ayanamshaId: string, graha: string, grahaCode: string,
  varga: string, role: 'bhavesha' | 'karaka',
): Promise<VargaDignity> {
  const base: VargaDignity = { graha, graha_code: grahaCode, role, varga, dignity_state: null, dignity_weight: null, fact_id: null }
  if (varga === 'D1') return base
  try {
    const res = await query<{ fact_id: string; fact_value_text: string | null }>(
      `SELECT fact_id, fact_value_text FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_dignity_per_varga'
         AND fact_subject = $3 AND fact_key = 'dignity_state'`,
      [chartId, ayanamshaId, `${varga}_${grahaCode}`],
    )
    if (res.rows[0]) {
      base.dignity_state = res.rows[0].fact_value_text
      base.dignity_weight = res.rows[0].fact_value_text ? DIGNITY_WEIGHT[res.rows[0].fact_value_text] ?? 0 : null
      base.fact_id = res.rows[0].fact_id
    }
  } catch {
    // non-fatal: operative-varga dignity is best-effort; absence contributes 0, disclosed in the receipt.
  }
  return base
}

/** D1 dignity + shadbala for one already-resolved graha entity. Never recomputes either —
 *  both are frozen build-time formula output (must_not_touch, R5 brief). */
async function gradeGraha(chartId: string, ayanamshaId: string, g: ResolvedGraha): Promise<GrahaCondition> {
  const fact_ids = [...g.fact_ids]
  let dignity_state: string | null = null
  let shadbala_rupa: number | null = null
  try {
    const dignityRes = await query<{ fact_id: string; fact_value_text: string | null }>(
      `SELECT fact_id, fact_value_text FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_dignity_per_varga'
         AND fact_subject = $3 AND fact_key = 'dignity_state'`,
      [chartId, ayanamshaId, `D1_${g.graha_code}`],
    )
    if (dignityRes.rows[0]) {
      dignity_state = dignityRes.rows[0].fact_value_text
      fact_ids.push(dignityRes.rows[0].fact_id)
    }
  } catch {
    // non-fatal: dignity annotation best-effort
  }
  try {
    const shadbalaRes = await query<{ fact_id: string; fact_value_num: number | null }>(
      `SELECT fact_id, fact_value_num FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_shadbala_total'
         AND fact_subject = $3 AND fact_key = 'rupa'`,
      [chartId, ayanamshaId, g.graha_code],
    )
    if (shadbalaRes.rows[0]) {
      shadbala_rupa = shadbalaRes.rows[0].fact_value_num !== null ? Number(shadbalaRes.rows[0].fact_value_num) : null
      fact_ids.push(shadbalaRes.rows[0].fact_id)
    }
  } catch {
    // non-fatal: shadbala annotation best-effort
  }
  return {
    graha: g.graha,
    graha_code: g.graha_code,
    house: g.house,
    sign: g.sign,
    dignity_state,
    dignity_weight: dignity_state ? DIGNITY_WEIGHT[dignity_state] ?? 0 : null,
    shadbala_rupa,
    fact_ids: Array.from(new Set(fact_ids)),
  }
}

async function fetchAspectingGrahas(
  chartId: string, ayanamshaId: string, house: number,
): Promise<{ grahas: string[]; fact_ids: string[] }> {
  try {
    const res = await query<{ fact_id: string; fact_key: string }>(
      `SELECT fact_id, fact_key FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'aspect_parashari_received'
         AND fact_subject = $3 AND fact_key LIKE 'from_%'`,
      [chartId, ayanamshaId, `HOUSE_${house}`],
    )
    const grahas = res.rows
      .map(r => r.fact_key.replace(/^from_/, ''))
      .map(code => GRAHA_CODE_TO_NAME[code] ?? code)
    return { grahas, fact_ids: res.rows.map(r => r.fact_id) }
  } catch {
    return { grahas: [], fact_ids: [] }
  }
}

export const judgmentQueryCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-JUDGMENT/judgment_query',
  type: 'tool',
  layer: 'L2',
  name: 'judgment_query',
  scope: 'per_chart',

  description: [
    'THE classical bhava-adhyaya judgment recipe as ONE instrument (design §28.1) — generalizes',
    'apex_marriage_assess/apex_career_assess/apex_health_assess/apex_wealth_assess into the',
    'acharya\'s own working method, for ANY bhava-question, not hardcoded to marriage.',
    'Pass either `domain` (e.g. "marriage", "career", "wealth", "health", "progeny", "education",',
    '"spirituality" — resolved via the shastra map) or a bare `bhava` (1-12) for any other house.',
    'Runs the COMPLETE classical checklist in one call: bhava condition (sign + occupants +',
    'aspecting grahas) · bhāveśa (lord) condition + own placement + dignity + strength ·',
    'kāraka condition (classical significator, e.g. Venus for marriage) · judged from BOTH lagna',
    'AND chandra (Sudarshana discipline, design §27.3 frame facet) · operative-varga confirmation',
    '(e.g. D9 for marriage) via the divisional chart · bearing yogas/doshas from the MSR signal',
    'store · timing hooks (which dasha periods carry the lord/karaka\'s promise, current + upcoming)',
    '· a deterministic promise-register verdict (never an LLM judgment, never a probability —',
    'that is L4/L5\'s job) · a classical-units completeness RECEIPT (design §28.6):',
    '{bhava, bhavesha, karaka, from_moon, varga_confirmed, yogas_checked, bhanga_checked, timing_anchored}.',
    'Every resolution (bhava/lord/occupants/karaka, both frames) goes through the SAME address',
    'resolver W1/W2 built (design §19 single-source) — no parallel resolver logic here.',
    'Honest gap: "notably-absent"/bhanga (cancellation) near-miss checking needs a data-plane',
    'addition (design §12 D3) that does not exist yet — bhanga_checked reports false, not fabricated.',
    'chart_id is required — never defaulted (principle #14).',
  ].join(' '),

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to use (default: 'lahiri_chitrapaksha').",
    },
    domain: {
      type: 'string',
      description:
        'Life-domain name, resolved via the shastra map (design §28.5): marriage/relationship/' +
        'partnership (bhava 7, Venus, D9), career/vocation (bhava 10, Sun+Mercury+Saturn, D10), ' +
        'wealth/finance (bhava 2, Jupiter, D2), health/vitality (bhava 1, Sun, D6), ' +
        'progeny/children (bhava 5, Jupiter, D7), education/vidya (bhava 4, Mercury+Jupiter+Ketu, D24), ' +
        'residence/property/home (bhava 4, Moon+Mars, D4), character/buddhi (bhava 1, Moon+Mercury, D1), ' +
        'spirituality (bhava 9 dharma, Jupiter+Ketu, D20), moksha/liberation (bhava 12 mokṣa-trikoṇa, ' +
        'Ketu+Saturn+Jupiter, D20 — distinct from spirituality/9th). Takes precedence over `bhava` if both given.',
    },
    bhava: {
      type: 'number',
      description:
        'Bhava (house) number 1-12, for a judgment question the shastra map does not name a ' +
        'domain for. If the house happens to match a mapped domain\'s bhava, its karaka(s)/varga ' +
        'are still applied; otherwise the recipe runs bhava/bhavesha/occupants/aspects/timing ' +
        'with no karaka leg (reported honestly in the receipt).',
    },
    response_format: {
      type: 'string',
      description: "Envelope shape: 'legacy' (default) or 'v3' (populated verdict/grounding/chart_header).",
      enum: ['legacy', 'v3'],
    },
    max_signals: {
      type: 'number',
      description: 'Max yoga/dosha signals to include in the bearing-yogas check (default: 15, max: 50).',
    },
    as_of_date: {
      type: 'string',
      description:
        'CR-1/R-39/T-3: point-in-time date (ISO 8601: YYYY-MM-DD) the timing hooks are anchored ' +
        'to. Default: today. Forwarded to the current-dasha-period fetch (containment filter — an ' +
        'expired dasha is never served as "current" for a past/future as_of_date) and to the ' +
        'kala_activation lookup below. Does not change which chart facts are read (those are ' +
        'timeless natal facts) — only which "what is active" timing hooks are surfaced.',
    },
  },

  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true, l0_citation_ids: true },
  lel_capable: false,
  // Lane 5 (§N.6 (iv), Doctrine Campaign D-1 Night-1): backs judgment_query; receipt-honesty
  // fixed this pass (timing_anchored no longer claims success over an all-empty dasha fetch).
  density_contract: {
    paginated: false, // one judgment per call, not a row list
    facets: ['domain', 'operative_varga', 'max_signals'],
    empty_reason: false, // judgment_flags[] carries the honest-gap disclosures instead
  },
  drill_children: [
    'marsys://tool/L1/get_divisionals',
    'marsys://tool/L2/query_signals',
    'marsys://tool/L1/get_dashas',
    'marsys://tool/L3/query_temporal_activation',
    'marsys://tool/L2/traverse_chart_graph',
    'marsys://tool/L0/query_classical_texts',
  ],

  llm_hints: {
    agentic: { cost_class: 'expensive', cacheable: true },
    bulk_context: { pre_fetch_priority: 30 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const chart_id = args['chart_id'] as string | undefined
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const domainInput = (args['domain'] as string | undefined)?.trim().toLowerCase()
    const bhavaInput = args['bhava'] !== undefined ? Number(args['bhava']) : undefined
    const max_signals = Math.min(Number(args['max_signals'] ?? 15), 50)
    // CR-1/R-39/T-3: as_of_date now forwarded through the whole timing-hooks
    // chain instead of a hardcoded `today` — see Step 9 below.
    const as_of_date = (args['as_of_date'] as string | undefined) ?? new Date().toISOString().slice(0, 10)

    // F-41: reject unknown domain before any DB work so callers get a typed error, not a silent
    // orientation-context flood. A truthy domainInput that is absent from SHASTRA_MAP is always
    // a caller mistake — reject explicitly with the live key list (never stale).
    if (domainInput && !SHASTRA_MAP[domainInput]) {
      return {
        content: {
          error:
            `judgment_query: unrecognized domain '${domainInput}'. ` +
            `Recognized domains: ${Object.keys(SHASTRA_MAP).sort().join(', ')}. ` +
            `Pass \`bhava\` (1-12) for any unlisted house question.`,
        },
        is_error: true,
      }
    }
    let spec: DomainSpec
    let domainKey: string | null = null
    if (domainInput && SHASTRA_MAP[domainInput]) {
      domainKey = domainInput
      spec = SHASTRA_MAP[domainInput]
    } else if (bhavaInput !== undefined && Number.isInteger(bhavaInput) && bhavaInput >= 1 && bhavaInput <= 12) {
      const impliedDomain = BHAVA_TO_DOMAIN[bhavaInput]
      if (impliedDomain) {
        domainKey = impliedDomain
        // W4-loop-1 (E-5 group3): a bare `bhava:N` must be JUDGED as house N. The prior code
        // did `spec = SHASTRA_MAP[impliedDomain]`, whose `.bhava` is the domain's CANONICAL
        // house — silently re-mapping bhava:6→1 (health), bhava:8→12 (moksha), bhava:11→2
        // (wealth), etc., making houses 3/6/8/11 (enemies/litigation/longevity/inheritance)
        // unjudgeable. Keep the domain's karaka/varga/signal enrichment but pin the bhāva
        // under judgment to the house the caller actually asked for.
        const enrich = SHASTRA_MAP[impliedDomain]
        spec = {
          ...enrich,
          bhava: bhavaInput as HouseNumber,
          label: `Bhava ${bhavaInput} — ${enrich.label}`,
        }
      } else {
        spec = { bhava: bhavaInput as HouseNumber, karakas: [], varga: 'D1', label: `Bhava ${bhavaInput}`, signal_domain: 'other' }
      }
    } else {
      return {
        content: {
          error:
            'judgment_query requires either `domain` (see recognized domain list) ' +
            'or `bhava` (1-12).',
        },
        is_error: true,
      }
    }

    const judgment_flags: JudgmentFlagEntry[] = []
    const fact_ids = new Set<string>()

    try {
      // ── Step 1+2 (lagna frame): bhava condition, bhāveśa condition, occupants, aspects ──
      const [bhavaLagna, lordLagna, occupantsLagna, aspectsLagna] = await Promise.all([
        resolveAddress(chart_id, { type: 'bhava', house: spec.bhava }, { ayanamsha_id }),
        resolveAddress(chart_id, { type: 'lord_of', house: spec.bhava }, { ayanamsha_id }),
        resolveAddress(chart_id, { type: 'occupants_of', house: spec.bhava }, { ayanamsha_id }),
        fetchAspectingGrahas(chart_id, ayanamsha_id, spec.bhava),
      ])
      const bhavaSignLagna = bhavaLagna.entities[0] as ResolvedSign
      const lordEntityLagna = lordLagna.entities[0] as ResolvedGraha
      const occupantsLagnaEntity = occupantsLagna.entities[0] as ResolvedOccupants
      const lordCondition = await gradeGraha(chart_id, ayanamsha_id, lordEntityLagna)
      bhavaSignLagna.fact_ids.forEach(f => fact_ids.add(f))
      occupantsLagnaEntity.fact_ids.forEach(f => fact_ids.add(f))
      aspectsLagna.fact_ids.forEach(f => fact_ids.add(f))
      lordCondition.fact_ids.forEach(f => fact_ids.add(f))

      // ── Step 3: kāraka condition (one or more; e.g. career has 3) ──
      const karakaConditions: GrahaCondition[] = []
      for (const karakaName of spec.karakas) {
        try {
          const res = await resolveAddress(chart_id, { type: 'graha', graha: karakaName }, { ayanamsha_id })
          const g = await gradeGraha(chart_id, ayanamsha_id, res.entities[0] as ResolvedGraha)
          g.fact_ids.forEach(f => fact_ids.add(f))
          karakaConditions.push(g)
        } catch (e) {
          judgment_flags.push(judgmentFlag('karaka_unresolved', `${karakaName} — ${String(e)}`))
        }
      }

      // ── Step 5: from-chandra (Sudarshana discipline, design §27.3) ──
      let bhavaSignMoon: ResolvedSign | null = null
      let lordConditionMoon: GrahaCondition | null = null
      let occupantsMoon: ResolvedOccupants | null = null
      try {
        const [bhavaMoon, lordMoon, occMoon] = await Promise.all([
          resolveAddress(chart_id, { type: 'bhava', house: spec.bhava, frame: 'chandra' }, { ayanamsha_id }),
          resolveAddress(chart_id, { type: 'lord_of', house: spec.bhava, frame: 'chandra' }, { ayanamsha_id }),
          resolveAddress(chart_id, { type: 'occupants_of', house: spec.bhava, frame: 'chandra' }, { ayanamsha_id }),
        ])
        bhavaSignMoon = bhavaMoon.entities[0] as ResolvedSign
        occupantsMoon = occMoon.entities[0] as ResolvedOccupants
        lordConditionMoon = await gradeGraha(chart_id, ayanamsha_id, lordMoon.entities[0] as ResolvedGraha)
        bhavaSignMoon.fact_ids.forEach(f => fact_ids.add(f))
        occupantsMoon.fact_ids.forEach(f => fact_ids.add(f))
        lordConditionMoon.fact_ids.forEach(f => fact_ids.add(f))
      } catch (e) {
        judgment_flags.push(judgmentFlag('from_moon_resolution_failed', String(e)))
      }

      // ── Step 6: operative-varga confirmation (reuses get_divisionals — no parallel query) ──
      const vargaConfirmation: Record<string, unknown>[] = []
      let vargaConfirmed = false
      try {
        const { getDivisionalsCapability } = await import('./L1_ganita/get_divisionals')
        const grahasToConfirm = [
          { role: 'bhavesha', name: lordCondition.graha },
          ...karakaConditions.map(k => ({ role: 'karaka', name: k.graha })),
        ]
        for (const { role, name } of grahasToConfirm) {
          // chart_divisionals.graha stores the classical display name ("Venus"), NOT a
          // 2-letter code — verified against both canonical charts before wiring this call
          // (a 2-letter code here would silently return zero rows, the exact P1 failure
          // class this run's standing requirement warns about).
          const res = await getDivisionalsCapability.handler(
            { chart_id, ayanamsha_id, varga: spec.varga, graha: name }, undefined,
          )
          if (!res.is_error) {
            const c = res.content as Record<string, unknown>
            const rows = (c['rows'] as Record<string, unknown>[]) ?? []
            for (const r of rows) vargaConfirmation.push({ role, ...r })
            if (rows.length > 0) vargaConfirmed = true
          }
        }
      } catch (e) {
        judgment_flags.push(judgmentFlag('varga_confirmation_failed', String(e)))
      }

      // ── Step 7: bearing yogas/doshas (formed) — notably-absent is an honest gap (D3 unbuilt) ──
      // A3 (CR-92 residue, R-3): firings-authoritative source is ga_yoga_firings (real strength +
      // bhaṅga/cancellation state), not the MSR yoga signal projection — see the YOGA_* constants'
      // comment above for the full rationale. `domainActors` is the SAME actor set (bhāveśa +
      // kāraka(s)) the D1 dignity leg already grades — a fired yoga whose constituent_planets are
      // a subset of this set is genuine corroboration of an already-graded actor, not a new,
      // independent claim (kept SUB-D1 accordingly, see YOGA_MATCH_WEIGHT).
      let yogasChecked = 0
      let bearingYogaFirings: Record<string, unknown>[] = []
      let yogaTerm = 0
      const domainActors = new Set(
        [lordCondition.graha, ...karakaConditions.map(k => k.graha)]
          .filter((g): g is string => Boolean(g))
          .map(g => g.toLowerCase()),
      )
      try {
        const { getYogaFiringsCapability } = await import('./L1_ganita/get_yoga_firings')
        const res = await getYogaFiringsCapability.handler(
          { chart_id, ayanamsha_id, fired: true, limit: 50 },
          undefined,
        )
        if (!res.is_error) {
          const c = res.content as Record<string, unknown>
          const firedRows = (c['rows'] as Record<string, unknown>[]) ?? []
          yogasChecked = firedRows.length
          let yogaTermRaw = 0
          bearingYogaFirings = firedRows.map(r => {
            const constituentPlanets = ((r['constituent_planets'] as string[] | null) ?? []).map(p => p.toLowerCase())
            const domainMatch = constituentPlanets.length > 0 && constituentPlanets.every(p => domainActors.has(p))
            const bhangaActive = r['bhanga_active'] === true
            const strength = typeof r['strength'] === 'number' ? r['strength'] : Number(r['strength'] ?? 0)
            if (domainMatch && Number.isFinite(strength)) {
              yogaTermRaw += strength * (bhangaActive ? YOGA_BHANGA_DISCOUNT : 1) * YOGA_MATCH_WEIGHT
              for (const fid of (r['constituent_fact_ids'] as string[] | null) ?? []) fact_ids.add(fid)
            }
            return {
              yoga_canonical_id: r['yoga_canonical_id'],
              strength: r['strength'],
              strength_label: r['strength_label'],
              bhanga_active: r['bhanga_active'],
              bhanga_rule_fired: r['bhanga_rule_fired'],
              constituent_planets: r['constituent_planets'],
              constituent_houses: r['constituent_houses'],
              source: 'ga_yoga_firings',
              domain_match: domainMatch,
            }
          })
          // D-1.5a wave gate finding (live post-deploy verification): the response-budget
          // trimmer's generic minKeep cut is a blind `slice(0, N)` — it has no notion of
          // which entries are semantically load-bearing for THIS domain call. Left in
          // strength-descending order (the ga_yoga_firings query's own order), a high-
          // strength but domain-irrelevant yoga (e.g. Śaśa on career) can rank ahead of a
          // lower-strength but domain-matching one (e.g. this Dhana Yoga at 1.02 vs Śaśa's
          // 1.57), so the trim silently drops the exact row the verdict's yoga_term already
          // counted — the served bearing_yogas then contradicts the composite score it's
          // supposed to justify. Domain-matching firings must sort first so any N-cut keeps
          // them; relative strength order is preserved within each group.
          bearingYogaFirings.sort((a, b) => {
            const am = a['domain_match'] === true, bm = b['domain_match'] === true
            if (am !== bm) return am ? -1 : 1
            return 0
          })
          yogaTerm = Math.min(yogaTermRaw, YOGA_TERM_CAP)
        }
      } catch (e) {
        judgment_flags.push(judgmentFlag('yoga_firings_fetch_failed', String(e)))
      }
      if (bearingYogaFirings.length === 0) {
        judgment_flags.push(judgmentFlag(
          'bearing_yogas_empty',
          'no fired rows returned from ga_yoga_firings (firings-authoritative) ' +
          'for this chart/ayanamsha — honest absence, not fabricated.',
        ))
      } else if (!bearingYogaFirings.some(y => y['domain_match'] === true)) {
        judgment_flags.push(judgmentFlag(
          'bearing_yogas_no_domain_match',
          `${bearingYogaFirings.length} yoga(s) fired on this chart ` +
          `but none name only this domain's bhāveśa/kāraka(s) (${[...domainActors].join(', ') || 'none resolved'}) ` +
          '— shown for context; none contributed to the verdict composite (verdict.yoga_term = 0).',
        ))
      }

      // D-13 demotion (A3): MSR yoga signals are no longer the primary bearing_yogas source —
      // kept as a secondary corroboration annotation (never discarded, B.10), still carrying the
      // JL-004 single-pass-catalog-match caveat that motivated the demotion in the first place.
      let yogaSignalsCorroboration: Record<string, unknown>[] = []
      try {
        const { querySignalsCapability } = await import('./L2_bodha/query_signals')
        const res = await querySignalsCapability.handler(
          {
            chart_id, ayanamsha_id, domain: spec.signal_domain,
            signal_type_class: 'yoga', top_k: max_signals,
          },
          undefined,
        )
        if (!res.is_error) {
          const c = res.content as Record<string, unknown>
          yogaSignalsCorroboration = ((c['signals'] as Record<string, unknown>[]) ?? []).map(s => ({
            signal_id: s['signal_id'],
            signal_summary: s['signal_summary_text'],
            computed_salience: s['computed_salience'],
            signal_tradition: s['signal_tradition'],
          }))
        }
      } catch (e) {
        judgment_flags.push(judgmentFlag('yoga_signal_corroboration_fetch_failed', String(e)))
      }
      if (yogaSignalsCorroboration.length > 0) {
        judgment_flags.push(judgmentFlag(
          'bearing_yogas_corroboration_caveat',
          'bearing_yogas_corroboration (MSR yoga signals) are ' +
          'requires_pass catalog label matches (single-pass evaluation against L1 facts) — not ' +
          'cross-verified confirmed firings. bearing_yogas above (ga_yoga_firings) is the primary, ' +
          'firings-authoritative source (A3/R-3); this corroboration is secondary context only (JL-004).',
        ))
      }
      // A3/R-3: bhaṅga (cancellation) state on a FIRED, formed yoga is now consulted directly
      // (see the ga_yoga_firings mapping above — bhanga_active discounts a firing's contribution
      // to yogaTerm). What remains unbuilt is "notably-absent" near-miss detection — a yoga that
      // did NOT fire but came close — a distinct, still-absent data-plane addition (design §12 D3).
      judgment_flags.push(judgmentFlag(
        'notably_absent_not_checked',
        'near-miss ("almost formed but for one leg") yoga detection ' +
        'requires a data-plane addition (design §12 D3) not yet built for any chart — reported ' +
        'honestly, not fabricated. Bhaṅga (cancellation) state on FIRED yogas IS consulted above ' +
        '(ga_yoga_firings.bhanga_active discounts a firing\'s verdict contribution, A3/R-3).',
      ))

      // ── Step 9: timing hooks (reuses get_dashas — no parallel dasha query) ──
      // CR-1/R-39/T-3: as_of_date (default today) now drives the "current" fetch instead
      // of a hardcoded today — get_dashas' as_of_date containment filter
      // (start_date <= X AND end_date >= X) means an expired dasha is never served as
      // "current" for a past as_of_date and a not-yet-started one never for a future date.
      const timing: Record<string, unknown> = {
        current: null, lord_mahadasha_windows: [], karaka_mahadasha_windows: [],
        kala_activations: [],
      }
      let timingAnchored = false
      try {
        const { getDashasCapability } = await import('./L1_ganita/get_dashas')
        const currentRes = await getDashasCapability.handler(
          { chart_id, ayanamsha_id, system: 'vimshottari', as_of_date, all_levels: true, limit: 5 },
          undefined,
        )
        if (!currentRes.is_error) {
          const c = currentRes.content as Record<string, unknown>
          timing['current'] = c['rows'] ?? []
        }
        // chart_dashas.lord_graha stores the classical display name ("Venus"), NOT a 2-letter
        // code — verified against both canonical charts before wiring this call (see the
        // varga_confirmation note above; the same param-shape trap applies here).
        const relevantNames = Array.from(new Set([lordCondition.graha, ...karakaConditions.map(k => k.graha)]))
        const windowsByGraha: Record<string, unknown> = {}
        for (const name of relevantNames) {
          const windowRes = await getDashasCapability.handler(
            { chart_id, ayanamsha_id, system: 'vimshottari', level: 1, lord_graha: name, window_start: '1900-01-01', window_end: '2100-01-01' },
            undefined,
          )
          if (!windowRes.is_error) {
            const c = windowRes.content as Record<string, unknown>
            windowsByGraha[name] = c['rows'] ?? []
          }
        }
        timing['mahadasha_windows_by_graha'] = windowsByGraha

        // CR-1/R-39 (S-4): wire timing_hooks to the now-dated kala_activation output too
        // (R-45 fix — activation_start/end are no longer ~99% NULL), not just chart_dashas.
        // Domain-scoped (when a shastra-map domain matched) so this stays a targeted timing
        // hook, not a generic activation dump — reuses query_temporal_activation, no parallel
        // kala_activation SQL in this file (design §19 single-source discipline).
        try {
          const { queryTemporalActivationCapability } = await import('./L3_kala/query_temporal_activation')
          const activationRes = await queryTemporalActivationCapability.handler(
            {
              chart_id, ayanamsha_id, as_of: as_of_date,
              ...(domainKey ? { domain: domainKey } : {}),
              top_k: 10,
            },
            undefined,
          )
          if (!activationRes.is_error) {
            const c = activationRes.content as Record<string, unknown>
            // §N.6 budget fix (D-2 gate): the raw activation rows each carry a ~3.5KB
            // activation_predicted_dates_jsonb + ~1KB active_dasha_periods_jsonb, so 10 rows
            // ballooned timing_hooks to ~51KB (69% of a 73KB v3 payload) and pushed the
            // load-bearing adverse layers (affliction_mechanisms, bearing_afflictions) past a
            // floor-model consumer's token budget. Project each row to its essential scalar
            // fields, drop the verbose JSONB blobs (available via the kala temporal-activation
            // drill tool), and dedupe by distinct activation window — keeping the highest
            // convergence per window, capped at 6.
            const rawActivations = (Array.isArray(c['activations']) ? c['activations'] : []) as Array<Record<string, unknown>>
            const byWindow = new Map<string, Record<string, unknown>>()
            for (const a of rawActivations) {
              const compact = {
                id: a['id'],
                signal_id: a['signal_id'],
                signature_class: a['signature_class'],
                activation_start: a['activation_start'],
                activation_peak_date: a['activation_peak_date'],
                activation_end: a['activation_end'],
                convergence_score: a['convergence_score'],
                dasha_activation_proximity_score: a['dasha_activation_proximity_score'],
                orb_strength: a['orb_strength'],
                domains_affected_array: a['domains_affected_array'],
                source_citation: a['source_citation'],
              }
              const key = `${String(a['activation_start'] ?? '')}|${String(a['activation_peak_date'] ?? '')}|${String(a['activation_end'] ?? '')}|${String(a['signature_class'] ?? '')}`
              const prev = byWindow.get(key)
              const prevConv = prev ? Number(prev['convergence_score'] ?? -Infinity) : -Infinity
              const curConv = Number(a['convergence_score'] ?? -Infinity)
              if (!prev || curConv > prevConv) byWindow.set(key, compact)
            }
            const trimmedActivations = [...byWindow.values()]
              .sort((x, y) => {
                const csDiff = Number(y['convergence_score'] ?? 0) - Number(x['convergence_score'] ?? 0)
                if (csDiff !== 0) return csDiff
                return String(x['id'] ?? '').localeCompare(String(y['id'] ?? ''))
              })
              .slice(0, 6)
            timing['kala_activations'] = trimmedActivations
            if (rawActivations.length > trimmedActivations.length) {
              judgment_flags.push(judgmentFlag(
                'kala_activations_trimmed',
                `${rawActivations.length} raw activation row(s) deduped by ` +
                `window to ${trimmedActivations.length} distinct window(s); per-row ` +
                `activation_predicted_dates_jsonb / active_dasha_periods_jsonb dropped from this ` +
                `envelope (§N.6 budget) — full predicted-date detail via the kala temporal-activation drill.`,
              ))
            }
            // T-12/T-13 (honest-flags-only this wave): kala_activation windows are a single
            // transit/dasha cycle's worth of resolution, not a multi-cycle recurrence model
            // (the multi-cycle generator is D-3 scope) — disclose so a caller never reads
            // "no activation returned" as "this never recurs".
            if (Array.isArray(timing['kala_activations']) && (timing['kala_activations'] as unknown[]).length > 0) {
              judgment_flags.push(judgmentFlag(
                'kala_activations_single_cycle',
                'the kala_activations timing hook reflects ONE ' +
                'resolved dasha/convergence window per signal, not an exhaustive multi-cycle ' +
                'recurrence forecast (the multi-cycle generator is out of this wave\'s scope, D-3) ' +
                '— treat as "at least one activation window exists", not "the only one ever".',
              ))
            }
          }
        } catch {
          // kala_activation lookup is a supplementary hook — a failure here must not fail
          // the whole judgment_query response (get_dashas above remains the primary source).
        }

        // Lane 5 (§N.6 / CR-1/63 handoff, serving-only — no new joins): honesty fix only.
        // The fetches above can each succeed (is_error=false) yet still hand back an empty
        // rows array — that is NOT the same thing as "timing anchored". Require actual
        // content (a current-period row, at least one non-empty mahadasha window, or a
        // kala_activation hit) before claiming timing_anchored=true; an all-empty result is
        // an honest false, no new dasha joins (anti-scope respected).
        const currentRows = (timing['current'] as unknown[] | undefined) ?? []
        const hasWindowRows = Object.values(windowsByGraha).some(
          w => Array.isArray(w) && w.length > 0,
        )
        const hasActivationRows = Array.isArray(timing['kala_activations']) && (timing['kala_activations'] as unknown[]).length > 0
        timingAnchored = currentRows.length > 0 || hasWindowRows || hasActivationRows
        if (!timingAnchored) {
          judgment_flags.push(judgmentFlag(
            'timing_anchored_false',
            'dasha fetches succeeded but returned zero rows for the ' +
            'current period, every mahadasha window checked, and kala_activation — reported ' +
            'honestly as not-anchored rather than claiming success over an empty payload (CR-1/63 class).',
          ))
        }
      } catch (e) {
        judgment_flags.push(judgmentFlag('timing_hook_failed', String(e)))
      }

      // ── Step 8: deterministic promise-register verdict (never an LLM judgment) ──
      // D1 (rasi) leg — dignity/shadbala/occupant/aspect.
      let d1Score = lordCondition.dignity_weight ?? 0
      for (const k of karakaConditions) d1Score += k.dignity_weight ?? 0
      const beneficOccupants = occupantsLagnaEntity.grahas.filter(g => NATURAL_BENEFICS.has(g)).length
      const maleficOccupants = occupantsLagnaEntity.grahas.filter(g => NATURAL_MALEFICS.has(g)).length
      d1Score += beneficOccupants * 0.5 - maleficOccupants * 0.5
      const beneficAspects = aspectsLagna.grahas.filter(g => NATURAL_BENEFICS.has(g)).length
      const maleficAspects = aspectsLagna.grahas.filter(g => NATURAL_MALEFICS.has(g)).length
      d1Score += beneficAspects * 0.3 - maleficAspects * 0.3
      if (lordCondition.shadbala_rupa !== null && lordCondition.shadbala_rupa < 3) d1Score -= 0.5
      if (lordConditionMoon?.dignity_weight) d1Score += lordConditionMoon.dignity_weight * 0.5

      // ── R-46 (WP-1.8): operative-varga (amsha) term — the ripening of the rasi promise ──
      // Re-derived operative-varga dignity of bhāveśa + kāraka(s), weighted sub-D1. Sequenced
      // after WP-1.5's R-38 (varga rows now exist to weigh). This is what lets D9-contradicts-D1
      // (e.g. a bhāveśa neutral in rasi but debilitated in navamsha) actually MOVE the verdict.
      const bhaveshaVarga = await vargaDignity(chart_id, ayanamsha_id, lordCondition.graha, lordCondition.graha_code, spec.varga, 'bhavesha')
      if (bhaveshaVarga.fact_id) fact_ids.add(bhaveshaVarga.fact_id)
      const karakaVargaList: VargaDignity[] = []
      for (const k of karakaConditions) {
        const kv = await vargaDignity(chart_id, ayanamsha_id, k.graha, k.graha_code, spec.varga, 'karaka')
        if (kv.fact_id) fact_ids.add(kv.fact_id)
        karakaVargaList.push(kv)
      }
      const bhaveshaVargaContribution = (bhaveshaVarga.dignity_weight ?? 0) * VARGA_BHAVESHA_WEIGHT
      const karakaVargaWeights = karakaVargaList.map(k => k.dignity_weight).filter((w): w is number => w !== null)
      const karakaVargaMean = karakaVargaWeights.length > 0
        ? karakaVargaWeights.reduce((a, b) => a + b, 0) / karakaVargaWeights.length
        : 0
      const karakaVargaContribution = karakaVargaMean * VARGA_KARAKA_WEIGHT
      const vargaTerm = spec.varga === 'D1' ? 0 : bhaveshaVargaContribution + karakaVargaContribution
      const vargaTermApplied = spec.varga !== 'D1' && (bhaveshaVarga.fact_id !== null || karakaVargaList.some(k => k.fact_id !== null))

      // A3/R-3: the composite now ALSO consumes bearing-yoga detector strength (yogaTerm, built in
      // Step 7 above from ga_yoga_firings — bhaṅga-discounted, domain-actor-scoped, capped). Before
      // this pass the composite had NO yoga term at all, so a fired Dhana Yoga (or any other
      // classical yoga) structurally could not move a verdict regardless of how many fired —
      // the standing bug this wave closes.
      const compositeScore = d1Score + vargaTerm + yogaTerm

      /** Design §28.1 grading bands, shared by every partial/full verdict grade below so the
       *  composite, D1-only, and D1+varga (pre-yoga) grades can never silently drift apart. */
      const gradeFor = (score: number): string =>
        score >= 2.5 ? 'convergent_strong'
        : score >= 1 ? 'convergent_moderate'
        : score >= -1 ? 'mixed'
        : 'contested'

      const verdict_grade = gradeFor(compositeScore)

      // D1-only grade (what the pre-WP-1.8 formula would have returned) — surfaced so the
      // varga contribution is auditable and a reviewer can see WHEN the amsha moved the verdict.
      const d1_only_grade = gradeFor(d1Score)

      // Pre-yoga grade (what the pre-A3 formula — D1 + varga, no bearing-yoga term — would have
      // returned) — surfaced so the yoga contribution is auditable the same way the varga
      // contribution already is above.
      const preYogaScore = d1Score + vargaTerm
      const d1_plus_varga_grade = gradeFor(preYogaScore)
      const yogaTermApplied = yogaTerm > 0

      const verdict = {
        domain: domainKey ?? null,
        domain_label: spec.label,
        bhava: spec.bhava,
        verdict_grade,
        composite_score: Math.round(compositeScore * 100) / 100,
        d1_score: Math.round(d1Score * 100) / 100,
        d1_only_grade,
        operative_varga: spec.varga,
        varga_term: Math.round(vargaTerm * 100) / 100,
        varga_moved_verdict: vargaTermApplied && d1_only_grade !== d1_plus_varga_grade,
        varga_subscores: {
          bhavesha: { graha: bhaveshaVarga.graha, varga: spec.varga, dignity_state: bhaveshaVarga.dignity_state, weight: bhaveshaVarga.dignity_weight, contribution: Math.round(bhaveshaVargaContribution * 100) / 100 },
          karakas: karakaVargaList.map(k => ({ graha: k.graha, varga: spec.varga, dignity_state: k.dignity_state, weight: k.dignity_weight })),
          note: spec.varga === 'D1'
            ? 'Operative varga is D1 — varga term skipped to avoid double-counting the D1 dignity already in the composite.'
            : (vargaTermApplied
                ? `Operative-varga (${spec.varga}) dignity of bhāveśa (×${VARGA_BHAVESHA_WEIGHT}) + kāraka(s) mean (×${VARGA_KARAKA_WEIGHT}) — the amsha as the ripening of the rasi promise (BPHS Ch.6-7; Parashari D9-is-the-fruit dictum).`
                : `No ${spec.varga} dignity rows resolved for bhāveśa/kāraka — varga term = 0 (honest absence, not fabricated).`),
        },
        // A3/R-3: bearing-yoga contribution — auditable the same way varga is above.
        yoga_term: Math.round(yogaTerm * 100) / 100,
        yoga_moved_verdict: yogaTermApplied && d1_plus_varga_grade !== verdict_grade,
        yoga_subscore: {
          domain_bearing_firings: bearingYogaFirings.filter(y => y['domain_match'] === true).length,
          total_fired_on_chart: bearingYogaFirings.length,
          note: yogaTermApplied
            ? `${bearingYogaFirings.filter(y => y['domain_match'] === true).length} fired ga_yoga_firings ` +
              `row(s) name only this domain's bhāveśa/kāraka(s) — strength summed (×${YOGA_MATCH_WEIGHT}, ` +
              `bhaṅga-active firings discounted to ×${YOGA_BHANGA_DISCOUNT}), capped at ${YOGA_TERM_CAP}.`
            : 'No fired ga_yoga_firings row names only this domain\'s bhāveśa/kāraka(s) — yoga term = 0 (honest absence, not fabricated).',
        },
        note:
          'Deterministic weighted aggregation of already-computed dignity/shadbala/occupant/aspect ' +
          'signals PLUS a re-derived operative-varga (amsha) term PLUS a bearing-yoga (ga_yoga_firings) ' +
          'term — NOT an LLM judgment and NOT a calibrated probability (that is L4/L5\'s domain). ' +
          'D1 weights: dignity ±2..−2, benefic/malefic occupant ±0.5, benefic/malefic aspect ±0.3, ' +
          'weak-lord (<3 rupas) −0.5, from-Moon lord dignity ×0.5. Varga term (R-46/WP-1.8): bhāveśa ' +
          `operative-varga dignity ×${VARGA_BHAVESHA_WEIGHT} + kāraka(s) mean ×${VARGA_KARAKA_WEIGHT} ` +
          '(skipped when operative varga is D1). Yoga term (A3/R-3): domain-bearing fired-yoga ' +
          `strength ×${YOGA_MATCH_WEIGHT} (bhaṅga-active ×${YOGA_BHANGA_DISCOUNT}), capped at ${YOGA_TERM_CAP}. ` +
          'composite_score = d1_score + varga_term + yoga_term; d1_only_grade shows the pre-varga-and-yoga ' +
          'verdict; d1_plus_varga_grade shows the pre-yoga verdict.',
        d1_plus_varga_grade,
      }

      // ── The receipt (design §28.6 — classical-units completeness) ──
      const receipt = {
        bhava: true,
        bhavesha: true,
        karaka: karakaConditions.length > 0,
        from_moon: bhavaSignMoon !== null && lordConditionMoon !== null,
        varga_confirmed: vargaConfirmed ? `${spec.varga}✓` : `${spec.varga}✗ (no divisional row found)`,
        // R-46 (WP-1.8): distinct from varga_confirmed (placement rows exist) — this asserts the
        // operative-varga dignity actually ENTERED the verdict composite as a weighted term.
        varga_weighted_into_verdict: vargaTermApplied,
        yogas_checked: yogasChecked,
        // A3/R-3: bhaṅga (cancellation) state on FIRED yogas is now consulted (ga_yoga_firings.
        // bhanga_active discounts a firing's contribution to verdict.yoga_term — see Step 7 above).
        // Distinct from "notably-absent" near-miss detection, which remains unbuilt (see the
        // notably_absent_not_checked judgment_flag) — bhanga_checked is honestly true, not blanket
        // false, now that it genuinely feeds the composite.
        bhanga_checked: true,
        timing_anchored: timingAnchored,
      }

      // ── DR-9 Part B (native-ratified 2026-07-17): partitioned SIGNED serve ──
      // The threatening/adverse layer, symmetric to bearing_yogas. Now that the
      // valence doctrine (VAL-ROOT) emits real malefic/mixed valence, this
      // surfaces the domain's adverse-valence signals + graha-to-house
      // affliction mechanisms (e.g. Rahu-occupies-dhana) in their OWN layer with
      // its own §N.6 hardFloor — never crowded out of a unified top-K by the
      // benefic yogas (the exact reason a wealth chart with 12 fired benefic
      // yogas showed zero adverse content; D-16/G-04). The verdict stays a signed
      // composite; supporting and threatening layers are served SEPARATELY.
      let bearing_afflictions: Record<string, unknown>[] = []
      let affliction_mechanisms: Record<string, unknown>[] = []
      try {
        const advRes = await query<{
          signal_id: string; signal_type_id: string; signal_summary_text: string | null
          valence: string | null; valence_source: string | null
          computed_salience: number | null; constituent_facts_array: string[] | null
        }>(
          `SELECT signal_id, signal_type_id, signal_summary_text, valence, valence_source,
                  computed_salience, constituent_facts_array
             FROM bodha_msr_signals
            WHERE chart_id = $1 AND ayanamsha_id = $2
              AND $3 = ANY(domains_affected_array)
              AND valence IN ('malefic','mixed')
            ORDER BY computed_salience DESC NULLS LAST
            LIMIT $4`,
          [chart_id, ayanamsha_id, spec.signal_domain, max_signals],
        )
        bearing_afflictions = advRes.rows.map(r => {
          for (const fid of (r.constituent_facts_array ?? [])) fact_ids.add(fid)
          return {
            signal_id: r.signal_id, signal_type_id: r.signal_type_id,
            signal_summary: r.signal_summary_text, valence: r.valence,
            valence_source: r.valence_source, computed_salience: r.computed_salience,
            constituent_facts_array: r.constituent_facts_array,
          }
        })
        const mechRes = await query<{
          mechanism_name: string; mechanism_class: string; valence: string | null
          citation_human: string | null
        }>(
          `SELECT mechanism_name, mechanism_class, valence, citation_human
             FROM bodha_mechanisms
            WHERE chart_id = $1 AND ayanamsha_id = $2
              AND valence IN ('malefic','mixed')
              AND $3 = ANY(domains_affected_array)
            ORDER BY CASE valence WHEN 'malefic' THEN 0 ELSE 1 END
            LIMIT $4`,
          [chart_id, ayanamsha_id, spec.signal_domain, max_signals],
        )
        affliction_mechanisms = mechRes.rows.map(r => ({
          mechanism_name: r.mechanism_name, mechanism_class: r.mechanism_class,
          valence: r.valence, citation_human: r.citation_human,
        }))
      } catch (e) {
        judgment_flags.push(judgmentFlag('afflictions_fetch_failed', String(e)))
      }
      if (bearing_afflictions.length === 0 && affliction_mechanisms.length === 0) {
        judgment_flags.push(judgmentFlag(
          'afflictions_empty',
          'no adverse-valence (malefic/mixed) signal or affliction mechanism ' +
          'bears on this domain — reported honestly (DR-9 Part B partitioned serve; an honest ' +
          'empty threat layer, not an omission).',
        ))
      } else {
        judgment_flags.push(judgmentFlag(
          'afflictions_present',
          `${bearing_afflictions.length} adverse signal(s) + ` +
          `${affliction_mechanisms.length} affliction mechanism(s) served in the THREAT layer ` +
          '(DR-9 Part B, native-ratified). The verdict is a SIGNED composite; the supporting ' +
          '(bearing_yogas) and threatening (bearing_afflictions/affliction_mechanisms) layers are ' +
          'served SEPARATELY, each with its own §N.6 hardFloor — neither crowds out the other. A ' +
          'unified top-K would fill with the benefic yogas and hide the adverse content (D-16/G-04).',
        ))
      }

      // ── T5 Leg A: fired sensitive-degree checks (MC-030) ──────────────────────────
      // The rare, high-information firings salience priors bury below routine descriptor
      // rows (on 482012f1: Mars in puṣkara — the ONLY graha in puṣkara, and the lagneśa/
      // Indu-lagna lord). Surfaced STRUCTURALLY in its own slot so it appears in EVERY
      // domain judgment without the caller asking for sensitive degrees. Chart-wide, not
      // domain-scoped: a fired sensitive degree on a chart-critical graha bears across
      // domains. Reads the frozen L1 fact (§N.5), never recomputes.
      const sensitive = await fetchSensitiveDegreeFirings(chart_id, ayanamsha_id)
      for (const f of sensitive.fact_ids) fact_ids.add(f)
      if (sensitive.firings.length > 0) {
        judgment_flags.push(judgmentFlag(
          'sensitive_degree_firings_present',
          `${sensitive.firings.length} fired sensitive-degree check(s) surfaced ` +
          `(${sensitive.firings.map(f => `${f.graha}:${f.check_type}`).join(', ')}) — rare high-information ` +
          'events that salience-ranked surfaces floor below routine descriptor rows (MC-030); served here ' +
          'structurally so they are never silently dropped.',
        ))
      } else if (sensitive.available) {
        judgment_flags.push(judgmentFlag(
          'sensitive_degree_firings_empty',
          'sensitive_degree_check computed for this chart but no high-signal ' +
          '(puṣkara/gaṇḍānta/mṛtyu-bhāga/kartari) check fired — an honest negative, not an omission.',
        ))
      }

      // ── T5 Leg B: KP cuspal sub-lord chain (MC-031) ───────────────────────────────
      // Two-pass-computed + wealth/career-tagged but previously reachable ONLY via the
      // bottom-10% dissent tail (synth_tail_divergence_get). Joined here into the domain's
      // decisive cusps. Reuses the frozen getKpCuspsCapability (single-source, §19).
      const kpCusps = domainKey && DOMAIN_KP_CUSPS[domainKey]
        ? DOMAIN_KP_CUSPS[domainKey]!
        : [spec.bhava as number]
      const kp = await fetchKpCuspChain(chart_id, ayanamsha_id, kpCusps)
      for (const f of kp.fact_ids) fact_ids.add(f)
      if (kp.cusps.length === 0) {
        judgment_flags.push(judgmentFlag(
          'kp_cusp_chain_unavailable',
          `no KP cuspal facts resolved for cusp(s) ${kpCusps.join('/')} ` +
          '— the KP cuspal asset may not be built for this chart/ayanamsha.',
        ))
      }

      // ── T5 Leg C: forward gochara sweep (MC-033) ──────────────────────────────────
      // The gochara sweep was never joined into a domain reading by default. One
      // domain-scoped forward sweep, compact (top windows + valence tally). Reads the
      // untouchable kala_gochara_windows field READ-ONLY.
      const gochara = await fetchGocharaSweep(chart_id, spec.signal_domain, as_of_date)
      if (gochara.available && !gochara.domain_covered) {
        judgment_flags.push(judgmentFlag(
          'gochara_domain_not_covered',
          `the gochara sweep does not cover the '${spec.signal_domain}' domain ` +
          'for this chart — its silence here is NOT an all-clear (S4-05 discipline); drill kala_windows_get.',
        ))
      }
      if (gochara.windows[0]?.is_past_peak === true) {
        judgment_flags.push(judgmentFlag(
          'gochara_top_window_already_peaked',
          `the top-ranked (highest |intensity|) window in gochara_sweep.top_windows ` +
          `('${gochara.windows[0].event_class}', peak_date=${gochara.windows[0].peak_date}) ` +
          `already peaked before as_of_date=${as_of_date} — served for context (it is still ` +
          `inside the query's date-overlap horizon), but its intensity ranking should not be ` +
          `read as a forward-looking signal. See top_windows[].is_past_peak for the full set.`,
          'info',
        ))
      }

      // ── T5: the served reading_checklist receipt ──────────────────────────────────
      // Names WHICH classical units this response actually served, and for every absent
      // box WHY (not_computed / not_joined / salience_floored / not_yet_available). A
      // response that is not exhaustive over the classical territory self-discloses
      // `non_exhaustive: 'salience_sampled'`. This is the affordable completeness receipt —
      // the acharya's own checklist, served, not a catalog-id firehose.
      const reading_checklist_units: ChecklistUnit[] = [
        { unit: 'bhava_bhavesha_from_lagna', state: 'served', detail: `bhāva ${spec.bhava} sign + lord + occupants + aspects (lagna frame)` },
        { unit: 'bhava_bhavesha_from_chandra', state: bhavaSignMoon !== null && lordConditionMoon !== null ? 'served' : 'not_computed', detail: 'Sudarshana (Moon-frame) leg' },
        { unit: 'karakas', state: karakaConditions.length > 0 ? 'served' : 'not_joined', count: karakaConditions.length, detail: karakaConditions.length > 0 ? spec.karakas.join(', ') : 'no kāraka defined for a bare-bhāva query', ...(karakaConditions.length === 0 ? { drill: 'ganita_chart_facts_get' } : {}) },
        { unit: 'operative_varga', state: vargaConfirmed ? 'served' : 'empty_for_this_chart', detail: `${spec.varga} confirmation of bhāveśa/kāraka` },
        { unit: 'ashtakavarga', state: 'not_joined', detail: 'bhāva AV bindus not folded into judgment_query', drill: 'ganita_chart_facts_get (category=ashtakavarga_*) / assess_* (varga_analysis)' },
        { unit: 'special_lagnas', state: 'not_joined', detail: 'Indu/Ārūḍha/Hora lagnas not folded here', drill: 'ganita_special_lagnas_get' },
        { unit: 'sensitive_degree_firings', state: sensitive.firings.length > 0 ? 'served' : (sensitive.available ? 'empty_for_this_chart' : 'not_computed'), count: sensitive.firings.length, detail: 'puṣkara/gaṇḍānta/mṛtyu-bhāga/kartari fired-state (MC-030)' },
        { unit: 'kp_cusp_chain', state: kp.cusps.length > 0 ? 'served' : 'not_computed', count: kp.cusps.length, detail: `KP sub-lord chain for cusp(s) ${kpCusps.join('/')} (MC-031)` },
        { unit: 'yogi_avayogi', state: 'not_joined', detail: 'yogi/avayogi/duplicate-yogi/sahayogi now computed (T6 / MC-029, fact_category sensitive_point_yogi) but not yet folded into this judgment', drill: 'ganita_sensitive_degrees_get' },
        { unit: 'dasha_levels', state: timingAnchored ? 'served' : 'empty_for_this_chart', detail: 'Vimśottarī current + lord/kāraka mahādaśā windows + kala activation' },
        { unit: 'gochara_sweep', state: gochara.domain_covered ? 'served' : (gochara.available ? 'empty_for_this_chart' : 'not_computed'), count: gochara.upcoming_window_count, detail: `forward transit windows, domain='${spec.signal_domain}' (MC-033)` },
        { unit: 'tajaka', state: 'not_joined', detail: 'annual (varṣaphala/tājaka) not folded into the natal judgment', drill: 'ganita_tajaka_get' },
      ]
      const exhaustiveness = checklistExhaustiveness(reading_checklist_units)
      const reading_checklist = {
        units: reading_checklist_units,
        ...exhaustiveness,
        note: 'The classical bhāva-adhyāya checklist, served: each unit names whether THIS ' +
          'response carried it and — for every absent box — WHY. not_joined units carry a live ' +
          'drill handle. When not every unit is served/empty, the response self-discloses ' +
          'non_exhaustive: "salience_sampled" (an honest "this is not the whole territory").',
      }

      // Astrologically typed per design §28.4 ("the closed pointer vocabulary becomes
      // shastra moves") — pointer_type is ADDITIVE alongside the pre-existing
      // {instrument, hint} shape (R5 W3 Phase B); no caller reading only instrument/hint
      // is affected. The tail_dissent pointer is new this pass — it names the mandatory
      // dissent/tail-check step (design §26 PACT/investigation discipline) that a
      // judgment_query verdict, being convergent-by-construction, does not itself surface.
      const drill_pointers: Array<{ instrument: string; hint: string; pointer_type: DrillPointerType }> = [
        { instrument: 'ganita_chart_facts_get', hint: `divisional_chart=${spec.varga}: full ${spec.varga} placements for every graha (this call confirmed only bhāveśa/kāraka). (SC-18: was 'get_divisionals', a non-existent MCP tool name.)`, pointer_type: 'confirm_in_varga' },
        // A3/R-3: bearing_yogas is now ga_yoga_firings-sourced (firings-authoritative); the primary
        // drill pointer follows suit. get_signals remains for the demoted bearing_yogas_corroboration
        // (MSR) leg, distinct from this.
        { instrument: 'ganita_yoga_firings_get', hint: 'full fired-yoga detail (strength, bhaṅga/cancellation, partial-formation %, dāśā-activation) beyond the domain-bearing subset shown in bearing_yogas here.', pointer_type: 'opposing_yoga' },
        { instrument: 'bodha_signals_get', hint: `domain=${spec.signal_domain}, full yoga+dosha+karaka_alignment MSR signal set beyond bearing_yogas_corroboration's top ${max_signals} shown here — secondary/corroboration only (A3/R-3). (SC-18: was 'query_signals', a non-existent MCP tool name.)`, pointer_type: 'opposing_yoga' },
        { instrument: 'ganita_dashas_get', hint: 'full multi-level dasha timeline beyond the current + mahadasha-window slice shown here.', pointer_type: 'dasha_of_promise' },
        { instrument: 'bodha_graph_traverse_get', hint: `about:lord_of(bhava ${spec.bhava}) — causal graph context for the bhāveśa.`, pointer_type: 'dispositor_chain' },
        { instrument: 'ref_rules_search', hint: `verse citations for ${spec.label.toLowerCase()} judgment (BPHS/Phaladeepika bhava-adhyaya). (RC-04: was 'query_classical_texts', the internal registry capability name (marsys://tool/L0/query_classical_texts), not a live MCP tool name — same SC-18 dead-pointer class as the two siblings above; ref_rules_search is one of the tool's live MCP aliases per mcp_capability_bridge.ts.)`, pointer_type: 'other' },
        { instrument: 'synth_tail_divergence_get', hint: `the mandatory dissent/tail-check step (design §26) — contrarian signals and unresolved tensions bearing on ${spec.label.toLowerCase()} not surfaced by this call's convergent verdict.`, pointer_type: 'tail_dissent' },
        // T5 (PŪRTI): drill handles for the three legs now served inline.
        { instrument: 'ganita_sensitive_degrees_get', hint: 'full sensitive-degree table (all check types, fired + not-fired, per graha) beyond the high-signal firings surfaced in sensitive_degree_firings here.', pointer_type: 'other' },
        { instrument: 'ganita_kp_cusps_get', hint: `full 12-cusp KP picture (Placidus/Sripati degrees, ruling planets, per-graha KP chains) beyond the ${kpCusps.join('/')} cusp(s) in kp_cusp_chain here.`, pointer_type: 'other' },
        { instrument: 'gochara_forecast_get', hint: `full forward gochara window set with signed intensities for domain='${spec.signal_domain}' beyond the compact top-windows summary in gochara_sweep here.`, pointer_type: 'other' },
      ]

      return {
        content: {
          chart_id,
          ayanamsha_id,
          about: { domain: domainKey, bhava: spec.bhava, label: spec.label, karakas: spec.karakas, operative_varga: spec.varga },
          checklist: {
            bhava_condition: {
              from_lagna: { sign: bhavaSignLagna.sign, house_number: bhavaSignLagna.house_number, frame: 'lagna' },
              from_chandra: bhavaSignMoon ? { sign: bhavaSignMoon.sign, house_number: bhavaSignMoon.house_number, frame: 'chandra' } : null,
            },
            bhavesha_condition: { from_lagna: lordCondition, from_chandra: lordConditionMoon },
            karaka_condition: karakaConditions,
            occupants: {
              from_lagna: occupantsLagnaEntity.grahas,
              from_chandra: occupantsMoon?.grahas ?? null,
            },
            aspecting_grahas: aspectsLagna.grahas,
            varga_confirmation: { varga: spec.varga, rows: vargaConfirmation },
            // A3/R-3: bearing_yogas is now ga_yoga_firings-sourced (firings-authoritative — real
            // strength + bhaṅga state) and stays a flat array (registry_bridge.ts's response-budget
            // trimmer + the existing integration test both expect `Array.isArray(bearing_yogas)`).
            // The prior primary source (MSR yoga signals via query_signals) is demoted to a
            // sibling array, never discarded (B.10) — see judgment_flags for both caveats.
            bearing_yogas: bearingYogaFirings,
            bearing_yogas_corroboration: yogaSignalsCorroboration,
            // DR-9 Part B: the threatening layer (signed partitioned serve).
            bearing_afflictions,
            affliction_mechanisms,
            timing_hooks: timing,
            // T5 (PŪRTI): the three computed-but-never-joined classical legs, now served inline.
            sensitive_degree_firings: sensitive.firings,
            kp_cusp_chain: { cusps: kp.cusps, note: kp.note },
            gochara_sweep: {
              domain: spec.signal_domain,
              domain_covered: gochara.domain_covered,
              upcoming_window_count: gochara.upcoming_window_count,
              past_peak_window_count: gochara.past_peak_window_count,
              valence_breakdown: gochara.valence_breakdown,
              window_range: gochara.window_range,
              // F-119 (EKAVĀKYATĀ A-06): attach resolution_disclosure so callers
              // distinguish genuine timing windows from era-scale context rows.
              // Bare point rows (point-shaped, no peak_date) are suppressed per §N.6.
              top_windows: withSweepDisclosure(gochara.windows ?? []),
              note: gochara.note,
            },
          },
          verdict,
          receipt,
          // T5 (PŪRTI): the served completeness receipt — which classical units this
          // response carried, and WHY each absent one is absent (the Offer-Law fix).
          reading_checklist,
          judgment_flags,
          drill_pointers,
          resolution_chains: {
            bhava_lagna: bhavaLagna.chain,
            bhavesha_lagna: lordLagna.chain,
            occupants_lagna: occupantsLagna.chain,
          },
          fact_id_refs: Array.from(fact_ids),
        },
        is_error: false,
      }
    } catch (err) {
      if (err instanceof AddressResolutionError) {
        return { content: { error: err.message, chart_id, spec }, is_error: true }
      }
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

/**
 * Register the D9 judgment-query capability.
 * GATE A: only registers a NEW file for this wave — does not edit registry/index.ts.
 */
export function registerD9JudgmentCapabilities(): void {
  registerCapability(judgmentQueryCapability)
}

/** D9 capability URI roster (for Gate C reverse-citation checks and roster smoke tests). */
export const D9_CAPABILITY_URIS = [
  'marsys://tool/L-JUDGMENT/judgment_query',
] as const

// Auto-register on import — consistent with the D5-D8 layer pattern.
registerD9JudgmentCapabilities()
