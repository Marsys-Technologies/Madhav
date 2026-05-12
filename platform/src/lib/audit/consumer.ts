import 'server-only'

import { telemetry } from '@/lib/telemetry/index'
import { writeAuditLog } from './writer'
import { logPrediction } from '@/lib/prediction/writer'
import { getFlag } from '@/lib/config/index'
import { writeConsumePerformanceRow } from '@/lib/performance/ingestion'
import type { AuditEvent, ValidatorRecord, ToolCallRecord } from './types'
import type { SynthesisAuditEvent } from '@/lib/synthesis/types'
import type { QueryPlan } from '@/lib/router/types'
import type { Bundle } from '@/lib/bundle/types'
import type { ToolBundle } from '@/lib/retrieve/types'
import type { ValidationResult } from '@/lib/validators/types'

export interface AuditConsumerContext {
  query_text: string
  query_plan: QueryPlan
  bundle: Bundle
  tool_results: ToolBundle[]
  validator_results: ValidationResult[]
  disclosure_tier: string
}

/**
 * Build a consumer callback for synthesis audit events. The callback is
 * non-blocking: it fires async writes and catches all failures into telemetry
 * so the response path is never affected.
 *
 * Pass the returned callback as `onAuditEvent` in SynthesisRequest when
 * AUDIT_ENABLED flag is ON. When flag is OFF, pass nothing.
 */
export function createAuditConsumer(
  ctx: AuditConsumerContext
): (event: SynthesisAuditEvent) => void {
  return (event: SynthesisAuditEvent): void => {
    const toolsCalledRecords: ToolCallRecord[] = ctx.tool_results.map(r => ({
      tool: r.tool_name,
      params_hash: r.result_hash,
      latency_ms: r.latency_ms,
      cached: r.served_from_cache,
    }))

    const validatorsRunRecords: ValidatorRecord[] = ctx.validator_results.map(r => ({
      validator_id: r.validator_id,
      passed: r.vote === 'pass',
      message: r.reason ?? '',
    }))

    const auditEvent: AuditEvent = {
      query_id: event.query_plan_id,
      query_text: ctx.query_text,
      query_class: ctx.query_plan.query_class,
      bundle_keys: ctx.bundle.mandatory_context.map(e => e.canonical_id),
      tools_called: toolsCalledRecords,
      validators_run: validatorsRunRecords,
      synthesis_model: event.synthesizer_model_id,
      synthesis_input_tokens: event.input_tokens,
      synthesis_output_tokens: event.output_tokens,
      disclosure_tier: ctx.disclosure_tier,
      final_output: event.final_output,
      audit_event_version: 1,
    }

    writeAuditLog(auditEvent).catch(err => {
      telemetry.recordError(
        'audit_consumer',
        'audit_write_failed',
        err instanceof Error ? err : new Error(String(err))
      )
    })

    // Gate I: fire-and-forget performance row. Writer is non-throwing.
    void writeConsumePerformanceRow({
      query_id: event.query_plan_id,
      query_plan: ctx.query_plan,
      tool_results: ctx.tool_results,
      validator_results: ctx.validator_results,
      disclosure_tier: ctx.disclosure_tier,
      synthesis_event: event,
    })

    // L.5.1: checkpoint-derived prediction (Phase 6 path, flag-gated).
    // Sacrosanct: no outcome field is set here — outcome is always a separate post-hoc write.
    if (event.prediction && getFlag('CHECKPOINT_8_5_PREDICTION_EXTRACT')) {
      logPrediction({
        ...event.prediction,
        query_id: event.query_plan_id,
      }).catch(err => {
        telemetry.recordError(
          'audit_consumer',
          'prediction_log_failed',
          err instanceof Error ? err : new Error(String(err))
        )
      })
    } else if (isPredictiveContext(ctx.query_plan, event.final_output)) {
      // Heuristic fallback (pre-Phase-6 behavior preserved).
      const extracted = extractPredictionHint(event.final_output, event.query_plan_id)
      if (extracted) {
        logPrediction(extracted).catch(err => {
          telemetry.recordError(
            'audit_consumer',
            'prediction_log_failed',
            err instanceof Error ? err : new Error(String(err))
          )
        })
      }
    }
  }
}

/**
 * Heuristic: treat as predictive if the query class is 'predictive' OR the
 * output contains a date-range pattern alongside a confidence assertion.
 * Phase 6 replaces this with checkpoint-derived extraction.
 */
function isPredictiveContext(queryPlan: QueryPlan, outputText: string): boolean {
  if (queryPlan.query_class === 'predictive') return true
  if (queryPlan.expected_output_shape === 'time_indexed_prediction') return true
  // Heuristic: date-range + confidence keyword in output
  const hasDateRange = /\b(20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).{0,40}(20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b/i.test(outputText)
  const hasConfidence = /\b(\d{1,3}\s*%|probability|confidence|likelihood|likely|probable)\b/i.test(outputText)
  return hasDateRange && hasConfidence
}

/**
 * Minimal heuristic extraction: builds a single Prediction from the first
 * date-range and confidence value found in the output. Returns null when
 * extraction yields insufficient structure.
 * Phase 6 replaces this entirely with a structured checkpoint payload.
 */
function extractPredictionHint(
  outputText: string,
  queryId: string
): import('@/lib/prediction/types').Prediction | null {
  // Extract year range like "2026–2027" or "mid-2026 to late-2027"
  const yearRangeMatch = outputText.match(/\b(20\d{2})\b.{0,30}\b(20\d{2})\b/)
  if (!yearRangeMatch) return null

  const horizonStart = `${yearRangeMatch[1]}-01-01`
  const horizonEnd = `${yearRangeMatch[2]}-12-31`

  // Extract confidence percentage if present
  const confidenceMatch = outputText.match(/\b(\d{1,2})\s*%\s*(confidence|probability|likelihood)/i)
  const confidence = confidenceMatch ? Math.min(parseInt(confidenceMatch[1], 10) / 100, 1) : 0.5

  // Extract a short prediction snippet (first 300 chars)
  const predictionText = outputText.slice(0, 300).trim()
  if (predictionText.length < 20) return null

  return {
    query_id: queryId,
    prediction_text: predictionText,
    confidence,
    horizon_start: horizonStart,
    horizon_end: horizonEnd,
    falsifier: 'No significant event matching this prediction observed within the horizon window',
    subject: 'native:abhisek',
  }
}
