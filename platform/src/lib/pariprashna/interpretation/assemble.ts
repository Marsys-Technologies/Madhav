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
  /** Injectable for tests — see `worker.ts#InterpretationLlmCaller`. */
  caller?: InterpretationLlmCaller
}

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
  const detected = detectSignificantJudgments(args)
  const ordered = [...detected].sort(
    (a, b) => (CATEGORY_PRIORITY[a.category] ?? 99) - (CATEGORY_PRIORITY[b.category] ?? 99),
  )
  const toProcess = ordered.slice(0, MAX_SIGNIFICANT_JUDGMENTS_PER_TURN)
  const truncatedCount = ordered.length - toProcess.length

  const sets = await generateInterpretationSets(toProcess, args.caller)
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
