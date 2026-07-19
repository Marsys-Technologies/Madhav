/**
 * POST /api/mcp/oauth/codes/consume — consume (one-time-use) an auth code.
 *
 * Returns the code record (with uid, scopes, PKCE info) so the token endpoint
 * can issue tokens. Stamps consumed_at atomically — replay is impossible.
 *
 * Service-to-service only (X-MCP-Internal-Token required).
 *
 * Body: { code: string }
 *
 * Response 200: the consumed auth code record.
 * Response 400: code not found, expired, or already consumed.
 *
 * M5 — MCP elevation arc (production OAuth, 2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { consumeAuthCode } from '@/lib/mcp/oauth/store'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { code?: string }
  try {
    body = await request.json() as { code?: string }
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  if (!body.code) {
    return NextResponse.json({ error: 'code required' }, { status: 400 })
  }

  try {
    const record = await consumeAuthCode(body.code)
    if (!record) {
      return NextResponse.json(
        { error: 'invalid_grant', error_description: 'code expired, consumed, or not found' },
        { status: 400 }
      )
    }
    return NextResponse.json({ record })
  } catch (err) {
    console.error('[mcp:oauth:codes:consume] consumeAuthCode error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}
