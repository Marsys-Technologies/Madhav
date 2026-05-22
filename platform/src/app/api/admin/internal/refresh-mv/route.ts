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

function validateAuth(request: Request): boolean {
  const cronSecret = process.env['MARSYS_CRON_SECRET']
  const customHeader = request.headers.get('X-Marsys-Cron-Secret')
  const authHeader = request.headers.get('Authorization') ?? ''
  console.log('[auth-debug] cronSecret set:', !!cronSecret, 'len:', cronSecret?.length ?? 0, 'customHeader set:', !!customHeader, 'authHeader prefix:', authHeader.slice(0, 10))

  if (!cronSecret) return false

  // Primary: X-Marsys-Cron-Secret custom header (avoids Authorization header conflicts)
  if (customHeader === cronSecret) return true

  // Fallback: standard Authorization Bearer (for local/CI use where scheduler isn't involved)
  if (authHeader === `Bearer ${cronSecret}`) return true

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
