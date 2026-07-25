/**
 * ayanamsha_variation.ts — Elevation Campaign v2.1 · Stream γ (PŪRṆA) · Lane I (EL-27 + EL-56).
 * The cross-ayanamsha agreement engine: ONE mechanism serving both EL-27 (the planner gains
 * ayanamsha as an expressible axis) and EL-56 (family-collapse dedup that preserves the
 * variation signal instead of destroying it).
 * ============================================================================================
 *
 * WHAT THIS IS
 * ------------
 * A deterministic comparison primitive family. For a single planet/point it takes the SAME
 * already-computed L1 fact read once per ayanamsha (via `ganita_chart_facts_get`, which accepts
 * an `ayanamsha_id` — verified live: the tool advertises "any of the 6 stored ayanamshas") and
 * computes the deltas that actually matter across ayanamshas:
 *   - dignity_delta   — does the graha's dignity_state flip (e.g. friend → enemy) between reads?
 *   - house_shift     — does its bhāva placement move (a near-cusp longitude crossing a boundary)?
 *   - vargottama_delta — does its vargottama status change (sign identity across D1/D9)?
 * and emits `ayanamsha_agreement: "n/5"` — a CONFIDENCE field on the finding.
 *
 * NO FABRICATED COMPUTATION (B.10). This module NEVER computes a chart value. It is a pure
 * transform over reads the L1 `ga_*` writers already produced and `ganita_chart_facts_get`
 * already serves per ayanamsha. `computeAyanamshaAgreement` is a comparison of existing values,
 * exactly like a family-collapse dedup — a legitimate deterministic transform (§N.4
 * deterministic-first). If a per-ayanamsha read is missing, the point is reported with a smaller
 * denominator and a `missing_ayanamshas` note — never back-filled with an invented value.
 *
 * WHY n/5 AND NOT n/6 (the charter's number) — Ω1-VERIFIED BASELINE CORRECTION
 * ---------------------------------------------------------------------------
 * The charter (ELEVATION_CAMPAIGN_CHARTER_v2_1.md §γ.I, EL-27) specifies "ayanamsha_agreement:
 * n/6 across the 6 ayanamshas". Six ids ARE stored (`ganita_chart_facts_get` advertises them:
 * lahiri_chitrapaksha, krishnamurti, raman, surya_siddhanta_classical, true_chitra, INVARIANT).
 * But `INVARIANT` is a SENTINEL, not a real ayanamsha: it is a fixed, non-astronomical baseline
 * used internally to detect which facts are ayanamsha-sensitive at all (a fact that is identical
 * under INVARIANT and under a real ayanamsha is ayanamsha-invariant by construction). Counting it
 * as a sixth "vote" would systematically INFLATE the agreement score toward consensus and, worse,
 * mask genuine disagreement. Lane Ω1 independently re-verified this baseline (the sentinel is not
 * a chart the native was born under). Therefore the agreement denominator is the count of the 5
 * REAL ayanamshas only. This is a deliberate, documented divergence from the charter number,
 * ratified by the Ω1 baseline. See `REAL_AYANAMSHAS` below.
 *
 * FAMILY-COLLAPSE WARNING (EL-56) — THE SIGNAL A NAIVE DEDUP DESTROYS
 * ------------------------------------------------------------------
 * The E-6 `family_aggregation` key (query_ucd.ts / synthesis digest) collapses repeat signals of
 * the same `graha × signal_type_id` — e.g. per-varga dignity signals — into one composite row so
 * the caller is not flooded. If that same collapse were applied naively ACROSS ayanamshas, five
 * reads of "Saturn dignity" would silently collapse to one ayanamsha's value and the cross-
 * ayanamsha variation — the whole EL-27 signal — would vanish. `ayanamshaFamilyKey` extends the
 * family key to INCLUDE the ayanamsha axis, so:
 *   - full agreement (5/5) COMPRESSES cleanly (identical reads → one row + agreement: "5/5");
 *   - DISagreement is preserved and surfaces as a rarity signal (agreement: "3/5" with the
 *     divergent ayanamshas named) rather than being averaged/dropped into invisibility.
 * A collapse that would erase disagreement is a bug, never an optimization.
 */

/**
 * The five REAL ayanamshas (long-form L1 ids as stored in `chart_facts.ayanamsha_id` and
 * accepted by `ganita_chart_facts_get`). ORDER IS STABLE (determinism: the agreement engine and
 * the family key must produce byte-identical output across runs). The `INVARIANT` sentinel is
 * DELIBERATELY EXCLUDED — see the file header ("WHY n/5 AND NOT n/6").
 */
export const REAL_AYANAMSHAS = [
  'krishnamurti',
  'lahiri_chitrapaksha',
  'raman',
  'surya_siddhanta_classical',
  'true_chitra',
] as const;

export type RealAyanamsha = (typeof REAL_AYANAMSHAS)[number];

/** The sentinel that is NOT a real ayanamsha and MUST NOT enter the agreement denominator. */
export const AYANAMSHA_SENTINEL = 'INVARIANT' as const;

/** The agreement denominator — always 5 (the count of `REAL_AYANAMSHAS`). */
export const AYANAMSHA_AGREEMENT_DENOMINATOR = REAL_AYANAMSHAS.length;

/**
 * One per-ayanamsha read of a single planet/point, distilled to the three ayanamsha-sensitive
 * dimensions. Every field is a value the L1 read ALREADY carries — this type restates, never
 * derives. `null` means the read did not carry that dimension (honest absence, not a default).
 */
export interface AyanamshaRead {
  readonly ayanamsha: RealAyanamsha;
  /** D1 dignity_state (exalted/own/friend/neutral/enemy/debilitated), or null if not read. */
  readonly dignity_state: string | null;
  /** Bhāva (1..12) the point occupies, or null if not read. */
  readonly house: number | null;
  /** Rāśi (sign) identity, used for the vargottama check, or null if not read. */
  readonly sign: string | null;
  /** Vargottama status (same sign in D1 & D9), or null if not read. */
  readonly vargottama: boolean | null;
}

/**
 * The computed cross-ayanamsha variation for one point. This is the row a finding carries its
 * `ayanamsha_agreement` confidence from. It is ALSO a family-collapse row (see `family_key`):
 * one row stands for up-to-5 per-ayanamsha reads, with the divergent ones named rather than lost.
 */
export interface CrossAyanamshaVariation {
  readonly point: string;
  /** "n/5" — how many of the 5 real ayanamshas AGREE on the modal (most-common) reading. */
  readonly ayanamsha_agreement: string;
  /** The numerator of `ayanamsha_agreement` (1..5). */
  readonly agreement_count: number;
  /** Always 5 — the real-ayanamsha denominator (never 6; the sentinel is excluded). */
  readonly agreement_denominator: number;
  /** True iff all reads present agree on every dimension — the compressible case. */
  readonly unanimous: boolean;
  /** Dignity_state flips observed across ayanamshas (empty ⇒ dignity is ayanamsha-stable). */
  readonly dignity_delta: readonly string[];
  /** Distinct houses the point lands in across ayanamshas (length > 1 ⇒ a house_shift). */
  readonly house_shift: readonly number[];
  /** True iff vargottama status is NOT unanimous across ayanamshas. */
  readonly vargottama_delta: boolean;
  /** Ayanamshas whose read diverged from the modal reading — the rarity signal (EL-56). */
  readonly divergent_ayanamshas: readonly RealAyanamsha[];
  /** Real ayanamshas with no read supplied (denominator shrinks; never back-filled). */
  readonly missing_ayanamshas: readonly RealAyanamsha[];
  /**
   * The E-6 family_aggregation key EXTENDED with the ayanamsha axis (EL-56). A dedup keyed on
   * this collapses full-agreement families cleanly while preserving disagreement — it can never
   * silently flatten five ayanamsha reads to one value.
   */
  readonly family_key: string;
}

/** The most-common value in a list (modal), with a stable tie-break by first appearance. */
function modal<T>(values: readonly T[]): { value: T | null; count: number } {
  if (values.length === 0) return { value: null, count: 0 };
  const counts = new Map<T, number>();
  for (const v of values) counts.set(v, (counts.get(v) ?? 0) + 1);
  let best: T = values[0]!;
  let bestCount = 0;
  for (const v of values) {
    const c = counts.get(v)!;
    if (c > bestCount) {
      best = v;
      bestCount = c;
    }
  }
  return { value: best, count: bestCount };
}

/**
 * The E-6 family_aggregation key, extended with the ayanamsha axis (EL-56). Same shape a
 * synthesis-side dedup would key on — `graha × signal_type` — but with `ayanamsha_agreement`
 * folded in, so a collapse GROUPS agreeing reads yet CANNOT erase the disagreement signal.
 *
 * @param point         the graha/point id (the "graha" of the E-6 key)
 * @param signalType    the signal family (dignity/vargottama/house — the "signal_type" of E-6)
 * @param agreement     the computed "n/5" agreement string
 */
export function ayanamshaFamilyKey(point: string, signalType: string, agreement: string): string {
  return `${point}::${signalType}::ayanamsha_agreement=${agreement}`;
}

/**
 * Compute the cross-ayanamsha variation + agreement for one point from its per-ayanamsha reads.
 * Pure and deterministic. `reads` may contain 1..5 entries; the denominator is ALWAYS 5 and any
 * absent real ayanamsha is reported in `missing_ayanamshas` (honest, never back-filled).
 *
 * `agreement_count` = how many reads share the MODAL (most-common) combined reading. A point
 * that reads identically under all 5 → "5/5", unanimous. A near-cusp graha that shifts house
 * under one ayanamsha → "4/5" with that ayanamsha named in `divergent_ayanamshas` and the two
 * houses in `house_shift`.
 */
export function computeAyanamshaAgreement(
  point: string,
  reads: readonly AyanamshaRead[],
  signalType = 'dignity',
): CrossAyanamshaVariation {
  const seen = new Set(reads.map((r) => r.ayanamsha));
  const missing = REAL_AYANAMSHAS.filter((a) => !seen.has(a));

  // Combined per-read fingerprint — the tuple whose agreement we score.
  const fingerprint = (r: AyanamshaRead): string =>
    `${r.dignity_state ?? '∅'}|${r.house ?? '∅'}|${r.sign ?? '∅'}|${r.vargottama ?? '∅'}`;

  const fingerprints = reads.map(fingerprint);
  const { value: modalFp, count: agreementCount } = modal(fingerprints);

  const divergent = reads.filter((r) => fingerprint(r) !== modalFp).map((r) => r.ayanamsha);

  const dignityValues = [...new Set(reads.map((r) => r.dignity_state).filter((d): d is string => d !== null))];
  const houseValues = [...new Set(reads.map((r) => r.house).filter((h): h is number => h !== null))].sort(
    (a, b) => a - b,
  );
  const vargottamaValues = new Set(reads.map((r) => r.vargottama).filter((v): v is boolean => v !== null));

  const agreement = `${agreementCount}/${AYANAMSHA_AGREEMENT_DENOMINATOR}`;

  return {
    point,
    ayanamsha_agreement: agreement,
    agreement_count: agreementCount,
    agreement_denominator: AYANAMSHA_AGREEMENT_DENOMINATOR,
    unanimous: divergent.length === 0 && missing.length === 0,
    dignity_delta: dignityValues.length > 1 ? dignityValues : [],
    house_shift: houseValues.length > 1 ? houseValues : [],
    vargottama_delta: vargottamaValues.size > 1,
    divergent_ayanamshas: divergent,
    missing_ayanamshas: missing,
    family_key: ayanamshaFamilyKey(point, signalType, agreement),
  };
}

/**
 * The `tool_args` template the `cross_ayanamsha_variation` planner primitive resolves to. It
 * names the ONE live tool (`ganita_chart_facts_get`) and the axis the executor iterates: the
 * caller invokes it once per entry of `REAL_AYANAMSHAS`, then feeds the 5 reads to
 * `computeAyanamshaAgreement`. The `{point}` placeholder is filled by the floor's args_override
 * (a graha id or a point like "LAGNA"); `ayanamsha_axis` is an EXPRESSED axis, not a single value
 * — the planner's first-ever ayanamsha expressibility (EL-27).
 */
export const CROSS_AYANAMSHA_TOOL_ARGS = {
  chart_id: '{chart_id}',
  about: '{point}',
  ayanamsha_axis: REAL_AYANAMSHAS,
} as const;
