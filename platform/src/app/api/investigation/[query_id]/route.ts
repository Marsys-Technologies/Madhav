/**
 * MON-9 — Investigation endpoint (W2-TRACE-B).
 *
 * GET /api/investigation/:query_id
 *
 * Returns a joined view of every monitoring row recorded for the given
 * query_id across the four monitoring tables. The four reads run in
 * parallel; auth is super_admin only (same pattern as /api/audit and
 * /api/trace/stream).
 *
 * Response shape:
 *   {
 *     query_id,
 *     llm_calls: LlmCallLogRow[],
 *     query_plan: QueryPlanLogRow | null,
 *     tool_executions: ToolExecutionLogRow[],
 *     context_assembly: ContextAssemblyLogRow | null,
 *   }
 *
 * 404 when no records exist for the supplied query_id.
 */

import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type {
  ContextAssemblyLogRow,
  LlmCallLogRow,
  QueryPlanLogRow,
  ToolExecutionLogRow,
} from '@/lib/db/monitoring-types'

export interface InvestigationResponse {
  query_id: string
  llm_calls: LlmCallLogRow[]
  query_plan: QueryPlanLogRow | null
  tool_executions: ToolExecutionLogRow[]
  context_assembly: ContextAssemblyLogRow | null
}

export const dynamic = 'force-dynamic'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ query_id: string }> },
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { query_id } = await params
  if (!query_id || typeof query_id !== 'string') {
    return res.badRequest('query_id required')
  }

  try {
    const [llmCallsRes, queryPlanRes, toolExecutionsRes, contextAssemblyRes] =
      await Promise.all([
        query<LlmCallLogRow>(
          'SELECT * FROM llm_call_log WHERE query_id = $1 ORDER BY created_at ASC',
          [query_id],
        ),
        query<QueryPlanLogRow>(
          'SELECT * FROM query_plan_log WHERE query_id = $1 LIMIT 1',
          [query_id],
        ),
        query<ToolExecutionLogRow>(
          'SELECT * FROM tool_execution_log WHERE query_id = $1 ORDER BY created_at ASC',
          [query_id],
        ),
        // TODO(ws-2): context_assembly_log dropped WS-0; repoint to context_assembly_item_log.
        Promise.resolve({ rows: [] as ContextAssemblyLogRow[] }),
      ])

    const noRecords =
      llmCallsRes.rows.length === 0 &&
      queryPlanRes.rows.length === 0 &&
      toolExecutionsRes.rows.length === 0 &&
      contextAssemblyRes.rows.length === 0

    if (noRecords) {
      return res.notFound(`No investigation records for query_id ${query_id}`)
    }

    const body: InvestigationResponse = {
      query_id,
      llm_calls: llmCallsRes.rows,
      query_plan: queryPlanRes.rows[0] ?? null,
      tool_executions: toolExecutionsRes.rows,
      context_assembly: contextAssemblyRes.rows[0] ?? null,
    }

    return NextResponse.json(body)
  } catch (err) {
    console.error('[api/investigation/[query_id]] GET failed', err)
    return res.internal('Failed to load investigation records.')
  }
}
