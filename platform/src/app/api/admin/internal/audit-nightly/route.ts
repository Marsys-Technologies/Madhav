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

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = parts[1]
    const padded = payload + '=='.slice((payload.length % 4) || 4)
    const decoded = Buffer.from(padded.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8')
    return JSON.parse(decoded) as Record<string, unknown>
  } catch {
    return null
  }
}

function validateAuth(request: Request): boolean {
  const authHeader = request.headers.get('Authorization') ?? ''

  const cronSecret = process.env['MARSYS_CRON_SECRET']
  if (cronSecret && authHeader === `Bearer ${cronSecret}`) return true

  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7)
    const payload = decodeJwtPayload(token)
    if (!payload) return false

    const schedulerSA = process.env['MARSYS_SCHEDULER_SA']
    if (schedulerSA && payload['email'] === schedulerSA) return true

    const email = payload['email'] as string | undefined
    if (email?.endsWith('.iam.gserviceaccount.com')) return true
  }

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
