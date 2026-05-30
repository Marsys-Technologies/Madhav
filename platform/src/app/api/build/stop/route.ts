/**
 * POST /api/build/stop
 * Sets stop_requested on all events for a build.
 * [PHASE-C-07]
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { build_id } = await req.json().catch(() => ({}))
  if (!build_id) return NextResponse.json({ error: 'build_id required' }, { status: 400 })

  await query(
    `UPDATE build_events SET stop_requested = true WHERE build_id = $1`,
    [build_id],
  )

  return NextResponse.json({ ok: true })
}
