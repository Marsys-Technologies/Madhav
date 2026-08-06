/**
 * kala_janma_micro_rules.ts — ṢAḌ-DARŚANA W3, Lane w3-muh, Item 14.
 * ==========================================================================
 * Janma-anchored election micro-rules for `kala_elect_get`.
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v1_0.md §3.2:
 *   "Personal star overlay: tārā-bala from janma-nakṣatra (vadha/vipat/pratyak = veto),
 *    chandra-bala (transit Moon house from natal Moon), and BUILD: janma-anchored
 *    micro-rules — janma-tithi/vara/nakṣatra returns as personally-potent days."
 *
 * §N.5 IMPORTANT: This module contains NO new astrological computation. The tāra
 * formula and the TARA_NAMES cycle are REFERENCED from:
 *   - `panchang_engine/tara_bala.py`'s `_TARA_QUALITY` table (Python sidecar)
 *   - `muhurta_finder.ts`'s `computeTaraBala` helper (same codebase)
 *   - `kala_sky_pattern.ts`'s `TARA_CYCLE` export
 * The formula `count = ((current - janma + 27) % 27) + 1; index = ((count-1) % 9) + 1`
 * is stated once in those sources; this file MIRRORS that formula, not re-derives it.
 *
 * Accuracy anchors verified against panchang_engine/tara_bala.py for native 482012f1
 * (janma nakshatra = Purva Bhadrapada, id=25):
 *   Purva Bhadrapada → Purva Bhadrapada: count=1, Janma (neutral)
 *   Purva Bhadrapada → Ashwini (id=1): count=4, Kshema (auspicious)
 *   Purva Bhadrapada → Uttara Phalguni (id=12): count=15, tara_index=6, Sadhaka (auspicious)
 *   Purva Bhadrapada → Ardra (id=6): count=9, Ati-Mitra (auspicious)
 *   Purva Bhadrapada → Rohini (id=4): count=7, Vadha (severe veto)
 *
 * §N.8: every coverage claim in this module has a real detector behind it. The
 * `hard_veto` field is true ONLY when `severity === 'severe'` (Vadha), never when
 * the result is unavailable or null.
 */

// ── Tārā cycle constants (sourced from panchang_engine/tara_bala.py §_TARA_QUALITY) ──
// Source: Muhurta Chintamani §Tara Bala; Brihat Parashara Hora Shastra §Tara.

/** The 9 tārā names in cycle order (1-indexed: position 1 = Janma, position 9 = Ati-Mitra).
 *  Source: panchang_engine/tara_bala.py `_TARA_QUALITY` keys in order. */
export const TARA_NAMES = [
  'Janma',      // 1 — neutral
  'Sampat',     // 2 — auspicious
  'Vipat',      // 3 — inauspicious (caution)
  'Kshema',     // 4 — auspicious
  'Pratyari',   // 5 — inauspicious (caution)
  'Sadhaka',    // 6 — auspicious
  'Vadha',      // 7 — inauspicious (severe)
  'Mitra',      // 8 — auspicious
  'Ati-Mitra',  // 9 — auspicious
] as const

export type TaraName = (typeof TARA_NAMES)[number]

/** Adverse tārā indices (1-indexed): Vipat(3), Pratyari(5), Vadha(7).
 *  Source: Muhurta Chintamani §Tara Bala; BPHS §Tara. */
export const ADVERSE_TARA_INDICES: ReadonlySet<number> = new Set([3, 5, 7])

/** Severe tārā indices (1-indexed): only Vadha(7) disqualifies an election window.
 *  Vipat and Pratyari are caution but not election-disqualifiers.
 *  Source: Muhurta Chintamani §Tara Bala (vadha-tārā = election veto). */
export const SEVERE_TARA_INDICES: ReadonlySet<number> = new Set([7])

// ── TaraMicroRule: the result of applying tārā to one election window ──────────────

/** The result of computing tārā bala for an election window nakshatra relative to
 *  the native's janma nakshatra. Pure — no I/O. */
export interface TaraMicroRule {
  /** Inclusive count from janma nakshatra (1..27). count=1 means the same as janma. */
  count_from_janma: number
  /** Position within the 9-fold cycle (1..9). */
  tara_index: number
  /** Classical tārā name for this position. */
  tara_name: TaraName
  /** True for Sampat(2), Kshema(4), Sadhaka(6), Mitra(8), Ati-Mitra(9). */
  favorable: boolean
  /** True for Vipat(3), Pratyari(5), Vadha(7). */
  adverse: boolean
  /** 'severe' = Vadha (election disqualifier); 'caution' = Vipat/Pratyari; 'none' otherwise. */
  severity: 'none' | 'caution' | 'severe'
  /** Classical citation for this rule. */
  citation: string
}

// ── JanmaMicroRuleContext: the fixed native anchor ─────────────────────────────────

/** The native's fixed janma anchor. Used to compute personal resonance flags per window.
 *  Values sourced from the chart's L1 facts (never fabricated). */
export interface JanmaMicroRuleContext {
  /** Janma nakshatra id, 1-indexed (1=Ashwini, 27=Revati). */
  janma_nakshatra_id: number
  /** Janma tithi number (1=Shukla Pratipada, 15=Purnima, 16=Krishna Pratipada, 30=Amavasya). */
  janma_tithi_num: number
  /** Janma vara (weekday) index, 0=Sunday, 6=Saturday. */
  janma_vara_index: number
}

// ── JanmaMicroRules: the composite output per election window ─────────────────────

/** The janma-anchored micro-rule result for one election window. Attached to each
 *  `KalaElectCandidate` as `janma_micro_rules` when a janma context is available. */
export interface JanmaMicroRules {
  /** Tārā bala of this window's nakshatra relative to native's janma nakshatra.
   *  Null when `window_nakshatra_id` was not supplied. */
  tara_micro_rule: TaraMicroRule | null
  /** True when this window's nakshatra is the same as the janma nakshatra.
   *  Null when `window_nakshatra_id` was not supplied. */
  janma_nakshatra_resonance: boolean | null
  /** True when this window's tithi matches the native's janma tithi.
   *  Null when `window_tithi_num` was not supplied. */
  janma_tithi_resonance: boolean | null
  /** True when this window's vara (weekday) matches the native's janma vara.
   *  Null when `window_vara_index` was not supplied. */
  janma_vara_resonance: boolean | null
  /** Count of the non-null resonance flags that are true (0..3). */
  resonance_count: number
  /** True when tara_micro_rule is non-null AND severity === 'severe' (Vadha-tārā election veto).
   *  This is the window-level disqualification signal; elect.ts gates the candidate on it.
   *  Never true when tara_micro_rule is null. */
  hard_veto: boolean
  /** The human-readable reason for hard_veto. Null when hard_veto is false. */
  hard_veto_reason: string | null
  /** Classical citation string. */
  citation: string
}

// ── JanmaMicroWindowInput: the per-window inputs ──────────────────────────────────

/** The panchanga data for one election window, used by computeJanmaMicroRules.
 *  Any field can be null when not available — the result degrades gracefully. */
export interface JanmaMicroWindowInput {
  /** 1-indexed nakshatra id for the Moon's position at this window's start.
   *  Null when the window's panchanga does not carry a Moon nakshatra. */
  window_nakshatra_id: number | null
  /** Tithi number at this window's start (1..30). Null when unavailable. */
  window_tithi_num: number | null
  /** Vara (weekday) index at this window's start (0=Sunday). Null when unavailable. */
  window_vara_index: number | null
}

// ── Tithi name → number lookup ────────────────────────────────────────────────────
//
// Source: the 30-tithi system (15 Shukla paksha + 15 Krishna paksha).
// Classical reference: BPHS ch. Panchanga + Muhurta Chintamani §Tithi.
// Used to resolve `tithi_name` from panchanga_details (e.g. "Shukla Tritiya" → 3).

/** Map of normalized tithi name fragments → tithi number (1..30).
 *  Shukla tithis 1–15; Krishna tithis 16–30.
 *  Uses lowercase, no-spaces matching so "Shukla Tritiya" / "shukla_tritiya" both resolve. */
const TITHI_NAME_MAP: Record<string, number> = {
  // Shukla paksha (1–15)
  'shuklapratipad': 1, 'shukladvitiya': 2, 'shuklatritiya': 3, 'shuklachaturthi': 4,
  'shuklapanchami': 5, 'shuklashtami': 8, 'shuklanawami': 9, 'shukladashami': 10,
  'shuklaekadashi': 11, 'shukladwadashi': 12, 'shuklat rayodashi': 13, 'shuklatrayodashi': 13,
  'shuklechaturdashi': 14, 'shukla chaturdashi': 14, 'purnima': 15, 'poornima': 15,
  'shukla panchami': 5, 'shukla shashthi': 6, 'shukla saptami': 7,
  // Krishna paksha (16–30, continued from 15)
  'krishnapratipad': 16, 'krishnadvitiya': 17, 'krishnatritiya': 18,
  'krishnachaturthi': 19, 'krishnapanchami': 20, 'krishnashashthi': 21,
  'krishnasaptami': 22, 'krishnashtami': 23, 'krishnanavami': 24, 'krishnadashami': 25,
  'krishnaekadashi': 26, 'krishnadwadashi': 27, 'krishnatrayodashi': 28,
  'krishnachaturdashi': 29, 'amavasya': 30,
}

/**
 * Resolve a tithi name string (from panchanga_details.tithi_name) to a tithi number (1..30).
 * Returns null if the name cannot be resolved.
 * Source: the 30-tithi cycle — BPHS §Panchanga; Muhurta Chintamani §Tithi.
 */
export function tithiNumFromName(name: string | null | undefined): number | null {
  if (!name) return null
  // Normalize: lowercase, strip spaces/underscores/hyphens, common spelling variants
  const norm = name.toLowerCase().replace(/[\s_\-]+/g, '')
    .replace(/aa/g, 'a').replace(/sh/g, 's').replace(/ph/g, 'f')
    .replace('shukla', 'sukla').replace('krishna', 'krsna')
  // Try direct normalized map first (re-normalize the map keys)
  for (const [k, v] of Object.entries(TITHI_NAME_MAP)) {
    const kNorm = k.toLowerCase().replace(/[\s_\-]+/g, '')
      .replace(/aa/g, 'a').replace(/sh/g, 's').replace(/ph/g, 'f')
      .replace('shukla', 'sukla').replace('krishna', 'krsna')
    if (kNorm === norm) return v
  }
  // Fallback: detect paksha + tithi from the name fragments
  const isShukla = /sukla|shukla|bright|waxing/.test(name.toLowerCase())
  const isKrishna = /krsna|krishna|dark|waning/.test(name.toLowerCase())
  const tithiNums: Record<string, number> = {
    pratipad: 1, pratipat: 1, pratipada: 1,
    dvitiya: 2, dwitiya: 2, dwidiya: 2,
    tritiya: 3, trutiya: 3,
    chaturthi: 4, chathurthi: 4,
    panchami: 5, panchami5: 5,
    shashthi: 6, shashti: 6, shashthi6: 6,
    saptami: 7,
    ashtami: 8, shtami: 8,
    navami: 9, nawami: 9,
    dashami: 10, dasami: 10,
    ekadashi: 11, ekadasi: 11,
    dwadashi: 12, dwadassi: 12,
    trayodashi: 13, tryodashi: 13,
    chaturdashi: 14,
    purnima: 15, poornima: 15, pournami: 15,
    amavasya: 30, amavas: 30, new_moon: 30,
  }
  for (const [fragment, posInPaksha] of Object.entries(tithiNums)) {
    if (name.toLowerCase().includes(fragment)) {
      if (posInPaksha === 30) return 30  // amavasya always 30
      if (posInPaksha === 15 && !isKrishna) return 15  // purnima
      if (isKrishna && posInPaksha < 15) return 15 + posInPaksha
      if (isShukla || (!isKrishna && posInPaksha < 15)) return posInPaksha
    }
  }
  return null
}

/**
 * Resolve a vara lord name (e.g. "Sun", "Moon", ...) to a weekday index (0=Sunday, 6=Saturday).
 * Returns null if unrecognised.
 * Source: VARA_LORD from muhurta_finder.ts (Sun/Mon/Tue/Wed/Thu/Fri/Sat = 0..6).
 */
export function varaIndexFromLord(lord: string | null | undefined): number | null {
  if (!lord) return null
  const VARA_LORDS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
  const idx = VARA_LORDS.findIndex((v) => v.toLowerCase() === lord.toLowerCase())
  return idx === -1 ? null : idx
}

// ── Core pure functions ────────────────────────────────────────────────────────────

const TARA_CITATION =
  'Nava Tara Chakra — Muhurta Chintamani §Tara Bala; Brihat Parashara Hora Shastra §Tara; ' +
  'panchang_engine/tara_bala.py `_TARA_QUALITY` (formula: count=((current-janma+27)%27)+1, ' +
  'tara_index=((count-1)%9)+1).'

const MICRO_RULES_CITATION =
  'Janma-anchored election micro-rules — KALA_SIX_VIEWS_DESIGN_v1_0.md §3.2 (personal star ' +
  'overlay: tārā-bala from janma-nakṣatra + janma-tithi/vara/nakṣatra resonance as ' +
  'personally-potent election anchors).'

/**
 * Compute the tārā bala of `currentNakshatraId` relative to `janmaNakshatraId`.
 * Pure function; no I/O; throws RangeError for ids outside 1..27.
 *
 * Formula: count=((current - janma + 27) % 27) + 1; tara_index=((count-1) % 9) + 1.
 * Source: panchang_engine/tara_bala.py `compute_tara_position` + `get_tara_detail`.
 */
export function computeTaraMicroRule(
  janmaNakshatraId: number,
  currentNakshatraId: number,
): TaraMicroRule {
  if (janmaNakshatraId < 1 || janmaNakshatraId > 27) {
    throw new RangeError(`janmaNakshatraId must be 1..27, got ${janmaNakshatraId}`)
  }
  if (currentNakshatraId < 1 || currentNakshatraId > 27) {
    throw new RangeError(`currentNakshatraId must be 1..27, got ${currentNakshatraId}`)
  }

  const count = ((currentNakshatraId - janmaNakshatraId + 27) % 27) + 1  // 1..27
  const tara_index = ((count - 1) % 9) + 1                                 // 1..9
  const tara_name = TARA_NAMES[tara_index - 1]!
  const adverse = ADVERSE_TARA_INDICES.has(tara_index)
  const severity: 'none' | 'caution' | 'severe' =
    SEVERE_TARA_INDICES.has(tara_index) ? 'severe' : adverse ? 'caution' : 'none'
  // Favorable: Sampat(2), Kshema(4), Sadhaka(6), Mitra(8), Ati-Mitra(9).
  // Janma(1) and neutral positions are not classified as "favorable" (they are neutral).
  const favorable_indices = new Set([2, 4, 6, 8, 9])
  const favorable = favorable_indices.has(tara_index)

  return { count_from_janma: count, tara_index, tara_name, favorable, adverse, severity, citation: TARA_CITATION }
}

/**
 * Compute the composite janma micro-rules for one election window.
 * Pure; no I/O; never throws (degrades gracefully on null inputs).
 *
 * Called by elect.ts for each candidate window when a janma context is available.
 */
export function computeJanmaMicroRules(
  context: JanmaMicroRuleContext,
  window: JanmaMicroWindowInput,
): JanmaMicroRules {
  // ── Tārā bala ───────────────────────────────────────────────────────────────
  let tara_micro_rule: TaraMicroRule | null = null
  if (window.window_nakshatra_id !== null) {
    tara_micro_rule = computeTaraMicroRule(context.janma_nakshatra_id, window.window_nakshatra_id)
  }

  // ── Janma nakshatra resonance ────────────────────────────────────────────────
  const janma_nakshatra_resonance: boolean | null =
    window.window_nakshatra_id !== null
      ? window.window_nakshatra_id === context.janma_nakshatra_id
      : null

  // ── Janma tithi resonance ────────────────────────────────────────────────────
  const janma_tithi_resonance: boolean | null =
    window.window_tithi_num !== null
      ? window.window_tithi_num === context.janma_tithi_num
      : null

  // ── Janma vara resonance ──────────────────────────────────────────────────────
  const janma_vara_resonance: boolean | null =
    window.window_vara_index !== null
      ? window.window_vara_index === context.janma_vara_index
      : null

  // ── Resonance count (non-null truths only) ────────────────────────────────────
  const resonance_count =
    (janma_nakshatra_resonance === true ? 1 : 0) +
    (janma_tithi_resonance === true ? 1 : 0) +
    (janma_vara_resonance === true ? 1 : 0)

  // ── Hard veto (Vadha-tārā election disqualifier) ──────────────────────────────
  // §N.8: this signal is true ONLY when tara_micro_rule is non-null AND severity=severe.
  // Never fabricated when the nakshatra is unavailable.
  const hard_veto = tara_micro_rule !== null && tara_micro_rule.severity === 'severe'
  const hard_veto_reason = hard_veto
    ? `${tara_micro_rule!.tara_name}-tārā (position ${tara_micro_rule!.tara_index}) is a severe veto for this election window — the native's janma nakshatra is ${context.janma_nakshatra_id} positions away and lands on the classical election-disqualifying star. Source: Muhurta Chintamani §Tara Bala.`
    : null

  return {
    tara_micro_rule,
    janma_nakshatra_resonance,
    janma_tithi_resonance,
    janma_vara_resonance,
    resonance_count,
    hard_veto,
    hard_veto_reason,
    citation: MICRO_RULES_CITATION,
  }
}

/**
 * Guard wrapper: returns null when context is null/undefined (no janma anchor available).
 * Never fabricates a result. Called by elect.ts before building each candidate.
 */
export function applyJanmaMicroRulesOrNull(
  context: JanmaMicroRuleContext | null | undefined,
  window: JanmaMicroWindowInput,
): JanmaMicroRules | null {
  if (context == null) return null
  return computeJanmaMicroRules(context, window)
}
