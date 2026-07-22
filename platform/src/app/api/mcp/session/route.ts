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
 * GET query params:
 *   ?pin_chart_id=<uuid>  — optional (R5 W4, design §10.6/§31.3/§31.5). When present,
 *                           resolves (and persists if new/drifted) the provenance stamp
 *                           for this chart_id and includes it in the response as
 *                           `provenance_stamp` + any `judgment_flags`. chart_id is ALWAYS
 *                           explicit here — never inferred from active_chart_id (the
 *                           §31.3 mitigation: correctness never rests on active_chart).
 *
 * POST body (JSON):
 *   { active_chart_id?: string | null, pin_chart_id?: string }
 *   pin_chart_id: same semantics as the GET query param — resolves/refreshes the
 *   provenance stamp for this chart_id after the active_chart_id write (if any).
 *   Independent of active_chart_id so a caller can stamp a chart without also
 *   making it "active".
 *
 * Responses:
 *   200: { session: McpSession, provenance_stamp?: ProvenanceStampValues, judgment_flags?: string[] }
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
 *   - pin_chart_id is NOT an entitlement check either (same as active_chart_id) —
 *     the MCP sidecar/tool layer must already have authorized the chart before
 *     ever passing its chart_id here.
 *
 * M3 — MCP elevation arc (2026-07-01). Provenance stamp — R5 W4 (2026-07-09).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import {
  getOrCreateSession,
  updateActiveChart,
  listUserSessions,
  getOrRefreshProvenanceStamp,
} from '@/lib/mcp/sessions'
import { validateServiceToken } from '@/lib/mcp/service_token'

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

  const url = new URL(request.url)
  const pinChartId = url.searchParams.get('pin_chart_id')

  try {
    const session = await getOrCreateSession(uid, sessionKey)

    if (pinChartId) {
      const { pin, judgment_flags } = await getOrRefreshProvenanceStamp(
        session.session_id,
        uid,
        pinChartId
      )
      return NextResponse.json({
        session,
        provenance_stamp: pin,
        ...(judgment_flags.length > 0 ? { judgment_flags } : {}),
      })
    }

    return NextResponse.json({ session })
  } catch (err) {
    console.error('[api/mcp/session] GET error', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// ── POST — upsert session + optional active_chart_id ─────────────────────────

interface SessionPostBody {
  active_chart_id?: string | null
  pin_chart_id?: string
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

    if (body.pin_chart_id) {
      const { pin, judgment_flags } = await getOrRefreshProvenanceStamp(
        session.session_id,
        uid,
        body.pin_chart_id
      )
      return NextResponse.json({
        session,
        provenance_stamp: pin,
        ...(judgment_flags.length > 0 ? { judgment_flags } : {}),
      })
    }

    return NextResponse.json({ session })
  } catch (err) {
    console.error('[api/mcp/session] POST error', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

