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
import type { DrillPointerType } from '../../envelope'

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
}

const SHASTRA_MAP: Record<string, DomainSpec> = {
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
            'judgment_query requires either `domain` (marriage/career/wealth/health/progeny/education/spirituality) ' +
            'or `bhava` (1-12).',
        },
        is_error: true,
      }
    }

    const judgment_flags: string[] = []
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
          judgment_flags.push(`karaka_unresolved: ${karakaName} — ${String(e)}`)
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
        judgment_flags.push(`from_moon_resolution_failed: ${String(e)}`)
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
        judgment_flags.push(`varga_confirmation_failed: ${String(e)}`)
      }

      // ── Step 7: bearing yogas/doshas (formed) — notably-absent is an honest gap (D3 unbuilt) ──
      let yogasChecked = 0
      let yogaSignals: Record<string, unknown>[] = []
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
          yogaSignals = ((c['signals'] as Record<string, unknown>[]) ?? []).map(s => ({
            signal_id: s['signal_id'],
            signal_summary: s['signal_summary_text'],
            computed_salience: s['computed_salience'],
            signal_tradition: s['signal_tradition'],
          }))
          yogasChecked = yogaSignals.length
        }
      } catch (e) {
        judgment_flags.push(`yoga_signal_fetch_failed: ${String(e)}`)
      }
      // D-13: bearing_yogas surfaces bodha_msr_signals 'yoga' signal_type_class rows —
      // the SAME requires_pass catalog shape graha_portrait caveats under JL-004 (a
      // single-pass rule-catalog match against L1 facts, not a cross-verified confirmed
      // firing). Restated here at THIS point of use rather than left implicit, per D-13 —
      // never present these as settled findings without the caveat.
      if (yogaSignals.length > 0) {
        judgment_flags.push(
          'bearing_yogas_caveat: bearing_yogas are requires_pass catalog label matches ' +
          '(single-pass evaluation against L1 facts) — not cross-verified confirmed firings. ' +
          'Treat as candidate classifications to verify, not settled findings (JL-004).',
        )
      }
      judgment_flags.push(
        'bhanga_not_checked: notably-absent/cancellation (bhaṅga) near-miss checking requires ' +
        'a data-plane addition (design §12 D3) not yet built for any chart — reported honestly, not fabricated.',
      )

      // ── Step 9: timing hooks (reuses get_dashas — no parallel dasha query) ──
      const timing: Record<string, unknown> = { current: null, lord_mahadasha_windows: [], karaka_mahadasha_windows: [] }
      let timingAnchored = false
      try {
        const { getDashasCapability } = await import('./L1_ganita/get_dashas')
        const today = new Date().toISOString().slice(0, 10)
        const currentRes = await getDashasCapability.handler(
          { chart_id, ayanamsha_id, system: 'vimshottari', as_of_date: today, all_levels: true, limit: 5 },
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
        // Lane 5 (§N.6 / CR-1/63 handoff, serving-only — no new joins): honesty fix only.
        // The fetches above can each succeed (is_error=false) yet still hand back an empty
        // rows array — that is NOT the same thing as "timing anchored". Require actual
        // content (a current-period row, or at least one non-empty mahadasha window) before
        // claiming timing_anchored=true; an all-empty result is an honest false, one line,
        // no new dasha joins (anti-scope respected).
        const currentRows = (timing['current'] as unknown[] | undefined) ?? []
        const hasWindowRows = Object.values(windowsByGraha).some(
          w => Array.isArray(w) && w.length > 0,
        )
        timingAnchored = currentRows.length > 0 || hasWindowRows
        if (!timingAnchored) {
          judgment_flags.push(
            'timing_anchored_false: dasha fetches succeeded but returned zero rows for both ' +
            'the current period and every mahadasha window checked — reported honestly as ' +
            'not-anchored rather than claiming success over an empty payload (CR-1/63 class).',
          )
        }
      } catch (e) {
        judgment_flags.push(`timing_hook_failed: ${String(e)}`)
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

      const compositeScore = d1Score + vargaTerm

      let verdict_grade: string
      if (compositeScore >= 2.5) verdict_grade = 'convergent_strong'
      else if (compositeScore >= 1) verdict_grade = 'convergent_moderate'
      else if (compositeScore >= -1) verdict_grade = 'mixed'
      else verdict_grade = 'contested'

      // D1-only grade (what the pre-WP-1.8 formula would have returned) — surfaced so the
      // varga contribution is auditable and a reviewer can see WHEN the amsha moved the verdict.
      let d1_only_grade: string
      if (d1Score >= 2.5) d1_only_grade = 'convergent_strong'
      else if (d1Score >= 1) d1_only_grade = 'convergent_moderate'
      else if (d1Score >= -1) d1_only_grade = 'mixed'
      else d1_only_grade = 'contested'

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
        varga_moved_verdict: vargaTermApplied && d1_only_grade !== verdict_grade,
        varga_subscores: {
          bhavesha: { graha: bhaveshaVarga.graha, varga: spec.varga, dignity_state: bhaveshaVarga.dignity_state, weight: bhaveshaVarga.dignity_weight, contribution: Math.round(bhaveshaVargaContribution * 100) / 100 },
          karakas: karakaVargaList.map(k => ({ graha: k.graha, varga: spec.varga, dignity_state: k.dignity_state, weight: k.dignity_weight })),
          note: spec.varga === 'D1'
            ? 'Operative varga is D1 — varga term skipped to avoid double-counting the D1 dignity already in the composite.'
            : (vargaTermApplied
                ? `Operative-varga (${spec.varga}) dignity of bhāveśa (×${VARGA_BHAVESHA_WEIGHT}) + kāraka(s) mean (×${VARGA_KARAKA_WEIGHT}) — the amsha as the ripening of the rasi promise (BPHS Ch.6-7; Parashari D9-is-the-fruit dictum).`
                : `No ${spec.varga} dignity rows resolved for bhāveśa/kāraka — varga term = 0 (honest absence, not fabricated).`),
        },
        note:
          'Deterministic weighted aggregation of already-computed dignity/shadbala/occupant/aspect ' +
          'signals PLUS a re-derived operative-varga (amsha) term — NOT an LLM judgment and NOT a ' +
          'calibrated probability (that is L4/L5\'s domain). D1 weights: dignity ±2..−2, ' +
          'benefic/malefic occupant ±0.5, benefic/malefic aspect ±0.3, weak-lord (<3 rupas) −0.5, ' +
          'from-Moon lord dignity ×0.5. Varga term (R-46/WP-1.8): bhāveśa operative-varga dignity ' +
          `×${VARGA_BHAVESHA_WEIGHT} + kāraka(s) mean ×${VARGA_KARAKA_WEIGHT} (skipped when operative varga is D1). ` +
          'composite_score = d1_score + varga_term; d1_only_grade shows the pre-varga verdict.',
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
        bhanga_checked: false,
        timing_anchored: timingAnchored,
      }

      // Astrologically typed per design §28.4 ("the closed pointer vocabulary becomes
      // shastra moves") — pointer_type is ADDITIVE alongside the pre-existing
      // {instrument, hint} shape (R5 W3 Phase B); no caller reading only instrument/hint
      // is affected. The tail_dissent pointer is new this pass — it names the mandatory
      // dissent/tail-check step (design §26 PACT/investigation discipline) that a
      // judgment_query verdict, being convergent-by-construction, does not itself surface.
      const drill_pointers: Array<{ instrument: string; hint: string; pointer_type: DrillPointerType }> = [
        { instrument: 'ganita_chart_facts_get', hint: `divisional_chart=${spec.varga}: full ${spec.varga} placements for every graha (this call confirmed only bhāveśa/kāraka). (SC-18: was 'get_divisionals', a non-existent MCP tool name.)`, pointer_type: 'confirm_in_varga' },
        { instrument: 'get_signals', hint: `domain=${spec.signal_domain}, full yoga+dosha+karaka_alignment signal set beyond the top ${max_signals} shown here. (SC-18: was 'query_signals', a non-existent MCP tool name.)`, pointer_type: 'opposing_yoga' },
        { instrument: 'get_dashas', hint: 'full multi-level dasha timeline beyond the current + mahadasha-window slice shown here.', pointer_type: 'dasha_of_promise' },
        { instrument: 'traverse_graph', hint: `about:lord_of(bhava ${spec.bhava}) — causal graph context for the bhāveśa.`, pointer_type: 'dispositor_chain' },
        { instrument: 'query_classical_texts', hint: `verse citations for ${spec.label.toLowerCase()} judgment (BPHS/Phaladeepika bhava-adhyaya).`, pointer_type: 'other' },
        { instrument: 'synth_tail_divergence_get', hint: `the mandatory dissent/tail-check step (design §26) — contrarian signals and unresolved tensions bearing on ${spec.label.toLowerCase()} not surfaced by this call's convergent verdict.`, pointer_type: 'tail_dissent' },
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
            bearing_yogas: yogaSignals,
            timing_hooks: timing,
          },
          verdict,
          receipt,
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
