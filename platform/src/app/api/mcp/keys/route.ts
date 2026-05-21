/**
 * /api/mcp/keys — MCP API key administration endpoint.
 *
 * GET  — List keys (super_admin sees all; regular user sees own keys only).
 * POST — Create a new key (super_admin only). Returns the full_key ONCE.
 *
 * Auth: standard Firebase session cookie (same as all admin routes).
 * This is an admin UI endpoint called by browsers, NOT by the MCP server.
 * The MCP server uses validateMcpKey() from auth.ts directly.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { generateMcpKey } from '@/lib/mcp/auth'
import { res } from '@/lib/errors'
import type { McpApiKeyRow, McpKeyCreatedResponse } from '@/lib/mcp/types'

// ── GET — list keys ───────────────────────────────────────────────────────────

export async function GET() {
  const ctx = await getServerUserWithProfile()
  if (!ctx) return res.unauthenticated()

  try {
    let rows: McpApiKeyRow[]
    if (ctx.profile.role === 'super_admin') {
      // Admin sees all keys
      const result = await query<McpApiKeyRow>(
        `SELECT key_id, label, audience_tier, user_uid, scopes, created_at, last_used_at, revoked_at
         FROM mcp_api_keys
         ORDER BY created_at DESC`
      )
      rows = result.rows
    } else {
      // Regular user sees only their own keys
      const result = await query<McpApiKeyRow>(
        `SELECT key_id, label, audience_tier, user_uid, scopes, created_at, last_used_at, revoked_at
         FROM mcp_api_keys
         WHERE user_uid = $1
         ORDER BY created_at DESC`,
        [ctx.user.uid]
      )
      rows = result.rows
    }
    return NextResponse.json({ keys: rows })
  } catch (err) {
    console.error('[mcp:keys] GET error', err)
    return res.dbError()
  }
}

// ── POST — create key ─────────────────────────────────────────────────────────

interface CreateKeyBody {
  user_uid?: string
  audience_tier?: string
  label?: string
}

export async function POST(request: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  let body: CreateKeyBody
  try {
    body = await request.json()
  } catch {
    return res.badRequest('Invalid JSON body')
  }

  const targetUid = body.user_uid ?? auth.user.uid
  const audienceTier = body.audience_tier === 'super_admin' ? 'super_admin' : 'client'
  const label = body.label ? String(body.label).slice(0, 128) : null

  // Validate target user exists
  try {
    const { rows } = await query<{ id: string }>(
      'SELECT id FROM profiles WHERE id=$1 LIMIT 1',
      [targetUid]
    )
    if (!rows[0]) return res.notFound('user')
  } catch {
    return res.dbError()
  }

  // Determine env tag
  const env: 'prod' | 'dev' | 'test' =
    process.env.NODE_ENV === 'production' ? 'prod' :
    process.env.NODE_ENV === 'test' ? 'test' : 'dev'

  try {
    const { key_id, full_key, key_hash } = await generateMcpKey(env)

    await query(
      `INSERT INTO mcp_api_keys (key_id, key_hash, user_uid, audience_tier, label)
       VALUES ($1, $2, $3, $4, $5)`,
      [key_id, key_hash, targetUid, audienceTier, label]
    )

    const response: McpKeyCreatedResponse = {
      key_id,
      full_key,  // Shown ONCE — never retrievable again
      label,
      audience_tier: audienceTier,
      user_uid: targetUid,
      created_at: new Date().toISOString(),
    }
    return NextResponse.json(response, { status: 201 })
  } catch (err) {
    console.error('[mcp:keys] POST error', err)
    return res.internal('Key creation failed')
  }
}
