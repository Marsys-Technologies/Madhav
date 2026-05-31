/**
 * POST /api/build/reap
 *
 * Cron-invoked reaper. Cancels stale builds (DB rows in non-terminal states
 * whose containers have already terminated abnormally or were never picked up).
 *
 * Auth: OIDC token from Cloud Scheduler (service account check).
 * Schedule: every 15 minutes (see infra/cloud_scheduler/build_reaper.tf).
 *
 * Reap criteria:
 *   - status = 'running'   AND started_at  < NOW() - INTERVAL '1 hour'
 *   - status = 'queued'    AND created_at  < NOW() - INTERVAL '15 minutes'
 *   - status = 'cancelling' AND queued_at  < NOW() - INTERVAL '15 minutes'
 * Excludes any build_id whose Cloud Run execution is still Running (live-set check).
 *
 * Brief: CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md §L3
 */

import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { verifyOidcToken } from '@/lib/auth/oidc'
import { listLiveBuildExecutions } from '@/lib/cloud_run/jobs'

export const dynamic = 'force-dynamic'

export async function POST(request: Request): Promise<Response> {
  // ── Auth (OIDC from Cloud Scheduler) ──────────────────────────────────────
  const token = request.headers.get('Authorization')?.replace(/^Bearer /, '')
  if (!token) return NextResponse.json({ error: 'unauthorized' }, { status: 401 })

  const claims = await verifyOidcToken(token, {
    expectedAudience: process.env.NEXT_PUBLIC_APP_URL ?? 'https://amjis-web',
    expectedServiceAccount: process.env.BUILD_REAPER_SA_EMAIL,
  }).catch(() => null)
  if (!claims) return NextResponse.json({ error: 'forbidden' }, { status: 403 })

  // ── Live-execution exclusion set ───────────────────────────────────────────
  const liveBuildIds = await listLiveBuildExecutions().catch(() => new Set<string>())

  // ── Find candidates ────────────────────────────────────────────────────────
  const { rows } = await query<{ build_id: string; status: string; age_minutes: number }>(
    `SELECT build_id, status,
            EXTRACT(EPOCH FROM (NOW() - COALESCE(started_at, queued_at, created_at))) / 60 AS age_minutes
       FROM builds
      WHERE (status = 'running'    AND started_at < NOW() - INTERVAL '1 hour')
         OR (status = 'queued'     AND queued_at  < NOW() - INTERVAL '15 minutes')
         OR (status = 'cancelling' AND queued_at  < NOW() - INTERVAL '15 minutes')`,
  )

  const toReap = rows.filter((r) => !liveBuildIds.has(r.build_id))
  if (toReap.length === 0) {
    return NextResponse.json({ reaped: 0, candidates: rows.length, live_skipped: rows.length - toReap.length })
  }

  // ── Reap (atomic) ──────────────────────────────────────────────────────────
  const reapIds = toReap.map((r) => r.build_id)
  await query(
    `UPDATE builds
        SET status       = 'cancelled',
            finished_at  = COALESCE(finished_at, NOW()),
            cancelled_at = COALESCE(cancelled_at, NOW())
      WHERE build_id = ANY($1)`,
    [reapIds],
  )
  await query(
    `UPDATE build_steps
        SET status       = 'skipped',
            completed_at = COALESCE(completed_at, NOW())
      WHERE build_id = ANY($1)
        AND status IN ('running', 'queued')`,
    [reapIds],
  )
  await query(
    `INSERT INTO build_notifications (build_id, event_type, payload)
     SELECT build_id, 'build_cancelled',
            jsonb_build_object('reason', 'reaped_stale', 'reaped_at', NOW()::text)
       FROM unnest($1::uuid[]) AS build_id`,
    [reapIds],
  )

  return NextResponse.json({
    reaped: reapIds.length,
    candidates: rows.length,
    live_skipped: rows.length - toReap.length,
    build_ids: reapIds,
  })
}
