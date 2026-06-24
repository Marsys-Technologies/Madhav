import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type { AdminChart } from '@/components/admin/types'

export async function GET() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  try {
    const { rows } = await query<AdminChart>(`
      SELECT
        c.id,
        c.name,
        COALESCE(c.preferred_name, c.subject_name, c.name) AS subject_name,
        c.birth_date::text                                  AS birth_date,
        c.birth_place,
        c.owner_id,
        p.id       AS owner_profile_id,
        p.username AS owner_username,
        p.name     AS owner_name,
        COUNT(g.id)::int AS grant_count
      FROM charts c
      LEFT JOIN profiles p ON p.id = c.owner_id
      LEFT JOIN chart_grants g ON g.chart_id = c.id
      GROUP BY c.id, p.id, p.username, p.name
      ORDER BY c.created_at DESC
    `)
    return NextResponse.json({ charts: rows })
  } catch (err) {
    console.error('[admin/charts] GET failed', err)
    return res.internal('Failed to load charts.')
  }
}
