/**
 * GET /api/panchang/charts
 *
 * Returns charts accessible to the authenticated user.
 * - Super admin: all charts
 * - Guest: charts they own or have a view grant for
 *
 * Used by useChartList hook to populate the Personalise dropdown.
 *
 * Phase: 4C-5 (Item 3 support route)
 */

import { NextResponse } from 'next/server'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

export async function GET() {
  try {
    const ctx = await getServerUserWithProfile()
    if (!ctx) return res.unauthenticated()
    if (ctx.profile.status !== 'active') return res.forbidden()

    const result = ctx.profile.role === 'super_admin'
      ? await query('SELECT id, name, birth_date FROM charts ORDER BY created_at DESC')
      : await query(
          `SELECT c.id, c.name, c.birth_date
           FROM charts c
           WHERE c.owner_id = $1
              OR EXISTS (
                SELECT 1 FROM chart_grants g
                WHERE g.chart_id = c.id AND g.principal_id = $1 AND g.permission = 'view'
              )
           ORDER BY c.created_at DESC`,
          [ctx.user.uid],
        )

    return NextResponse.json({ charts: result.rows })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error'
    return res.internal(message)
  }
}
