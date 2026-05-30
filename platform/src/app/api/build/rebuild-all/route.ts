/**
 * POST /api/build/rebuild-all
 * Enqueues a full chart rebuild.
 * [PHASE-C-07]
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { chart_id } = await req.json().catch(() => ({}))
  if (!chart_id) return NextResponse.json({ error: 'chart_id required' }, { status: 400 })

  const { rows } = await query<{ build_id: string }>(
    `INSERT INTO build_events (build_id, chart_id, event_type, payload, created_at)
     VALUES (gen_random_uuid(), $1, 'rebuild_all_requested', '{}', NOW())
     RETURNING build_id`,
    [chart_id],
  )

  return NextResponse.json({ ok: true, build_id: rows[0]?.build_id })
}
