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
import {
  resolveProvenanceStamp,
  buildPinPatch,
  type ProvenanceStampValues,
} from '@/lib/retrieval/provenance_stamp'

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

// ── Provenance stamp (R5 W4 — design §10.6 + §31.3 + §31.5) ───────────────────

export interface ProvenanceStampResult {
  pin: ProvenanceStampValues
  drift: boolean
  judgment_flags: string[]
}

/**
 * Resolve (and, if needed, refresh + persist) the provenance stamp for
 * (session_id, user_uid, chart_id). Re-keys the stamp by chart_id INSIDE the
 * session's existing state_json — see provenance_stamp.ts's doc comment for the full
 * design-mandate trace (§10.6 SESSION STABILITY, §31.3 SESSION-PIN COLLISION,
 * §31.5 BUILD PROVENANCE). No schema change (D6): state_json is the free-form
 * JSONB column already provisioned by migration 382.
 *
 * Lookup-mutate-writeback, same discipline as the rest of this file: reads the
 * current state_json, resolves the stamp (reusing it untouched if the chart's
 * build hasn't moved), and writes back ONLY when the stamp is new or drifted —
 * an unchanged stamp causes no write (last_seen_at is still touched by the
 * caller's own getOrCreateSession call, so this does not need to duplicate that).
 */
export async function getOrRefreshProvenanceStamp(
  session_id: string,
  user_uid: string,
  chart_id: string
): Promise<ProvenanceStampResult> {
  const { rows } = await query<{ state_json: Record<string, unknown> }>(
    `SELECT state_json
     FROM mcp_sessions
     WHERE session_id = $1 AND user_uid = $2
     LIMIT 1`,
    [session_id, user_uid]
  )
  const stateJson = rows[0]?.state_json ?? {}
  const { pin, drift, judgment_flags } = await resolveProvenanceStamp(stateJson, chart_id)

  const alreadyPersisted = !drift && rows.length > 0 &&
    (stateJson['pins'] as Record<string, unknown> | undefined)?.[chart_id] !== undefined
  if (alreadyPersisted) {
    return { pin, drift, judgment_flags }
  }

  const newState = buildPinPatch(stateJson, chart_id, pin)
  await query(
    `UPDATE mcp_sessions
     SET state_json = $1::jsonb, last_seen_at = NOW()
     WHERE session_id = $2 AND user_uid = $3`,
    [JSON.stringify(newState), session_id, user_uid]
  )

  return { pin, drift, judgment_flags }
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
