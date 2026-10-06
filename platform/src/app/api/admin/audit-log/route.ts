import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { readAudit } from '@/lib/admin/audit-read'
import { ZodError } from 'zod'
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
  source?: string
}

export async function GET(request: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  try {
    return NextResponse.json(await readAudit(new URL(request.url)),
      { headers: { 'Cache-Control': 'private, no-store' } })
  } catch (err) {
    if (err instanceof ZodError || err instanceof SyntaxError) return res.badRequest('Invalid audit filters or cursor.')
    console.error('[admin/audit-log] GET failed', err)
    return res.internal('Failed to load audit log.')
  }
}
