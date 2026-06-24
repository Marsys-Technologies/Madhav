/**
 * POST /api/build/continue
 * Resumes the most recent build for the given chart_id.
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

  // Get latest build
  const { rows } = await query<{ build_id: string }>(
    `SELECT id AS build_id FROM builds WHERE chart_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [chart_id],
  )
  const build_id = rows[0]?.build_id
  if (!build_id) return NextResponse.json({ error: 'no prior build found' }, { status: 404 })

  await query(
    `INSERT INTO build_events (build_id, chart_id, event_type, payload, created_at)
     VALUES ($1, $2, 'resume_requested', '{}', NOW())`,
    [build_id, chart_id],
  )

  return NextResponse.json({ ok: true, build_id })
}
