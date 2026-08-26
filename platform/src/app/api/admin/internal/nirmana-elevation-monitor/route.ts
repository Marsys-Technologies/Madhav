import 'server-only'
import { NextResponse } from 'next/server'
import { runNirmanaElevationMonitor } from '@/lib/nirmana-elevation/monitor'

function validateCronSecret(request: Request): boolean {
  const expected = process.env.MARSYS_CRON_SECRET
  if (!expected) return false
  if (request.headers.get('X-Marsys-Cron-Secret') === expected) return true
  return request.headers.get('Authorization') === `Bearer ${expected}`
}

export async function POST(request: Request) {
  if (!validateCronSecret(request)) {
    return NextResponse.json(
      { error: 'unauthorized' },
      { status: 401, headers: { 'Cache-Control': 'no-store' } },
    )
  }

  try {
    const observation = await runNirmanaElevationMonitor()
    return NextResponse.json(
      {
        ok: true,
        observation_id: observation.id,
        status: observation.status,
        source_state: observation.source_state,
        freshness_state: observation.freshness_state,
        freshness_deadline_at: observation.freshness_deadline_at,
        runtime_liveness: observation.runtime_liveness,
        release_state: observation.release_state,
      },
      { headers: { 'Cache-Control': 'no-store' } },
    )
  } catch {
    console.error('[nirmana-elevation] monitor observation write failed', {
      error_code: 'NIRMANA_MONITOR_WRITE_FAILED',
    })
    return NextResponse.json(
      { ok: false, error: 'monitor_unavailable' },
      { status: 503, headers: { 'Cache-Control': 'no-store' } },
    )
  }
}
