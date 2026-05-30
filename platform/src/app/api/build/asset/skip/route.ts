/**
 * POST /api/build/asset/skip
 * [PHASE-C-07]
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { build_id, asset_id } = await req.json().catch(() => ({}))
  if (!build_id || !asset_id) {
    return NextResponse.json({ error: 'build_id and asset_id required' }, { status: 400 })
  }

  await query(
    `INSERT INTO build_checkpoints (build_id, asset_id, ayanamsha_id, status)
     VALUES ($1, $2, 'all', 'skipped')
     ON CONFLICT (build_id, asset_id, ayanamsha_id) DO UPDATE SET status = 'skipped'`,
    [build_id, asset_id],
  )

  return NextResponse.json({ ok: true })
}
