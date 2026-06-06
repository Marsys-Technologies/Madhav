import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const user = await requireSuperAdmin()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const { id } = await params

  const result = await query<{ id: string }>(
    `UPDATE build_runs
     SET stop_requested_at = NOW()
     WHERE id=$1 AND state IN ('running','paused')
     RETURNING id`,
    [id]
  )

  if (result.rows.length === 0) {
    return NextResponse.json({ error: 'Run not found or already completed/stopped' }, { status: 404 })
  }

  return NextResponse.json({ data: { run_id: id, stop_requested: true } })
}
