/**
 * pariprashna/interpretation/schema.ts — the `interpretation_sets` contract
 * (lane G3-B, PPR-02).
 *
 * PARIPRASHNA_ARCHITECTURE_v1_0.md PPR-02 (line 147): "Every SIGNIFICANT
 * interpretive judgment (domain verdict, time-indexed, remedial,
 * prediction-detected, or rules-in-tension) MUST carry >=3 candidate
 * interpretations, a selected reading with rationale, and a falsifier — or
 * an explicit waiver whose rate is monitored."
 *
 * Same DESIGN CONVENTION as `receipt/schema.ts`: the top-level field is a
 * `{ status: 'measured' | 'unavailable', <data, all nullable>,
 * unavailable_reason }` envelope — `status: 'measured'` iff a real detector
 * (`interpretation/detect.ts`) plus a real structured-output call
 * (`interpretation/worker.ts`) actually ran this turn. `receipt/validate.ts`
 * enforces the measured/unavailable coherence structurally, same as every
 * other complex receipt field.
 *
 * Every `InterpretationSetEntry` is EITHER `status: 'generated'` (>=3
 * genuinely distinct candidates, a selected reading + rationale, and a
 * falsifier — all real model output, never fabricated client-side) OR
 * `status: 'waived'` (a specific, non-empty reason the call could not
 * produce 3 distinct candidates) — never a half-populated state. This is
 * the exact §N.8 "earned or null" contract PPR-01's receipt already
 * enforces, applied to a second surface.
 */

import { z } from 'zod'

// ---------------------------------------------------------------------------
// Judgment categories — PPR-02's own five, verbatim.
// ---------------------------------------------------------------------------

export const SIGNIFICANT_JUDGMENT_CATEGORIES = [
  'domain_verdict',
  'time_indexed',
  'remedial',
  'prediction_detected',
  'rules_in_tension',
] as const

export const SignificantJudgmentCategorySchema = z.enum(SIGNIFICANT_JUDGMENT_CATEGORIES)
export type SignificantJudgmentCategory = z.infer<typeof SignificantJudgmentCategorySchema>

/** PPR-02's own floor: "MUST carry >=3 candidate interpretations". */
export const MIN_INTERPRETATION_CANDIDATES = 3 as const

// ---------------------------------------------------------------------------
// One candidate interpretation.
// ---------------------------------------------------------------------------

export const InterpretationCandidateSchema = z.object({
  /** The candidate reading itself, in reader register (no internal ids). */
  reading: z.string().min(1),
  /** Why this is a genuinely distinct, defensible reading of the evidence. */
  rationale: z.string().min(1),
})
export type InterpretationCandidate = z.infer<typeof InterpretationCandidateSchema>

// ---------------------------------------------------------------------------
// One judgment's interpretation set — generated XOR waived, never half of
// either. `candidates`/`selected_*`/`falsifier` are populated iff
// `status === 'generated'`; `waiver_reason` is populated iff
// `status === 'waived'`. Enforced structurally by `receipt/validate.ts`.
// ---------------------------------------------------------------------------

export const InterpretationSetEntrySchema = z.object({
  /** Stable id from `interpretation/detect.ts` (`sig-<category>-<n>`). */
  judgment_id: z.string(),
  category: SignificantJudgmentCategorySchema,
  status: z.enum(['generated', 'waived']),
  /** >=3 distinct candidates when generated; null when waived. */
  candidates: z.array(InterpretationCandidateSchema).nullable(),
  /** Index into `candidates` of the reading actually selected. */
  selected_index: z.number().int().nonnegative().nullable(),
  /** Why the selected reading beats the other candidates. */
  selected_rationale: z.string().nullable(),
  /** What would have to be true/observed for the selected reading to be wrong. */
  falsifier: z.string().nullable(),
  /** Non-empty, specific reason a waiver was issued instead of a set. */
  waiver_reason: z.string().nullable(),
})
export type InterpretationSetEntry = z.infer<typeof InterpretationSetEntrySchema>

// ---------------------------------------------------------------------------
// The receipt-level field — `AcharyaReadingReceipt.interpretation_sets`
// (additive extension of the v1 schema; see `receipt/schema.ts`).
//
// `interpretation_sets_schema_version` versions THIS sub-surface
// independently of the receipt's own outer `receipt_schema_version` — same
// convention as `citations/types.ts`'s `CITATION_EVENT_CONTRACT_VERSION`
// versioning a sub-surface of the wire protocol independently of the
// protocol's own top-level version. Bumping the receipt's OWN literal for an
// additive optional field would break every receipt persisted before this
// lane (`receipt/store.ts`'s read path does a strict `safeParse` against the
// literal) for no reason — the field is optional precisely so old rows stay
// valid; this sub-version is what actually changes if this contract's own
// shape changes later.
// ---------------------------------------------------------------------------

export const INTERPRETATION_SETS_SCHEMA_VERSION = 1 as const

export const ReceiptInterpretationSetsSchema = z.object({
  status: z.enum(['measured', 'unavailable']),
  interpretation_sets_schema_version: z.literal(INTERPRETATION_SETS_SCHEMA_VERSION).nullable(),
  /** Every SIGNIFICANT judgment `interpretation/detect.ts` found this turn. */
  detected_count: z.number().int().nonnegative().nullable(),
  /** Judgments actually sent to the structured-output call (<= detected_count). */
  covered_count: z.number().int().nonnegative().nullable(),
  /**
   * `detected_count - covered_count` — judgments detected but not processed
   * this turn under the per-turn cost/latency cap
   * (`MAX_SIGNIFICANT_JUDGMENTS_PER_TURN`, `interpretation/assemble.ts`).
   * Zero when nothing was truncated. A REAL, disclosed count — never a
   * silently-dropped judgment (§N.6/§N.8).
   */
  truncated_count: z.number().int().nonnegative().nullable(),
  /** `sets.filter(s => s.status === 'waived').length` — the real numerator
   *  the monitored waiver rate is computed from (never hardcoded). */
  waived_count: z.number().int().nonnegative().nullable(),
  /** One entry per COVERED judgment — `sets.length === covered_count`. */
  sets: z.array(InterpretationSetEntrySchema).nullable(),
  unavailable_reason: z.string().nullable(),
})
export type ReceiptInterpretationSets = z.infer<typeof ReceiptInterpretationSetsSchema>
