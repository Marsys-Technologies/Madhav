/**
 * muhurta_finder.ts — MCP tool: muhurta_finder (PH-4-4)
 * Layer L4 · Phala (Predictive Engine) · Asset PH-4-4 (phala.muhurta)
 * BRAHMA-PH-4-4
 *
 * INVERTS the Phala prediction engine:
 *   - Prediction: "what will happen given the current time?"
 *   - Electional: "WHEN is best to act for a desired action_type?"
 *
 * Tool: muhurta_finder(chart_id, action_type, date_range, min_score?)
 *   → {windows:[{start,end,score,factors}], provenance_envelope}
 *
 * Algorithm: for each 48-hour window in the requested date range (max 90 days):
 *   auspiciousness_score = panchanga_quality(40%) + dasha_quality(30%)
 *                        + transit_quality(20%) + signal_activation(10%)
 *
 * action_types: marriage | travel | business | medical | education | property | general
 *
 * Contract (BRAHMA PH-4-4):
 *   - 0 <= score <= 1 on every window
 *   - len(windows) >= 1 for a valid 90-day range
 *   - source_citation non-null on every window (B.3 mandate)
 *   - provenance_envelope on every response
 *
 * FORENSIC grounding:
 *   Reference birth: 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *   A high-score education muhurta for this chart should align with
 *   Mercury+Pushya windows (Mercury MD + Pushya nakshatra per BPHS ch.46).
 *
 * Architecture:
 *   MCP tool → callPlatformPrimitive('muhurta_finder', params)
 *   → /api/mcp/primitives/muhurta_finder (platform) → query_muhurat retrieval tool
 *   → sidecar POST /api/compute/muhurat (Phase 4C-6 muhurat router)
 *
 * surgical: true (pure retrieval; no LLM calls)
 * BRAHMA-PH-4-4
 */

import { z } from 'zod'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── MCP response wrapping (T-7 fix) ─────────────────────────────────────────
//
// R6 0b-deadtools (T-7): muhurta_finder returned nothing at all — no windows,
// no empty_reason, no error object. Root cause: handleMuhurtaFinder's early
// auth-denied branch aside, both the `!env.ok` branch and the success branch
// returned the raw McpEnvelope-shaped object ({ok, trace_id, epistemics,
// result, ...}) directly from the tool handler. The MCP SDK tool-call
// contract requires a `{content: [...], structuredContent?, isError?}` shape
// (see every sibling tool's `dualOutput`/`errOut` helper, e.g.
// kala_muhurta_get in register_p1_aliases.ts) — an object with no `content`
// key is not a valid tool result, so the client silently rendered empty.
// This was never an unreturned promise; it was a mis-shaped resolved one.
// W3-L5 (budget unification): muhurta_finder's `windows` array (up to a 90-day scan of
// 48-hour windows) previously shipped through this dualOutput with no response-budget
// pass at all — part of the ~36-of-~115 unclamped surface (GT-48).
function dualOutput(data: unknown): { structuredContent: { type: 'object'; object: unknown }; content: [{ type: 'text'; text: string }] } {
  const budgeted = budgetMcpContent(data, 'muhurta_finder')
  return {
    structuredContent: { type: 'object', object: budgeted },
    content: [{ type: 'text', text: JSON.stringify(budgeted) }],
  }
}

function errorOutput(message: string, extra?: Record<string, unknown>): { structuredContent: { type: 'object'; object: unknown }; content: [{ type: 'text'; text: string }]; isError: true } {
  return { ...dualOutput({ ok: false, error: message, tool: 'muhurta_finder', ...extra }), isError: true }
}

// ── Input schema ───────────────────────────────────────────────────────────────

export const MuhurtaFinderInputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to find auspicious windows for. Must be a valid chart UUID from the charts table.'
    ),

  action_type: z
    .enum([
      'marriage', 'travel', 'business', 'medical', 'education', 'property', 'general',
      // ── Lane F (EL-50) taxonomy extension — spiritual/remedial classes ──
      'spiritual_initiation', 'remedial_ritual', 'japa_start',
    ])
    .describe(
      'The type of action to find auspicious windows for. ' +
      'marriage — vivah muhurta (Rohini/Guruvara auspicious per BPHS ch.46); ' +
      'travel — yatra muhurta (Ashwini/Mrigashira/Pushya preferred); ' +
      'business — vyapara muhurta (Rohini/Hasta/Budhavara); ' +
      'medical — rogashanti muhurta (Pushya/Ashwini; avoid Krittika); ' +
      'education — vidya muhurta (Pushya nakshatra most auspicious; Mercury/Thursday days); ' +
      'property — griha/bhumi muhurta (Uttaraphalguni/Uttarashada); ' +
      'general — all action types permissible. ' +
      // Lane F (EL-50) additions, each with a cited classical rule set (see ACTIVITY_RULES):
      'spiritual_initiation — mantra/guru dīkṣā (Pushya/Punarvasu/Anuradha/Revati; Jupiter-day/hora; ' +
      'avoid ugra & tīkṣṇa nakshatras — Muhurta Chintamani dīkṣā-prakaraṇa); ' +
      'remedial_ritual — upaya/homa/dāna/śānti-karma (Pushya/Ashwini/Hasta/Mrigashira mridu-kshipra; ' +
      'BPHS Grahaśānti Adhyāya; Muhurta Chintamani śānti-karma); ' +
      'japa_start — beginning a sustained japa/anuṣṭhāna (dhruva/sthira nakshatras Rohini/Uttara-* for ' +
      'permanence + Pushya; Jupiter/Moon day — Muhurta Martanda anuṣṭhāna-ārambha).'
    ),

  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
    })
    .describe(
      'Date range to search for auspicious windows. ' +
      'Maximum 90 days (up to 45 × 48-hour windows). ' +
      'Windows are 48-hour blocks starting at midnight UTC. ' +
      'Example next 90 days: {"start":"2026-06-04","end":"2026-09-01"}.'
    ),

  min_score: z
    .number()
    .min(0.0)
    .max(1.0)
    .optional()
    .describe(
      'Minimum auspiciousness_score [0.0–1.0]. Default 0.0 (all windows). ' +
      'Recommended thresholds: high ≥ 0.70; medium 0.50–0.69; low < 0.50. ' +
      'Score = panchanga_quality(40%) + dasha_quality(30%) ' +
      '+ transit_quality(20%) + signal_activation(10%).'
    ),

  limit: z
    .number()
    .int()
    .min(1)
    .max(45)
    .default(20)
    .describe(
      'Maximum number of windows to return, ranked by auspiciousness_score DESC. ' +
      'Default 20; maximum 45 (one per 48-hour slot in a 90-day range).'
    ),

  // ── Lane F (EL-50) — native tāra bala join ──────────────────────────────────
  native_janma_nakshatra: z
    .string()
    .optional()
    .describe(
      "The native's janma (birth) nakshatra — the Moon's natal nakshatra — used to join " +
      'tāra-bala into the ranking. When supplied, each window is checked for adverse tārā ' +
      '(Vipat/Pratyak/Vadha counted from the janma nakshatra to the window-day Moon nakshatra, ' +
      'Nava-tārā chakra, Muhurta Chintamani): an adverse tārā HARD-FLAGS and DEMOTES the window ' +
      'so it can never silently rank #1. Accepts the nakshatra name (e.g. "Purva Bhadrapada"). ' +
      'Omit → tāra-bala reported as unavailable (never fabricated).'
    ),

  // ── Lane F (EL-50) — target-graha transit gate (consumes β C5 sidereal service) ──
  target_graha: z
    .enum(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'])
    .optional()
    .describe(
      'When the election is tied to a specific planet (e.g. a gemstone/remedy timing for a graha), ' +
      "check that graha's TRANSIT dignity/combustion/retrogression during each window and " +
      'flag/deprioritize windows where the target graha is combust, debilitated, or retrograde. ' +
      'Transit dignity is sourced from β\'s C5 sidereal ephemeris service; while C5 is DRAFT this ' +
      'emits a documented pending-C5 marker per window (never a fabricated dignity).'
    ),

  // ── Lane F (EL-53) — file the elected window as a falsifiable prediction ─────
  file_as_prediction: z
    .boolean()
    .optional()
    .describe(
      'When true, the response gains a prediction_filing block: a prospective-ledger-shaped row ' +
      'for the top-ranked elected window (claim, event_class, window, predicted quality, scoring ' +
      'factors, mandatory falsifier) that is closable via mimamsa_outcome_record. Turns elections ' +
      'into the fastest-cycling falsifiable evidence stream.'
    ),
})

export type MuhurtaFinderInput = z.infer<typeof MuhurtaFinderInputSchema>

// ── Output shape (documented; actual shape comes from the platform) ────────────

/** Factors breakdown for one muhurta window. */
export interface MuhurtaFactors {
  panchanga_quality: number      // [0.0, 1.0] — tithi × vara × nakshatra × yoga
  dasha_quality: number          // [0.0, 1.0] — active MD/AD benefic quality
  transit_quality: number        // [0.0, 1.0] — key transits in the window
  signal_activation: number      // [0.0, 1.0] — MSR signal activation for action_type
  panchanga_details: {
    tithi_name: string
    vara_lord: string
    moon_nakshatra: string
    yoga: string
    inauspicious_windows: string[]
  }
  dasha_details: {
    md_lord: string
    ad_lord: string
  }
  avoid_notes: string[]          // empty if no knockout conditions apply
}

/** Lane F (EL-50) — tāra-bala verdict for one window relative to the native's janma nakshatra. */
export interface TaraBalaVerdict {
  janma_nakshatra: string
  day_nakshatra: string
  count_from_janma: number       // inclusive Nava-tārā count 1..27
  tara_index: number             // 1..9
  tara_name: string              // Janma | Sampat | Vipat | ... | Ati-Mitra
  favorable: boolean
  adverse: boolean               // Vipat(3) | Pratyak(5) | Vadha(7)
  severity: 'none' | 'caution' | 'severe'
  citation: string
}

/** Lane F (EL-50) — target-graha transit-gate verdict for one window. */
export interface TargetGrahaVerdict {
  graha: string
  status: 'ok' | 'flagged' | 'pending_c5_service'
  combust: boolean | null
  debilitated: boolean | null
  retrograde: boolean | null
  transit_dignity: string | null
  note: string
  citation: string
}

/** Lane F (EL-50) — one planetary-hour (horā) sub-slot inside a window. */
export interface HoraSlot {
  start_ist: string              // ISO +05:30
  end_ist: string                // ISO +05:30
  hora_lord: string
  benefic: boolean
}

/** One ranked auspicious window. */
export interface MuhurtaWindow {
  start: string                  // ISO datetime UTC
  end: string                    // ISO datetime UTC (48h after start)
  score: number                  // auspiciousness_score [0.0, 1.0]
  factors: MuhurtaFactors
  source_citation: string        // NEVER null — B.3 mandate
  // ── Lane F (EL-50) enrichment (all optional; present only when the relevant input was given) ──
  start_ist?: string             // window start as explicit IST (+05:30) timestamp
  end_ist?: string               // window end as explicit IST (+05:30) timestamp
  activity_fit?: {
    favorable_nakshatra: boolean
    favorable_vara: boolean
    avoid_nakshatra_hit: boolean
    note: string
    citation: string
  }
  tara_bala?: TaraBalaVerdict
  target_graha_check?: TargetGrahaVerdict
  hora_ladder?: HoraSlot[]
  hard_flag?: boolean            // adverse tārā or flagged target graha — never a silent top rank
  disqualified?: boolean         // severe (Vadha tārā, or combust/debilitated target graha)
  rank_penalty_reason?: string[]
}

/** Provenance envelope on every muhurta_finder response. */
export interface MuhurtaProvenanceEnvelope {
  source: string           // 'phala.muhurta'
  asset: string            // 'PH-4-4'
  algorithm: string        // score formula
  min_score_applied: number
  chart_id: string
  action_type: string
  queried_at: string       // ISO datetime UTC
  l1_ground_truth: string  // FORENSIC + panchanga_daily + MSR citations
  b3_citation_compliant: boolean
}

/** Full muhurta_finder response. */
export interface MuhurtaFinderResult {
  ok: boolean
  chart_id: string
  action_type: string
  query_window: { start: string; end: string }
  windows: MuhurtaWindow[]
  window_count: number
  provenance_envelope: MuhurtaProvenanceEnvelope
  /**
   * R5.1 C3 — present (and windows: []) when the requested date_range has no
   * real panchanga_daily coverage (outside the rolling +12-month populated
   * window). Never fabricated data for out-of-window dates — see
   * brahmagyan/phala/muhurta.py muhurta_finder()'s empty_reason construction.
   */
  empty_reason?: string
  // ── Lane F (EL-50 / EL-53) enrichment envelope ──────────────────────────────
  lane_f?: {
    activity_rule_set?: ActivityRule & { action_type: string; base_action_type: string }
    tara_bala_status: 'applied' | 'unavailable_no_janma_nakshatra'
    tara_bala_note?: string
    target_graha_status?: 'applied' | 'pending_c5_service' | 'not_requested'
    target_graha_note?: string
    hora_status: 'applied'
    hora_sunrise_assumption: string
    ranking_note: string
  }
  /** EL-53 — prospective-ledger-shaped filing for the top elected window. */
  prediction_filing?: PredictionFiling
}

/** Lane F (EL-53) — prospective-ledger-shaped filing payload (matches
 *  platform/src/lib/lel/prospective_ledger.ts fileProspectivePrediction input). */
export interface PredictionFiling {
  claim: string
  event_class: string
  claim_shape: 'window'
  window_start: string
  window_end: string
  confidence: number
  falsifier: string
  generator_class: 'engine'
  source_citation: string
  scoring_factors: MuhurtaFactors
  elected_window: { start: string; end: string; start_ist?: string; end_ist?: string }
  predicted_quality: { score: number; star_rating: number }
  close_via: {
    tool: 'mimamsa_outcome_record'
    verdict_vocabulary: ['confirmed', 'partial', 'denied']
    note: string
  }
  /** Whether the row was persisted. In γ.F scope the persistence write lives in
   *  platform/src/lib/lel/prospective_ledger.ts (out of scope) → 'payload_only'. */
  persistence: 'payload_only' | 'filed'
  persistence_note: string
}

// ══════════════════════════════════════════════════════════════════════════════
// Lane F (EL-50) — muhūrta elevation primitives
// ══════════════════════════════════════════════════════════════════════════════
// All functions below are pure, deterministic, classically-grounded re-derivations
// (B.10-compliant: they compute from KNOWN nakshatra/vara inputs, never inventing a
// chart value). They post-process the platform's returned windows; the coarse
// panchanga/dasha/transit score still comes from the Python muhurta primitive.

/** The 27 nakshatras, index 0 → number 1 (Ashwini) … index 26 → number 27 (Revati). */
export const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
  'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
  'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
  'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
  'Uttara Bhadrapada', 'Revati',
] as const

/** Loose-match a nakshatra name → number 1..27 (case/spacing/diacritic tolerant). Returns null if unknown. */
export function nakshatraNumber(name: string | undefined | null): number | null {
  if (!name) return null
  const norm = (s: string) => s.toLowerCase().replace(/[\s_\-.]+/g, '').replace(/aa/g, 'a').replace(/sh/g, 's').replace(/ph/g, 'f')
  const target = norm(name)
  for (let i = 0; i < NAKSHATRAS.length; i++) {
    const nk = NAKSHATRAS[i]
    if (nk && norm(nk) === target) return i + 1
  }
  // common alias fragments
  const alias: Record<string, number> = {
    pushyami: 8, aslesha: 9, poorvaphalguni: 11, uttaraphalguni: 12, poorvaashadha: 20,
    uttaraashadha: 21, dhanistha: 23, satabhisha: 24, poorvabhadrapada: 25, uttarabhadrapada: 26,
    mrigasira: 5, arudra: 6, thiruvathirai: 6,
  }
  return alias[target] ?? null
}

// ── Tāra bala (Nava-tārā chakra — Muhurta Chintamani, Nakshatra Prakarana) ──────
export const TARA_NAMES = [
  'Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak', 'Sadhaka', 'Vadha', 'Mitra', 'Ati-Mitra',
] as const
/** The three adverse tārās: Vipat(3), Pratyak/Pratyari(5), Vadha/Naidhana(7). */
export const ADVERSE_TARA = new Set([3, 5, 7])
/** Vadha (7) — Naidhana, most severe (destruction). */
export const SEVERE_TARA = new Set([7])
export const TARA_CITATION = 'Nava-tārā chakra — Muhurta Chintamani, Nakshatra Prakaraṇa (tārā counted inclusively from janma nakshatra to the day Moon nakshatra, mod 9).'

/**
 * Compute the tāra-bala verdict for a window given the native's janma nakshatra and
 * the window-day Moon nakshatra. Pure classical re-derivation (no chart value invented).
 */
export function computeTaraBala(janmaNakNum: number, dayNakNum: number): {
  count_from_janma: number; tara_index: number; tara_name: string;
  favorable: boolean; adverse: boolean; severity: 'none' | 'caution' | 'severe';
} {
  const count = ((dayNakNum - janmaNakNum + 27) % 27) + 1   // inclusive 1..27
  const tara_index = ((count - 1) % 9) + 1                    // 1..9
  const adverse = ADVERSE_TARA.has(tara_index)
  const severity: 'none' | 'caution' | 'severe' =
    SEVERE_TARA.has(tara_index) ? 'severe' : adverse ? 'caution' : 'none'
  return {
    count_from_janma: count,
    tara_index,
    tara_name: TARA_NAMES[tara_index - 1] ?? 'Unknown',
    favorable: !adverse,
    adverse,
    severity,
  }
}

/** Safe nakshatra-name lookup by 1-based number. */
function nakName(num: number): string {
  return NAKSHATRAS[num - 1] ?? `Nakshatra#${num}`
}

// ── Activity taxonomy (EL-50 sub-item 1) — classical rule sets per action_type ──
export type ActionType =
  | 'marriage' | 'travel' | 'business' | 'medical' | 'education' | 'property' | 'general'
  | 'spiritual_initiation' | 'remedial_ritual' | 'japa_start'

export interface ActivityRule {
  /** canonical event_class in the L3 ka_muhurta_seva / score_muhurat vocabulary */
  event_class: string
  /** action_type the Python muhurta primitive is called with (new classes map to a known base) */
  base_action_type: string
  favorable_nakshatras: number[]
  favorable_varas: string[]       // weekday lord names (Sun..Saturn)
  avoid_nakshatras: number[]
  karaka_graha: string | null
  citation: string
}

// vara lords by weekday index (0=Sunday)
const VARA_LORD = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'] as const

export const ACTIVITY_RULES: Record<ActionType, ActivityRule> = {
  marriage: {
    event_class: 'vivah', base_action_type: 'marriage',
    favorable_nakshatras: [4, 5, 13, 12, 21, 26, 27, 17],  // Rohini, Mrigashira, Hasta, Uttara-*, U.Bhadra, Revati, Anuradha
    favorable_varas: ['Moon', 'Jupiter', 'Venus'],
    avoid_nakshatras: [2, 6, 9, 10, 19],
    karaka_graha: 'Venus',
    citation: 'BPHS ch.46 (vivāha muhūrta); Muhurta Chintamani vivāha-prakaraṇa.',
  },
  travel: {
    event_class: 'yatra', base_action_type: 'travel',
    favorable_nakshatras: [1, 5, 8, 7, 13, 22, 24, 26],
    favorable_varas: ['Moon', 'Mercury', 'Jupiter', 'Venus'],
    avoid_nakshatras: [3, 9, 16],
    karaka_graha: 'Mercury',
    citation: 'Muhurta Chintamani yātrā-prakaraṇa (Ashwini/Mrigashira/Pushya cara-nakshatras).',
  },
  business: {
    event_class: 'vyapara', base_action_type: 'business',
    favorable_nakshatras: [4, 13, 8, 15, 22, 23, 24],
    favorable_varas: ['Mercury', 'Jupiter', 'Venus'],
    avoid_nakshatras: [2, 10, 19],
    karaka_graha: 'Mercury',
    citation: 'Muhurta Chintamani vyāpāra/ārambha; Budha-vāra + Hasta/Chitra.',
  },
  medical: {
    event_class: 'upaya_ritual', base_action_type: 'medical',
    favorable_nakshatras: [8, 1, 5, 17, 27],
    favorable_varas: ['Moon', 'Mercury', 'Jupiter'],
    avoid_nakshatras: [3, 6, 9, 18, 19],   // avoid tīkṣṇa; Krittika
    karaka_graha: 'Sun',
    citation: 'Rogaśānti muhūrta — Muhurta Chintamani; Pushya/Ashwini mridu, avoid Krittika/tīkṣṇa.',
  },
  education: {
    event_class: 'vidya_arambha', base_action_type: 'education',
    favorable_nakshatras: [8, 7, 13, 12, 21, 26, 5, 17],
    favorable_varas: ['Mercury', 'Jupiter'],
    avoid_nakshatras: [2, 10, 19],
    karaka_graha: 'Mercury',
    citation: 'BPHS ch.46 §vidyā (Pushya + Budha/Guru-vāra most auspicious).',
  },
  property: {
    event_class: 'griha_pravesh', base_action_type: 'property',
    favorable_nakshatras: [4, 12, 21, 26, 13, 22, 27],   // dhruva/sthira nakshatras
    favorable_varas: ['Moon', 'Mercury', 'Jupiter', 'Venus'],
    avoid_nakshatras: [2, 6, 10, 19],
    karaka_graha: 'Mars',
    citation: 'Gṛha/bhūmi muhūrta — Uttara-*/Rohini (dhruva/sthira); Muhurta Chintamani gṛha-prakaraṇa.',
  },
  general: {
    event_class: 'general', base_action_type: 'general',
    favorable_nakshatras: [1, 4, 5, 8, 13, 17, 27],
    favorable_varas: ['Moon', 'Mercury', 'Jupiter', 'Venus'],
    avoid_nakshatras: [],
    karaka_graha: null,
    citation: 'General śubha-nakshatra set (mridu + kshipra); BPHS ch.46.',
  },
  // ── EL-50 taxonomy extension ──────────────────────────────────────────────────
  spiritual_initiation: {
    event_class: 'mantra_initiation', base_action_type: 'general',
    // Pushya, Punarvasu, Anuradha, Revati, Hasta, Ashwini, Mrigashira, U.Bhadrapada
    favorable_nakshatras: [8, 7, 17, 27, 13, 1, 5, 26],
    favorable_varas: ['Jupiter', 'Moon'],
    // avoid ugra (Bharani, Magha, P.Phalguni, P.Ashadha, P.Bhadrapada) + tīkṣṇa (Ardra, Ashlesha, Jyeshtha, Mula)
    avoid_nakshatras: [2, 10, 11, 20, 25, 6, 9, 18, 19],
    karaka_graha: 'Jupiter',
    citation: 'Mantra/guru dīkṣā — Muhurta Chintamani dīkṣā-prakaraṇa; Guru-vāra + Jupiter-horā, Pushya/Anuradha; avoid ugra & tīkṣṇa nakshatras.',
  },
  remedial_ritual: {
    event_class: 'upaya_ritual', base_action_type: 'general',
    // śānti-karma: mridu (Mrigashira, Chitra, Anuradha, Revati) + kshipra (Ashwini, Pushya, Hasta) + Shravana
    favorable_nakshatras: [8, 1, 13, 5, 14, 17, 27, 22],
    favorable_varas: ['Moon', 'Mercury', 'Jupiter', 'Venus'],
    avoid_nakshatras: [2, 10, 11, 20, 25],   // avoid ugra for pacific śānti
    karaka_graha: 'Jupiter',
    citation: 'Upaya/homa/dāna/śānti-karma — BPHS Grahaśānti Adhyāya; Muhurta Chintamani śānti-karma-prakaraṇa (mridu/kshipra nakshatras).',
  },
  japa_start: {
    event_class: 'sadhana_initiation', base_action_type: 'general',
    // sustained anuṣṭhāna → dhruva/sthira (Rohini, U.Phalguni, U.Ashadha, U.Bhadrapada) + Pushya + Shravana
    favorable_nakshatras: [4, 12, 21, 26, 8, 22, 7],
    favorable_varas: ['Jupiter', 'Moon'],
    avoid_nakshatras: [2, 6, 9, 10, 18, 19],
    karaka_graha: 'Jupiter',
    citation: 'Anuṣṭhāna/japa-ārambha — Muhurta Martanda anuṣṭhāna-prakaraṇa; dhruva/sthira nakshatras for permanence + Pushya.',
  },
}

/** Activity-fit annotation for one window (advisory; does not mutate the platform score). */
export function computeActivityFit(
  rule: ActivityRule,
  dayNakNum: number | null,
  windowStartUtc: string,
): { favorable_nakshatra: boolean; favorable_vara: boolean; avoid_nakshatra_hit: boolean; note: string; citation: string } {
  const varaLord = VARA_LORD[istWeekday(windowStartUtc)] ?? 'Sun'
  const favorable_nakshatra = dayNakNum != null && rule.favorable_nakshatras.includes(dayNakNum)
  const favorable_vara = rule.favorable_varas.includes(varaLord)
  const avoid_nakshatra_hit = dayNakNum != null && rule.avoid_nakshatras.includes(dayNakNum)
  const bits: string[] = []
  if (favorable_nakshatra) bits.push('favorable nakshatra')
  if (favorable_vara) bits.push(`favorable vāra (${varaLord})`)
  if (avoid_nakshatra_hit) bits.push('AVOID nakshatra (classical contraindication)')
  return {
    favorable_nakshatra, favorable_vara, avoid_nakshatra_hit,
    note: bits.length ? bits.join('; ') : 'no strong activity-specific nakshatra/vāra signal',
    citation: rule.citation,
  }
}

// ── Horā (planetary hour) — day-lord-first, Chaldean order ───────────────────────
// Chaldean order in which the hours advance: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon.
const HORA_CHALDEAN = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon'] as const
const BENEFIC_HORA = new Set(['Jupiter', 'Venus', 'Mercury', 'Moon'])
const IST_OFFSET_MS = (5 * 60 + 30) * 60 * 1000
export const HORA_SUNRISE_ASSUMPTION =
  'Equal-hour horā ladder anchored to a 06:00 IST sunrise proxy (precise sunrise from panchanga_daily is a documented follow-up — PARKED on the panchanga sunrise field). Classical horā: day-lord rules the first horā, subsequent horās follow the Chaldean order — Prasna Marga / Muhurta Chintamani horā-prakaraṇa.'

/** Convert a UTC instant to an explicit IST (+05:30) ISO string. */
export function toIstIso(utcIso: string): string {
  const t = new Date(utcIso).getTime()
  if (Number.isNaN(t)) return utcIso
  const ist = new Date(t + IST_OFFSET_MS)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${ist.getUTCFullYear()}-${pad(ist.getUTCMonth() + 1)}-${pad(ist.getUTCDate())}T` +
    `${pad(ist.getUTCHours())}:${pad(ist.getUTCMinutes())}:${pad(ist.getUTCSeconds())}+05:30`
}

/** IST weekday (0=Sunday) for a UTC instant. */
export function istWeekday(utcIso: string): number {
  const t = new Date(utcIso).getTime()
  if (Number.isNaN(t)) return 0
  return new Date(t + IST_OFFSET_MS).getUTCDay()
}

/**
 * Build a horā (planetary-hour) ladder for the first 24 horās of a window, anchored to a
 * 06:00-IST sunrise proxy. Each horā is 60 min; the day-lord rules horā 1, and horās advance
 * in Chaldean order. Optionally flags horās ruled by a specific graha (target/karaka).
 */
export function computeHoraLadder(windowStartUtc: string, highlightGraha?: string | null): HoraSlot[] {
  const wd = istWeekday(windowStartUtc)
  const dayLord = VARA_LORD[wd] ?? 'Sun'
  const startIdx = HORA_CHALDEAN.indexOf(dayLord as (typeof HORA_CHALDEAN)[number])
  // sunrise proxy: 06:00 IST on the window's IST date
  const t = new Date(windowStartUtc).getTime()
  const istMidUtc = Math.floor((t + IST_OFFSET_MS) / 86400000) * 86400000 - IST_OFFSET_MS
  const sunriseUtc = istMidUtc + 6 * 3600000
  const slots: HoraSlot[] = []
  for (let h = 0; h < 24; h++) {
    const lord = HORA_CHALDEAN[(startIdx + h) % 7] ?? 'Sun'
    if (highlightGraha && lord !== highlightGraha && !BENEFIC_HORA.has(lord)) continue
    const s = new Date(sunriseUtc + h * 3600000).toISOString()
    const e = new Date(sunriseUtc + (h + 1) * 3600000).toISOString()
    slots.push({ start_ist: toIstIso(s), end_ist: toIstIso(e), hora_lord: lord, benefic: BENEFIC_HORA.has(lord) })
  }
  return slots
}

// ── target_graha transit gate (EL-50 sub-item 3) — consumes β C5 sidereal service ──
/**
 * Provider that, given a graha and a UTC instant, returns its transit dignity/combustion/
 * retrogression. In production this is β's C5 sidereal ephemeris service. While C5 is DRAFT,
 * the default provider returns `pending_c5_service` (never a fabricated dignity). Tests inject
 * a deterministic stub to prove the flagging/demotion logic.
 */
export interface TargetGrahaTransitProvider {
  (graha: string, instantUtc: string): {
    combust: boolean | null
    debilitated: boolean | null
    retrograde: boolean | null
    transit_dignity: string | null
    available: boolean
  }
}

/** Default provider — C5 not yet frozen. Honest pending marker, no fabrication. */
export const c5PendingProvider: TargetGrahaTransitProvider = () => ({
  combust: null, debilitated: null, retrograde: null, transit_dignity: null, available: false,
})

export const TARGET_GRAHA_CITATION =
  'Combustion (astaṅgata), debilitation (nīca), and retrogression (vakra) of the target graha in transit are classical contraindications for a graha-tied election (gemstone/remedy timing) — BPHS grahabala; Muhurta Chintamani. Transit dignity sourced from β C5 sidereal ephemeris.'

export function computeTargetGrahaVerdict(
  graha: string,
  windowStartUtc: string,
  provider: TargetGrahaTransitProvider,
): TargetGrahaVerdict {
  const d = provider(graha, windowStartUtc)
  if (!d.available) {
    return {
      graha, status: 'pending_c5_service',
      combust: null, debilitated: null, retrograde: null, transit_dignity: null,
      note: 'β C5 sidereal ephemeris service is DRAFT — transit dignity of the target graha is not yet available; window ranked on panchanga/tāra only. NOT a clean bill for the target graha.',
      citation: TARGET_GRAHA_CITATION,
    }
  }
  const flagged = Boolean(d.combust || d.debilitated || d.retrograde)
  const reasons: string[] = []
  if (d.combust) reasons.push('combust (astaṅgata)')
  if (d.debilitated) reasons.push('debilitated (nīca)')
  if (d.retrograde) reasons.push('retrograde (vakra)')
  return {
    graha, status: flagged ? 'flagged' : 'ok',
    combust: d.combust, debilitated: d.debilitated, retrograde: d.retrograde,
    transit_dignity: d.transit_dignity,
    note: flagged
      ? `Target graha ${graha} is ${reasons.join(', ')} in transit — deprioritized for a ${graha}-tied election.`
      : `Target graha ${graha} is unafflicted in transit (${d.transit_dignity ?? 'dignity n/a'}).`,
    citation: TARGET_GRAHA_CITATION,
  }
}

/**
 * Re-rank windows so hard-flagged / disqualified windows can never silently hold the top rank.
 * Order: (1) non-flagged before flagged; (2) non-disqualified before disqualified;
 * (3) within a tier, higher score first. Stable, returns a new array.
 */
export function rerankWindows(windows: MuhurtaWindow[]): MuhurtaWindow[] {
  return [...windows].sort((a, b) => {
    const aDq = a.disqualified ? 1 : 0, bDq = b.disqualified ? 1 : 0
    if (aDq !== bDq) return aDq - bDq
    const aHf = a.hard_flag ? 1 : 0, bHf = b.hard_flag ? 1 : 0
    if (aHf !== bHf) return aHf - bHf
    return (b.score ?? 0) - (a.score ?? 0)
  })
}

// ── Tool description ───────────────────────────────────────────────────────────

export const MUHURTA_FINDER_DESCRIPTION =
  'Electional auspicious time-window finder (phala.muhurta / PH-4-4). ' +
  'INVERTS the Phala prediction engine: instead of "what will happen?", asks ' +
  '"WHEN is best to act for a given action_type?" ' +
  'For each 48-hour window in the requested date range (max 90 days), computes: ' +
  '  auspiciousness_score = panchanga_quality(40%) + dasha_quality(30%) ' +
  '                       + transit_quality(20%) + signal_activation(10%) ' +
  'Returns windows ranked by auspiciousness_score DESC. ' +
  'action_types: marriage | travel | business | medical | education | property | general. ' +
  'panchanga_quality: classical BPHS ch.46 muhurta rules — tithi, vara, nakshatra, yoga. ' +
  'dasha_quality: active Vimshottari MD/AD benefic quality for the chart. ' +
  'transit_quality: key planetary transits during the window. ' +
  'signal_activation: MSR v5.0 signal ensemble for the action_type. ' +
  'B.3 mandate: source_citation NON-NULL on every window. ' +
  'provenance_envelope present on every response. ' +
  'Education muhurta: Pushya nakshatra + Mercury/Thursday days most auspicious (BPHS ch.46 §vidya). ' +
  'Marriage muhurta: Rohini/Revati/Hasta + Monday/Thursday/Friday most auspicious. ' +
  'surgical: true — pure retrieval + pre-computed scoring, no LLM synthesis. ' +
  'BRAHMA-PH-4-4 | phala.muhurta contract.'

// ── Tool handler ───────────────────────────────────────────────────────────────

/**
 * muhurta_finder MCP tool handler.
 *
 * Delegates to /api/mcp/primitives/muhurta_finder on the platform service
 * (which maps to the query_muhurat retrieval tool via MCP_TO_RETRIEVAL_TOOL).
 *
 * Returns ranked auspicious windows with provenance_envelope.
 *
 * Error contract:
 *   - If date_range > 90 days, platform returns 422 validation error.
 *   - If chart_id has no pre-computed rows, falls back to on-the-fly scoring.
 *   - Invalid action_type returns 422 validation error.
 */
/**
 * Unwrap a surgical-primitive result into the raw MuhurtaFinderResult object.
 *
 * `getToolByName().retrieve()` (tool_name_bridge.ts) wraps EVERY capability
 * handler's return value into the generic legacy ToolBundle shape
 * (`{tool_bundle_id, results: [{content: "<JSON string>"}], ...}`) via
 * `capabilityResultToToolBundle` / `toToolBundleResults` — it never returns
 * the capability's raw object directly. `env.result` from
 * `callPlatformPrimitive()` is therefore that ToolBundle, not
 * `MuhurtaFinderResult`, so a direct cast (`env.result as MuhurtaFinderResult`)
 * always misses `.windows` and silently degrades to an empty array regardless
 * of what real data the underlying query_muhurat capability returned.
 *
 * This handles both shapes defensively: the ToolBundle (`results[0].content`,
 * either a JSON string or an already-parsed object depending on bridge
 * version) and a hypothetical direct-object result, so it keeps working if
 * the bridge's wrapping behavior ever changes.
 */
function unwrapMuhurtaFinderResult(raw: unknown): MuhurtaFinderResult | undefined {
  if (!raw || typeof raw !== 'object') return undefined

  // Already the raw shape (has `windows` directly) — no ToolBundle wrapper.
  if ('windows' in (raw as Record<string, unknown>)) {
    return raw as MuhurtaFinderResult
  }

  // ToolBundle shape: { results: [{ content: string | object }], ... }
  const bundle = raw as { results?: Array<{ content?: unknown }> }
  if (Array.isArray(bundle.results) && bundle.results.length > 0) {
    const content = bundle.results[0]?.content
    if (typeof content === 'string') {
      try {
        const parsed: unknown = JSON.parse(content)
        if (parsed && typeof parsed === 'object') return parsed as MuhurtaFinderResult
      } catch {
        // Not JSON — fall through to undefined below.
      }
    } else if (content && typeof content === 'object') {
      return content as MuhurtaFinderResult
    }
  }

  return undefined
}

/** Options for the Lane F enrichment pass (transitProvider injectable for tests). */
export interface LaneFEnrichOptions {
  transitProvider?: TargetGrahaTransitProvider
}

/**
 * Lane F (EL-50 / EL-53) enrichment pass over the platform's returned windows.
 *
 * Pure and deterministic — takes the raw windows + the finder input and returns the
 * enriched, re-ranked windows plus the `lane_f` envelope and (when requested) the
 * `prediction_filing`. Exported so the named regressions can drive it directly without
 * the platform round-trip.
 *
 * Guarantees:
 *   - an adverse tārā (Vipat/Pratyak/Vadha for the native's Moon) HARD-FLAGS and DEMOTES
 *     the window → it can never silently hold rank #1 (EL-50 Vadha-tārā regression);
 *   - a combust/debilitated/retrograde target graha flags+demotes every affected window
 *     (EL-50 Venus-debilitated regression) — or emits a pending-C5 marker, never fabricated;
 *   - every window gains explicit IST timestamps + a horā ladder (sub-day resolution).
 */
export function enrichWindowsLaneF(
  rawWindows: MuhurtaWindow[],
  input: MuhurtaFinderInput,
  opts: LaneFEnrichOptions = {},
): { windows: MuhurtaWindow[]; lane_f: NonNullable<MuhurtaFinderResult['lane_f']>; prediction_filing?: PredictionFiling } {
  const rule = ACTIVITY_RULES[input.action_type as ActionType] ?? ACTIVITY_RULES.general
  const janmaNum = nakshatraNumber(input.native_janma_nakshatra)
  const provider = opts.transitProvider ?? c5PendingProvider

  // The graha whose horā to highlight: explicit target_graha, else the activity karaka.
  const highlightGraha = input.target_graha ?? rule.karaka_graha

  let anyPendingC5 = false

  const enriched: MuhurtaWindow[] = rawWindows.map((w) => {
    const out: MuhurtaWindow = { ...w }
    const penalties: string[] = []
    const dayNak = nakshatraNumber(w.factors?.panchanga_details?.moon_nakshatra)

    // (d) IST anchoring + horā ladder — always applied.
    out.start_ist = toIstIso(w.start)
    out.end_ist = toIstIso(w.end)
    out.hora_ladder = computeHoraLadder(w.start, highlightGraha)

    // (a) activity-fit annotation.
    out.activity_fit = computeActivityFit(rule, dayNak, w.start)
    if (out.activity_fit.avoid_nakshatra_hit) {
      out.hard_flag = true
      penalties.push(`activity contraindication: ${w.factors?.panchanga_details?.moon_nakshatra} is an avoid-nakshatra for ${input.action_type}`)
    }

    // (b) tāra bala — adverse tārā disqualifies/hard-flags.
    if (janmaNum != null && dayNak != null) {
      const tb = computeTaraBala(janmaNum, dayNak)
      out.tara_bala = {
        janma_nakshatra: nakName(janmaNum),
        day_nakshatra: nakName(dayNak),
        count_from_janma: tb.count_from_janma,
        tara_index: tb.tara_index,
        tara_name: tb.tara_name,
        favorable: tb.favorable,
        adverse: tb.adverse,
        severity: tb.severity,
        citation: TARA_CITATION,
      }
      if (tb.adverse) {
        out.hard_flag = true
        penalties.push(`adverse tārā (${tb.tara_name}) from janma nakshatra ${nakName(janmaNum)}`)
        if (tb.severity === 'severe') out.disqualified = true   // Vadha/Naidhana
      }
    }

    // (c) target-graha transit gate.
    if (input.target_graha) {
      const tg = computeTargetGrahaVerdict(input.target_graha, w.start, provider)
      out.target_graha_check = tg
      if (tg.status === 'flagged') {
        out.hard_flag = true
        out.disqualified = true
        penalties.push(tg.note)
      } else if (tg.status === 'pending_c5_service') {
        anyPendingC5 = true
      }
    }

    if (penalties.length) out.rank_penalty_reason = penalties
    return out
  })

  const ranked = rerankWindows(enriched).slice(0, input.limit)

  const lane_f: NonNullable<MuhurtaFinderResult['lane_f']> = {
    activity_rule_set: { ...rule, action_type: input.action_type, base_action_type: rule.base_action_type },
    tara_bala_status: janmaNum != null ? 'applied' : 'unavailable_no_janma_nakshatra',
    hora_status: 'applied',
    hora_sunrise_assumption: HORA_SUNRISE_ASSUMPTION,
    ranking_note: 'Windows re-ranked so any hard-flagged (adverse tārā / flagged target graha) or disqualified window is demoted below clean windows — no adverse window can silently hold rank #1.',
  }
  if (janmaNum == null) {
    lane_f.tara_bala_note = input.native_janma_nakshatra
      ? `janma nakshatra "${input.native_janma_nakshatra}" not recognized — tāra bala not applied (no fabrication)`
      : 'native_janma_nakshatra not supplied — tāra bala not applied (pass it to enable the adverse-tārā disqualification)'
  }
  if (input.target_graha) {
    lane_f.target_graha_status = anyPendingC5 ? 'pending_c5_service' : 'applied'
    if (anyPendingC5) {
      lane_f.target_graha_note = `target_graha=${input.target_graha} requested, but β C5 sidereal ephemeris service is DRAFT — transit dignity is pending; windows carry a pending-C5 marker, not a clean bill. When C5 freezes, inject the C5-backed provider.`
    }
  } else {
    lane_f.target_graha_status = 'not_requested'
  }

  // (EL-53) prediction filing for the top elected window.
  let prediction_filing: PredictionFiling | undefined
  const top = ranked[0]
  if (input.file_as_prediction && top) {
    const star = Math.max(1, Math.min(5, Math.round(top.score * 5)))
    prediction_filing = {
      claim: `Acting on the ${input.action_type} election in the window ${top.start_ist ?? top.start} → ${top.end_ist ?? top.end} yields an auspicious outcome (predicted quality ${star}/5, score ${top.score.toFixed(3)}).`,
      event_class: rule.event_class,
      claim_shape: 'window',
      window_start: top.start,
      window_end: top.end,
      confidence: top.score,
      falsifier: `The elected ${input.action_type} action, taken in this window, is followed by a materially adverse or obstructed outcome (or the native reports the timing felt inauspicious) within the natural review horizon of the activity.`,
      generator_class: 'engine',
      source_citation: `phala.muhurta PH-4-4 auspiciousness score + Lane F tāra/activity/target-graha gate. ${rule.citation}`,
      scoring_factors: top.factors,
      elected_window: { start: top.start, end: top.end, start_ist: top.start_ist, end_ist: top.end_ist },
      predicted_quality: { score: top.score, star_rating: star },
      close_via: {
        tool: 'mimamsa_outcome_record',
        verdict_vocabulary: ['confirmed', 'partial', 'denied'],
        note: 'Close this election by calling mimamsa_outcome_record with {chart_id, prediction_id (from the filed row), outcome, verdict}. confirmed = timing proved auspicious; denied = outcome adverse (falsifier met); partial = mixed.',
      },
      persistence: 'payload_only',
      persistence_note: 'γ.F scope covers the tool surface; the prospective-ledger DB write lives in platform/src/lib/lel/prospective_ledger.ts (fileProspectivePrediction) — OUT of γ.F carve-out. This payload is shape-matched to that function\'s input so α can persist it in one step. PARKED-HONEST: blocked-on-alpha for the actual write.',
    }
  }

  return { windows: ranked, lane_f, prediction_filing }
}

export async function handleMuhurtaFinder(
  input: MuhurtaFinderInput,
  principal: Principal
): Promise<unknown> {
  const authorized = await remoteAuthorize(principal, input.chart_id)
  if (!authorized) {
    return {
      content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }],
      isError: true,
    }
  }

  // Lane F (EL-50): new spiritual/remedial classes map to a coarse base action_type the
  // Python muhurta primitive already knows (their activity-specific classical rules are
  // layered back in by enrichWindowsLaneF). Original action_type preserved for annotation.
  const baseActionType = (ACTIVITY_RULES[input.action_type as ActionType] ?? ACTIVITY_RULES.general).base_action_type
  const params: Record<string, unknown> = {
    chart_id: input.chart_id,
    action_type: baseActionType,
    date_range: input.date_range,
    // ask the platform for a wider candidate set so post-rank demotion still fills `limit`
    limit: Math.min(45, input.limit * 2),
  }
  if (input.min_score !== undefined) {
    params['min_score'] = input.min_score
  }

  const result = await callPlatformPrimitive('muhurta_finder', params, principal)
  const env = result.envelope
  if (!env.ok) return errorOutput(env.error?.message ?? 'muhurta_finder platform call failed', { chart_id: input.chart_id, trace_id: env.trace_id })

  const resultData = unwrapMuhurtaFinderResult(env.result)
  const windows: MuhurtaWindow[] = resultData?.windows ?? []

  // Assert B.3 grounding contract: surface any citation-null windows as a warning
  const uncited = windows.filter((w) => !w.source_citation)
  if (uncited.length > 0) {
    console.warn(
      `[PH-4-4] muhurta_finder: ${uncited.length} windows have null source_citation — ` +
      `contract violation (B.3 mandate)`
    )
  }

  // Assert score invariant
  const outOfRange = windows.filter((w) => w.score < 0.0 || w.score > 1.0)
  if (outOfRange.length > 0) {
    console.warn(
      `[PH-4-4] muhurta_finder: ${outOfRange.length} windows have score outside [0.0, 1.0]`
    )
  }

  const provenanceEnvelope: MuhurtaProvenanceEnvelope = resultData?.provenance_envelope ?? {
    source: 'phala.muhurta',
    asset: 'PH-4-4',
    algorithm: 'panchanga_quality(40%) + dasha_quality(30%) + transit_quality(20%) + signal_activation(10%)',
    min_score_applied: input.min_score ?? 0.0,
    chart_id: input.chart_id,
    action_type: input.action_type,
    queried_at: new Date().toISOString(),
    l1_ground_truth: 'FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD (2026-2043); panchanga_daily; MSR v5.0 SIG.*',
    b3_citation_compliant: uncited.length === 0,
  }

  // ── Lane F (EL-50 / EL-53) enrichment: tāra bala, activity fit, target-graha
  // gate, horā/IST resolution, re-rank, and optional prediction filing. ──
  const { windows: enrichedWindows, lane_f, prediction_filing } = enrichWindowsLaneF(windows, input)

  const finalResult: MuhurtaFinderResult = {
    ok: true,
    chart_id: input.chart_id,
    action_type: input.action_type,
    query_window: input.date_range,
    windows: enrichedWindows,
    window_count: enrichedWindows.length,
    provenance_envelope: provenanceEnvelope,
    lane_f,
  }
  if (prediction_filing) finalResult.prediction_filing = prediction_filing
  // R5.1 C3: propagate the honest empty-with-reason signal for out-of-window
  // date ranges instead of silently dropping it (never fabricate windows).
  if (resultData?.empty_reason) {
    finalResult.empty_reason = resultData.empty_reason
  }

  return dualOutput(finalResult)
}

// ── MCP server registration helper ────────────────────────────────────────────

/**
 * Register the muhurta_finder tool on an McpServer instance.
 *
 * Usage in server.ts:
 *   import { registerMuhurtaFinder } from './tools/muhurta_finder.js'
 *   registerMuhurtaFinder(server, getPrincipal)
 *
 * The tool is surgical (pure retrieval + pre-computed scoring) and appropriate
 * for all principal tiers. Maps to query_muhurat via MCP_TO_RETRIEVAL_TOOL.
 *
 * Contract assertions:
 *   - source_citation non-null on all returned windows (B.3 mandate)
 *   - provenance_envelope present in every response
 *   - 0 <= score <= 1 on every window
 *   - action_type ∈ {marriage, travel, business, medical, education, property, general}
 *
 * BRAHMA-PH-4-4
 */
export function registerMuhurtaFinder(
  server: {
    tool: (
      name: string,
      description: string,
      schema: Record<string, unknown>,
      handler: (args: unknown) => Promise<unknown>
    ) => void
  },
  getPrincipal: () => Principal
): void {
  server.tool(
    'muhurta_finder',
    MUHURTA_FINDER_DESCRIPTION,
    {
      chart_id: z
        .string()
        .uuid()
        .describe(
          'UUID of the chart. Must be a valid chart UUID from the charts table.'
        ),
      action_type: z
        .enum([
          'marriage', 'travel', 'business', 'medical', 'education', 'property', 'general',
          'spiritual_initiation', 'remedial_ritual', 'japa_start',
        ])
        .describe(
          'Action type: marriage | travel | business | medical | education | property | general | ' +
          'spiritual_initiation | remedial_ritual | japa_start. ' +
          'education = Pushya/Mercury/Thursday auspicious; marriage = Rohini/Guruvara; ' +
          'business = Rohini/Hasta/Budhavara; travel = Ashwini/Mrigashira; ' +
          'spiritual_initiation = mantra dīkṣā (Pushya/Anuradha, Guru-vāra); ' +
          'remedial_ritual = homa/dāna/śānti; japa_start = sustained anuṣṭhāna (dhruva nakshatras).'
        ),
      date_range: z
        .object({
          start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
          end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
        })
        .describe(
          'Search range (YYYY-MM-DD). Max 90 days. ' +
          '48-hour blocks returned. Example: {"start":"2026-06-04","end":"2026-09-01"}.'
        ),
      min_score: z
        .number()
        .min(0.0)
        .max(1.0)
        .optional()
        .describe(
          'Minimum auspiciousness_score [0.0–1.0]. Default 0.0. ' +
          'High ≥ 0.70; Medium 0.50–0.69.'
        ),
      limit: z
        .number()
        .int()
        .min(1)
        .max(45)
        .default(20)
        .describe('Max windows to return (ranked by score DESC). Default 20.'),
      native_janma_nakshatra: z
        .string()
        .optional()
        .describe(
          "Native's janma (Moon) nakshatra, e.g. \"Purva Bhadrapada\". Joins tāra-bala: an adverse " +
          'tārā (Vipat/Pratyak/Vadha) hard-flags & demotes the window so it never silently ranks #1. ' +
          'Omit → tāra-bala reported unavailable (never fabricated).'
        ),
      target_graha: z
        .enum(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'])
        .optional()
        .describe(
          'For a graha-tied election (e.g. gemstone/remedy timing). Flags/deprioritizes windows where ' +
          'the target graha is combust/debilitated/retrograde in transit (via β C5; pending-marker while DRAFT).'
        ),
      file_as_prediction: z
        .boolean()
        .optional()
        .describe(
          'When true, adds a prediction_filing block for the top elected window (prospective-ledger ' +
          'shaped, closable via mimamsa_outcome_record).'
        ),
    },
    async (args: unknown) => {
      const parsed = MuhurtaFinderInputSchema.parse(args)
      return handleMuhurtaFinder(parsed, getPrincipal())
    }
  )
}
