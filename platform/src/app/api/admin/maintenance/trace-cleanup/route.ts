import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { requireSuperAdmin } from '@/lib/auth/access-control'

export const dynamic = 'force-dynamic'

// POST /api/admin/maintenance/trace-cleanup
// Marks query_trace_steps rows stuck in 'running' for >2h as 'error'.
// Auth: super_admin session only (401 unauthenticated, 403 otherwise). It used to
// be an unauthenticated "Cloud Scheduler" endpoint, but proxy.ts only checks the
// cookie SHAPE, so that was open to a forged cookie (SS N-373, SESSION_GATE_AUDIT).
// Nothing in the repo or the deploy workflow calls it; a scheduler job would need
// its own cron-secret route like /api/admin/cron/*.
// QG4.1 fix: periodic cleanup for zombie trace steps from interrupted pipeline calls.
export async function POST() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

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
