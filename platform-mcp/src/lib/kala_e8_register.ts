/**
 * kala_e8_register.ts — E8: THE NON-ELEVATIONS REGISTER
 * ==========================================================================
 * KALA_SUPREME_ELEVATION_v1_0.md §13 + §14:
 *
 *   "E8 — the non-elevations register (§13) — standing constraints, carried
 *   as a ledger row and verified respected at every wave gate; the only
 *   E-row that is never 'built', only 'held'."
 *
 * Per R26 (MASTER_PLAN_v1_0.md §G12): "E8 register created (initially empty)
 * as the standing home for future conscious de-scopes."
 *
 * PURPOSE: This register lists every capability or precision level that is
 * CONSCIOUSLY NOT elevated in the Kāla serving layer, with a cited reason for
 * each. Its value is auditability: a PARĪKṢAKA or wave-gate reviewer can confirm
 * that each constraint is still intentionally held, and a builder who wants to
 * change one has a clear registered citation to update or retire.
 *
 * E8 is NEVER "done" — it is maintained across campaigns. Adding a new row means
 * a conscious decision was made. Removing a row (or changing its status to
 * LIFTED) means the constraint was retired via a ratified wave or ruling.
 *
 * SHAD_DARSHANA_CLOSE_v1_0.md §2: E8 disposition was NOT-STARTED (2026-08-07).
 * SAMPURTI G12 creates this file (2026-08-10).
 * ==========================================================================
 */

/** Disposition of a non-elevation entry. */
export type NonElevationDisposition =
  /** Constraint is actively held; no campaign has lifted it. */
  | 'HELD'
  /** Constraint was lifted by a named wave/ruling (see `lifted_by`). */
  | 'LIFTED'
  /** Constraint is under review — a wave is evaluating whether to lift it. */
  | 'UNDER_REVIEW'

/** A single entry in the E8 non-elevations register. */
export interface NonElevationEntry {
  /** Short identifier, stable across versions (e.g. 'NO_LLM_IN_SERVING_PATH'). */
  id: string
  /** One-sentence statement of what is NOT elevated. */
  constraint: string
  /** Cited reason — references the ratified design document or ruling. */
  rationale: string
  /** Which waves or tools does this constraint bind? Use '*' for all. */
  scope: string
  disposition: NonElevationDisposition
  /** Wave or ruling that lifted this constraint — null while HELD or UNDER_REVIEW. */
  lifted_by: string | null
  /** ISO date this entry was added. */
  registered: string
}

/**
 * THE E8 REGISTER — standing non-elevations for the Kāla serving layer.
 *
 * Adding an entry: append a new object below. `id` must be unique and stable.
 * Lifting an entry: change disposition to 'LIFTED', set `lifted_by` to the
 *   wave or ruling reference, and add a changelog comment.
 *
 * Currently empty per G12 R26 "E8 register created (initially empty)."
 * Constraints will be migrated here as they are identified during wave-gate
 * reviews. The three constraints named in KALA_SUPREME_ELEVATION_v1_0.md §13
 * are seeded below as the initial population.
 */
export const KALA_E8_NON_ELEVATIONS: readonly NonElevationEntry[] = [
  {
    id: 'NO_LLM_IN_SERVING_PATH',
    constraint:
      'No generative LLM calls in the Kāla serving path — all computation is deterministic.',
    rationale:
      'CLAUDE.md §N.4 (deterministic-first); KALA_SUPREME_ELEVATION_v1_0.md §13: ' +
      '"No generative LLM calls in the serving path (B.10 — determinism is the moat)." ' +
      'The instrument\'s only differentiator vs. superficial products is provably full-depth ' +
      'deterministic use of every computed concept; generative calls break that proof.',
    scope: '*',
    disposition: 'HELD',
    lifted_by: null,
    registered: '2026-08-10',
  },
  {
    id: 'NO_PERCENTAGES_BEFORE_CALIBRATION',
    constraint:
      'No percentage-form probability claims before the L5/field calibration pipeline has ' +
      'measured discrimination on real LEL events (LAW ZERO).',
    rationale:
      'KALA_SUPREME_ELEVATION_v1_0.md §13: "no percentages before calibration (LAW ZERO)." ' +
      'A percentage claim without a grounded denominator (a measured hit/miss rate on real ' +
      'outcomes) is an invented number that breaks trust the moment it is tested against reality. ' +
      'Until MEASUREMENT #4 (G1 / ka_kshetra temporal skill score) exists, all probabilistic ' +
      'language uses calibration-tier vocabulary (structural_prior / calibrated_provisional / ' +
      'calibrated), not invented percentages.',
    scope: '*',
    disposition: 'HELD',
    lifted_by: null,
    registered: '2026-08-10',
  },
  {
    id: 'NO_SUB_DAY_TRANSIT_PRECISION_BEFORE_GOCHARA_2',
    constraint:
      'No sub-day transit-edge precision claims before the GOCHARA-2.0 D-6 wave closes.',
    rationale:
      'KALA_SUPREME_ELEVATION_v1_0.md §13 (amended 2026-07-29): "no sub-day transit precision ' +
      'before the D-6 wave closes WITHIN this campaign." GOCHARA-2.0 (item 19) entered scope ' +
      'and landed (PR #1089, 2026-08-07, SHAD_DARSHANA_CLOSE §1 W2G LANDED). Until the full ' +
      'D-6 wave closes (sub-day ephemeris splines + root-found transitions), all transit-edge ' +
      'constraints remain day-grade and must carry the `day_grade` precision label. Precision ' +
      'is earned, never assumed.',
    scope: 'transit-consuming views: kala_now_get, kala_ahead_get, kala_elect_get',
    disposition: 'HELD',
    lifted_by: null,
    registered: '2026-08-10',
  },
  {
    id: 'NO_PRASHNA_AT_EVERY_QUERY',
    constraint:
      'Praśna (horary) is not invoked at every query — it is a distinct, separately-gated mode.',
    rationale:
      'KALA_SUPREME_ELEVATION_v1_0.md §13: "praśna-at-every-query stays reserved." Praśna ' +
      'operates on the chart of the moment of the question and a distinct interpretive grammar; ' +
      'conflating it with natal/field readings would mix two incompatible systems without ' +
      'disclosure. Registered as a standing constraint so no wave adds automatic praśna ' +
      'enrichment to natal view responses without an explicit adjudication.',
    scope: 'all six views (kala_now_get, kala_ahead_get, kala_elect_get, kala_story_get, kala_priority_get, kala_explain_get)',
    disposition: 'HELD',
    lifted_by: null,
    registered: '2026-08-10',
  },
  {
    id: 'STRANGLER_FIG_DISCIPLINE',
    constraint:
      'The strangler-fig migration discipline stands: each wave enriches computation and ' +
      'composition; it does not change migration physics except within explicitly ratified ' +
      'wave sub-arcs carrying their own migration plans and cutover disciplines.',
    rationale:
      'KALA_SUPREME_ELEVATION_v1_0.md §13: "the strangler-fig ruling stands untouched — this ' +
      'round enriches what the field computes and what the views compose; it changes no ' +
      'migration physics except within the D-6 wave." Prevents scope creep in wave gate reviews ' +
      'that might otherwise fold unrelated migration work into elevation wave PRs.',
    scope: 'all waves',
    disposition: 'HELD',
    lifted_by: null,
    registered: '2026-08-10',
  },
] as const

/**
 * Returns only HELD entries — the currently-active constraints.
 * Useful for wave-gate checkers that want to enumerate what must still be
 * respected without also listing lifted or under-review entries.
 */
export function heldNonElevations(): readonly NonElevationEntry[] {
  return KALA_E8_NON_ELEVATIONS.filter((e) => e.disposition === 'HELD')
}

/**
 * Look up a single entry by its stable `id`.
 * Returns `undefined` if the id does not exist — a caller asserting a
 * constraint's presence at a gate should fail explicitly when it is absent
 * rather than silently passing (§N.8 Earned-Signal Principle).
 */
export function lookupNonElevation(id: string): NonElevationEntry | undefined {
  return KALA_E8_NON_ELEVATIONS.find((e) => e.id === id)
}
