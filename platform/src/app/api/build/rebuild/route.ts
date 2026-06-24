/**
 * POST /api/build/rebuild
 * Enqueues a single-asset rebuild.
 * [PHASE-C-07]
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const body = await req.json().catch(() => null)
  const { asset_id, build_id, chart_id } = body ?? {}
  if (!asset_id || !build_id || !chart_id) {
    return NextResponse.json({ error: 'asset_id, build_id, chart_id required' }, { status: 400 })
  }

  await query(
    `INSERT INTO build_events (build_id, chart_id, event_type, payload, created_at)
     VALUES ($1, $2, 'rebuild_requested', $3::jsonb, NOW())`,
    [build_id, chart_id, JSON.stringify({ asset_id })],
  )

  return NextResponse.json({ ok: true })
}
