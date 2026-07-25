/**
 * evals/k2/types.ts — shared types for Lane K2 (consumption metric + standing battery upgrades).
 *
 * Elevation Campaign v2.1, Stream γ (PŪRṆA), Lane K2 · EL-04, 05, 06, 09, 10, 22, 23, 60a.
 *
 * These types describe the harness-run transcript format already established by Lane Ω7
 * (evals/omega7/harness_runs/*.json — verbatim tool-call log: {tool, arguments, result_raw}),
 * so K2's graders are drop-in usable against any captured transcript from the sealed
 * evaluator harness (SEALED_EVALUATOR_HARNESS_v1_0.md, FROZEN) without re-deriving a format.
 */

/** One tool invocation as captured verbatim by a sealed-harness consumer sub-agent. */
export interface TranscriptCall {
  tool: string
  arguments: Record<string, unknown>
  /** Raw JSON-stringified (or plain text) tool result, exactly as returned. */
  result_raw: string
  /** Optional wall-clock capture, when the consumer records it (§6.1 experience telemetry). */
  t_start_ms?: number
  t_end_ms?: number
  /** Optional error/timeout marker (§6.1 tool_errors_n / retry_recoveries_n). */
  error?: string
  retried?: boolean
}

/**
 * A full harness run. Accepts either the bare Ω7 array-of-calls shape (no final_answer field
 * captured) or the richer object shape with a final_answer string — normalizeTranscript()
 * below handles both so no K2 grader needs two code paths.
 */
export type RawTranscript =
  | TranscriptCall[]
  | {
      calls: TranscriptCall[]
      final_answer?: string
      query?: string
      domain?: string
      chart_id?: string
      t_query_posed_ms?: number
      t_answer_complete_ms?: number
      t_first_signal_ms?: number
      followups_needed?: boolean
      friction_notes?: string
    }

export interface NormalizedTranscript {
  calls: TranscriptCall[]
  final_answer: string
  query?: string
  domain?: string
  chart_id?: string
  t_query_posed_ms?: number
  t_answer_complete_ms?: number
  t_first_signal_ms?: number
  followups_needed?: boolean
  friction_notes?: string
}

/** One row of the Ω3 COMPLETENESS_ACCOUNTING_<domain>_<chart8>_v1_0.json (contract C7). */
export interface AccountingRow {
  concept_id: string
  chart_id: string
  domain: string
  state: 'served' | 'empty_for_this_chart' | 'not_computed_globally' | 'superseded_by_aggregate' | 'excluded_by_named_rule'
  evidence?: {
    tool?: string
    fact_ids?: string[]
    [k: string]: unknown
  }
}

export interface AccountingFile {
  artifact: 'COMPLETENESS_ACCOUNTING'
  chart_id: string
  domain: string
  state_counts: Record<string, number>
  slice_size: number
  rows: AccountingRow[]
  [k: string]: unknown
}
