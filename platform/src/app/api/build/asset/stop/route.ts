/**
 * POST /api/build/asset/stop
 * [PHASE-C-07]
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { requireBuildControl } from '@/lib/auth/requireBuildControl'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { build_id, asset_id } = await req.json().catch(() => ({}))
  if (!build_id || !asset_id) {
    return NextResponse.json({ error: 'build_id and asset_id required' }, { status: 400 })
  }

  // SS N-373: chart owner or super_admin only. The chart is resolved server-side
  // from build_id; a build tied to no chart is super_admin only.
  const denied = await requireBuildControl({ uid: user.uid, buildId: String(build_id) })
  if (denied) return denied

  await query(
    `UPDATE build_events SET stop_requested = true
     WHERE build_id = $1 AND (payload->>'asset_id') = $2`,
    [build_id, asset_id],
  )

  return NextResponse.json({ ok: true })
}
