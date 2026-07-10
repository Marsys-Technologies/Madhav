import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

// Auth: MARSYS_CRON_SECRET, checked via the x-marsys-cron-secret header before
// any work happens — NOT the Authorization header. R6 0a-envauth (O-2), same
// root cause as R5.2 A4 (bbee27c3): this route's Cloud Scheduler job
// (amjis-pending-stream-reaper, infra/scheduler/main.tf) authenticates via an
// oidc_token block, so Cloud Scheduler delivers a Google-signed OIDC identity
// token in the Authorization header on every dispatch — that header can never
// equal `Bearer <MARSYS_CRON_SECRET>`, so the old check 401'd on every live
// run (the "pre-existing sibling job" failure bbee27c3's commit message
// flagged but explicitly did not fix). Mirrors the already-proven
// x-watchdog-auth / x-marsys-cron-secret custom-header convention (see
// src/app/api/admin/cron/refresh-panchanga-daily/route.ts), which does not
// collide with Cloud Run's own OIDC-in-Authorization mechanism.
export async function POST(request: Request) {
  const expected = process.env.MARSYS_CRON_SECRET
  const auth = request.headers.get('x-marsys-cron-secret')

  if (!expected || auth !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const result = await query(
    'DELETE FROM pending_streams WHERE expires_at < now() RETURNING query_id',
    [],
  )

  const count = result.rows.length
  return NextResponse.json({ reaped: count })
}
