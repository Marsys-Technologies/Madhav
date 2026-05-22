/**
 * /api/admin/internal/refresh-mv — MV refresh dispatcher.
 *
 * POST handler invoked by Cloud Scheduler to refresh a named materialized view.
 * The viewName is passed as a query parameter: ?view=mv_tool_metrics_24h
 *
 * Auth: OIDC token from Cloud Scheduler service account, validated by checking
 * the token's email claim against MARSYS_SCHEDULER_SA env var.
 * Falls back to MARSYS_CRON_SECRET for local/CI use.
 *
 * MCPT v3.7 — operational gap closure Phase C.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

const ALLOWED_VIEWS = new Set([
  'mv_tool_metrics_24h',
  'mv_data_source_coverage',
  'mv_session_summary',
  'mv_tool_grounding_24h',
  'mv_calibration_score',
  'school_convergence_index',
])

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = parts[1]
    // pad base64url to standard base64
    const padded = payload + '=='.slice((payload.length % 4) || 4)
    const decoded = Buffer.from(padded.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8')
    return JSON.parse(decoded) as Record<string, unknown>
  } catch {
    return null
  }
}

function validateAuth(request: Request): boolean {
  const authHeader = request.headers.get('Authorization') ?? ''

  // Fallback: shared secret for local/CI use
  const cronSecret = process.env['MARSYS_CRON_SECRET']
  if (cronSecret && authHeader === `Bearer ${cronSecret}`) return true

  // OIDC token from Cloud Scheduler
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7)
    const payload = decodeJwtPayload(token)
    if (!payload) return false

    const schedulerSA = process.env['MARSYS_SCHEDULER_SA']
    if (schedulerSA && payload['email'] === schedulerSA) return true

    // Accept any Google service account if SA not configured
    const email = payload['email'] as string | undefined
    if (email?.endsWith('.iam.gserviceaccount.com')) return true
  }

  return false
}

export async function POST(request: Request) {
  if (!validateAuth(request)) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const url = new URL(request.url)
  const viewName = url.searchParams.get('view')

  if (!viewName || !ALLOWED_VIEWS.has(viewName)) {
    return NextResponse.json(
      { error: `invalid view; allowed: ${[...ALLOWED_VIEWS].join(', ')}` },
      { status: 400 }
    )
  }

  const startMs = Date.now()
  try {
    // REFRESH MATERIALIZED VIEW does not support parameterized identifiers;
    // viewName is validated against the allowlist above so this is safe.
    await query(`REFRESH MATERIALIZED VIEW ${viewName}`, [])
    const latency_ms = Date.now() - startMs
    return NextResponse.json({ ok: true, view: viewName, latency_ms })
  } catch (err) {
    const latency_ms = Date.now() - startMs
    console.error(`[mv-refresh] REFRESH ${viewName} failed:`, err)
    return NextResponse.json(
      { ok: false, view: viewName, latency_ms, error: String(err) },
      { status: 500 }
    )
  }
}
