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
 * M3 — MCP elevation arc (2026-07-01).
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
 * Persist an active_chart_id to the session.
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
