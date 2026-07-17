/**
 * errors_that_teach.ts — D-2 Lane V-3, CR-7 CLASS (BIND_D-2.md §F1.7 ledger row 24).
 *
 * design-§6 capability: a malformed / vocabulary-mismatched call does not just say "no results" —
 * it returns the CORRECTED CALL the caller should have made. The original CR-7 specimen is CLOSED;
 * this builds the reusable CLASS. Two mechanisms:
 *
 *  (1) buildTeachingError — a structured error carrying a concrete `corrected_call` (tool + params)
 *      so a consumer can retry mechanically.
 *  (2) reconcileVocabulary — for a facet whose value must be one of a stored controlled vocabulary
 *      (the ref_yogas_get domain trap, §B.5: domain=wealth returns 0 rows because the stored
 *      `category` vocabulary is raja/dhana/aristha/pancha_mahapurusha/sannyasa/other), maps the
 *      caller's near-miss to the closest stored term and emits the corrected call. Pure + exported
 *      so tests drive it against the real vocabulary (anti-vacuous §F1.7).
 */

export type CorrectedCall = { tool: string; params: Record<string, unknown> }

export type TeachingError = {
  ok: false
  error: string
  tool: string
  corrected_call: CorrectedCall | null
  hint: string
  vocabulary?: Record<string, readonly string[]>
}

export function buildTeachingError(
  tool: string,
  error: string,
  correctedParams: Record<string, unknown> | null,
  hint: string,
  vocabulary?: Record<string, readonly string[]>,
): TeachingError {
  return {
    ok: false,
    error,
    tool,
    corrected_call: correctedParams ? { tool, params: correctedParams } : null,
    hint,
    ...(vocabulary ? { vocabulary } : {}),
  }
}

/** Cheap edit-distance-free similarity: shared-substring + prefix affinity, good enough to route a
 *  near-miss facet value to its stored twin without a fuzzy-match dependency. */
function affinity(a: string, b: string): number {
  const x = a.toLowerCase(), y = b.toLowerCase()
  if (x === y) return 1
  if (y.includes(x) || x.includes(y)) return 0.9
  // token overlap (e.g. "money" vs "dhana" won't overlap, but "raj yoga" vs "raja" will)
  const xt = new Set(x.split(/[^a-z]+/).filter(Boolean))
  const yt = new Set(y.split(/[^a-z]+/).filter(Boolean))
  let shared = 0
  for (const t of xt) if (yt.has(t)) shared++
  const denom = Math.max(xt.size, yt.size, 1)
  let score = shared / denom
  // small prefix bonus
  if (x.length >= 3 && y.startsWith(x.slice(0, 3))) score += 0.3
  return Math.min(score, 0.89)
}

export type VocabularyReconciliation = {
  matched: boolean
  stored_value: string | null // the closest stored term, if a confident match
  suggestions: string[]       // ranked stored terms
}

/**
 * Reconcile a caller-supplied facet value against a stored controlled vocabulary.
 * `synonyms` maps common English/near-miss terms → the stored canonical term.
 */
export function reconcileVocabulary(
  value: string,
  vocabulary: readonly string[],
  synonyms: Record<string, string> = {},
): VocabularyReconciliation {
  const v = value.trim().toLowerCase()
  // exact stored hit
  const exact = vocabulary.find((t) => t.toLowerCase() === v)
  if (exact) return { matched: true, stored_value: exact, suggestions: [exact] }
  // synonym map
  const syn = synonyms[v]
  if (syn && vocabulary.includes(syn)) return { matched: false, stored_value: syn, suggestions: [syn] }
  // affinity ranking
  const ranked = [...vocabulary]
    .map((t) => ({ t, s: affinity(v, t) }))
    .sort((a, b) => b.s - a.s)
  const top = ranked[0]
  return {
    matched: false,
    stored_value: top && top.s >= 0.6 ? top.t : null,
    suggestions: ranked.filter((r) => r.s > 0).map((r) => r.t).slice(0, 3),
  }
}

// ── ref_yogas_get domain vocabulary (the §B.5 trap) ───────────────────────────
export const YOGA_CATALOG_DOMAINS = ['raja', 'dhana', 'aristha', 'pancha_mahapurusha', 'sannyasa', 'other'] as const
export const YOGA_CATALOG_TRADITIONS = ['parashari'] as const
// common English domain words a caller reaches for → the stored `category` term
export const YOGA_DOMAIN_SYNONYMS: Record<string, string> = {
  wealth: 'dhana', money: 'dhana', finance: 'dhana', prosperity: 'dhana', riches: 'dhana',
  power: 'raja', authority: 'raja', status: 'raja', kingship: 'raja', success: 'raja', career: 'raja',
  health: 'aristha', disease: 'aristha', illness: 'aristha', longevity: 'aristha', death: 'aristha',
  spirituality: 'sannyasa', renunciation: 'sannyasa', moksha: 'sannyasa', asceticism: 'sannyasa',
}
