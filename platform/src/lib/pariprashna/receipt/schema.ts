/**
 * pariprashna/receipt/schema.ts — `AcharyaReadingReceipt` v1 (lane G3-A, PPR-01).
 *
 * PARIPRASHNA_ARCHITECTURE_v1_0.md PPR-01 (line 146): every interpretive
 * reading MUST emit a receipt carrying coverage, facts consumed (by
 * reference, never restated — §N.5), derivation chains, cross-domain block,
 * evidence grades, honest gaps, safety decision, calibration disclosure,
 * prose binding, provenance, and a receipt hash. §N.8: every field is earned
 * by a detector or is null — never a plausible-looking fabrication.
 *
 * DESIGN CONVENTION (applies to every "complex" field below): a field that
 * can genuinely be absent for a turn (no real source ran, or the source
 * declined to produce a value) is modeled as `{ status: 'measured' | ...,
 * <data fields, all nullable>, unavailable_reason: string | null }` rather
 * than a bare nullable value. `status` names WHICH state the field is in;
 * `unavailable_reason` is populated iff status is not the measured state,
 * and is the ONLY place a human-readable "why" lives — never invented
 * elsewhere. `receipt/validate.ts` enforces the measured/unavailable
 * coherence structurally (see that module).
 *
 * A field whose real source ALWAYS runs deterministically for every
 * persisted turn (facts_consumed, derivation_chains, prose_binding,
 * calibration_disclosure) has no unavailable branch — there is no state in
 * which its detector could not run, so modeling one would itself be
 * dishonest (a fabricated "unavailable" the code can never actually reach).
 *
 * Reuses canonical schemas rather than shadowing them (§N.7 item 3):
 * `GroundingSummaryGradeCountsSchema` (protocol/events.ts) is imported
 * directly for `evidence_grades.grade_counts`.
 */

import { z } from 'zod'

import { GroundingSummaryGradeCountsSchema } from '@/lib/pariprashna/protocol/events'

// ---------------------------------------------------------------------------
// coverage — from the turn's own WebCompletenessReceipt (pipeline/
// completeness_wiring.ts), the SAME object receipt_stage.ts's
// emitCompletenessReceipt reports as the `completeness` grade.
// ---------------------------------------------------------------------------

export const ReceiptCoverageSchema = z.object({
  status: z.enum(['measured', 'unavailable']),
  served: z.number().int().nonnegative().nullable(),
  empty: z.number().int().nonnegative().nullable(),
  dark: z.number().int().nonnegative().nullable(),
  floor_item_total: z.number().int().nonnegative().nullable(),
  channel: z.literal('web').nullable(),
  channel_note: z.string().nullable(),
  unavailable_reason: z.string().nullable(),
})
export type ReceiptCoverage = z.infer<typeof ReceiptCoverageSchema>

// ---------------------------------------------------------------------------
// facts_consumed — BY REFERENCE ONLY (§N.5): the signal_id a citation names,
// never the value that signal carries. Source: the turn's own citation
// detection (`reading_parts.ts#detectTurnCitations`, or the G2-B live
// rewriter's resolution ledger when that flag is on) — always runs
// deterministically, so this is always an array, never null. An empty array
// is an honest "this turn cited zero facts", not a missing detector.
// ---------------------------------------------------------------------------

export const ReceiptFactRefSchema = z.object({
  /** The signal/fact reference token as cited in prose (e.g. `SIG.MSR.042`). */
  ref: z.string(),
  /** Source layer tag (e.g. `L2.5`). */
  layer: z.string(),
  /** Citation ordinal within the turn's prose. */
  index: z.number().int(),
})
export type ReceiptFactRef = z.infer<typeof ReceiptFactRefSchema>

// ---------------------------------------------------------------------------
// derivation_chains — "thread envelope refs through synthesis": for each
// committed block, which pass it belongs to and which facts its OWN text
// cites. Source: `ReadingPartsAssembler.committedBlocks` (real, already-
// produced synthesis output) + the same citation detector facts_consumed
// uses, run per-block. Always an array (the source always runs).
// ---------------------------------------------------------------------------

export const ReceiptDerivationLinkSchema = z.object({
  block_id: z.string(),
  /** Parsed from the block id's `blk-<pass>-<n>` shape; null on a genuine parse miss. */
  pass_id: z.number().int().nullable(),
  role: z.enum(['prose', 'thinking']),
  /** signal_id refs cited within THIS block's own committed text. */
  fact_refs: z.array(z.string()),
})
export type ReceiptDerivationLink = z.infer<typeof ReceiptDerivationLinkSchema>

// ---------------------------------------------------------------------------
// cross_domain — which domains the plan actually authorized. Source:
// `plan.domains` (PipelinePlan, populated by the planner).
// ---------------------------------------------------------------------------

export const ReceiptCrossDomainSchema = z.object({
  status: z.enum(['measured', 'unavailable']),
  domains: z.array(z.string()).nullable(),
  unavailable_reason: z.string().nullable(),
})
export type ReceiptCrossDomain = z.infer<typeof ReceiptCrossDomainSchema>

// ---------------------------------------------------------------------------
// evidence_grades — the turn's citation grade rollup. Source: the G2-B live
// rewriter's `resolvedCitations` grade tally (same tally
// `citations/grounding_summary.ts#buildGroundingSummary` computes — reused,
// never re-derived a second way) + `TurnCitationStream.hallucinationCount`.
// unavailable when the live rewriter did not run this turn (the regex
// fallback path carries no per-citation grade tier to report).
// ---------------------------------------------------------------------------

export const ReceiptEvidenceGradesSchema = z.object({
  status: z.enum(['measured', 'unavailable']),
  grade_counts: GroundingSummaryGradeCountsSchema.nullable(),
  hallucination_count: z.number().int().nonnegative().nullable(),
  unavailable_reason: z.string().nullable(),
})
export type ReceiptEvidenceGrades = z.infer<typeof ReceiptEvidenceGradesSchema>

// ---------------------------------------------------------------------------
// honest_gaps — the floor items this turn did NOT serve, each with its real,
// already-computed reason. Source: `WebCompletenessReceipt.empty` +
// `.dark` (vidhi/completeness_receipt.ts's own itemized, per-item honesty
// invariant — never a re-derived summary).
// ---------------------------------------------------------------------------

export const ReceiptHonestGapSchema = z.object({
  floor_item_id: z.string(),
  kind: z.enum(['empty', 'dark']),
  /** `empty_reason` for an empty item; a `cr_row`-citing note for a dark item. */
  reason: z.string(),
})
export type ReceiptHonestGap = z.infer<typeof ReceiptHonestGapSchema>

export const ReceiptHonestGapsSchema = z.object({
  status: z.enum(['measured', 'unavailable']),
  gaps: z.array(ReceiptHonestGapSchema).nullable(),
  unavailable_reason: z.string().nullable(),
})
export type ReceiptHonestGaps = z.infer<typeof ReceiptHonestGapsSchema>

// ---------------------------------------------------------------------------
// safety_decision — from G1-A's SafetyDecision object, by reference to its
// own decision_id (the FK into `pariprashna_safety_decisions`), plus the
// fields the reader-facing receipt needs inline. `enforced: false` is itself
// a MEASURED value (per SafetyDecision's own contract: "no safety question
// was asked this turn" is a real, distinct fact from "asked and clean") —
// only the total absence of a SafetyDecision object is `unavailable`.
// ---------------------------------------------------------------------------

export const ReceiptSafetyDecisionSchema = z.object({
  status: z.enum(['measured', 'unavailable']),
  decision_id: z.string().nullable(),
  enforced: z.boolean().nullable(),
  severity: z.string().nullable(),
  action: z.string().nullable(),
  classes_detected: z.array(z.string()).nullable(),
  review_id: z.string().nullable(),
  audit_written: z.boolean().nullable(),
  unavailable_reason: z.string().nullable(),
})
export type ReceiptSafetyDecision = z.infer<typeof ReceiptSafetyDecisionSchema>

// ---------------------------------------------------------------------------
// calibration_disclosure — did THIS turn's own retrieved evidence touch an
// L5 Mīmāṃsā calibration-bearing capability? Source: a deterministic scan of
// `validToolResults[].tool_name` against the registered L5 calibration tool
// names — always runs, so always measured (no unavailable branch: there is
// no state in which this detector cannot produce an answer). When nothing
// was consulted, the disclosure note is the CLAUDE.md §E structural-mode
// fact (L5 sealed in STRUCTURAL mode; calibration values fill in as
// prediction→outcome data accrues) — a fixed, doctrinally-sourced statement
// about the SYSTEM's current calibration state, never a computed claim
// about THIS reading's specific numbers (same convention
// `synthesis_stage.ts`'s `LENGTH_TIER_GUIDANCE` fixed strings already use).
// ---------------------------------------------------------------------------

export const ReceiptCalibrationDisclosureSchema = z.object({
  consulted: z.boolean(),
  consulted_tool_names: z.array(z.string()),
  disclosure_note: z.string(),
})
export type ReceiptCalibrationDisclosure = z.infer<typeof ReceiptCalibrationDisclosureSchema>

// ---------------------------------------------------------------------------
// prose_binding — ties the receipt's claims to the EXACT text the reader
// saw. Source: `ReadingPartsAssembler.committedBlocks` (block id, role,
// char count) + a sha256 of the turn's own `accumulatedText`. Optionally
// carries the G2-A semantic classification (`kind`/`role`) when
// `PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED` was on this turn AND the block was
// prose — reusing the SAME classification `reading_parts.ts#commitBlock`
// already computed for the wire event, never re-run a second time.
// ---------------------------------------------------------------------------

export const ReceiptProseBindingBlockSchema = z.object({
  block_id: z.string(),
  role: z.enum(['prose', 'thinking']),
  char_count: z.number().int().nonnegative(),
  /** G2-A `BlockClassification.kind`, when semantic blocks were on this turn. */
  semantic_kind: z.string().nullable(),
  /** G2-A `BlockClassification.role`, when semantic blocks were on this turn. */
  semantic_role: z.string().nullable(),
})
export type ReceiptProseBindingBlock = z.infer<typeof ReceiptProseBindingBlockSchema>

export const ReceiptProseBindingSchema = z.object({
  blocks: z.array(ReceiptProseBindingBlockSchema),
  accumulated_text_sha256: z.string(),
  accumulated_char_count: z.number().int().nonnegative(),
})
export type ReceiptProseBinding = z.infer<typeof ReceiptProseBindingSchema>

// ---------------------------------------------------------------------------
// provenance — WRAPS `computeTurnReceiptProvenance`'s own `TurnProvenanceStamp`
// (D-16, provenance/stamp.ts). This schema mirrors that interface's field
// NAMES for Zod validation; it never recomputes any of the five D-16 values
// — the assembler takes the already-computed stamp object as-is.
// ---------------------------------------------------------------------------

export const ReceiptProvenanceSchema = z.object({
  build_id: z.string().nullable(),
  priors_version: z.string(),
  formula_versions: z.object({ salience_formula_ver: z.string().nullable() }),
  ranking_config: z.object({ mode: z.string() }),
  now_context_date: z.string(),
  computed_at: z.string(),
})
export type ReceiptProvenance = z.infer<typeof ReceiptProvenanceSchema>

// ---------------------------------------------------------------------------
// The receipt.
// ---------------------------------------------------------------------------

export const ACHARYA_READING_RECEIPT_SCHEMA_VERSION = 1 as const

export const AcharyaReadingReceiptSchema = z.object({
  receipt_schema_version: z.literal(ACHARYA_READING_RECEIPT_SCHEMA_VERSION),
  turn_id: z.string(),
  conversation_id: z.string(),
  chart_id: z.string(),
  generated_at: z.string(),
  coverage: ReceiptCoverageSchema,
  facts_consumed: z.array(ReceiptFactRefSchema),
  derivation_chains: z.array(ReceiptDerivationLinkSchema),
  cross_domain: ReceiptCrossDomainSchema,
  evidence_grades: ReceiptEvidenceGradesSchema,
  honest_gaps: ReceiptHonestGapsSchema,
  safety_decision: ReceiptSafetyDecisionSchema,
  calibration_disclosure: ReceiptCalibrationDisclosureSchema,
  prose_binding: ReceiptProseBindingSchema,
  provenance: ReceiptProvenanceSchema,
  /** sha256 hex of the canonical JSON of every field above (this field excluded). */
  receipt_hash: z.string(),
})
export type AcharyaReadingReceipt = z.infer<typeof AcharyaReadingReceiptSchema>
