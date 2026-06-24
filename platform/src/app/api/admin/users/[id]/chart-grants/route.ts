import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type { AdminChartGrant } from '@/components/admin/types'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { id: guestId } = await params

  // Confirm the target user exists
  const { rows: userRows } = await query<{ id: string }>(
    'SELECT id FROM profiles WHERE id = $1',
    [guestId]
  )
  if (!userRows[0]) return res.notFound('User not found.')

  try {
    const { rows } = await query<AdminChartGrant>(`
      SELECT
        c.id,
        COALESCE(c.preferred_name, c.subject_name, c.name) AS subject_name,
        c.birth_date::text AS birth_date,
        c.birth_place,
        c.owner_id,
        p.username AS owner_username,
        (c.owner_id = $1)        AS is_own,
        (g.id IS NOT NULL)       AS granted
      FROM charts c
      LEFT JOIN profiles p  ON p.id  = c.owner_id
      LEFT JOIN chart_grants g ON g.chart_id = c.id AND g.principal_id = $1
      ORDER BY
        (g.id IS NOT NULL) DESC,
        (c.owner_id = $1)  ASC,
        c.created_at DESC
    `, [guestId])
    return NextResponse.json({ charts: rows })
  } catch (err) {
    console.error('[admin/users/chart-grants] GET failed', err)
    return res.internal('Failed to load chart grants.')
  }
}
