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
 *   - status = 'running'    AND started_at < NOW() - INTERVAL '1 hour'
 *   - status = 'queued'     AND queued_at  < NOW() - INTERVAL '15 minutes'
 *   - status = 'cancelling' AND COALESCE(started_at, queued_at) < NOW() - INTERVAL '15 minutes'
 * Excludes any build_id whose Cloud Run execution is still Running (live-set check).
 *
 * Brief: CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md §L3
 */

import { NextResponse } from 'next/server'
import { getPool } from '@/lib/db/client'
import { verifyOidcToken } from '@/lib/auth/oidc'
import { listLiveBuildExecutions } from '@/lib/cloud_run/jobs'

export const dynamic = 'force-dynamic'

// APP_URL must be set as a Cloud Run runtime env var so this server-side route
// can read it at request time. NEXT_PUBLIC_APP_URL is inlined at build time
// and acts as a fallback; the hardcoded URL is the last resort.
const AUDIENCE =
  process.env.APP_URL ??
  process.env.NEXT_PUBLIC_APP_URL ??
  'https://amjis-web-938361928218.asia-south1.run.app'

export async function POST(request: Request): Promise<Response> {
  // ── Auth (OIDC from Cloud Scheduler) ──────────────────────────────────────
  const token = request.headers.get('Authorization')?.replace(/^Bearer /, '')
  if (!token) return NextResponse.json({ error: 'unauthorized' }, { status: 401 })

  const claims = await verifyOidcToken(token, {
    expectedAudience: AUDIENCE,
    expectedServiceAccount: process.env.BUILD_REAPER_SA_EMAIL,
  }).catch(() => null)

  if (!claims) return NextResponse.json({ error: 'forbidden' }, { status: 403 })

  // Belt-and-suspenders: if BUILD_REAPER_SA_EMAIL is not configured, still
  // require a GCP service account identity (not just any Google OIDC token).
  const saEmail = process.env.BUILD_REAPER_SA_EMAIL
  if (!saEmail && !claims.email.endsWith('.gserviceaccount.com')) {
    return NextResponse.json({ error: 'forbidden' }, { status: 403 })
  }

  // ── Find candidates first (avoids Cloud Run API call when nothing is stale) ─
  const pool = await getPool()
  const candidateResult = await pool.query<{ build_id: string; status: string; age_minutes: number }>(
    `SELECT build_id, status,
            EXTRACT(EPOCH FROM (NOW() - COALESCE(started_at, queued_at))) / 60 AS age_minutes
       FROM builds
      WHERE (status = 'running'    AND started_at                       < NOW() - INTERVAL '1 hour')
         OR (status = 'queued'     AND queued_at                        < NOW() - INTERVAL '15 minutes')
         OR (status = 'cancelling' AND COALESCE(started_at, queued_at) < NOW() - INTERVAL '15 minutes')`,
  )
  const rows = candidateResult.rows

  if (rows.length === 0) {
    return NextResponse.json({ reaped: 0, candidates: 0, live_skipped: 0 })
  }

  // ── Live-execution exclusion set (only fetched when candidates exist) ──────
  const liveBuildIds = await listLiveBuildExecutions().catch(() => new Set<string>())

  const toReap = rows.filter((r) => !liveBuildIds.has(r.build_id))
  if (toReap.length === 0) {
    return NextResponse.json({ reaped: 0, candidates: rows.length, live_skipped: rows.length })
  }

  // ── Reap (single transaction — all three writes succeed or all roll back) ──
  const reapIds = toReap.map((r) => r.build_id)
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(
      `UPDATE builds
          SET status       = 'cancelled',
              finished_at  = COALESCE(finished_at, NOW()),
              cancelled_at = COALESCE(cancelled_at, NOW())
        WHERE build_id = ANY($1)`,
      [reapIds],
    )
    await client.query(
      `UPDATE build_steps
          SET status       = 'skipped',
              completed_at = COALESCE(completed_at, NOW())
        WHERE build_id = ANY($1)
          AND status IN ('running', 'queued')`,
      [reapIds],
    )
    await client.query(
      `INSERT INTO build_notifications (build_id, event_type, payload)
       SELECT build_id, 'build_cancelled',
              jsonb_build_object('reason', 'reaped_stale', 'reaped_at', NOW()::text)
         FROM unnest($1::uuid[]) AS build_id`,
      [reapIds],
    )
    await client.query('COMMIT')
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {})
    throw err
  } finally {
    client.release()
  }

  return NextResponse.json({
    reaped: reapIds.length,
    candidates: rows.length,
    live_skipped: rows.length - toReap.length,
    build_ids: reapIds,
  })
}
