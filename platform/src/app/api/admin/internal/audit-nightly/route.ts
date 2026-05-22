/**
 * /api/admin/internal/audit-nightly — Nightly audit trigger endpoint.
 *
 * POST handler invoked by Cloud Scheduler at 03:00 UTC to run the
 * operator-side nightly audit against the last 24h of tool_execution_log.
 *
 * Auth: same OIDC/MARSYS_CRON_SECRET pattern as refresh-mv.
 *
 * MCPT v3.7 — operational gap closure Phase C.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { runNightlyAudit } from '@/lib/perf/audit_nightly'

function validateAuth(request: Request): boolean {
  const cronSecret = process.env['MARSYS_CRON_SECRET']
  if (!cronSecret) return false

  const customHeader = request.headers.get('X-Marsys-Cron-Secret')
  if (customHeader === cronSecret) return true

  const authHeader = request.headers.get('Authorization') ?? ''
  if (authHeader === `Bearer ${cronSecret}`) return true

  return false
}

export async function POST(request: Request) {
  if (!validateAuth(request)) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const startMs = Date.now()
  try {
    const result = await runNightlyAudit()
    const latency_ms = Date.now() - startMs
    return NextResponse.json({ ok: true, latency_ms, ...result })
  } catch (err) {
    const latency_ms = Date.now() - startMs
    console.error('[audit-nightly] audit run failed:', err)
    return NextResponse.json(
      { ok: false, latency_ms, error: String(err) },
      { status: 500 }
    )
  }
}
