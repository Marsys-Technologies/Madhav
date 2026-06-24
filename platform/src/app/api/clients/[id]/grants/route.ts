/**
 * /api/clients/[id]/grants — Sharing CRUD (Unit 3.consult_nav, Commit 3).
 *
 * Super-admin only. Mutates chart_grants for one chart_id.
 *   GET    → list current grantees
 *   POST   → grant view access to a principal_id
 *   DELETE → revoke a grant by principal_id
 *
 * Auth model: profile.role === 'super_admin' (no tier check — tier excision
 * is concurrent). Returns 401/403 with no body leakage.
 *
 * The chart_grants schema (migration 081) enforces permission ∈ {'view'}
 * via CHECK constraint, so any future widening is a SQL-only change.
 */

import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { NextResponse } from 'next/server'
import { writeAuditLog } from '@/lib/admin/audit'

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return { error: NextResponse.json({ error: 'unauthorized' }, { status: 401 }), user: null }
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') {
    return { error: NextResponse.json({ error: 'forbidden' }, { status: 403 }), user: null }
  }
  return { error: null, user }
}

export interface GrantRow {
  id: string
  chart_id: string
  principal_id: string
  permission: 'view'
  granted_by: string
  granted_at: string
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const auth = await requireSuperAdmin()
  if (auth.error) return auth.error

  const { rows } = await query<GrantRow>(
    'SELECT id, chart_id, principal_id, permission, granted_by, granted_at FROM chart_grants WHERE chart_id=$1 ORDER BY granted_at DESC',
    [id]
  )
  return NextResponse.json({ grants: rows })
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const auth = await requireSuperAdmin()
  if (auth.error) return auth.error

  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'invalid_body' }, { status: 400 })
  }

  const principalId = typeof body.principal_id === 'string' ? body.principal_id.trim() : ''
  if (!principalId) {
    return NextResponse.json({ error: 'principal_id_required' }, { status: 400 })
  }

  // Confirm the chart exists first — yields 404 distinct from 400.
  const chartCheck = await query<{ id: string; name: string }>('SELECT id, name FROM charts WHERE id=$1', [id])
  if (!chartCheck.rows[0]) {
    return NextResponse.json({ error: 'chart_not_found' }, { status: 404 })
  }

  // INSERT … ON CONFLICT — idempotent.
  const { rows } = await query<GrantRow>(
    `INSERT INTO chart_grants (chart_id, principal_id, permission, granted_by)
     VALUES ($1, $2, 'view', $3)
     ON CONFLICT (chart_id, principal_id) DO UPDATE SET granted_by = EXCLUDED.granted_by
     RETURNING id, chart_id, principal_id, permission, granted_by, granted_at`,
    [id, principalId, auth.user!.uid]
  )
  await writeAuditLog(auth.user!.uid, 'chart_grant', principalId, {
    chart_id: id,
    chart_name: chartCheck.rows[0].name,
  })
  return NextResponse.json({ grant: rows[0] }, { status: 201 })
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const auth = await requireSuperAdmin()
  if (auth.error) return auth.error

  const url = new URL(request.url)
  const principalId = url.searchParams.get('principal_id')?.trim() ?? ''
  if (!principalId) {
    return NextResponse.json({ error: 'principal_id_required' }, { status: 400 })
  }

  const { rows: chartMeta } = await query<{ name: string }>(
    'SELECT name FROM charts WHERE id=$1', [id]
  )

  const { rows } = await query<{ id: string }>(
    'DELETE FROM chart_grants WHERE chart_id=$1 AND principal_id=$2 RETURNING id',
    [id, principalId]
  )
  if (rows.length === 0) {
    return NextResponse.json({ error: 'grant_not_found' }, { status: 404 })
  }
  await writeAuditLog(auth.user!.uid, 'chart_revoke', principalId, {
    chart_id: id,
    chart_name: chartMeta[0]?.name ?? null,
  })
  return NextResponse.json({ revoked: rows[0].id })
}
