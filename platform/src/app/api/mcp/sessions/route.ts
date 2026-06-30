/**
 * GET /api/mcp/sessions — list all sessions for the authenticated user.
 *
 * Service-to-service only (X-MCP-Internal-Token required). Returns the user's
 * session history (most recently seen first) for recall_session / list_my_sessions
 * MCP tools. Results are scoped strictly to the requesting user_uid.
 *
 * Request headers:
 *   X-MCP-Internal-Token: <service-secret>
 *   X-MCP-User:           <user_uid>
 *
 * Query params:
 *   limit: number (optional, default 20, max 50)
 *
 * Response:
 *   200: { sessions: McpSessionSummary[] }
 *   400: { error: string }
 *   401: { error: string }
 *   500: { error: string }
 *
 * M3 — MCP elevation arc (2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { listUserSessions } from '@/lib/mcp/sessions'

function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    if (process.env.NODE_ENV === 'development') return true
    return false
  }
  return token === expected
}

export async function GET(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const uid = request.headers.get('x-mcp-user')
  if (!uid) {
    return NextResponse.json({ error: 'X-MCP-User header required' }, { status: 400 })
  }

  const url = new URL(request.url)
  const limitParam = parseInt(url.searchParams.get('limit') ?? '20', 10)
  const limit = Math.min(isNaN(limitParam) ? 20 : limitParam, 50)

  try {
    const sessions = await listUserSessions(uid, limit)
    return NextResponse.json({ sessions })
  } catch (err) {
    console.error('[api/mcp/sessions] GET error', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
