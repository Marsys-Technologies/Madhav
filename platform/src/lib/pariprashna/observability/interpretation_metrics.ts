/**
 * pariprashna/observability/interpretation_metrics.ts — the REAL, measured
 * waiver rate (lane G3-B, PPR-02).
 *
 * PPR-02: "or an explicit waiver whose rate is monitored." Same discipline
 * `observability/turn_metrics.ts` (lane P2-E) already established: a pure,
 * in-memory computation over REAL per-turn data (never a hardcoded 0), plus
 * an ALWAYS-ON server-log emission in the same
 * `console.log('[pariprashna/observability] ...', JSON.stringify(...))`
 * shape `synthesis_stage.ts`'s `finalizeObservability` already uses — SERVER
 * LOG ONLY, deliberately never an `em.flag` (it never touches the SSE wire;
 * see that module's own header for why: wire-protocol discipline plus this
 * content is inherently a per-turn count, not a live-stream concern).
 *
 * The MONITORED rate is two things, both real:
 *   1. This per-turn log line (`interpretation_sets_metrics`), aggregable by
 *      whatever log-based monitoring already reads `synthesis_turn_metrics`.
 *   2. The counts this module computes are ALSO exactly the counts
 *      `interpretation/assemble.ts` persists onto
 *      `AcharyaReadingReceipt.interpretation_sets` (`covered_count`,
 *      `waived_count`) — a real, DB-queryable, aggregable-across-turns
 *      signal via `conversation_messages.metadata_json`, with NO new
 *      migration (this lane's `must_not_touch` forbids one; see
 *      `receipt/store.ts`'s own additive-jsonb convention).
 */

export interface InterpretationSetsMetrics {
  /** Judgments actually sent to the structured-output call this turn. */
  covered_count: number
  /** Judgments that got a real >=3-candidate set. */
  generated_count: number
  /** Judgments that got an explicit waiver instead. */
  waived_count: number
  /** `waived_count / covered_count`, or `null` when `covered_count === 0`
   *  (an honest "no rate exists yet" rather than a fabricated 0/0 → 0). */
  waiver_rate: number | null
}

/** Pure — computed from the SAME entries persisted to the receipt, never a
 *  second, independently-tracked (and therefore driftable) count. */
export function computeInterpretationSetsMetrics(
  entries: ReadonlyArray<{ status: 'generated' | 'waived' }>,
): InterpretationSetsMetrics {
  const covered_count = entries.length
  const waived_count = entries.filter((e) => e.status === 'waived').length
  const generated_count = covered_count - waived_count
  return {
    covered_count,
    generated_count,
    waived_count,
    waiver_rate: covered_count > 0 ? waived_count / covered_count : null,
  }
}

/** ALWAYS-ON, real per-turn summary — SERVER LOG ONLY. See module header for
 *  why this never becomes an `em.flag`. */
export function logInterpretationSetsMetrics(args: {
  turnId: string
  metrics: InterpretationSetsMetrics
  truncatedCount: number
}): void {
  console.log(
    '[pariprashna/observability] interpretation_sets_metrics',
    JSON.stringify({
      turn_id: args.turnId,
      covered_count: args.metrics.covered_count,
      generated_count: args.metrics.generated_count,
      waived_count: args.metrics.waived_count,
      waiver_rate: args.metrics.waiver_rate,
      truncated_count: args.truncatedCount,
    }),
  )
}
