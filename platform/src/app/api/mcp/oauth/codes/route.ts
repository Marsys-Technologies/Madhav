/**
 * POST /api/mcp/oauth/codes — create an auth code.
 * PATCH /api/mcp/oauth/codes — stamp a Firebase uid onto an existing code.
 *
 * Service-to-service only (X-MCP-Internal-Token required).
 *
 * POST body:
 *   { client_id, redirect_uri, scopes, uid?, pkce_challenge?, pkce_challenge_method? }
 *
 * PATCH body:
 *   { code, uid }
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { createAuthCode, stampAuthCodeUid } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: {
    client_id?: string
    redirect_uri?: string
    scopes?: string[]
    uid?: string
    pkce_challenge?: string
    pkce_challenge_method?: string
  }
  try {
    body = await request.json() as typeof body
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.client_id || !body.redirect_uri || !Array.isArray(body.scopes)) {
    return NextResponse.json({ error: 'client_id, redirect_uri, scopes required' }, { status: 400 })
  }

  try {
    const code = await createAuthCode({
      clientId: body.client_id,
      redirectUri: body.redirect_uri,
      scopes: body.scopes,
      uid: body.uid,
      pkceChallenge: body.pkce_challenge,
      pkceChallengeMethod: body.pkce_challenge_method,
    })
    return NextResponse.json({ code }, { status: 201 })
  } catch (err) {
    console.error('[mcp:oauth:codes] createAuthCode error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}

export async function PATCH(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { code?: string; uid?: string }
  try {
    body = await request.json() as { code?: string; uid?: string }
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.code || !body.uid) {
    return NextResponse.json({ error: 'code and uid required' }, { status: 400 })
  }

  try {
    const ok = await stampAuthCodeUid(body.code, body.uid)
    if (!ok) {
      return NextResponse.json({ error: 'Code not found, expired, or already consumed' }, { status: 404 })
    }
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('[mcp:oauth:codes] stampAuthCodeUid error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
