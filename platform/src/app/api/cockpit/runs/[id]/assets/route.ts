import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { blockedByAssetIdColumnPresent } from '@/lib/db/columnPresence'

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
    // Packet B2 — C-4, surface 2/3 (review B1_rereview2_20260926T193112Z.md,
    // "BLOCKS B2"): this route returned raw `bra.state` with no `disposition` at
    // all — a caller could not distinguish a cascade victim from a genuine root
    // failure without re-deriving it from `error` TEXT (the exact anti-pattern
    // Packet B1 removed everywhere else). Mirrors runs/active/route.ts's own C-2b
    // fix: `disposition` predates blocked_by_asset_id (selected unconditionally);
    // `blocked_by_asset_id` (migration 1201) is gated by the same process-cached
    // column probe stats/route.ts and runs/active/route.ts already use — never
    // select a column that may not exist yet in this environment.
    const includeBlockedBy = await blockedByAssetIdColumnPresent()
    const blockedByCol = includeBlockedBy ? 'bra.blocked_by_asset_id' : 'NULL::text AS blocked_by_asset_id'
    const { rows } = await query<{
      asset_id: string
      position: number
      state: string
      started_at: string | null
      ended_at: string | null
      error: string | null
      disposition: string | null
      blocked_by_asset_id: string | null
      sanskrit_name: string
      english_name: string
      layer: string
      target_floor: number | null
      rows_written: number | null
    }>(`
      SELECT
        bra.asset_id, bra.position, bra.state, bra.started_at, bra.ended_at,
        COALESCE(bra.error, at2.last_error) AS error,
        bra.disposition, ${blockedByCol},
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
