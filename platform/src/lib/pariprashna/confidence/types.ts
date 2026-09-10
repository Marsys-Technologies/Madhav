/**
 * pariprashna/confidence/types.ts — the PPR-03 five-type confidence enum
 * (lane G3-C, roadmap G3-C / PPR-03).
 *
 * PARIPRASHNA_ARCHITECTURE_v1_0.md PPR-03 (line 148): "Every confidence MUST
 * be typed: deterministic_fact · structural_prior · classical_prior ·
 * empirically_calibrated · unresolved. `empirically_calibrated` language MUST
 * NOT be used below a passing activation gate; a quantity MUST NOT be served
 * with more precision than its sample supports (T-8). New engine layers
 * surface at their earned tier only."
 *
 * Each member maps to a REAL, distinguishable source in this codebase — see
 * `type_claim.ts` for the typing function and its per-branch source citation,
 * and each member's own doc comment below for the short version:
 *
 *   - `deterministic_fact`      — an L1 Gaṇita chart_facts citation (citation
 *                                  `layer === 'L1'` — `citation_data_part.ts`'s
 *                                  own `layer: z.enum(['L1', 'L2.5'])`).
 *   - `structural_prior`        — an L2.5 MSR/Bodha structural signal citation
 *                                  (a yoga/dignity/structural computation —
 *                                  citation `layer === 'L2.5'`).
 *   - `classical_prior`         — a turn that consulted a real classical-text
 *                                  capability (`CLASSICAL_PRIOR_BEARING_TOOL_NAMES`
 *                                  in `type_claim.ts`, e.g.
 *                                  `classical_attribution_lookup`,
 *                                  `read_sutravali_rule`).
 *   - `empirically_calibrated`  — ONLY when a real L5 Mīmāṃsā calibration tool
 *                                  was consulted AND `activation_gate.ts`'s
 *                                  real sample-size gate is open. L5 is sealed
 *                                  in STRUCTURAL mode today (CLAUDE.md §E) —
 *                                  the gate is proven closed under today's
 *                                  real conditions (see
 *                                  `__tests__/activation_gate.test.ts`).
 *   - `unresolved`               — the honest fallback: none of the above
 *                                  detectors fired. Never a fabricated type.
 */

import { z } from 'zod'

export const CONFIDENCE_TYPES = [
  'deterministic_fact',
  'structural_prior',
  'classical_prior',
  'empirically_calibrated',
  'unresolved',
] as const

export const ConfidenceTypeSchema = z.enum(CONFIDENCE_TYPES)
export type ConfidenceType = z.infer<typeof ConfidenceTypeSchema>

/**
 * One claim's typed confidence — a fact/citation reference plus the type
 * assigned to it, and a machine-readable `basis` naming WHICH real detector
 * fired (never a free-text narrative — see §N.7 item 4: a flag needs a real
 * detector or it is null).
 */
export const TypedConfidenceEntrySchema = z.object({
  /** The signal/fact reference this typing applies to (same token as `facts_consumed[].ref`). */
  ref: z.string(),
  /** The citation's own layer tag, carried through verbatim (never re-derived). */
  layer: z.string(),
  confidence_type: ConfidenceTypeSchema,
  /** Which real detector assigned this type — a closed vocabulary, see `type_claim.ts#TYPING_BASIS`. */
  basis: z.string(),
})
export type TypedConfidenceEntry = z.infer<typeof TypedConfidenceEntrySchema>
