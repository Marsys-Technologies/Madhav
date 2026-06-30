/**
 * session_tools.ts — M3: recall_session + list_my_sessions MCP tools.
 *
 * M3.2 Session tools:
 *   recall_session:   fetch the caller's current session (active_chart_id, state).
 *                     Re-checks entitlement for the stored active_chart_id before
 *                     returning it — a grant may have been revoked between sessions.
 *   list_my_sessions: list all of the caller's sessions (most recently seen first).
 *                     Results scoped strictly to principal.user_uid.
 *
 * Security invariants:
 *   - Both tools are scoped to principal.user_uid; no cross-user access is possible.
 *   - recall_session re-checks entitlement for stored active_chart_id.
 *     If the grant was revoked, active_chart_id is NOT returned in the response
 *     and an advisory is included (the data is never replayed to an unentitled user).
 *   - Session key is opaque; treated as an identifier, not a secret.
 *
 * Chart-agnostic invariants:
 *   - No native chart_id or name appears in this file.
 *   - session_key comes from the caller; falls back to 'default'.
 *
 * M3 — MCP elevation arc (2026-07-01).
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { getOrCreateSession, listSessions } from '../lib/session.js'
import { remoteAuthorize } from '../lib/authz.js'

// ── Tool registration ──────────────────────────────────────────────────────────

/**
 * Register M3 session tools on the given MCP server.
 * Call once per McpServer instance.
 */
export function registerSessionTools(
  server: McpServer,
  principal: Principal
): void {
  // ── recall_session ──────────────────────────────────────────────────────────
  server.tool(
    'recall_session',
    'Recall your current session state, including the last active chart. ' +
    'Re-checks your current entitlement for the stored chart before returning it — ' +
    'if access was revoked, the chart will not be surfaced.',
    {
      session_key: z
        .string()
        .optional()
        .describe(
          'Opaque session identifier (e.g. device-id, thread-id). ' +
          'Omit to use your default session.'
        ),
    },
    async ({ session_key }) => {
      const key = session_key ?? 'default'
      const session = await getOrCreateSession(principal, key)

      if (!session) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: false,
                error: 'PLATFORM_UNAVAILABLE',
                message: 'Could not retrieve session. Platform may be unavailable.',
              }),
            },
          ],
          isError: true,
        }
      }

      // Entitlement re-check: if session has an active_chart_id, verify the user
      // is still entitled. A grant can be revoked between sessions.
      let entitledChartId: string | null = null
      let advisories: string[] = []

      if (session.active_chart_id) {
        const stillEntitled = await remoteAuthorize(
          principal,
          session.active_chart_id,
          'view'
        )
        if (stillEntitled) {
          entitledChartId = session.active_chart_id
        } else {
          advisories = [
            `Access to your previously active chart (${session.active_chart_id}) has been revoked. ` +
            'Use list_my_charts to see your current entitled charts.'
          ]
        }
      }

      const result = {
        ok: true,
        session: {
          session_id: session.session_id,
          session_key: session.session_key,
          active_chart_id: entitledChartId,
          last_seen_at: session.last_seen_at,
          created_at: session.created_at,
        },
        ...(advisories.length > 0 ? { advisories } : {}),
        usage_hint:
          entitledChartId
            ? `Your active chart is ${entitledChartId}. Pass it to chart-scoped tools, or use select_chart to switch.`
            : 'No active chart. Use list_my_charts to see your entitled charts, then select_chart to choose one.',
      }

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(result, null, 2),
          },
        ],
      }
    }
  )

  // ── list_my_sessions ────────────────────────────────────────────────────────
  server.tool(
    'list_my_sessions',
    'List all your MCP sessions across clients, showing the active chart and last activity time for each. ' +
    'Results include only your own sessions — never another user\'s.',
    {
      limit: z
        .number()
        .int()
        .min(1)
        .max(50)
        .optional()
        .describe('Maximum number of sessions to return (default 20, max 50).'),
    },
    async ({ limit }) => {
      const sessions = await listSessions(principal, limit ?? 20)

      if (!sessions) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: false,
                error: 'PLATFORM_UNAVAILABLE',
                message: 'Could not retrieve session list. Platform may be unavailable.',
              }),
            },
          ],
          isError: true,
        }
      }

      const result = {
        ok: true,
        count: sessions.length,
        sessions: sessions.map((s) => ({
          session_id: s.session_id,
          session_key: s.session_key,
          active_chart_id: s.active_chart_id,
          last_seen_at: s.last_seen_at,
        })),
        usage_hint:
          sessions.length === 0
            ? 'No sessions found. Make a tool call to create your first session.'
            : `Showing ${sessions.length} session(s). Use recall_session with session_key to resume a specific session.`,
      }

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(result, null, 2),
          },
        ],
      }
    }
  )
}
