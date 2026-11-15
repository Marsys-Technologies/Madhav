/**
 * GET /api/charts/[id]/ayanamsha-status
 *
 * Authenticated compatibility notice for the retired per-ayanamsha build-status
 * contract. Existing session and chart-ownership checks precede the 410 notice;
 * no engine/build status is read or inferred here.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

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

  return NextResponse.json(
    {
      error: 'ENDPOINT_GONE',
      status: 'unavailable',
      message: 'The legacy per-ayanamsha build-status contract is retired. This endpoint returns a compatibility notice only, without chart data, build progress or consensus.',
      guidance: {
        cockpit: 'Use the current Cockpit for chart-level run and asset readiness. It does not provide per-ayanamsha engine versions or step progress.',
        preparation: 'Use current chart preparation checks for preparation requirements; they do not reproduce the retired five-frame status contract.',
        fact_cross_check: 'The chart_snapshot tool provides a separately labelled identity fact cross-check. It does not measure per-ayanamsha build progress or consensus.',
      },
    },
    { status: 410, headers: { 'Cache-Control': 'no-store' } },
  )
}
