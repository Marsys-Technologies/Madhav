/**
 * GET /api/mcp/session   — return current session state for the authenticated user.
 * POST /api/mcp/session  — upsert session; optionally set active_chart_id.
 *
 * Both endpoints are service-to-service only (X-MCP-Internal-Token required).
 * The MCP sidecar passes the resolved principal's uid; this route is never
 * called directly by end-users.
 *
 * Request headers (both verbs):
 *   X-MCP-Internal-Token: <service-secret>
 *   X-MCP-User:           <user_uid>
 *   X-MCP-Role:           guest | super_admin
 *   X-MCP-Session-Key:    <opaque session key from the MCP client>
 *
 * POST body (JSON):
 *   { active_chart_id?: string | null }
 *
 * Responses:
 *   200: { session: McpSession }
 *   400: { error: string }    — missing required headers
 *   401: { error: string }    — invalid service token
 *   500: { error: string }    — DB error
 *
 * Security:
 *   - user_uid is NEVER read from the client body — always from X-MCP-User header
 *     (set by the MCP sidecar from the validated Bearer principal).
 *   - active_chart_id from POST body is stored as-is; entitlement is NOT
 *     checked here (the MCP sidecar checks it before calling this endpoint).
 *   - All DB ops are scoped to user_uid — no cross-user access.
 *
 * M3 — MCP elevation arc (2026-07-01).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { getOrCreateSession, updateActiveChart, listUserSessions } from '@/lib/mcp/sessions'

// ── Token validation ──────────────────────────────────────────────────────────

function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    // In development without a secret configured, allow through.
    if (process.env.NODE_ENV === 'development') return true
    return false
  }
  return token === expected
}

// ── GET — retrieve or create session ─────────────────────────────────────────

export async function GET(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const uid = request.headers.get('x-mcp-user')
  const sessionKey = request.headers.get('x-mcp-session-key')

  if (!uid) {
    return NextResponse.json({ error: 'X-MCP-User header required' }, { status: 400 })
  }
  if (!sessionKey) {
    return NextResponse.json({ error: 'X-MCP-Session-Key header required' }, { status: 400 })
  }

  try {
    const session = await getOrCreateSession(uid, sessionKey)
    return NextResponse.json({ session })
  } catch (err) {
    console.error('[api/mcp/session] GET error', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// ── POST — upsert session + optional active_chart_id ─────────────────────────

interface SessionPostBody {
  active_chart_id?: string | null
}

export async function POST(request: Request) {
  if (!validateServiceToken(request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const uid = request.headers.get('x-mcp-user')
  const sessionKey = request.headers.get('x-mcp-session-key')

  if (!uid) {
    return NextResponse.json({ error: 'X-MCP-User header required' }, { status: 400 })
  }
  if (!sessionKey) {
    return NextResponse.json({ error: 'X-MCP-Session-Key header required' }, { status: 400 })
  }

  let body: SessionPostBody = {}
  try {
    body = (await request.json()) as SessionPostBody
  } catch {
    // No body or invalid JSON — treat as empty update (just touch last_seen_at).
  }

  try {
    // Always upsert (touch last_seen_at); then update active_chart_id if supplied.
    const session = await getOrCreateSession(uid, sessionKey)

    if ('active_chart_id' in body) {
      await updateActiveChart(session.session_id, uid, body.active_chart_id ?? null)
      session.active_chart_id = body.active_chart_id ?? null
    }

    return NextResponse.json({ session })
  } catch (err) {
    console.error('[api/mcp/session] POST error', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

