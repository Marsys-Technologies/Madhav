/**
 * /api/mcp/keys/[key_id] — MCP API key revocation.
 *
 * DELETE — Revoke a key. Super_admin can revoke any key; a user can revoke
 *          only their own keys.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { query, withTransaction } from '@/lib/db/client'
import { res } from '@/lib/errors'

interface RouteParams {
  params: Promise<{ key_id: string }>
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) return res.unauthenticated()
  if (ctx.profile.status !== 'active') return res.forbidden()

  const { key_id } = await params

  try {
    // Fetch the key to verify ownership
    const { rows } = await query<{ key_id: string; user_uid: string; revoked_at: string | null }>(
      'SELECT key_id, user_uid, revoked_at FROM mcp_api_keys WHERE key_id=$1',
      [key_id]
    )
    const keyRow = rows[0]
    if (!keyRow) return res.notFound('key')

    // Permission check: super_admin can revoke any; user can only revoke own keys
    if (ctx.profile.role !== 'super_admin' && keyRow.user_uid !== ctx.user.uid) {
      return res.forbidden()
    }

    if (keyRow.revoked_at) {
      return NextResponse.json({ message: 'Key already revoked', key_id }, { status: 200 })
    }

    await withTransaction(async client => {
      const changed = await client.query(
        'UPDATE mcp_api_keys SET revoked_at = now() WHERE key_id = $1 AND revoked_at IS NULL RETURNING key_id', [key_id])
      if (changed.rowCount) await client.query(`INSERT INTO admin_audit_log (actor_id, action, target_user_id, detail)
        VALUES ($1, 'mcp_key_revoked', $2, $3)`,
      [ctx.user.uid, keyRow.user_uid, JSON.stringify({ key_id })])
    })

    return NextResponse.json({ message: 'Key revoked', key_id }, { status: 200 })
  } catch (err) {
    console.error('[mcp:keys] DELETE error', err)
    return res.dbError()
  }
}
