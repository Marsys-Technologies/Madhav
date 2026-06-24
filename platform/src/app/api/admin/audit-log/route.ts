import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

export interface AuditLogEntry {
  id: string
  actor_id: string | null
  actor_name: string | null
  actor_email: string | null
  action: string
  target_user_id: string | null
  target_name: string | null
  target_email: string | null
  detail: Record<string, unknown> | null
  created_at: string
}

export async function GET() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  try {
    const { rows } = await query<AuditLogEntry>(`
      SELECT
        l.id::text,
        l.actor_id,
        actor.name  AS actor_name,
        actor.email AS actor_email,
        l.action,
        l.target_user_id,
        target.name  AS target_name,
        target.email AS target_email,
        l.detail,
        l.created_at
      FROM admin_audit_log l
      LEFT JOIN profiles actor  ON actor.id  = l.actor_id
      LEFT JOIN profiles target ON target.id = l.target_user_id
      ORDER BY l.created_at DESC
      LIMIT 100
    `)
    return NextResponse.json({ entries: rows })
  } catch (err) {
    console.error('[admin/audit-log] GET failed', err)
    return res.internal('Failed to load audit log.')
  }
}
