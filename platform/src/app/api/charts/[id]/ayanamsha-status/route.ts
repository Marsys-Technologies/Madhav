/**
 * GET /api/charts/[id]/ayanamsha-status
 *
 * Returns per-ayanamsha build status for a given chart, sorted in canonical
 * order. Used by the Constellation UI to show which ayanamshas have been built.
 *
 * Behaviour:
 *   1. Auth: 401 if unauthenticated.
 *   2. Chart lookup: verify chart belongs to authenticated user (or super_admin).
 *      Returns 404 if chart not found / inaccessible.
 *   3. For each of the 5 canonical ayanamshas, find the latest build for this
 *      chart that contains that ayanamsha (JSONB contains match).
 *   4. Returns an array of 5 items sorted by CANONICAL_ORDER.
 *   5. If no build exists for an ayanamsha → status='not_built', all nulls.
 *   6. is_latest_engine: true if the build's engine_version matches the current
 *      engine (from engine_versions table, falls back to builds default when
 *      engine_versions is empty).
 *   7. Cache-Control: max-age=10 (short CDN cache — build status changes slowly).
 *
 * [BUILD-ORCH-D-08] /api/charts/[id]/ayanamsha-status per-ayanamsha build state.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// ─── Canonical constants ──────────────────────────────────────────────────────

const CANONICAL_ORDER = [
  'lahiri',
  'true_chitra',
  'kp',
  'raman',
  'surya_siddhanta',
] as const

type AyanamshaId = (typeof CANONICAL_ORDER)[number]

const DISPLAY_NAMES: Record<AyanamshaId, string> = {
  lahiri: 'Lahiri',
  true_chitra: 'True Chitra',
  kp: 'KP',
  raman: 'B.V. Raman',
  surya_siddhanta: 'Surya Siddhanta',
}

// ─── Build status type ────────────────────────────────────────────────────────

type BuildStatus =
  | 'not_built'
  | 'queued'
  | 'running'
  | 'complete'
  | 'failed'
  | 'cancelled'

// ─── Response shape ───────────────────────────────────────────────────────────

interface AyanamshaStatusItem {
  ayanamsha_id: AyanamshaId
  display_name: string
  latest_build_id: string | null
  status: BuildStatus
  finished_at: string | null
  engine_version: string | null
  is_latest_engine: boolean
  steps_complete: number
  steps_total: number
}

// ─── DB row types ─────────────────────────────────────────────────────────────

interface BuildRow {
  build_id: string
  status: string
  finished_at: string | null
  failed_at: string | null
  engine_version: string
  ayanamshas: string[] | null
  steps_complete: number | string
  steps_total: number | string
}

interface EngineVersionRow {
  version_str: string
}

// ─── Handler ──────────────────────────────────────────────────────────────────

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id: chartId } = await params

  if (!chartId?.trim()) {
    return NextResponse.json({ error: 'missing_chart_id' }, { status: 400 })
  }

  // ── Auth ───────────────────────────────────────────────────────────────────
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  // ── Fetch user role ────────────────────────────────────────────────────────
  const profileResult = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [user.uid],
  )
  const rawRole = profileResult.rows[0]?.role ?? ''
  const isSuperAdmin = rawRole === 'super_admin'

  // ── Verify chart ownership ─────────────────────────────────────────────────
  // super_admin can access any chart; regular user must own it.
  const chartResult = await query<{ chart_id: string }>(
    isSuperAdmin
      ? 'SELECT chart_id FROM charts WHERE chart_id=$1'
      : 'SELECT chart_id FROM charts WHERE chart_id=$1 AND owner_id=$2',
    isSuperAdmin ? [chartId] : [chartId, user.uid],
  )

  if (chartResult.rows.length === 0) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 })
  }

  // ── Resolve current engine version ─────────────────────────────────────────
  // Use the most recently added entry in engine_versions (is_current or latest
  // by created_at). If the table is empty, fall back to the builds column default.
  const engineVerResult = await query<EngineVersionRow>(
    `SELECT version_str
     FROM engine_versions
     ORDER BY created_at DESC
     LIMIT 1`,
    [],
  )
  const currentEngineVersion = engineVerResult.rows[0]?.version_str ?? null

  // ── Per-ayanamsha build lookup ─────────────────────────────────────────────
  // For each canonical ayanamsha, fetch the latest build for this chart that
  // contains that ayanamsha in its JSONB array, along with step counts.
  //
  // We run one query per ayanamsha (5 total) to keep the SQL simple and
  // individually indexable via builds_chart_idx (chart_id, queued_at DESC).
  //
  // The JSONB containment operator @> is used:
  //   b.ayanamshas @> '["lahiri"]'::jsonb
  // which is the correct way to check JSONB array membership in Postgres.

  const ayanamshaItems: AyanamshaStatusItem[] = []

  for (const ayanamshaId of CANONICAL_ORDER) {
    const containsExpr = JSON.stringify([ayanamshaId])

    const buildResult = await query<BuildRow>(
      `SELECT
         b.build_id,
         b.status,
         b.finished_at,
         b.failed_at,
         b.engine_version,
         b.ayanamshas,
         COUNT(DISTINCT bs.step_id) FILTER (WHERE bs.status = 'complete') AS steps_complete,
         COUNT(DISTINCT bs.step_id)                                         AS steps_total
       FROM builds b
       LEFT JOIN build_steps bs
         ON bs.build_id = b.build_id
            AND bs.ayanamsha_id = $2
       WHERE b.chart_id = $1
         AND b.ayanamshas @> $3::jsonb
       GROUP BY b.build_id, b.status, b.finished_at, b.failed_at,
                b.engine_version, b.ayanamshas, b.queued_at
       ORDER BY b.queued_at DESC
       LIMIT 1`,
      [chartId, ayanamshaId, containsExpr],
    )

    if (buildResult.rows.length === 0) {
      // No build has ever included this ayanamsha
      ayanamshaItems.push({
        ayanamsha_id: ayanamshaId,
        display_name: DISPLAY_NAMES[ayanamshaId],
        latest_build_id: null,
        status: 'not_built',
        finished_at: null,
        engine_version: null,
        is_latest_engine: false,
        steps_complete: 0,
        steps_total: 0,
      })
      continue
    }

    const row = buildResult.rows[0]
    const stepsComplete = Number(row.steps_complete) || 0
    const stepsTotal = Number(row.steps_total) || 0

    // Determine effective finished_at — prefer finished_at, fall back to failed_at
    const effectiveFinishedAt = row.finished_at ?? row.failed_at ?? null

    // is_latest_engine: compare build's engine_version with current engine.
    // If we have no current engine in the table, we cannot determine currency —
    // default to true (assume latest) to avoid spurious UI warnings.
    const isLatestEngine =
      currentEngineVersion === null
        ? true
        : row.engine_version === currentEngineVersion

    // Normalise status — the DB constraint ensures it's one of the valid values,
    // but we coerce for type safety.
    const status = (row.status as BuildStatus) ?? 'not_built'

    ayanamshaItems.push({
      ayanamsha_id: ayanamshaId,
      display_name: DISPLAY_NAMES[ayanamshaId],
      latest_build_id: row.build_id,
      status,
      finished_at: effectiveFinishedAt,
      engine_version: row.engine_version,
      is_latest_engine: isLatestEngine,
      steps_complete: stepsComplete,
      steps_total: stepsTotal,
    })
  }

  return NextResponse.json(ayanamshaItems, {
    status: 200,
    headers: {
      'Cache-Control': 'max-age=10',
    },
  })
}
