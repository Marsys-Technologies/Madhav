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
 *   3. Accepts optional ayanamshas[] array; defaults to all 5 canonical.
 *      Validates against VALID_AYANAMSHAS whitelist; returns 422 for invalid entries.
 *   4. Inserts a builds row + 14 build_steps rows (one per DAG asset).
 *   5. Also enqueues Cloud Task → /api/build/task (legacy path preserved).
 *   6. Returns { build_id, chart_id, ayanamshas, step_count: 14, status: 'queued' }.
 *
 * [BUILD-ORCH-D-01] Extended to support 5-ayanamsha build system.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { authorizeChartAccess, type DbLike } from '@/lib/auth/authorizeChartAccess'
import { getFlag } from '@/lib/config'
import { enqueueBuild } from '@/lib/build/trigger'

export const dynamic = 'force-dynamic'

// ─── Constants ──────────────────────────────────────────────────────────────

export const VALID_AYANAMSHAS = [
  'lahiri',
  'true_chitra',
  'kp',
  'raman',
  'surya_siddhanta',
] as const

export type Ayanamsha = (typeof VALID_AYANAMSHAS)[number]

export const DEFAULT_AYANAMSHAS: Ayanamsha[] = [...VALID_AYANAMSHAS]

export const DAG_ASSETS = [
  'A1_engine',
  'A2_forensic_render',
  'A3_chart_facts',
  'A4_panchanga',
  'A5_sensitive_points',
  'A6_vargas',
  'A7_dashas',
  'A8_t1_structural',
  'A9_sade_sati',
  'A10_msr',
  'A11_cdlm',
  'A12_cgm',
  'A13_rm',
  'A14_ucn_digest',
] as const

export type DagAsset = (typeof DAG_ASSETS)[number]

// ─── Request body type ───────────────────────────────────────────────────────

interface StartRequestBody {
  chart_id?: string
  ayanamshas?: string[]
}

// ─── Handler ─────────────────────────────────────────────────────────────────

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

  // ── Parse body ─────────────────────────────────────────────────────────────
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

  // ── Validate ayanamshas ────────────────────────────────────────────────────
  const rawAyanamshas = body.ayanamshas
  let ayanamshas: Ayanamsha[]

  if (rawAyanamshas === undefined || rawAyanamshas === null) {
    ayanamshas = DEFAULT_AYANAMSHAS
  } else {
    if (!Array.isArray(rawAyanamshas) || rawAyanamshas.length === 0) {
      return NextResponse.json(
        { error: 'invalid_ayanamshas', message: 'ayanamshas must be a non-empty array' },
        { status: 422 },
      )
    }
    const validSet = new Set<string>(VALID_AYANAMSHAS)
    const invalid = rawAyanamshas.filter((a) => typeof a !== 'string' || !validSet.has(a))
    if (invalid.length > 0) {
      return NextResponse.json(
        {
          error: 'invalid_ayanamshas',
          message: `Unknown ayanamsha value(s): ${invalid.join(', ')}`,
          invalid,
          valid: VALID_AYANAMSHAS,
        },
        { status: 422 },
      )
    }
    ayanamshas = rawAyanamshas as Ayanamsha[]
  }

  // ── Auth ───────────────────────────────────────────────────────────────────
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const profileResult = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid],
  )
  const rawRole = profileResult.rows[0]?.role ?? ''
  const role: 'super_admin' | 'guest' = rawRole === 'super_admin' ? 'super_admin' : 'guest'

  // ── Verify chart ownership ─────────────────────────────────────────────────
  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role },
    chartId,
    db: { query: (sql: string, params?: unknown[]) => query(sql, params).then(r => ({ rows: r.rows })) } as DbLike,
  })

  if (permission !== 'all') {
    return NextResponse.json(
      { error: 'forbidden', permission },
      { status: permission === 'deny' ? 404 : 403 },
    )
  }

  // ── Verify chart_id exists in charts table ─────────────────────────────────
  // authorizeChartAccess above already confirms ownership (or deny → 404 above),
  // but we also need chart_id (uuid column) to insert into builds.chart_id (uuid FK).
  const chartRow = await query<{ chart_id: string }>(
    'SELECT chart_id FROM charts WHERE chart_id=$1',
    [chartId],
  )
  if (!chartRow.rows[0]) {
    return NextResponse.json({ error: 'chart_not_found' }, { status: 404 })
  }
  const resolvedChartId = chartRow.rows[0].chart_id

  // ── Concurrency guard ──────────────────────────────────────────────────────
  // Refuse if a non-terminal build already exists for this chart. Returns 409
  // with the existing build_id — caller can poll or cancel it. Prevents the
  // "stuck builds pile up" failure mode (CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0).
  const existing = await query<{ build_id: string; status: string; started_at: string | null }>(
    `SELECT build_id, status, started_at
       FROM builds
      WHERE chart_id = $1
        AND status IN ('running', 'queued', 'cancelling')
      ORDER BY created_at DESC
      LIMIT 1`,
    [resolvedChartId],
  )
  if (existing.rows[0]) {
    const row = existing.rows[0]
    return NextResponse.json(
      {
        error: 'build_already_active',
        build_id: row.build_id,
        status: row.status,
        started_at: row.started_at,
        message: 'A build for this chart is already in flight. Cancel it before starting a new one.',
      },
      { status: 409 },
    )
  }

  // ── Insert builds row ──────────────────────────────────────────────────────
  let buildId: string
  try {
    const insertBuildResult = await query<{ build_id: string }>(
      `INSERT INTO builds
         (chart_id, triggered_by_uid, triggered_by_role, engine_version,
          ayanamshas, status, queued_at)
       VALUES ($1, $2, $3, $4, $5::jsonb, 'queued', NOW())
       RETURNING build_id`,
      [
        resolvedChartId,
        user.uid,
        role,
        'natal_engine/0.2.0-jh-parity',
        JSON.stringify(ayanamshas),
      ],
    )
    buildId = insertBuildResult.rows[0].build_id
  } catch (err) {
    console.error('[api/build/start] builds INSERT failed', err)
    return NextResponse.json(
      { error: 'db_error', message: (err as Error).message },
      { status: 500 },
    )
  }

  // ── Insert 14 build_steps rows (one per DAG asset) ─────────────────────────
  // ayanamsha_id is set to 'all' for multi-ayanamsha builds; the executor
  // expands per-ayanamsha when it processes each step.
  try {
    const stepValues = DAG_ASSETS.map((_, i) => {
      const base = i * 3
      return `($${base + 1}, $${base + 2}, $${base + 3}, 'queued')`
    }).join(', ')

    const stepParams: string[] = []
    for (const asset of DAG_ASSETS) {
      stepParams.push(buildId, 'all', asset)
    }

    await query(
      `INSERT INTO build_steps (build_id, ayanamsha_id, category, status)
       VALUES ${stepValues}`,
      stepParams,
    )
  } catch (err) {
    console.error('[api/build/start] build_steps INSERT failed', err)
    // Attempt cleanup: mark build as failed so it doesn't hang as 'queued'
    await query(
      `UPDATE builds SET status='failed', failed_at=NOW(),
       error_summary=$1 WHERE build_id=$2`,
      [`build_steps insert failed: ${(err as Error).message}`, buildId],
    ).catch(() => {})
    return NextResponse.json(
      { error: 'db_error', message: (err as Error).message },
      { status: 500 },
    )
  }

  // ── Optionally enqueue Cloud Task (best-effort; non-blocking for the response) ──
  // The legacy Cloud Task path is preserved for background execution.
  // If the task queue env vars are not set (dev mode), we skip without error.
  try {
    await enqueueBuild({
      chartId: resolvedChartId,
      ayanamshaRole: 'jh_true_chitra', // legacy single-role for task executor
      triggeredBy: `manual:${user.uid}`,
    })
  } catch (err) {
    // Non-fatal: if the task queue is not configured (e.g. local dev), log and continue.
    // The builds row is already persisted and will be picked up by the job runner.
    console.warn('[api/build/start] enqueueBuild skipped (non-fatal):', (err as Error).message)
  }

  return NextResponse.json({
    build_id: buildId,
    chart_id: resolvedChartId,
    ayanamshas,
    step_count: DAG_ASSETS.length,
    status: 'queued',
  })
}
