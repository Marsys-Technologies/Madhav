/**
 * citations/floor_gate.ts — PB-2 (SMṚTI) lane M-4.
 *
 * Structural weakness gate: maps a resolved citation's grade onto a
 * `FloorItemObservation` (`platform/src/lib/vidhi/completeness_receipt.ts`) —
 * the per-floor-item "did this actually satisfy the B.11 acharya floor this
 * turn" signal that `emitCompletenessReceipt` consumes to build the served /
 * empty / dark completeness receipt.
 *
 * WHY THIS EXISTS: lane M-4 adds the `prior_reading` citation grade (recalled
 * cross-thread conclusions — see `../recall/`). §I B.11 + the acharya-floor
 * completeness receipt must NEVER treat a recalled prior-thread conclusion as
 * equivalent to live-turn evidence for THIS turn's floor — a plan that only
 * "covered" a floor item by citing an old conversation must still report that
 * item honestly (`empty`, never `served`).
 *
 * The enforcement here is STRUCTURAL, not a documentation promise:
 * `deriveFloorObservation` has NO parameter, override, or code path that can
 * produce `status: 'served'` for grade `prior_reading` (or `unverified`,
 * which is excluded for the same "not live evidence" reason — a hallucinated
 * sentinel obviously cannot satisfy a floor item either). Every branch that
 * matches those two grades returns `status: 'empty'` unconditionally.
 * `floor_gate.test.ts` proves this two ways: (a) a property-style sweep of
 * `prior_reading` inputs across many floor_item_ids/sources, asserting every
 * single output is `empty`; and (b) an end-to-end proof that runs the derived
 * observations through the REAL `emitCompletenessReceipt` against a REAL
 * compiled vidhi contract and asserts `coverage.served === 0`.
 */
import type { CitationGrade } from './types'
import type { FloorItemObservation } from '../../vidhi/completeness_receipt'

/**
 * Grades that MAY satisfy a floor item (mark it `served`) when a citation is
 * offered as evidence that a floor primitive was actually consulted this
 * turn. `unverified` and `prior_reading` are excluded BY CONSTRUCTION — see
 * the branches below, neither of which has a code path returning `served`.
 */
const FLOOR_SATISFYING_GRADES: ReadonlySet<CitationGrade> = new Set([
  'primary',
  'supporting',
  'contextual',
])

export interface FloorObservationInput {
  /** The compiled floor item (`CompiledFloorItem.primitive_id`) this citation is offered against. */
  readonly floor_item_id: string
  /** The citation's verification grade. */
  readonly grade: CitationGrade
  /** Tool/source that produced the evidence — reported on a `served` observation's `source`. */
  readonly source: string
}

/**
 * Derive a `FloorItemObservation` from a resolved citation's grade.
 *
 * - `primary` / `supporting` / `contextual` → `served` (this turn's live
 *   evidence actually grounds the floor item).
 * - `prior_reading` → ALWAYS `empty`, with an honest reason naming exactly
 *   why: recalled cross-thread conclusions are corroborative context, never
 *   live-turn evidence. No caller can flip this — there is no parameter on
 *   `FloorObservationInput` that changes the outcome for this grade.
 * - `unverified` → ALWAYS `empty` (a hallucination-flagged sentinel cannot
 *   satisfy a floor item either).
 */
export function deriveFloorObservation(input: FloorObservationInput): FloorItemObservation {
  if (FLOOR_SATISFYING_GRADES.has(input.grade)) {
    return { floor_item_id: input.floor_item_id, status: 'served', source: input.source }
  }

  if (input.grade === 'prior_reading') {
    return {
      floor_item_id: input.floor_item_id,
      status: 'empty',
      empty_reason:
        'prior_reading citation cannot satisfy the B.11 acharya floor — recalled cross-thread ' +
        `conclusions are corroborative context only, never live-turn evidence (source=${input.source})`,
    }
  }

  // unverified — hallucination-flagged sentinel, also cannot satisfy the floor.
  return {
    floor_item_id: input.floor_item_id,
    status: 'empty',
    empty_reason: `citation grade '${input.grade}' does not satisfy the floor (source=${input.source})`,
  }
}

/** Convenience batch form — one observation per input, same rules as `deriveFloorObservation`. */
export function deriveFloorObservations(
  inputs: readonly FloorObservationInput[],
): FloorItemObservation[] {
  return inputs.map(deriveFloorObservation)
}
