/**
 * MARSYS-JIS Query Trace Panel — DB persistence
 * schema_version: 1.1
 *
 * v1.1 (BHISMA-B3, 2026-05-01): added fetchTraceHistoryAnalytics() for the
 * History analytics tab. Existing fetchTraceHistory() and writeTraceStep()
 * remain unchanged — additive.
 */

import { query } from '@/lib/db/client'
import type { TraceStep, TraceHistoryRow } from './types'

/** Persist a single trace step. Called fire-and-forget from emitter. */
export async function writeTraceStep(step: TraceStep): Promise<void> {
  // mcp_tool column added by migration 116. Extract from data_summary so the
  // column is populated for all mcp_primitive calls without changing TraceStep shape.
  // Migration 116 must be applied before this code runs in production.
  const mcpTool = step.data_summary?.mcp_tool ?? null

  // Try writing with mcp_tool column (requires migration 116).
  // Falls back to the pre-migration INSERT shape if the column is absent,
  // so trace writes are never dropped during a rolling deploy.
  try {
    await query(
      `INSERT INTO public.query_trace_steps
         (query_id, conversation_id, user_id, step_seq, step_name, mcp_tool, step_type, status,
          started_at, completed_at, latency_ms, parallel_group, data_summary, payload)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb, $14::jsonb)
       ON CONFLICT DO NOTHING`,
      [
        step.query_id,
        step.conversation_id ?? null,
        step.user_id ?? null,
        step.step_seq,
        step.step_name,
        mcpTool,
        step.step_type,
        step.status,
        step.started_at,
        step.completed_at ?? null,
        step.latency_ms ?? null,
        step.parallel_group ?? null,
        JSON.stringify(step.data_summary),
        JSON.stringify(step.payload),
      ]
    )
  } catch (err) {
    // Fallback: if mcp_tool column doesn't exist yet (pre-migration 116),
    // write without it so trace steps are never silently dropped.
    const msg = err instanceof Error ? err.message : String(err)
    if (msg.includes('mcp_tool') || msg.includes('column')) {
      await query(
        `INSERT INTO public.query_trace_steps
           (query_id, conversation_id, user_id, step_seq, step_name, step_type, status,
            started_at, completed_at, latency_ms, parallel_group, data_summary, payload)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13::jsonb)
         ON CONFLICT DO NOTHING`,
        [
          step.query_id,
          step.conversation_id ?? null,
          step.user_id ?? null,
          step.step_seq,
          step.step_name,
          step.step_type,
          step.status,
          step.started_at,
          step.completed_at ?? null,
          step.latency_ms ?? null,
          step.parallel_group ?? null,
          JSON.stringify(step.data_summary),
          JSON.stringify(step.payload),
        ]
      )
    } else {
      throw err
    }
  }
}

/** Fetch all steps for a query, ordered by step_seq (for historical replay). */
export async function fetchTraceSteps(queryId: string): Promise<TraceStep[]> {
  const result = await query<{
    query_id: string
    conversation_id: string | null
    step_seq: number
    step_name: string
    step_type: string
    status: string
    started_at: string
    completed_at: string | null
    latency_ms: number | null
    parallel_group: string | null
    data_summary: Record<string, unknown>
    payload: Record<string, unknown>
  }>(
    `SELECT
       query_id, conversation_id, step_seq, step_name, step_type,
       status, started_at, completed_at, latency_ms, parallel_group,
       data_summary, payload
     FROM public.query_trace_steps
     WHERE query_id = $1
     ORDER BY step_seq ASC`,
    [queryId]
  )

  return result.rows.map(r => ({
    query_id: r.query_id,
    conversation_id: r.conversation_id ?? undefined,
    step_seq: r.step_seq,
    step_name: r.step_name,
    step_type: r.step_type as TraceStep['step_type'],
    status: r.status as TraceStep['status'],
    started_at: r.started_at,
    completed_at: r.completed_at ?? undefined,
    latency_ms: r.latency_ms ?? undefined,
    parallel_group: r.parallel_group ?? undefined,
    data_summary: r.data_summary as TraceStep['data_summary'],
    payload: r.payload as TraceStep['payload'],
  }))
}

/** For the history list: recent distinct queries with aggregate stats. */
export async function fetchTraceHistory(limit = 50): Promise<TraceHistoryRow[]> {
  const result = await query<{
    query_id: string
    query_text: string | null
    created_at: string
    step_count: number
    total_latency_ms: number | null
  }>(
    `SELECT
       t.query_id,
       a.query_text,
       MIN(t.started_at)::text                                            AS created_at,
       COUNT(*)::int                                                       AS step_count,
       ROUND(
         EXTRACT(EPOCH FROM (MAX(t.completed_at) - MIN(t.started_at))) * 1000
       )::int                                                              AS total_latency_ms
     FROM public.query_trace_steps t
     LEFT JOIN public.audit_log a ON a.query_id = t.query_id
     GROUP BY t.query_id, a.query_text
     ORDER BY MIN(t.started_at) DESC
     LIMIT $1`,
    [limit]
  )
  return result.rows
}

/**
 * Analytics-mode history fetch — extends fetchTraceHistory with per-stage
 * latencies, query_class, citation_count, tools_used, error flag.
 *
 * Implementation note: per-stage latencies and JSONB-extracted fields are
 * computed by aggregating filtered rows from query_trace_steps using PG's
 * jsonb operators. Step name conventions (BHISMA-B2 + pre-BHISMA):
 *   classify | plan          → planning stage
 *   synthesis | synthesis_done → synthesis stage
 *   any tool step (sql|vector|gcs step_type) → tool fetch stage
 *
 * If a step name does not exist (e.g. synthesis_done not yet emitted by B2),
 * the corresponding latency column comes back null and the UI guards it.
 */
export async function fetchTraceHistoryAnalytics(
  limit = 50
): Promise<TraceHistoryRow[]> {
  const result = await query<{
    query_id: string
    query_text: string | null
    created_at: string
    step_count: number
    total_latency_ms: number | null
    query_class: string | null
    plan_latency_ms: number | null
    synthesis_latency_ms: number | null
    tool_fetch_latency_ms: number | null
    citation_count: number | null
    planning_confidence: number | null
    has_error: boolean
    tools_used: string[] | null
  }>(
    `SELECT
       t.query_id,
       a.query_text,
       MIN(t.started_at)::text                                              AS created_at,
       COUNT(*)::int                                                         AS step_count,
       ROUND(
         EXTRACT(EPOCH FROM (MAX(t.completed_at) - MIN(t.started_at))) * 1000
       )::int                                                                AS total_latency_ms,
       MAX(CASE
         WHEN t.step_name IN ('classify', 'plan')
         THEN COALESCE(
           t.data_summary->>'query_class',
           (t.payload->'query_plan'->>'query_class')
         )
         ELSE NULL
       END)                                                                  AS query_class,
       MAX(CASE
         WHEN t.step_name IN ('classify', 'plan') AND t.status = 'done'
         THEN t.latency_ms
         ELSE NULL
       END)                                                                  AS plan_latency_ms,
       MAX(CASE
         WHEN t.step_name IN ('synthesis', 'synthesis_done') AND t.status = 'done'
         THEN t.latency_ms
         ELSE NULL
       END)                                                                  AS synthesis_latency_ms,
       MAX(CASE
         WHEN t.parallel_group = 'tool_fetch' AND t.status = 'done'
         THEN t.latency_ms
         ELSE NULL
       END)                                                                  AS tool_fetch_latency_ms,
       MAX(CASE
         WHEN t.step_name IN ('synthesis', 'synthesis_done')
         THEN (t.data_summary->>'citation_count')::int
         ELSE NULL
       END)                                                                  AS citation_count,
       MAX(CASE
         WHEN t.step_name IN ('classify', 'plan')
         THEN (
           COALESCE(
             t.data_summary->>'planning_confidence',
             t.data_summary->>'confidence',
             t.data_summary->>'router_confidence'
           )
         )::float
         ELSE NULL
       END)                                                                  AS planning_confidence,
       BOOL_OR(t.status = 'error')                                            AS has_error,
       ARRAY_REMOVE(
         ARRAY_AGG(DISTINCT
           CASE
             WHEN t.step_type IN ('sql', 'vector', 'gcs')
             THEN COALESCE(t.data_summary->>'tool_name', t.step_name)
             ELSE NULL
           END
         ),
         NULL
       )                                                                     AS tools_used
     FROM public.query_trace_steps t
     LEFT JOIN public.audit_log a ON a.query_id = t.query_id
     GROUP BY t.query_id, a.query_text
     ORDER BY MIN(t.started_at) DESC
     LIMIT $1`,
    [limit]
  )
  return result.rows.map(r => ({
    query_id: r.query_id,
    query_text: r.query_text,
    created_at: r.created_at,
    step_count: r.step_count,
    total_latency_ms: r.total_latency_ms,
    query_class: r.query_class,
    plan_latency_ms: r.plan_latency_ms,
    synthesis_latency_ms: r.synthesis_latency_ms,
    tool_fetch_latency_ms: r.tool_fetch_latency_ms,
    citation_count: r.citation_count,
    planning_confidence: r.planning_confidence,
    has_error: r.has_error,
    tools_used: r.tools_used ?? [],
  }))
}
