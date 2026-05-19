/**
 * GET /api/panchang/charts
 *
 * Returns charts accessible to the authenticated user.
 * - Astrologer (super_admin role): all charts
 * - Client: only their own chart(s) (client_id = their uid)
 *
 * Used by useChartList hook to populate the Personalise dropdown.
 *
 * Phase: 4C-5 (Item 3 support route)
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

export async function GET() {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    // Determine role
    const profileResult = await query<{ role: string }>(
      'SELECT role FROM profiles WHERE id=$1',
      [user.uid],
    )
    const role = profileResult.rows[0]?.role ?? 'client'

    let charts: Array<{
      id: string
      name: string
      birth_date: string
      birth_place: string
      client_id: string
    }>

    if (role === 'super_admin' || role === 'astrologer') {
      // Astrologer / admin: see all charts
      const result = await query<{
        id: string
        name: string
        birth_date: string
        birth_place: string
        client_id: string
      }>(
        'SELECT id, name, birth_date, birth_place, client_id FROM charts ORDER BY created_at DESC',
      )
      charts = result.rows
    } else {
      // Client: only own chart(s) — client_id = Firebase uid
      const result = await query<{
        id: string
        name: string
        birth_date: string
        birth_place: string
        client_id: string
      }>(
        'SELECT id, name, birth_date, birth_place, client_id FROM charts WHERE client_id=$1 ORDER BY created_at DESC',
        [user.uid],
      )
      charts = result.rows
    }

    return NextResponse.json({ charts })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DB error'
    return res.internal(message)
  }
}
