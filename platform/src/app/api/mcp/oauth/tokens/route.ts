/**
 * POST /api/mcp/oauth/tokens — issue a new access + refresh token pair.
 * DELETE /api/mcp/oauth/tokens — revoke all tokens for a uid (scoped).
 *
 * Service-to-service only (X-MCP-Internal-Token required).
 *
 * POST body: { uid: string, scopes: string[] }
 * DELETE body: { uid: string }
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { issueTokens, revokeTokensForUid } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { uid?: string; scopes?: string[] }
  try {
    body = await request.json() as { uid?: string; scopes?: string[] }
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.uid || !Array.isArray(body.scopes)) {
    return NextResponse.json({ error: 'uid and scopes required' }, { status: 400 })
  }

  // Fail-closed: never mint a token with 'anonymous' uid.
  if (!body.uid || body.uid === 'anonymous') {
    return NextResponse.json(
      { error: 'invalid_grant', error_description: 'cannot mint token for anonymous uid' },
      { status: 400 }
    )
  }

  try {
    const tokens = await issueTokens(body.uid, body.scopes)
    return NextResponse.json(tokens, { status: 201 })
  } catch (err) {
    console.error('[mcp:oauth:tokens] issueTokens error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}

export async function DELETE(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { uid?: string }
  try {
    body = await request.json() as { uid?: string }
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.uid) {
    return NextResponse.json({ error: 'uid required' }, { status: 400 })
  }

  try {
    await revokeTokensForUid(body.uid)
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('[mcp:oauth:tokens] revokeTokensForUid error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
