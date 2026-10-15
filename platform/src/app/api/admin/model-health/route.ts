/**
 * BHISMA-B1 §3.5 — /api/admin/model-health
 *
 * GET  (no params)         → returns current in-memory health statuses
 * GET  ?refresh=true       → re-pings all FAMILY_WORKER models, then returns
 *
 * Auth: super_admin only (401 unauthenticated, 403 otherwise). It was
 * "unauthenticated for simplicity", but ?refresh=true pings every worker model
 * with the production provider keys and proxy.ts only checks the session cookie
 * SHAPE, so the guard runs FIRST — before any refresh or ping (SS N-373,
 * SESSION_GATE_AUDIT).
 */
import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { runHealthChecks, getAllHealthStatuses } from '@/lib/models/health'

export async function GET(request: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { searchParams } = new URL(request.url)
  const refresh = searchParams.get('refresh') === 'true'

  if (refresh) {
    const results = await runHealthChecks()
    return NextResponse.json({
      checked_at: new Date().toISOString(),
      results,
    })
  }

  return NextResponse.json({
    checked_at: new Date().toISOString(),
    results: getAllHealthStatuses(),
  })
}
