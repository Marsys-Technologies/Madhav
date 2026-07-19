/**
 * POST /api/mcp/oauth/clients/validate — validate a client_id + optional client_secret.
 *
 * Used by the token endpoint for client_credentials grant.
 * Service-to-service only (X-MCP-Internal-Token required).
 *
 * Body: { client_id: string, client_secret?: string }
 * Response 200: { valid: true, owner_uid, scopes } or { valid: false }
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { validateClient } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ valid: false, error: 'Unauthorized' }, { status: 401 })
  }

  let body: { client_id?: string; client_secret?: string }
  try {
    body = await request.json() as { client_id?: string; client_secret?: string }
  } catch {
    return NextResponse.json({ valid: false, error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.client_id) {
    return NextResponse.json({ valid: false, error: 'client_id required' }, { status: 400 })
  }

  try {
    const client = await validateClient(body.client_id, body.client_secret)
    if (!client) {
      return NextResponse.json({ valid: false })
    }
    return NextResponse.json({
      valid: true,
      owner_uid: client.owner_uid,
      scopes: client.scopes,
    })
  } catch (err) {
    console.error('[mcp:oauth:clients:validate] validateClient error:', err)
    return NextResponse.json({ valid: false, error: 'Internal error' }, { status: 500 })
  }
}
