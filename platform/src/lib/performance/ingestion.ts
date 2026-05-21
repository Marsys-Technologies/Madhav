import 'server-only'

import { query } from '@/lib/db/client'
import { telemetry } from '@/lib/telemetry/index'
import type { QueryPlan, RichQueryPlan } from '@/lib/router/types'
import type { ToolBundle } from '@/lib/retrieve/types'
import type { ValidationResult } from '@/lib/validators/types'
import type { SynthesisAuditEvent } from '@/lib/synthesis/types'
import { summarize } from '@/lib/validators/index'

import { detectB10Violation, detectB11Violation, parseCitations } from './compliance'

/**
 * Gate I Performance — ingestion writers.
 *
 * Brief: CLAUDECODE_BRIEF.md (GATE-I-PERF-CMD-001), W2 + W3.
 *
 * All writers are non-throwing in the consume path: failures are logged
 * to telemetry and swallowed so a DB outage never blocks a user response.
 * Eval writers DO propagate errors because the eval script can decide
 * how to handle them.
 */

// PERF-S1: per-tool top-score capture now covers ALL tools, not just vector_search.
// The original RETRIEVAL_TOP_SCORE_TOOLS set is removed; see retrieval_scores ingestion below.

// ─────────────────────────────────────────────────────────────────────────────
// Consume-query writer (W2)
// ─────────────────────────────────────────────────────────────────────────────

export interface ConsumePerformanceInput {
  query_id: string
  query_plan: QueryPlan | RichQueryPlan
  tool_results: ToolBundle[]
  validator_results: ValidationResult[]
  disclosure_tier: string
  synthesis_event: SynthesisAuditEvent
  /**
   * Bundle-assembly stage latency in milliseconds (PERF-S1, fix c).
   * Available in route.ts as `composeBundleMs` but not yet threaded through the
   * audit-consumer path — the audit consumer is called from a synthesis event
   * callback that does not receive stage timings.
   *
   * TODO (PERF-S2 candidate): Thread composeBundleMs from route.ts into the
   * AuditConsumerContext so it is available here. Until then, callers that do
   * not have access to the value should omit this field; the column will be null.
   */
  compose_bundle_latency_ms?: number | null
}

/**
 * Insert one performance_queries row for a successful consume run.
 *
 * Fire-and-forget contract: never throws; failures are reported via telemetry.
 * The audit_event_id is set to the audit_log row id when an audit_log row
 * exists for this query_id; otherwise null. The lookup is best-effort.
 */
export async function writeConsumePerformanceRow(input: ConsumePerformanceInput): Promise<void> {
  try {
    const { query_plan, tool_results, validator_results, synthesis_event } = input

    const queryClass = query_plan.query_class
    const planType = query_plan.expected_output_shape
    const toolsSelected = tool_results.map((t) => t.tool_name)
    const plannerConfidence = query_plan.router_confidence ?? null

    const validatorAgg = summarize(validator_results ?? [])
    const validatorVerdict = validatorAgg.overall // 'pass' | 'warn' | 'fail'

    const planningLatencyMs = (query_plan as RichQueryPlan).planning_latency_ms ?? null
    const retrievalLatencyMs = tool_results.reduce((s, r) => s + (r.latency_ms ?? 0), 0)
    const synthesisLatencyMs =
      Date.parse(synthesis_event.finished_at) - Date.parse(synthesis_event.started_at)
    // PERF-S1 fix (d): preserve null instead of silently coercing to 0.
    // latencyComplete=false signals that the total is unreliable due to bad timestamps.
    const synthesisLatencyValid = Number.isFinite(synthesisLatencyMs)
    const totalLatencyMs = synthesisLatencyValid
      ? (planningLatencyMs ?? 0) + retrievalLatencyMs + synthesisLatencyMs
      : null
    const latencyComplete = synthesisLatencyValid

    const finalOutput = synthesis_event.final_output ?? ''
    const citationObjects = parseCitations(finalOutput)
    const citationCount = citationObjects.length
    const citationsPresent = citationCount > 0

    const synthesisStatus =
      synthesis_event.finish_reason === 'stop' || synthesis_event.finish_reason === 'end_turn'
        ? 'success'
        : synthesis_event.finish_reason === 'tool-calls'
        ? 'partial'
        : 'failure'

    const retrievalHit = tool_results.some(
      (t) =>
        t.results.length > 0 &&
        (t.results[0].significance ?? t.results[0].confidence ?? 0) > 0
    )

    // PERF-S1 fix (b): capture per-tool top-1 score across ALL tools, not just vector_search.
    // retrieval_scores is a JSON object mapping tool_name → top-1 score.
    // retrieval_score_top1 is kept for backwards compatibility (schema column remains).
    const retrievalScoresMap: Record<string, number> = {}
    let retrievalScoreTop1: number | null = null
    for (const t of tool_results) {
      const top = t.results[0]
      if (!top) continue
      const score = top.significance ?? top.confidence ?? null
      if (score === null) continue
      retrievalScoresMap[t.tool_name] = score
      if (retrievalScoreTop1 === null || score > retrievalScoreTop1) retrievalScoreTop1 = score
    }
    const retrievalScores = Object.keys(retrievalScoresMap).length > 0
      ? JSON.stringify(retrievalScoresMap)
      : null

    const b10 = detectB10Violation({ synthesisText: finalOutput, citationObjects })
    const b11 = detectB11Violation({ toolResults: tool_results })

    const isPrediction =
      queryClass === 'predictive' ||
      query_plan.expected_output_shape === 'time_indexed_prediction'

    // Best-effort lookup of audit_log.id. If the row hasn't been written yet
    // (writeAuditLog is also fire-and-forget), audit_event_id stays null.
    let auditEventId: string | null = null
    try {
      const r = await query<{ id: string }>(
        'SELECT id FROM audit_log WHERE query_id = $1 ORDER BY created_at DESC LIMIT 1',
        [input.query_id]
      )
      auditEventId = r.rows[0]?.id ?? null
    } catch {
      auditEventId = null
    }

    await query(
      `INSERT INTO performance_queries (
        audit_event_id, eval_run_id, source, query_text, query_class, plan_type,
        plan_tools_selected, planner_confidence,
        latency_planner_ms, latency_retrieval_ms, latency_synthesis_ms, latency_total_ms,
        citations_present, citation_count, synthesis_status, validator_verdict, disclosure_tier,
        b10_violation, b11_violation, retrieval_hit, retrieval_score_top1,
        plan_accuracy_label, plan_accuracy_source, is_prediction, prediction_outcome_state,
        retrieval_scores, compose_bundle_latency_ms, latency_complete
      ) VALUES (
        $1, NULL, 'consume', $2, $3, $4,
        $5, $6,
        $7, $8, $9, $10,
        $11, $12, $13, $14, $15,
        $16, $17, $18, $19,
        'unjudged', NULL, $20, $21,
        $22, $23, $24
      )`,
      [
        auditEventId,                                          // $1
        input.query_plan.query_text,                           // $2
        queryClass,                                            // $3
        planType,                                              // $4
        JSON.stringify(toolsSelected),                         // $5
        plannerConfidence,                                     // $6
        planningLatencyMs,                                     // $7
        retrievalLatencyMs,                                    // $8
        synthesisLatencyValid ? synthesisLatencyMs : null,     // $9
        totalLatencyMs,                                        // $10 (null when latency incomplete)
        citationsPresent,                                      // $11
        citationCount,                                         // $12
        synthesisStatus,                                       // $13
        validatorVerdict,                                      // $14
        input.disclosure_tier,                                 // $15
        b10,                                                   // $16
        b11,                                                   // $17
        retrievalHit,                                          // $18
        retrievalScoreTop1,                                    // $19
        isPrediction,                                          // $20
        isPrediction ? 'pending' : 'n_a',                     // $21
        retrievalScores,                                       // $22 (PERF-S1 fix b)
        input.compose_bundle_latency_ms ?? null,               // $23 (PERF-S1 fix c)
        latencyComplete,                                       // $24 (PERF-S1 fix d)
      ]
    )
  } catch (err) {
    telemetry.recordError(
      'performance_writer',
      'consume_write_failed',
      err instanceof Error ? err : new Error(String(err))
    )
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Eval-script writers (W3)
// ─────────────────────────────────────────────────────────────────────────────

export interface EvalRunMeta {
  golden_set_version: string
  planner_prompt_version?: string
  synthesis_prompt_version?: string
  triggered_by: string
}

export interface EvalPerformanceRow {
  query_id: string
  query_text: string
  query_class: string | null
  plan_type: string | null
  plan_tools_selected: string[]
  planner_confidence: number | null
  latency_planner_ms: number | null
  latency_retrieval_ms: number | null
  latency_synthesis_ms: number | null
  latency_total_ms: number | null
  citations_present: boolean
  citation_count: number
  synthesis_status: 'success' | 'failure' | 'partial'
  validator_verdict: string | null
  disclosure_tier: string | null
  b10_violation: boolean
  b11_violation: boolean
  retrieval_hit: boolean
  retrieval_score_top1: number | null
  plan_accuracy_label: 'correct' | 'wrong' | 'ambiguous'
  is_prediction: boolean
}

export interface EvalRunAggregates {
  finishedAt?: Date | string
  queryCount: number
  recall: number | null
  precision: number | null
  citationRate: number | null
  avgLatencyMs: number | null
  synthesisPassRate: number | null
  retrievalHitRate: number | null
  b10ComplianceRate: number | null
  b11ComplianceRate: number | null
  notes?: string
}

/** Begin an eval run; returns the new run id. */
export async function writeEvalRun(meta: EvalRunMeta): Promise<{ runId: string }> {
  const r = await query<{ id: string }>(
    `INSERT INTO eval_runs (
      golden_set_version, planner_prompt_version, synthesis_prompt_version, triggered_by
    ) VALUES ($1, $2, $3, $4) RETURNING id`,
    [
      meta.golden_set_version,
      meta.planner_prompt_version ?? null,
      meta.synthesis_prompt_version ?? null,
      meta.triggered_by,
    ]
  )
  return { runId: r.rows[0].id }
}

/** Append one performance_queries row tagged source='eval'. */
export async function writeEvalPerformanceRow(
  runId: string,
  row: EvalPerformanceRow
): Promise<void> {
  await query(
    `INSERT INTO performance_queries (
      audit_event_id, eval_run_id, source, query_text, query_class, plan_type,
      plan_tools_selected, planner_confidence,
      latency_planner_ms, latency_retrieval_ms, latency_synthesis_ms, latency_total_ms,
      citations_present, citation_count, synthesis_status, validator_verdict, disclosure_tier,
      b10_violation, b11_violation, retrieval_hit, retrieval_score_top1,
      plan_accuracy_label, plan_accuracy_source, is_prediction, prediction_outcome_state
    ) VALUES (
      NULL, $1, 'eval', $2, $3, $4,
      $5, $6,
      $7, $8, $9, $10,
      $11, $12, $13, $14, $15,
      $16, $17, $18, $19,
      $20, 'golden', $21, $22
    )`,
    [
      runId,
      row.query_text,
      row.query_class,
      row.plan_type,
      JSON.stringify(row.plan_tools_selected),
      row.planner_confidence,
      row.latency_planner_ms,
      row.latency_retrieval_ms,
      row.latency_synthesis_ms,
      row.latency_total_ms,
      row.citations_present,
      row.citation_count,
      row.synthesis_status,
      row.validator_verdict,
      row.disclosure_tier,
      row.b10_violation,
      row.b11_violation,
      row.retrieval_hit,
      row.retrieval_score_top1,
      row.plan_accuracy_label,
      row.is_prediction,
      row.is_prediction ? 'pending' : 'n_a',
    ]
  )
}

/** Close out an eval run with aggregate metrics. */
export async function finalizeEvalRun(runId: string, agg: EvalRunAggregates): Promise<void> {
  const finishedAt =
    agg.finishedAt instanceof Date
      ? agg.finishedAt.toISOString()
      : agg.finishedAt ?? new Date().toISOString()

  await query(
    `UPDATE eval_runs SET
      finished_at = $2,
      query_count = $3,
      plan_accuracy_recall = $4,
      plan_accuracy_precision = $5,
      citation_rate = $6,
      avg_latency_total_ms = $7,
      synthesis_pass_rate = $8,
      retrieval_hit_rate = $9,
      b10_compliance_rate = $10,
      b11_compliance_rate = $11,
      notes = $12
    WHERE id = $1`,
    [
      runId,
      finishedAt,
      agg.queryCount,
      agg.recall,
      agg.precision,
      agg.citationRate,
      agg.avgLatencyMs,
      agg.synthesisPassRate,
      agg.retrievalHitRate,
      agg.b10ComplianceRate,
      agg.b11ComplianceRate,
      agg.notes ?? null,
    ]
  )
}
