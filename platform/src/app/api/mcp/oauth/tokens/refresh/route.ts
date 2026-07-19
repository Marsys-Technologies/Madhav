/**
 * POST /api/mcp/oauth/tokens/refresh — exchange a refresh token for a new pair.
 *
 * Service-to-service only (X-MCP-Internal-Token required).
 *
 * Body: { refresh_token: string }
 * Response 200: { access_token, refresh_token, expires_in, scope }
 * Response 400: invalid/expired refresh token.
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { refreshAccessToken } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { refresh_token?: string }
  try {
    body = await request.json() as { refresh_token?: string }
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.refresh_token) {
    return NextResponse.json({ error: 'refresh_token required' }, { status: 400 })
  }

  try {
    const tokens = await refreshAccessToken(body.refresh_token)
    if (!tokens) {
      return NextResponse.json(
        { error: 'invalid_grant', error_description: 'refresh_token expired or invalid' },
        { status: 400 }
      )
    }
    return NextResponse.json(tokens)
  } catch (err) {
    console.error('[mcp:oauth:tokens:refresh] refreshAccessToken error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
