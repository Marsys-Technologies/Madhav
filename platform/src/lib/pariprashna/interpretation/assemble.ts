/**
 * pariprashna/interpretation/assemble.ts — glue: detect -> generate ->
 * `ReceiptInterpretationSets` (lane G3-B, PPR-02).
 *
 * The sole caller is `pipeline/persistence_stage.ts`, gated behind
 * `isInterpretationSetsEnabled()` (and, transitively, G3-A's own receipt
 * flag — see `feature_flags.ts`'s declaration comment). Everything below is
 * pure with respect to I/O EXCEPT the one real LLM call inside
 * `generateInterpretationSets` (`./worker.ts`) — no DB read of its own.
 */
import 'server-only'

import {
  detectSignificantJudgments,
  type DetectSignificantJudgmentsArgs,
} from './detect'
import { generateInterpretationSets, type InterpretationLlmCaller } from './worker'
import { INTERPRETATION_SETS_SCHEMA_VERSION, type ReceiptInterpretationSets } from './schema'
import {
  computeInterpretationSetsMetrics,
  logInterpretationSetsMetrics,
} from '@/lib/pariprashna/observability/interpretation_metrics'

/**
 * Per-turn cost/latency bound on how many SIGNIFICANT judgments get a real
 * structured-output call. A REAL, disclosed cap — never a silent drop:
 * anything past the cap is counted in `truncated_count` on the persisted
 * receipt field, not dropped without a trace (§N.6/§N.8).
 */
export const MAX_SIGNIFICANT_JUDGMENTS_PER_TURN = 8

/** Priority order when truncating to the cap — categories more likely to be
 *  load-bearing for the reader (a verdict, a detected prediction) go first;
 *  the more numerous, finer-grained `time_indexed` category is truncated
 *  first when a turn has more significant judgments than the cap allows. */
const CATEGORY_PRIORITY: Readonly<Record<string, number>> = {
  domain_verdict: 0,
  prediction_detected: 1,
  remedial: 2,
  rules_in_tension: 3,
  time_indexed: 4,
}

export interface AssembleInterpretationSetsArgs extends DetectSignificantJudgmentsArgs {
  turnId: string
  /**
   * G3BC hardening defect 1. Real state of `PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED`
   * (G2-A/G3-A's flag) THIS turn — required, not defaulted, so every call
   * site must be explicit about a real dependency this module's own
   * `detect.ts` header already documents but `feature_flags.ts` never
   * declared: 4 of the 5 SIGNIFICANT-judgment categories (domain_verdict,
   * rules_in_tension, remedial, time_indexed) classify from
   * `OpenBlock.semantic`, which is `undefined` when semantic blocks are off.
   * `false` here means `detectSignificantJudgments` would structurally find
   * (at most) only `prediction_detected` hits — a receipt that reported
   * `status: 'measured'` with a low/zero `detected_count` in that state would
   * read as "genuinely no significant judgments this turn" when the real
   * story is "the detector was structurally blind for 4/5 categories". This
   * function reports the honest `unavailable` state instead — see
   * `SEMANTIC_BLOCKS_DISABLED_REASON` below.
   */
  semanticBlocksEnabled: boolean
  /** Injectable for tests — see `worker.ts#InterpretationLlmCaller`. */
  caller?: InterpretationLlmCaller
}

/** Exported so callers/tests can assert on the exact reason string without
 *  re-typing it (and so `persistence_stage.ts`'s error paths can reuse it). */
export const SEMANTIC_BLOCKS_DISABLED_REASON =
  'PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED was off this turn — 4 of the 5 significant-judgment ' +
  'categories (domain_verdict, rules_in_tension, remedial, time_indexed) classify from ' +
  'OpenBlock.semantic, which detect.ts cannot read without semantic blocks on; only ' +
  'prediction_detected is structurally independent of this flag, so the field reports ' +
  'unavailable as a whole rather than a partial/misleading detected_count'

/** The default "the field was never even attempted this turn" value —
 *  used by `persistence_stage.ts` when the flag is off, and by
 *  `receipt/assemble.ts` as the field's own honest default when the caller
 *  supplies nothing at all. */
export function unavailableInterpretationSets(reason: string): ReceiptInterpretationSets {
  return {
    status: 'unavailable',
    interpretation_sets_schema_version: null,
    detected_count: null,
    covered_count: null,
    truncated_count: null,
    waived_count: null,
    sets: null,
    unavailable_reason: reason,
  }
}

export async function assembleInterpretationSets(
  args: AssembleInterpretationSetsArgs,
): Promise<ReceiptInterpretationSets> {
  if (!args.semanticBlocksEnabled) {
    return unavailableInterpretationSets(SEMANTIC_BLOCKS_DISABLED_REASON)
  }

  const detected = detectSignificantJudgments(args)
  const ordered = [...detected].sort(
    (a, b) => (CATEGORY_PRIORITY[a.category] ?? 99) - (CATEGORY_PRIORITY[b.category] ?? 99),
  )
  const toProcess = ordered.slice(0, MAX_SIGNIFICANT_JUDGMENTS_PER_TURN)
  const truncatedCount = ordered.length - toProcess.length

  const sets = await generateInterpretationSets(toProcess, args.caller, args.turnId)
  const metrics = computeInterpretationSetsMetrics(sets)
  logInterpretationSetsMetrics({ turnId: args.turnId, metrics, truncatedCount })

  return {
    status: 'measured',
    interpretation_sets_schema_version: INTERPRETATION_SETS_SCHEMA_VERSION,
    detected_count: ordered.length,
    covered_count: sets.length,
    truncated_count: truncatedCount,
    waived_count: metrics.waived_count,
    sets,
    unavailable_reason: null,
  }
}
