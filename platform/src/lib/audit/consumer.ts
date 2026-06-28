import 'server-only'

import { telemetry } from '@/lib/telemetry/index'
import { writeAuditLog } from './writer'
import { writeConsumePerformanceRow } from '@/lib/performance/ingestion'
import type { AuditEvent, ValidatorRecord, ToolCallRecord } from './types'
import type { SynthesisAuditEvent } from '@/lib/synthesis/types'
import type { QueryPlan } from '@/lib/router/types'
import type { Bundle } from '@/lib/bundle/types'
// D7 migration Step 3: ToolBundle sourced from lib/retrieve/types (canonical until Step 4 deletion).
// When lib/retrieve is retired, update to ToolResult from @/lib/retrieval/registry/types.
import type { ToolBundle } from '@/lib/retrieval/shared_types'
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
  }
}
