/**
 * POST /api/build/cancel/[buildId]
 *
 * Requests cancellation of an in-flight or queued build.
 *
 * Behaviour:
 *   1. Auth: user must be authenticated (401 if not).
 *   2. Look up build by buildId — 404 if not found.
 *   3. Ownership: build.triggered_by_uid must match authenticated user, OR
 *      the user must be super_admin. Returns 403 if neither condition holds.
 *   4. Status gating:
 *        - 'queued' | 'running'    → update to 'cancelling', return 200
 *        - 'cancelling'            → already in progress, return 200 (idempotent)
 *        - 'cancelled' | 'complete' | 'failed' → 409 (terminal, cannot cancel)
 *   5. Returns { message, build_id } on success.
 *
 * [BUILD-ORCH-D-02] /api/build/cancel/[buildId] endpoint.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// ─── Terminal statuses (cannot be cancelled) ────────────────────────────────

const TERMINAL_STATUSES = ['cancelled', 'complete', 'failed'] as const
const CANCELLABLE_STATUSES = ['queued', 'running'] as const

type BuildStatus =
  | (typeof TERMINAL_STATUSES)[number]
  | (typeof CANCELLABLE_STATUSES)[number]
  | 'cancelling'

// ─── Handler ─────────────────────────────────────────────────────────────────

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ buildId: string }> },
): Promise<Response> {
  const { buildId } = await params

  if (!buildId?.trim()) {
    return NextResponse.json({ error: 'missing_build_id' }, { status: 400 })
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

  // ── Look up build ──────────────────────────────────────────────────────────
  const buildResult = await query<{
    build_id: string
    triggered_by_uid: string
    status: BuildStatus
  }>(
    'SELECT build_id, triggered_by_uid, status FROM builds WHERE build_id=$1',
    [buildId],
  )

  if (!buildResult.rows[0]) {
    return NextResponse.json({ error: 'build_not_found' }, { status: 404 })
  }

  const build = buildResult.rows[0]

  // ── Ownership check ────────────────────────────────────────────────────────
  if (!isSuperAdmin && build.triggered_by_uid !== user.uid) {
    return NextResponse.json({ error: 'forbidden' }, { status: 403 })
  }

  // ── Status gating ──────────────────────────────────────────────────────────

  // Already cancelling — idempotent OK
  if (build.status === 'cancelling') {
    return NextResponse.json(
      { message: 'Cancellation already in progress', build_id: buildId },
      { status: 200 },
    )
  }

  // Terminal statuses — cannot cancel
  if ((TERMINAL_STATUSES as readonly string[]).includes(build.status)) {
    return NextResponse.json(
      {
        error: 'Build cannot be cancelled',
        current_status: build.status,
        build_id: buildId,
      },
      { status: 409 },
    )
  }

  // Cancellable statuses ('queued' | 'running') — update to 'cancelling'
  if (!(CANCELLABLE_STATUSES as readonly string[]).includes(build.status)) {
    // Unknown status — treat as non-cancellable
    return NextResponse.json(
      {
        error: 'Build cannot be cancelled',
        current_status: build.status,
        build_id: buildId,
      },
      { status: 409 },
    )
  }

  await query(
    `UPDATE builds SET status='cancelling', cancelled_at=NOW() WHERE build_id=$1`,
    [buildId],
  )

  return NextResponse.json(
    { message: 'Cancellation requested', build_id: buildId },
    { status: 200 },
  )
}
