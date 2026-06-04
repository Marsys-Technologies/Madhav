/**
 * monitoring-write.ts — fire-and-forget DB write helpers for the W2 monitoring
 * tables (migrations 032–035). Each function inserts one row and never throws
 * to the caller — DB errors are warn-logged internally so instrumentation
 * never adds latency or failure modes to the request path.
 *
 * Row shape mirrors `monitoring-types.ts` 1:1; callers omit `id` and
 * `created_at` (DB-defaulted).
 */

import 'server-only'
import { getStorageClient } from '@/lib/storage'
import { getModelMeta } from '@/lib/models/registry'
import type {
  LlmCallLogRow,
  QueryPlanLogRow,
  ToolExecutionLogRow,
  ContextAssemblyLogRow,
  ObservatoryQueryEventInput,
} from './monitoring-types'

export async function writeLlmCallLog(
  row: Omit<LlmCallLogRow, 'id' | 'created_at'>
): Promise<void> {
  try {
    await getStorageClient().query(
      `INSERT INTO llm_call_log
        (query_id, conversation_id, call_stage, model_id, provider,
         input_tokens, output_tokens, reasoning_tokens, latency_ms,
         cost_usd, fallback_used, error_code, payload,
         decision_alternatives, decision_reasoning,
         prompt_template_id, prompt_template_version, parent_call_id)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
               $14, $15, $16, $17, $18)`,
      [
        row.query_id,
        row.conversation_id,
        row.call_stage,
        row.model_id,
        row.provider,
        row.input_tokens,
        row.output_tokens,
        row.reasoning_tokens,
        row.latency_ms,
        row.cost_usd,
        row.fallback_used,
        row.error_code,
        row.payload === null || row.payload === undefined ? null : JSON.stringify(row.payload),
        row.decision_alternatives === null || row.decision_alternatives === undefined
          ? null : JSON.stringify(row.decision_alternatives),
        row.decision_reasoning ?? null,
        row.prompt_template_id ?? null,
        row.prompt_template_version ?? null,
        row.parent_call_id ?? null,
      ]
    )
  } catch (err) {
    console.warn('[mon] writeLlmCallLog failed:', err)
  }
}

export async function writeQueryPlanLog(
  row: Omit<QueryPlanLogRow, 'id' | 'created_at'>
): Promise<void> {
  try {
    await getStorageClient().query(
      `INSERT INTO query_plan_log
        (query_id, conversation_id, chart_id, planner_model_id, query_text,
         query_class, tool_count, plan_json, parsing_success, parse_error,
         fallback_used, planner_latency_ms)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
       ON CONFLICT (query_id) DO NOTHING`,
      [
        row.query_id,
        row.conversation_id,
        row.chart_id,
        row.planner_model_id,
        row.query_text,
        row.query_class,
        row.tool_count,
        row.plan_json === null || row.plan_json === undefined ? null : JSON.stringify(row.plan_json),
        row.parsing_success,
        row.parse_error,
        row.fallback_used,
        row.planner_latency_ms,
      ]
    )
  } catch (err) {
    console.warn('[mon] writeQueryPlanLog failed:', err)
  }
}

export async function writeToolExecutionLog(
  row: Omit<ToolExecutionLogRow, 'id' | 'created_at'>
): Promise<void> {
  try {
    await getStorageClient().query(
      `INSERT INTO tool_execution_log
        (query_id, tool_name, params_json, status, rows_returned, latency_ms,
         token_estimate, data_asset_id, error_code, served_from_cache,
         fallback_used,
         raw_result_count, kept_result_count, dropped_items, kept_items,
         tool_input_payload, tool_output_summary, error_class, retrieval_score)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
               $12, $13, $14, $15, $16, $17, $18, $19)`,
      [
        row.query_id,
        row.tool_name,
        row.params_json === null || row.params_json === undefined ? null : JSON.stringify(row.params_json),
        row.status,
        row.rows_returned,
        row.latency_ms,
        row.token_estimate,
        row.data_asset_id,
        row.error_code,
        row.served_from_cache,
        row.fallback_used,
        row.raw_result_count ?? null,
        row.kept_result_count ?? null,
        row.dropped_items === null || row.dropped_items === undefined
          ? null : JSON.stringify(row.dropped_items),
        row.kept_items === null || row.kept_items === undefined
          ? null : JSON.stringify(row.kept_items),
        row.tool_input_payload === null || row.tool_input_payload === undefined
          ? null : JSON.stringify(row.tool_input_payload),
        row.tool_output_summary === null || row.tool_output_summary === undefined
          ? null : JSON.stringify(row.tool_output_summary),
        row.error_class ?? 'OK',
        row.retrieval_score ?? null,
      ]
    )
  } catch (err) {
    console.warn('[mon] writeToolExecutionLog failed:', err)
  }
}

// context_assembly_log dropped in WS-0; write is a no-op until WS-2.
// TODO(ws-2): repoint to context_assembly_item_log (platform-modernization replacement).
export async function writeContextAssemblyLog(
  _row: Omit<ContextAssemblyLogRow, 'id' | 'created_at' | 'total_tokens'>
): Promise<void> {
  // no-op
}

export function resolveProvider(modelId: string): string {
  const raw = getModelMeta(modelId)?.provider ?? 'unknown'
  if (raw === 'google') return 'gemini'
  if (raw === 'nvidia') return 'nim'
  return raw
}

export async function writeObservatoryQueryEvent(
  input: ObservatoryQueryEventInput
): Promise<void> {
  try {
    const now = new Date()
    const latencyMs = Math.round(now.getTime() - input.setupStart.getTime())
    const provider = resolveProvider(input.modelId)
    const promptText = input.queryText.length > 4000
      ? input.queryText.slice(0, 4000)
      : input.queryText
    const responseText = input.responseText !== null && input.responseText.length > 4000
      ? input.responseText.slice(0, 4000)
      : input.responseText

    const inputTokens = input.inputTokens ?? null
    const outputTokens = input.outputTokens ?? null
    const cacheReadTokens = input.cacheReadTokens ?? null
    const cacheWriteTokens = input.cacheWriteTokens ?? null
    const reasoningTokens = input.reasoningTokens ?? null

    // Compute cost from pricing table when token counts are available
    let computedCostUsd: number | null = null
    let pricingVersionId: string | null = null
    if (inputTokens !== null && outputTokens !== null) {
      try {
        const db = getStorageClient()
        const pricingRows = await db.query<{
          pricing_version_id: string
          token_class: string
          price_per_million_usd: number
        }>(
          `SELECT pricing_version_id, token_class, price_per_million_usd
           FROM llm_pricing_versions
           WHERE provider = $1 AND model = $2
             AND effective_from <= $3
             AND (effective_to IS NULL OR effective_to > $3)`,
          [provider, input.modelId, input.setupStart.toISOString()]
        )
        if (pricingRows.rows.length > 0) {
          const tokenMap: Record<string, number | null> = {
            input: inputTokens,
            output: outputTokens,
            cache_read: cacheReadTokens,
            cache_write: cacheWriteTokens,
            reasoning: reasoningTokens,
          }
          let total = 0
          for (const row of pricingRows.rows) {
            const tokens = tokenMap[row.token_class] ?? 0
            if (tokens > 0) total += (tokens / 1_000_000) * row.price_per_million_usd
            if (row.token_class === 'input') pricingVersionId = row.pricing_version_id
            else pricingVersionId ??= row.pricing_version_id
          }
          computedCostUsd = total
        }
      } catch {
        // pricing lookup failure is non-fatal
      }
    }

    await getStorageClient().query(
      `INSERT INTO llm_usage_events
        (conversation_id, prompt_id, user_id, provider, model, pipeline_stage,
         prompt_text, response_text, status, latency_ms, started_at, finished_at,
         parameters, input_tokens, output_tokens, cache_read_tokens,
         cache_write_tokens, reasoning_tokens, computed_cost_usd, pricing_version_id)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
               $14, $15, $16, $17, $18, $19, $20)
       ON CONFLICT (prompt_id) DO NOTHING`,
      [
        input.conversationId ?? 'unknown',
        input.queryId,
        input.userId,
        provider,
        input.modelId,
        'other',
        promptText,
        responseText,
        'success',
        latencyMs,
        input.setupStart,
        now,
        JSON.stringify({ query_class: input.queryClass, stack: input.stack }),
        inputTokens,
        outputTokens,
        cacheReadTokens,
        cacheWriteTokens,
        reasoningTokens,
        computedCostUsd,
        pricingVersionId,
      ]
    )
  } catch (err) {
    console.warn('[mon] writeObservatoryQueryEvent failed:', err)
  }
}
