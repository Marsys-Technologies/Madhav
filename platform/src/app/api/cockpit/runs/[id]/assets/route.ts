import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const maxDuration = 8

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const user = await requireSuperAdmin()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const { id } = await params

  try {
    const { rows } = await query<{
      asset_id: string
      position: number
      state: string
      started_at: string | null
      ended_at: string | null
      error: string | null
      sanskrit_name: string
      english_name: string
      layer: string
      target_floor: number | null
      rows_written: number | null
    }>(`
      SELECT
        bra.asset_id, bra.position, bra.state, bra.started_at, bra.ended_at,
        COALESCE(bra.error, at2.last_error) AS error,
        ar.sanskrit_name, ar.english_name, ar.layer, ar.target_floor,
        at2.rows_written
      FROM build_run_assets bra
      JOIN build_runs br ON br.id = bra.run_id
      JOIN asset_registry ar ON ar.asset_id = bra.asset_id
      LEFT JOIN asset_throughput at2
        ON at2.asset_id = bra.asset_id
        AND at2.chart_id = br.chart_id
        AND at2.ayanamsha_id IS NULL
      WHERE bra.run_id = $1
      ORDER BY bra.position
    `, [id])

    return NextResponse.json({ data: { run_assets: rows } })
  } catch (err) {
    console.error('[cockpit/runs/assets]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}
