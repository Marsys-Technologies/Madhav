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
 *   - pin_chart_id IS entitlement-checked (V3-E-011 finding 1 fix,
 *     2026-08-28): unlike active_chart_id, pin_chart_id drives
 *     `getOrRefreshProvenanceStamp`, which resolves and persists a
 *     provenance stamp (build_id/build_status/ledger_version/priors_version/
 *     now_context_date) for whatever chart_id is passed — the calling tool
 *     layer (`session_recall`) was found to let an explicitly-passed
 *     `chart_id` argument win over the session's own entitled chart without
 *     itself re-checking ownership, so this route can no longer assume the
 *     caller already authorized the chart. Both GET (`pin_chart_id` query
 *     param) and POST (`pin_chart_id` body field) now run
 *     `authorizeChartAccess` (read/'view'-or-better) before ever calling
 *     `getOrRefreshProvenanceStamp`, mirroring the same brain
 *     `/api/mcp/bundles/[name]/route.ts` and `/api/mcp/prashna_ask/route.ts`
 *     already gate chart_id on. A denied chart never reaches
 *     `getOrRefreshProvenanceStamp` — no stamp is computed OR persisted.
 *
 * Responses (pin_chart_id path only):
 *   401: { error: 'AUTHZ_DENIED', chartId, denial: {...} } — caller has no
 *        'view'-or-better grant on the requested pin_chart_id.
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
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { query } from '@/lib/db/client'

// ── pin_chart_id authorization gate (V3-E-011 finding 1) ────────────────────
//
// Shared by GET and POST: resolves the caller's role and runs the same
// `authorizeChartAccess` brain every other /api/mcp/* route gates chart_id
// access through (see bundles/[name]/route.ts, prashna_ask/route.ts). Returns
// a ready-to-return 401 NextResponse on denial, or null when access is
// granted ('all' owner/super_admin, or 'view' chart_grants). This is a
// metadata READ (provenance stamp), so 'view' is sufficient — not a
// write-level check.
async function denyPinChartAccess(uid: string, chartId: string): Promise<NextResponse | null> {
  const role = await resolveMcpPrincipalRole(uid)
  const perm = await authorizeChartAccess({ principal: { uid, role }, chartId, db: { query } })
  if (perm === 'deny') {
    return NextResponse.json(
      {
        error: 'AUTHZ_DENIED',
        chartId,
        denial: {
          reason: 'entitlement' as const,
          chart_id: chartId,
          permission_found: 'deny' as const,
          permission_required: 'view' as const,
          distinct_from_empty: true as const,
        },
      },
      { status: 401 }
    )
  }
  return null
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

  const url = new URL(request.url)
  const pinChartId = url.searchParams.get('pin_chart_id')

  try {
    const session = await getOrCreateSession(uid, sessionKey)

    if (pinChartId) {
      const denied = await denyPinChartAccess(uid, pinChartId)
      if (denied) return denied

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
      const denied = await denyPinChartAccess(uid, body.pin_chart_id)
      if (denied) return denied

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

