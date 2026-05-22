import 'server-only'

/**
 * tool_loop_metrics.ts — E-S9 R11.E
 *
 * Observatory-side aggregation for agentic tool-loop iteration telemetry.
 *
 * Per-iteration records emitted by agentic_loop.ts are picked up by the
 * Cloud Run log sink (marsys_event_type: 'tool_loop_iteration') → BigQuery.
 *
 * This module provides:
 * 1. Typed interfaces for the telemetry records.
 * 2. Summary aggregation helpers for the ToolLoopMetricsTile (E-S9 UI).
 * 3. Cost-per-turn breakdown by iteration (sum of per-iteration usage).
 */

// ---------------------------------------------------------------------------
// Telemetry record (mirrors LoopIterationTelemetry in agentic_loop.ts)
// ---------------------------------------------------------------------------

export interface ToolLoopIterationRecord {
  /** Loop iteration number (1-indexed in log; 0-indexed in state). */
  iteration: number
  providerId: string
  conversationId?: string
  inputTokens: number
  outputTokens: number
  cacheReadTokens: number
  cacheCreationTokens: number
  reasoningTokens: number
  toolCallCount: number
  toolErrorCount: number
  /** The stop/finish reason that triggered this iteration. */
  terminationSignal: string | null
  /** ISO-8601 timestamp. */
  completedAt: string
}

// ---------------------------------------------------------------------------
// Aggregated summary for a single turn (all iterations combined)
// ---------------------------------------------------------------------------

export interface ToolLoopTurnSummary {
  conversationId?: string
  providerId: string
  totalIterations: number
  totalInputTokens: number
  totalOutputTokens: number
  totalCacheReadTokens: number
  totalCacheCreationTokens: number
  totalReasoningTokens: number
  totalToolCalls: number
  totalToolErrors: number
  /** True if the loop hit MAX_ITERATIONS (AgenticLoopCapExceeded). */
  capExceeded: boolean
  /** ISO-8601 of the first iteration start. */
  startedAt?: string
  /** ISO-8601 of the last iteration end. */
  completedAt?: string
}

/**
 * Aggregates an array of per-iteration records into a single turn summary.
 */
export function aggregateTurnSummary(
  records: ToolLoopIterationRecord[],
  capExceeded = false,
): ToolLoopTurnSummary | null {
  if (!records.length) return null

  const first = records[0]
  const last = records[records.length - 1]

  return {
    conversationId: first.conversationId,
    providerId: first.providerId,
    totalIterations: records.length,
    totalInputTokens: records.reduce((s, r) => s + r.inputTokens, 0),
    totalOutputTokens: records.reduce((s, r) => s + r.outputTokens, 0),
    totalCacheReadTokens: records.reduce((s, r) => s + r.cacheReadTokens, 0),
    totalCacheCreationTokens: records.reduce((s, r) => s + r.cacheCreationTokens, 0),
    totalReasoningTokens: records.reduce((s, r) => s + r.reasoningTokens, 0),
    totalToolCalls: records.reduce((s, r) => s + r.toolCallCount, 0),
    totalToolErrors: records.reduce((s, r) => s + r.toolErrorCount, 0),
    capExceeded,
    startedAt: first.completedAt,  // proxy; real start would require iteration start timestamps
    completedAt: last.completedAt,
  }
}

// ---------------------------------------------------------------------------
// Cost breakdown per iteration
// ---------------------------------------------------------------------------

/**
 * Rough token cost breakdown per iteration.
 * Actual USD values depend on provider + model pricing; this uses normalized
 * "token units" scaled to provider-specific prices downstream.
 */
export interface IterationCostBreakdown {
  iteration: number
  inputCostUnits: number   // inputTokens (standard cost)
  outputCostUnits: number  // outputTokens (standard cost)
  cacheReadSavingUnits: number   // cacheReadTokens * (1 - 0.1) = 0.9x saving
  cacheWriteExtraUnits: number   // cacheCreationTokens * 0.25 extra cost
  netCostUnits: number     // inputCostUnits + outputCostUnits - cacheReadSavingUnits + cacheWriteExtraUnits
}

/**
 * Computes cost breakdown per iteration from the telemetry records.
 * Uses Anthropic cost model as the reference (0.1x cache read, 1.25x cache write).
 */
export function computeIterationCostBreakdown(
  records: ToolLoopIterationRecord[],
): IterationCostBreakdown[] {
  return records.map(r => {
    const inputCostUnits = r.inputTokens
    const outputCostUnits = r.outputTokens
    const cacheReadSavingUnits = r.cacheReadTokens * 0.9
    const cacheWriteExtraUnits = r.cacheCreationTokens * 0.25
    const netCostUnits =
      inputCostUnits + outputCostUnits - cacheReadSavingUnits + cacheWriteExtraUnits

    return {
      iteration: r.iteration,
      inputCostUnits,
      outputCostUnits,
      cacheReadSavingUnits,
      cacheWriteExtraUnits,
      netCostUnits,
    }
  })
}

// ---------------------------------------------------------------------------
// Log sink — emit aggregated summary
// ---------------------------------------------------------------------------

/**
 * Emits a ToolLoopTurnSummary to the structured log.
 * Tagged with marsys_event_type: 'tool_loop_turn_summary' for BigQuery routing.
 */
export function emitToolLoopTurnSummary(summary: ToolLoopTurnSummary): void {
  console.log(
    JSON.stringify({
      marsys_event_type: 'tool_loop_turn_summary',
      ...summary,
    }),
  )
}
