/**
 * POST /api/mcp/oauth/clients — dynamic client registration.
 *
 * Called by the MCP sidecar's POST /oauth/register endpoint.
 * Writes to mcp_oauth_clients (migration 383).
 *
 * Service-to-service only: X-MCP-Internal-Token required.
 * The owner_uid comes from the X-MCP-User header (resolved principal — never client body).
 *
 * Request (JSON body):
 *   { redirect_uris: string[], scopes?: string[] }
 *
 * Response (201):
 *   { client_id: string, client_secret: string }
 *   ↑ client_secret is plaintext — only time it is returned; hash stored in DB.
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { registerClient } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const ownerUid = request.headers.get('x-mcp-user')
  if (!ownerUid) {
    return NextResponse.json({ error: 'X-MCP-User header required' }, { status: 400 })
  }

  let body: { redirect_uris?: string[]; scopes?: string[] }
  try {
    body = await request.json() as { redirect_uris?: string[]; scopes?: string[] }
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!Array.isArray(body.redirect_uris) || body.redirect_uris.length === 0) {
    return NextResponse.json({ error: 'redirect_uris required (non-empty array)' }, { status: 400 })
  }

  try {
    const result = await registerClient({
      ownerUid,
      redirectUris: body.redirect_uris,
      scopes: body.scopes,
    })
    return NextResponse.json(result, { status: 201 })
  } catch (err) {
    console.error('[mcp:oauth:clients] registerClient error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
