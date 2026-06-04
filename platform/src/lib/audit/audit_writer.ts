import 'server-only'

import { query } from '@/lib/db/client'
import { telemetry } from '@/lib/telemetry/index'
import type { QueryPlan } from '@/lib/router/types'

export interface ToolBundleSummary {
  tool_name: string
  item_count: number
  latency_ms: number
  cached: boolean
}

export interface AuditEventParams {
  queryId: string
  queryPlanId?: string
  queryText: string
  queryClass: string
  userId: string
  chartId?: string
  conversationId?: string
  toolBundles: ToolBundleSummary[]
  latencyMs: number
  auditStatus?: string
  auditWarnings?: unknown[]
}

/**
 * Write one row to audit_events. Never throws — failures are routed to
 * telemetry so the response path is never affected.
 */
export async function writeAuditEvent(params: AuditEventParams): Promise<void> {
  try {
    await query(
      `INSERT INTO audit_events (
        query_id, query_plan_id, query_text, query_class,
        user_id, chart_id, conversation_id, tool_bundles,
        latency_ms, audit_status, audit_warnings
      ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`,
      [
        params.queryId,
        params.queryPlanId ?? null,
        params.queryText,
        params.queryClass,
        params.userId,
        params.chartId ?? null,
        params.conversationId ?? null,
        JSON.stringify(params.toolBundles),
        params.latencyMs,
        params.auditStatus ?? 'ok',
        params.auditWarnings != null ? JSON.stringify(params.auditWarnings) : null,
      ]
    )
  } catch (err) {
    telemetry.recordError(
      'audit_writer',
      'write_audit_event_failed',
      err instanceof Error ? err : new Error(String(err))
    )
  }
}

/**
 * query_plans table dropped in WS-0. No-op until WS-2 rebuild.
 * TODO(ws-2): repoint to query_plan_log (platform-modernization replacement).
 */
export async function writeQueryPlan(_plan: QueryPlan): Promise<void> {
  // no-op
}
