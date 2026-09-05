/**
 * Declared salience orderings for L4 Phala's ordinal TEXT columns.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * Six L4 serving queries ordered by an ordinal value stored as TEXT, so Postgres sorted them
 * ALPHABETICALLY. `ORDER BY magnitude DESC` on `phala_anchors` yields
 * `pivotal > moderate > minor > major` — which puts the layer's most consequential anchors
 * LAST. Measured on the canonical chart: the default `top_k = 50` page returned 45 `minor`
 * and 5 `moderate` anchors and **none of the 3 `major` ones**.
 *
 * That is §N.6 item 2 inverted — "the densest, most-actionable layer is the one a budget trim
 * protects first" — and it made every one of these pages trim exactly the rows a caller most
 * needs. D-SALIENCE names the same failure from the doctrine side.
 *
 * SOURCE OF THE ORDERINGS
 * -----------------------
 * Each array below is the vocabulary of that column's DB CHECK constraint, re-stated in
 * SALIENCE-DESCENDING order (most consequential first). The constraint is the source of truth
 * for MEMBERSHIP; this file is the source of truth for ORDER, which the constraint does not
 * encode. `salience_order.test.ts` asserts each list is total and duplicate-free, and the
 * DB-integration suite asserts membership still matches the live CHECK — so a vocabulary
 * added in a migration cannot silently fall off the end of a ranking.
 *
 * USAGE: `ORDER BY ${salienceRank('magnitude', ANCHOR_MAGNITUDE_ORDER)}` — see `salienceRank`.
 */

/** `phala_anchors.magnitude` — CHECK: minor | moderate | major | pivotal. */
export const ANCHOR_MAGNITUDE_ORDER = ['pivotal', 'major', 'moderate', 'minor'] as const

/** `phala_sodhana.anomaly_severity` — CHECK: critical | major | minor | informational. */
export const ANOMALY_SEVERITY_ORDER = ['critical', 'major', 'minor', 'informational'] as const

/** `phala_suddha_sodhana.cleanliness_status` — CHECK: clean | flagged | staged_revision.
 *  Ordered by ATTENTION REQUIRED: a staged revision is the row a reader must see. */
export const CLEANLINESS_ATTENTION_ORDER = ['staged_revision', 'flagged', 'clean'] as const

/** `phala_mitigation.obstruction_severity` — writer-mapped from kala_obstruction's
 *  mild|moderate|severe. No CHECK constraint exists on this column; the vocabulary is
 *  `ph_pratikara.py`'s `_SEVERITY_MAP` image. */
export const OBSTRUCTION_SEVERITY_ORDER = ['high', 'medium', 'low'] as const

/** `phala_pramana.window_status` — CHECK: pending | open | past_window.
 *  Ordered by ACTIONABILITY: an open window is live now; a past one is closed. */
export const WINDOW_STATUS_ACTIONABILITY_ORDER = ['open', 'pending', 'past_window'] as const

/** `phala_muhurta.window_quality_verdict` — CHECK: strong | adequate | mediocre | none_genuine. */
export const MUHURTA_VERDICT_ORDER = ['strong', 'adequate', 'mediocre', 'none_genuine'] as const

/**
 * A SQL ordering expression that ranks `column` by its declared salience order.
 *
 * Emits `array_position(ARRAY[...]::text[], column)` ascending, so index 0 (the most
 * consequential value) sorts FIRST. An unrecognised or NULL value yields NULL from
 * `array_position` and is placed LAST by `NULLS LAST` — an unknown value must never
 * outrank a known one, and must never be silently dropped either.
 *
 * The vocabulary is inlined as a literal array rather than parameterised because these
 * expressions appear in `ORDER BY`, where a bind parameter is not usable in every driver
 * path. Values are compile-time constants from this module, never caller input.
 */
export function salienceRank(column: string, order: readonly string[]): string {
  const literal = order.map((v) => `'${v.replace(/'/g, "''")}'`).join(', ')
  return `array_position(ARRAY[${literal}]::text[], ${column}) NULLS LAST`
}
