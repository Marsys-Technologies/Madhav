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
import { validateClient, getClientMetadata } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ valid: false, error: 'Unauthorized' }, { status: 401 })
  }

  let body: { client_id?: string; client_secret?: string; metadata_only?: boolean }
  try {
    body = await request.json() as { client_id?: string; client_secret?: string; metadata_only?: boolean }
  } catch {
    return NextResponse.json({ valid: false, error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.client_id) {
    return NextResponse.json({ valid: false, error: 'client_id required' }, { status: 400 })
  }

  // SF-004 (PARIŚEṢA-V4): lookup-only mode for /authorize's redirect_uri
  // allowlist check. Fully separate from the secret-required branch below —
  // never calls validateClient, never touches SF-002's guard. Returns ONLY
  // non-secret fields; see SF004_OAUTH_BINDING_CONTRACT_v1_0.md §4.
  // Strict `=== true` check: a truthy-but-not-literal-true value must not
  // divert this request away from the authenticating path below.
  if (body.metadata_only === true) {
    try {
      const metadata = await getClientMetadata(body.client_id)
      if (!metadata) {
        return NextResponse.json({ found: false })
      }
      return NextResponse.json({
        found: true,
        redirect_uris: metadata.redirect_uris,
        scopes: metadata.scopes,
      })
    } catch (err) {
      console.error('[mcp:oauth:clients:validate] getClientMetadata error:', err)
      return NextResponse.json({ found: false, error: 'Internal error' }, { status: 500 })
    }
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
