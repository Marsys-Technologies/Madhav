import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// POST /api/admin/maintenance/trace-cleanup
// Marks query_trace_steps rows stuck in 'running' for >2h as 'error'.
// Intended for Cloud Scheduler (unauthenticated internal call) or super-admin.
// QG4.1 fix: periodic cleanup for zombie trace steps from interrupted pipeline calls.
export async function POST() {
  try {
    const { rowCount } = await query(
      `UPDATE query_trace_steps
       SET status = 'error'
       WHERE status = 'running' AND started_at < NOW() - INTERVAL '2 hours'`,
      [],
    )
    return NextResponse.json({ cleaned: rowCount ?? 0 })
  } catch (err) {
    console.error('[maintenance/trace-cleanup] failed', err)
    return NextResponse.json({ error: 'cleanup failed' }, { status: 500 })
  }
}
