import 'server-only'
import { NextResponse } from 'next/server'
import { verifyOidcToken } from '@/lib/auth/oidc'
import { runNirmanaElevationMonitor } from '@/lib/nirmana-elevation/monitor'

const SCHEDULER_OIDC_AUDIENCE = 'https://amjis-web-938361928218.asia-south1.run.app'
const SCHEDULER_SERVICE_ACCOUNT = 'amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com'

export async function POST(request: Request) {
  const authorization = request.headers.get('Authorization')
  if (!authorization?.startsWith('Bearer ')) {
    return NextResponse.json(
      { error: 'unauthorized' },
      { status: 401, headers: { 'Cache-Control': 'no-store' } },
    )
  }

  try {
    const identity = await verifyOidcToken(authorization.slice('Bearer '.length), {
      expectedAudience: SCHEDULER_OIDC_AUDIENCE,
      expectedServiceAccount: SCHEDULER_SERVICE_ACCOUNT,
    })
    if (!identity) {
      return NextResponse.json(
        { error: 'forbidden' },
        { status: 403, headers: { 'Cache-Control': 'no-store' } },
      )
    }
  } catch {
    return NextResponse.json(
      { error: 'forbidden' },
      { status: 403, headers: { 'Cache-Control': 'no-store' } },
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
