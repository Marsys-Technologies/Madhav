/**
 * /api/admin/internal/spine-bundle-refresh — post-build spine bundle materialization
 * hook (W5 Lane L5).
 *
 * POST body: { chart_id: string, ayanamsha_id?: string }
 *
 * Intended caller: whatever already observes a chart build reaching a terminal
 * 'completed' state — e.g. the cockpit watchdog's Cloud Scheduler cadence, or a
 * webhook fired at the end of the orchestrator's run. This route deliberately does
 * NOT hook into the orchestrator itself (FROZEN per CLAUDE.md §N.2) — it is a
 * downstream consumer of the completion signal build_runs.state already exposes
 * (see platform/src/app/api/cockpit/sse/route.ts's TERMINAL_STATES /
 * platform/src/app/api/cockpit/watchdog/route.ts for the existing places that key
 * off the same signal), not a modification of how the orchestrator produces it.
 *
 * If this hook is never wired in a given environment, spine bundles still stay
 * correct: query_spine_bundle's read path (platform/src/lib/retrieval/spine/
 * materialize.ts's getOrMaterializeSpineBundle) lazily recomputes+persists on the
 * first request whenever the persisted row is missing or stale — this endpoint is
 * a proactive optimization (avoid paying the fan-out cost on the FIRST post-build
 * read), not the only path to a correct materialized view.
 *
 * Auth: MARSYS_CRON_SECRET, same header/bearer convention as
 * /api/admin/internal/refresh-mv (X-Marsys-Cron-Secret or Authorization: Bearer).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { materializeAllDomainsForChart } from '@/lib/retrieval/spine/materialize'

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

  let body: { chart_id?: string; ayanamsha_id?: string }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'invalid JSON body' }, { status: 400 })
  }

  const chart_id = body.chart_id
  if (!chart_id) {
    return NextResponse.json({ error: 'chart_id is required' }, { status: 400 })
  }

  const startMs = Date.now()
  try {
    const results = await materializeAllDomainsForChart(chart_id, body.ayanamsha_id)
    const latency_ms = Date.now() - startMs
    return NextResponse.json({ ok: true, chart_id, domains: results, latency_ms })
  } catch (err) {
    const latency_ms = Date.now() - startMs
    console.error('[spine-bundle-refresh] materialization failed:', err)
    return NextResponse.json(
      { ok: false, chart_id, latency_ms, error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    )
  }
}
