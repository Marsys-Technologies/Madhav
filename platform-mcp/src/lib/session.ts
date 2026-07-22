/**
 * session.ts — MCP sidecar session helper (M3).
 *
 * Delegates to the platform's /api/mcp/session and /api/mcp/sessions endpoints.
 * The MCP sidecar has no direct DB access — it calls the platform via HTTP.
 *
 * Session key:
 *   The MCP client sends an optional X-MCP-Session-Key header. If absent,
 *   the server falls back to a default key derived from the user uid ("default").
 *   This preserves backward compatibility: a client that sends no session key
 *   gets a single per-user "default" session.
 *
 * Security model:
 *   - session_key is opaque; it is NOT a secret (entitlement is the gate).
 *   - user_uid is ALWAYS from the validated Bearer principal — never from a
 *     client-supplied header or body.
 *   - active_chart_id in the session is a hint; every chart-scoped tool call
 *     still calls remoteAuthorize before serving data.
 *
 * Provenance stamp (R5 W4 — design §10.6 SESSION STABILITY + §31.3 SESSION-PIN
 * COLLISION + §31.5 BUILD PROVENANCE):
 *   getOrCreateSession/persistActiveChart accept an optional `pinChartId` to
 *   resolve+refresh {priors_version, formula_versions, ranking_config, build_id,
 *   now_context_date} for that EXPLICIT chart_id (never inferred from
 *   active_chart_id — the §31.3 mitigation). The stamp is re-keyed inside
 *   state_json by chart_id on the platform side, so two chart contexts sharing
 *   one (user, session_key) get independent stamps. A mid-session chart rebuild
 *   surfaces as `judgment_flags: ['chart_rebuilt_mid_provenance_stamp_refreshed']`.
 *   `ProvenanceStampValues` here mirrors `platform/src/lib/retrieval/provenance_stamp.ts`
 *   (same hand-mirror precedent already used for `McpSession` itself in this
 *   file — the envelope shape is the one contract under the §19 codegen
 *   mandate; this session-state shape is not).
 *
 * M3 — MCP elevation arc (2026-07-01). Provenance stamp — R5 W4 (2026-07-09).
 */

import type { Principal } from '../types.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Types ──────────────────────────────────────────────────────────────────────

export interface McpSession {
  session_id: string
  user_uid: string
  session_key: string
  active_chart_id: string | null
  created_at: string
  last_seen_at: string
  state_json: Record<string, unknown>
}

export interface McpSessionSummary {
  session_id: string
  session_key: string
  active_chart_id: string | null
  last_seen_at: string
}

/** Mirror of platform's ProvenanceStampValues (provenance_stamp.ts) — see doc comment above.
 *  W3-L8: added `ledger_version` (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-3/4, W-26) — the
 *  concept-ledger staleness signal, orthogonal to `build_id`. Kept in sync by hand per the
 *  precedent already documented above (this shape is not under the §19 codegen mandate). */
export interface ProvenanceStampValues {
  chart_id: string
  priors_version: string
  formula_versions: { salience_formula_ver: string | null }
  ranking_config: { mode: string }
  build_id: string | null
  build_status: string | null
  ledger_version: string | null
  now_context_date: string
  pinned_at: string
}

export interface ProvenanceStampResponse {
  session: McpSession | null
  provenance_stamp?: ProvenanceStampValues
  judgment_flags?: string[]
}

// ── Internal fetch helpers ────────────────────────────────────────────────────

function sessionHeaders(principal: Principal, sessionKey: string): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
    'X-MCP-User': principal.user_uid,
    'X-MCP-Role': principal.role,
    'X-MCP-Session-Key': sessionKey,
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Get or create a session for the principal.
 *
 * @param principal   The authenticated MCP principal.
 * @param sessionKey  Opaque session identifier from the client.
 *                    Falls back to 'default' if absent.
 * @returns The session, or null on platform error.
 */
export async function getOrCreateSession(
  principal: Principal,
  sessionKey: string
): Promise<McpSession | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/session`, {
      method: 'GET',
      headers: sessionHeaders(principal, sessionKey),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { session?: McpSession }
    return data.session ?? null
  } catch {
    return null
  }
}

/**
 * Get or create a session AND resolve/refresh the provenance stamp (R5 W4) for an
 * EXPLICIT chart_id. Use this instead of getOrCreateSession whenever the
 * caller needs stamp data (recall_session, select_chart) — chart_id is never
 * inferred from active_chart_id (design §31.3 mitigation).
 *
 * @param principal    The authenticated MCP principal.
 * @param sessionKey   Opaque session identifier from the client.
 * @param pinChartId   The chart_id to resolve/refresh the stamp for.
 * @returns {session, provenance_stamp, judgment_flags}. `session` is null on platform
 *          error; `provenance_stamp`/`judgment_flags` are absent if the call failed
 *          or no stamp could be resolved.
 */
export async function getSessionWithPin(
  principal: Principal,
  sessionKey: string,
  pinChartId: string
): Promise<ProvenanceStampResponse> {
  try {
    const url = new URL(`${PLATFORM_URL}/api/mcp/session`)
    url.searchParams.set('pin_chart_id', pinChartId)
    const res = await fetch(url.toString(), {
      method: 'GET',
      headers: sessionHeaders(principal, sessionKey),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return { session: null }
    const data = (await res.json()) as ProvenanceStampResponse
    return { session: data.session ?? null, provenance_stamp: data.provenance_stamp, judgment_flags: data.judgment_flags }
  } catch {
    return { session: null }
  }
}

/**
 * Persist an active_chart_id to the session, and (R5 W4) resolve/refresh the
 * session pin for that same chart_id in one round trip.
 * Called by select_chart after entitlement is confirmed.
 *
 * @param principal    The authenticated MCP principal.
 * @param sessionKey   Session key from the client.
 * @param chartId      The chart_id to store (or null to clear).
 * @returns true on success, false on platform error.
 */
export async function persistActiveChart(
  principal: Principal,
  sessionKey: string,
  chartId: string | null
): Promise<boolean> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/session`, {
      method: 'POST',
      headers: sessionHeaders(principal, sessionKey),
      body: JSON.stringify({ active_chart_id: chartId }),
      signal: AbortSignal.timeout(5_000),
    })
    return res.ok
  } catch {
    return false
  }
}

/**
 * Persist an active_chart_id AND resolve/refresh the provenance stamp for it, in
 * one round trip. Use this (rather than persistActiveChart) when the caller
 * wants the stamp back synchronously (select_chart).
 *
 * @param principal    The authenticated MCP principal.
 * @param sessionKey    Session key from the client.
 * @param chartId       The chart_id to store as active AND stamp.
 * @returns {session, provenance_stamp, judgment_flags}. `session` is null on platform error.
 */
export async function persistActiveChartAndPin(
  principal: Principal,
  sessionKey: string,
  chartId: string
): Promise<ProvenanceStampResponse> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/session`, {
      method: 'POST',
      headers: sessionHeaders(principal, sessionKey),
      body: JSON.stringify({ active_chart_id: chartId, pin_chart_id: chartId }),
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) return { session: null }
    const data = (await res.json()) as ProvenanceStampResponse
    return { session: data.session ?? null, provenance_stamp: data.provenance_stamp, judgment_flags: data.judgment_flags }
  } catch {
    return { session: null }
  }
}

/**
 * List all sessions for the principal (most recently seen first).
 * Results are scoped to principal.user_uid by the platform — no cross-user leakage.
 *
 * @param principal  The authenticated MCP principal.
 * @param limit      Max sessions to return (default 20, capped at 50 by platform).
 * @returns Array of session summaries, or null on platform error.
 */
export async function listSessions(
  principal: Principal,
  limit = 20
): Promise<McpSessionSummary[] | null> {
  try {
    const res = await fetch(
      `${PLATFORM_URL}/api/mcp/sessions?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
          'X-MCP-User': principal.user_uid,
          'X-MCP-Role': principal.role,
        },
        signal: AbortSignal.timeout(5_000),
      }
    )
    if (!res.ok) return null
    const data = (await res.json()) as { sessions?: McpSessionSummary[] }
    return data.sessions ?? null
  } catch {
    return null
  }
}
