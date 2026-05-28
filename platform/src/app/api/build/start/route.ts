/**
 * POST /api/build/start
 *
 * Triggered by the cockpit Build/Rebuild button at /clients/[id]/build.
 *
 * Behaviour:
 *   1. Feature-flag-gated by MARSYS_FLAG_BUILD_TRIGGER_ENABLED (default false).
 *      503 + logged when disabled (kill-switch per BRIEF_4_build_trigger §scope).
 *   2. Auth: authorizeChartAccess({ chartId }) — must return 'all' (owner or
 *      super_admin). 'view' grantees get 403; unauth gets 401.
 *   3. Enqueue Cloud Task → /api/build/task. Returns { buildId, taskName }.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { getFlag } from '@/lib/config'
import { enqueueBuild, type AyanamshaRole } from '@/lib/build/trigger'

export const dynamic = 'force-dynamic'

interface StartRequestBody {
  chart_id?: string
  ayanamsha_role?: AyanamshaRole
}

export async function POST(request: Request): Promise<Response> {
  if (!getFlag('BUILD_TRIGGER_ENABLED')) {
    console.warn('[api/build/start] disabled by feature flag')
    return NextResponse.json(
      {
        error: 'build_trigger_disabled',
        message:
          'The autonomous build trigger is disabled. ' +
          'Set MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true on amjis-web to enable.',
      },
      { status: 503 },
    )
  }

  let body: StartRequestBody = {}
  try {
    body = (await request.json()) as StartRequestBody
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 })
  }

  const chartId = body.chart_id?.trim()
  if (!chartId) {
    return NextResponse.json({ error: 'missing_chart_id' }, { status: 400 })
  }
  const ayanamshaRole: AyanamshaRole = body.ayanamsha_role ?? 'jh_true_chitra'
  if (ayanamshaRole !== 'jh_true_chitra' && ayanamshaRole !== 'kp') {
    return NextResponse.json({ error: 'invalid_ayanamsha_role' }, { status: 400 })
  }

  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const profile = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid],
  )
  const rawRole = profile.rows[0]?.role ?? ''
  const role: 'super_admin' | 'guest' = rawRole === 'super_admin' ? 'super_admin' : 'guest'

  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role },
    chartId,
    db: { query },
  })

  if (permission !== 'all') {
    // 'view' grantees + 'deny' both forbidden — Build is owner/super_admin only.
    return NextResponse.json(
      { error: 'forbidden', permission },
      { status: permission === 'deny' ? 404 : 403 },
    )
  }

  try {
    const result = await enqueueBuild({
      chartId,
      ayanamshaRole,
      triggeredBy: `manual:${user.uid}`,
    })
    return NextResponse.json({
      build_id: result.buildId,
      task_name: result.taskName,
    })
  } catch (err) {
    console.error('[api/build/start] enqueue failed', err)
    return NextResponse.json(
      { error: 'enqueue_failed', message: (err as Error).message },
      { status: 500 },
    )
  }
}
