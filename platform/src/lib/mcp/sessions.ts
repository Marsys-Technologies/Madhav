/**
 * sessions.ts — MCP session state service (M3).
 *
 * Provides lookup-mutate-writeback semantics for mcp_sessions.
 * Statelessness preserved: no in-process session held; the MCP sidecar
 * calls GET/POST /api/mcp/session on the platform, which delegates here.
 *
 * Session keyed by (user_uid, session_key):
 *   - user_uid:    from the authenticated principal (never trusted from the client)
 *   - session_key: opaque string supplied by the MCP client (e.g. device-id,
 *                  thread-id). Treated as an opaque identifier — not a secret.
 *
 * Security:
 *   - All queries are scoped to user_uid — no cross-user access possible.
 *   - active_chart_id stored as a convenience; entitlement is always
 *     re-checked at call time (the grant may be revoked between sessions).
 *   - DELETEs are scoped to (user_uid, session_key) — reverse-citation gate.
 *
 * M3 — MCP elevation arc (2026-07-01).
 */

import 'server-only'
import { query } from '@/lib/db/client'

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

// ── Session lookup / creation ─────────────────────────────────────────────────

/**
 * Get an existing session by (user_uid, session_key), or create one if it
 * does not exist. Updates last_seen_at on each access.
 *
 * Returns the full session row.
 */
export async function getOrCreateSession(
  user_uid: string,
  session_key: string
): Promise<McpSession> {
  // Upsert: insert if not exists; on conflict update last_seen_at.
  const { rows } = await query<McpSession>(
    `INSERT INTO mcp_sessions (user_uid, session_key, active_chart_id, state_json)
     VALUES ($1, $2, NULL, '{}')
     ON CONFLICT (user_uid, session_key)
       DO UPDATE SET last_seen_at = NOW()
     RETURNING
       session_id::text,
       user_uid,
       session_key,
       active_chart_id::text,
       created_at,
       last_seen_at,
       state_json`,
    [user_uid, session_key]
  )
  const row = rows[0]
  if (!row) throw new Error('[mcp:sessions] getOrCreateSession: no row returned')
  return row
}

// ── Active chart persistence ───────────────────────────────────────────────────

/**
 * Update the active_chart_id for a session.
 * Scoped to user_uid for safety — never updates another user's session.
 *
 * @param session_id  UUID of the session to update.
 * @param user_uid    Owner of the session (enforced in WHERE clause).
 * @param chart_id    New active chart, or null to clear.
 */
export async function updateActiveChart(
  session_id: string,
  user_uid: string,
  chart_id: string | null
): Promise<void> {
  await query(
    `UPDATE mcp_sessions
     SET active_chart_id = $1, last_seen_at = NOW()
     WHERE session_id = $2 AND user_uid = $3`,
    [chart_id, session_id, user_uid]
  )
}

/**
 * Get the active_chart_id for a session.
 * Returns null if no session found, or if active_chart_id is not set.
 * Scoped to user_uid.
 */
export async function getActiveChart(
  session_id: string,
  user_uid: string
): Promise<string | null> {
  const { rows } = await query<{ active_chart_id: string | null }>(
    `SELECT active_chart_id::text
     FROM mcp_sessions
     WHERE session_id = $1 AND user_uid = $2
     LIMIT 1`,
    [session_id, user_uid]
  )
  return rows[0]?.active_chart_id ?? null
}

// ── Session listing ────────────────────────────────────────────────────────────

/**
 * List all sessions for a user (most recently seen first).
 * Scoped to user_uid — never returns another user's sessions.
 *
 * @param user_uid  The authenticated principal's uid.
 * @param limit     Max rows to return (default 20).
 */
export async function listUserSessions(
  user_uid: string,
  limit = 20
): Promise<McpSessionSummary[]> {
  const { rows } = await query<McpSessionSummary>(
    `SELECT
       session_id::text,
       session_key,
       active_chart_id::text,
       last_seen_at
     FROM mcp_sessions
     WHERE user_uid = $1
     ORDER BY last_seen_at DESC
     LIMIT $2`,
    [user_uid, limit]
  )
  return rows
}

// ── Session deletion (scoped) ─────────────────────────────────────────────────

/**
 * Delete a single session. Scoped to (session_id, user_uid) — reverse-citation gate.
 * A user can only delete their own sessions.
 */
export async function deleteSession(
  session_id: string,
  user_uid: string
): Promise<void> {
  await query(
    `DELETE FROM mcp_sessions
     WHERE session_id = $1 AND user_uid = $2`,
    [session_id, user_uid]
  )
}
