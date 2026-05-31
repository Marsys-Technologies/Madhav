/**
 * POST /api/build/task
 *
 * Cloud Tasks handler endpoint. Cloud Tasks signs the request with an OIDC
 * token whose audience equals BUILD_TASK_AUDIENCE; we verify the bearer
 * matches that audience and only then invoke the Cloud Run Job.
 *
 * Body: { build_id, chart_id, ayanamsha_role, triggered_by }
 *
 * On Job-dispatch failure we record a `failed_to_dispatch` build_event row
 * so the cockpit reflects the rollback (per BRIEF §scope: per-asset
 * verification + freeze-old archive pattern from 2a; auto-rollback path).
 */

import { NextResponse } from 'next/server'
import { getFlag } from '@/lib/config'
import { invokeBuildJob } from '@/lib/build/jobInvoker'
import { recordBuildEvent } from '@/lib/build/events'
import type { AyanamshaRole } from '@/lib/build/trigger'

// Defense-in-depth: if BUILD_TASK_AUTH_BYPASS is present in env, log a security
// alert. The var was used during Cloud Tasks IAM debugging (2026-05-28) and was
// removed from the codebase. Its presence now means someone set it directly in
// Cloud Run env vars — investigate and remove immediately.
if (process.env.BUILD_TASK_AUTH_BYPASS !== undefined) {
  console.error(
    '[SECURITY][api/build/task] BUILD_TASK_AUTH_BYPASS is set in env — ' +
      'this var no longer grants any access but signals a potential security ' +
      'misconfiguration. Remove it from Cloud Run env vars immediately.',
  )
}

export const dynamic = 'force-dynamic'
export const maxDuration = 300

interface TaskBody {
  build_id?: string
  chart_id?: string
  ayanamsha_role?: AyanamshaRole
  triggered_by?: string
}

/**
 * Cloud Tasks sets `X-CloudTasks-QueueName` + `X-CloudTasks-TaskName`.
 * We additionally validate the OIDC bearer (audience match) via the Auth
 * header. Cloud Run verifies the JWT signature; we check the audience claim.
 */
function isAuthorized(request: Request): boolean {
  const queueName = request.headers.get('x-cloudtasks-queuename')
  if (!queueName) return false

  // Defence-in-depth: confirm the OIDC bearer matches the expected audience.
  // Cloud Run already verifies the JWT signature; we additionally check the
  // audience claim is present (parsing only — no crypto here).
  const authz = request.headers.get('authorization') ?? ''
  if (!authz.toLowerCase().startsWith('bearer ')) return false

  const expectedAud = process.env.BUILD_TASK_AUDIENCE ?? ''
  if (!expectedAud) return false

  try {
    const token = authz.slice('bearer '.length).trim()
    const parts = token.split('.')
    if (parts.length !== 3) return false
    const payload = JSON.parse(
      Buffer.from(parts[1]!.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8'),
    ) as { aud?: string }
    return typeof payload.aud === 'string' && payload.aud === expectedAud
  } catch {
    return false
  }
}

export async function POST(request: Request): Promise<Response> {
  if (!getFlag('BUILD_TRIGGER_ENABLED')) {
    console.warn('[api/build/task] disabled by feature flag')
    return NextResponse.json({ error: 'build_trigger_disabled' }, { status: 503 })
  }

  if (!isAuthorized(request)) {
    console.warn('[api/build/task] unauthorized — missing/invalid Cloud Tasks OIDC')
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  let body: TaskBody
  try {
    body = (await request.json()) as TaskBody
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 })
  }

  const { build_id: buildId, chart_id: chartId, ayanamsha_role: ayanamshaRole, triggered_by: triggeredBy } = body
  if (!buildId || !chartId || !ayanamshaRole || !triggeredBy) {
    return NextResponse.json({ error: 'missing_fields' }, { status: 400 })
  }
  if (ayanamshaRole !== 'jh_true_chitra' && ayanamshaRole !== 'kp') {
    return NextResponse.json({ error: 'invalid_ayanamsha_role' }, { status: 400 })
  }

  try {
    const result = await invokeBuildJob({
      buildId,
      chartId,
      ayanamshaRole,
      triggeredBy,
    })
    await recordBuildEvent({
      buildId,
      chartId,
      ayanamshaRole,
      asset: 'orchestrator',
      stage: 'dispatch',
      status: 'started',
      message: `Cloud Run Job dispatched — ${result.executionName}`,
      metadata: { execution_name: result.executionName },
    })
    return NextResponse.json({ ok: true, execution_name: result.executionName })
  } catch (err) {
    const message = (err as Error).message
    console.error('[api/build/task] Job invocation failed', err)
    // Auto-rollback signal: record the failure so the cockpit reverts the
    // staging swap visualization (per BRIEF §commit cadence / rollback).
    await recordBuildEvent({
      buildId,
      chartId,
      ayanamshaRole,
      asset: 'orchestrator',
      stage: 'dispatch',
      status: 'failed',
      message,
      metadata: { error: 'job_dispatch_failed' },
    })
    return NextResponse.json({ error: 'job_dispatch_failed', message }, { status: 500 })
  }
}
