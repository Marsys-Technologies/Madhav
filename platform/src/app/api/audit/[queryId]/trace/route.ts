import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type { TraceStep } from '@/lib/trace/types'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ queryId: string }> }
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { queryId } = await params

  try {
    const result = await query<TraceStep>(
      `SELECT
         query_id, step_seq, step_name, step_type, status,
         started_at, completed_at, latency_ms, parallel_group,
         data_summary, payload
       FROM query_trace_steps
       WHERE query_id = $1
       ORDER BY step_seq ASC`,
      [queryId]
    )

    if (result.rows.length === 0) return res.notFound()

    return NextResponse.json({ steps: result.rows })
  } catch (err) {
    console.error('[api/audit/[queryId]/trace] GET failed', err)
    return res.internal('Failed to load trace steps.')
  }
}
