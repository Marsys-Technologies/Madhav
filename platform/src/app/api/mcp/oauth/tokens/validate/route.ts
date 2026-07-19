/**
 * GET /api/mcp/oauth/tokens/validate — validate an OAuth access token.
 *
 * Called by the MCP sidecar to validate an incoming Bearer OAuth token.
 * Returns { valid: true, uid, scopes } or { valid: false }.
 *
 * Service-to-service only (X-MCP-Internal-Token required).
 * Token passed via Authorization: Bearer <token> header.
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { validateAccessToken } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function GET(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ valid: false, error: 'Unauthorized' }, { status: 401 })
  }

  const authHeader = request.headers.get('x-mcp-oauth-token')
  if (!authHeader) {
    return NextResponse.json({ valid: false, error: 'X-MCP-OAuth-Token header required' }, { status: 400 })
  }

  try {
    const record = await validateAccessToken(authHeader)
    if (!record) {
      return NextResponse.json({ valid: false })
    }
    return NextResponse.json({ valid: true, uid: record.uid, scopes: record.scopes })
  } catch (err) {
    console.error('[mcp:oauth:tokens:validate] validateAccessToken error:', err)
    return NextResponse.json({ valid: false, error: 'Internal error' }, { status: 500 })
  }
}
