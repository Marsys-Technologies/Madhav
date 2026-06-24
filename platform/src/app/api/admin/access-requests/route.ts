import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

export async function GET() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  try {
    const { rows } = await query<{
      id: string
      full_name: string
      email: string
      reason: string | null
      status: string
      requested_at: string
      reviewed_at: string | null
      approved_user_id: string | null
      approved_username: string | null
      approved_name: string | null
    }>(`
      SELECT
        ar.id,
        ar.full_name,
        ar.email,
        ar.reason,
        ar.status,
        ar.requested_at,
        ar.reviewed_at,
        ar.approved_user_id,
        p.username AS approved_username,
        p.name     AS approved_name
      FROM access_requests ar
      LEFT JOIN profiles p ON p.id = ar.approved_user_id
      ORDER BY ar.requested_at DESC
    `)
    return NextResponse.json({ requests: rows })
  } catch (err) {
    console.error('[admin/access-requests] query failed', err)
    return res.internal('Failed to load requests.')
  }
}
