/**
 * signal_glossary.ts — serve-time acharya-grade labelling + internal-marker classification
 * for raw `bodha_msr_signals.signal_headline_text` template strings.
 * =============================================================================
 * WHY THIS FILE EXISTS (F-131, PARIŚEṢA-V4):
 *   `kala_priority_ranking_get` served `bodha_msr_signals.signal_headline_text` verbatim.
 *   That column is a deterministic TEMPLATE built by `bo_laksana._build_headline_text()`:
 *
 *       "{SUBJECT}({H#, VARGA}): {fact_category with _→space}: {fact_key with _→space} = {value} [{l1_asset}]"
 *
 *   so the native was reading raw schema keys, e.g.
 *       "SAT: arudha pada: sign = Aquarius [ga_sensitive]"
 *   and — worse — an internal computation-abstention marker was salience-scored and served
 *   as if it were a priority finding deserving attention:
 *       "graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method [ga_structural]"
 *   (the writer honestly FLOORED D14 ceṣṭā bala per §B.10 because no verifiable classical
 *   per-varga formula for it exists — the floor REASON, not an astrological finding, was
 *   ranked #5 by priority_score on the native's own chart, 6-month window, 2026-08-21.)
 *
 * WHY SERVE-TIME AND NOT WRITE-TIME: the DB column is the deterministic L1-referencing
 * template and stays exactly as written (§N.5 — L2+ never restates an L1 value as its own
 * truth, and B.10 forbids destroying stored data). This module adds a DISPLAY layer beside
 * it; `signal_headline_text` is still returned raw on every row. No chart rebuild required.
 *
 * DATA SOURCE: `./signal_glossary.generated.ts`, generated from the Python single source of
 * truth `brahmagyan/signal_register_glossary.py`. Never hand-edit the tables here.
 *
 * PURE / CLIENT-SAFE: zero I/O, zero `@/lib/db/client` import — same discipline as
 * `graha_labels.ts`, so a client component may import it directly.
 */

import {
  FACT_CATEGORY_DISPLAY_LABEL,
  INTERNAL_MARKER_PATTERNS,
} from './signal_glossary.generated'

export {
  FACT_CATEGORY_DISPLAY_LABEL,
  INTERNAL_MARKER_PATTERNS,
  SIGNAL_TYPE_GLOSSARY,
  SOURCE_SHA256,
  SOURCE_PATH,
} from './signal_glossary.generated'

// ── Marker dispositions ───────────────────────────────────────────────────────
// `INTERNAL_MARKER_PATTERNS` is a flat list in the Python source, but its own inline
// annotations distinguish two genuinely different things, and they must NOT get the same
// disposition:
//
//   ABSTENTION — "floored:", "no_canonical_per_varga_method", "[COMPUTATION-ABSTENTION",
//   "[FLOOR-VALUE", "floor_reason=". These are not astrological findings at all; they are
//   the writer's honest record that a computation was declined (§B.10). Serving one as a
//   ranked priority signal is the F-131 defect. → EXCLUDED from `ranked_signals`, and
//   disclosed as excluded (never silently dropped).
//
//   CATALOG_ONLY — "requires_pass", annotated in the Python source itself as "yoga
//   catalog-only rows not yet cross-verified". That IS a real astrological candidate; it
//   simply has not had its second pass. §N.6 item 1 is explicit that such a row is "still
//   served — B.10 forbids silently dropping data — but is counted and flagged SEPARATELY
//   from confirmed findings". → KEPT in `ranked_signals`, flagged `catalog_only_unverified`.
//
// Deriving both sets FROM the generated list (rather than re-typing the strings) means a
// Python-side pattern edit still flows through: any new pattern defaults to ABSTENTION,
// which is the conservative disposition.

/** Patterns whose rows are real astrological candidates awaiting cross-verification (§N.6). */
export const CATALOG_ONLY_MARKER_PATTERNS: readonly string[] = Object.freeze(
  INTERNAL_MARKER_PATTERNS.filter(p => p === 'requires_pass'),
)

/** Patterns whose rows are NOT astrological findings — internal computation abstentions. */
export const ABSTENTION_MARKER_PATTERNS: readonly string[] = Object.freeze(
  INTERNAL_MARKER_PATTERNS.filter(p => !CATALOG_ONLY_MARKER_PATTERNS.includes(p)),
)

export type SignalMarkerDisposition = 'abstention' | 'catalog_only'

export interface SignalMarkerClassification {
  disposition: SignalMarkerDisposition | null
  /** The exact pattern that matched, verbatim from the glossary. `null` when nothing matched. */
  matched_pattern: string | null
}

const NO_MARKER: SignalMarkerClassification = Object.freeze({
  disposition: null,
  matched_pattern: null,
})

/**
 * Classify a headline/summary string against the glossary's internal-marker patterns.
 * Case-insensitive plain substring containment — no regex, no LIKE wildcards (two patterns
 * contain `[` and one contains `_`, both of which are metacharacters in the surfaces this
 * would otherwise be expressed in).
 *
 * Abstention patterns are checked first, in glossary order, so the most specific F-131
 * pattern ("floored: no_canonical_per_varga_method") is the one reported when several match.
 */
export function classifySignalMarker(text: string | null | undefined): SignalMarkerClassification {
  if (!text) return NO_MARKER
  const hay = text.toLowerCase()
  for (const p of ABSTENTION_MARKER_PATTERNS) {
    if (hay.includes(p.toLowerCase())) return { disposition: 'abstention', matched_pattern: p }
  }
  for (const p of CATALOG_ONLY_MARKER_PATTERNS) {
    if (hay.includes(p.toLowerCase())) return { disposition: 'catalog_only', matched_pattern: p }
  }
  return NO_MARKER
}

// ── Headline labelling ────────────────────────────────────────────────────────

/** Space-separated form of each raw fact_category — the form that actually appears in a
 *  headline, because `_build_headline_text` does `fact_category.replace("_", " ")`.
 *  Sorted longest-first so a longer category wins over a shorter one that is its suffix. */
const SPACE_FORM_ENTRIES: ReadonlyArray<readonly [string, string, string]> = Object.freeze(
  Object.entries(FACT_CATEGORY_DISPLAY_LABEL)
    .map(([rawCategory, label]) => [rawCategory.replace(/_/g, ' '), label, rawCategory] as const)
    .sort((a, b) => b[0].length - a[0].length),
)

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Precompiled matcher per category. The category segment is anchored: it must start the
 *  string or follow a ": " subject separator, and must be followed by ": ". That anchoring is
 *  what stops "graha position" from matching inside "SAT: upagraha position: sign = X". */
const SPACE_FORM_MATCHERS: ReadonlyArray<readonly [RegExp, string, string]> = Object.freeze(
  SPACE_FORM_ENTRIES.map(([spaceForm, label, rawCategory]) =>
    [new RegExp(`(^|:\\s)${escapeRegExp(spaceForm)}(?=:\\s)`), label, rawCategory] as const),
)

export interface HumanizedHeadline {
  /** Display form. IDENTICAL to the input when no mapping exists — never a fabricated label. */
  headline_label: string
  /** True only when a real glossary mapping was applied. */
  label_mapped: boolean
  /** The raw fact_category the label came from, or `null` when unmapped. */
  matched_fact_category: string | null
}

/**
 * Replace the raw `fact_category` segment of a signal headline with its acharya-grade label.
 *
 * HONESTY CONTRACT (§N.7 item 6 — an honest null beats an invented judgment): when the
 * headline's category has no glossary entry, the ORIGINAL STRING is returned unchanged with
 * `label_mapped: false`. Nothing is guessed, prettified, or title-cased into looking like a
 * classical term. Callers surface the unmapped count so a reader can tell a translated
 * headline from a passed-through raw template.
 *
 * Only the category segment is rewritten; subject prefix, fact_key, value and the
 * `[l1_asset]` provenance suffix are left exactly as the writer emitted them.
 */
export function humanizeSignalHeadline(raw: string | null | undefined): HumanizedHeadline {
  if (!raw) {
    return { headline_label: raw ?? '', label_mapped: false, matched_fact_category: null }
  }
  for (const [re, label, rawCategory] of SPACE_FORM_MATCHERS) {
    const m = re.exec(raw)
    if (m) {
      const headline_label = raw.slice(0, m.index) + m[1] + label + raw.slice(m.index + m[0].length)
      return { headline_label, label_mapped: true, matched_fact_category: rawCategory }
    }
  }
  return { headline_label: raw, label_mapped: false, matched_fact_category: null }
}
