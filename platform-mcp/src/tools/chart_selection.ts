/**
 * chart_selection.ts — M2+M3+M4: list_my_charts + select_chart MCP tools.
 *
 * M2.1 — list_my_charts:
 *   Returns the caller's entitled chart set by display name + stable id + 0-indexed label.
 *   Never returns raw-UUID-only output. Calls /api/mcp/my/charts on the platform
 *   (which calls getEntitledCharts internally).
 *
 * M2.2 — select_chart:
 *   Validates a chosen chart_id is entitled (calls remoteAuthorize).
 *   Returns the canonical chart_id + display_name for use in subsequent tool calls.
 *
 * M3 additions (session persistence):
 *   - select_chart accepts an optional session_key param.
 *   - After entitlement confirmed, persists active_chart_id to mcp_sessions
 *     via POST /api/mcp/session.
 *   - Prior active_chart_id fetched for M4 switch detection.
 *
 * M4 — chart-switch advisory:
 *   When the incoming chart_id differs from the session's active_chart_id,
 *   select_chart includes an advisory in the response. Call still proceeds
 *   (warn, not block) after the entitlement gate.
 *
 * Selection NEVER weakens the per-call entitlement gate:
 *   - Every chart-scoped tool still calls remoteAuthorize before serving data.
 *   - select_chart merely validates + resolves the chart_id ergonomically.
 *
 * Chart-agnostic invariants:
 *   - No native chart_id or name appears in this file.
 *   - list_my_charts takes no chart_id param.
 *
 * Session pin (R5 W4 — design §10.6/§31.3/§31.5): select_chart is the natural
 * "session open" anchor for the chart being selected — after persisting
 * active_chart_id it also resolves/refreshes the session_pin for that same
 * chart_id ({priors_version, formula_versions, ranking_config, build_id,
 * now_context_date}) and returns it. A mid-session rebuild of the chart being
 * (re-)selected surfaces honestly as an advisory + `judgment_flags`.
 *
 * M2+M3+M4 chart selection (MCP elevation arc, 2026-07-01). Session pin — R5 W4 (2026-07-09).
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { getOrCreateSession, persistActiveChartAndPin } from '../lib/session.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── Environment ────────────────────────────────────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ChartListItem {
  id: string
  display_name: string
  index: number
}

// ── Platform fetch helper ──────────────────────────────────────────────────────

/**
 * Call GET /api/mcp/my/charts on the platform to retrieve the entitled chart list.
 * Returns null if the call fails (fail-closed).
 */
async function fetchMyCharts(
  principal: Principal
): Promise<ChartListItem[] | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/my/charts`, {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        'X-MCP-Role': principal.role,
      },
      signal: AbortSignal.timeout(10_000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { charts?: ChartListItem[] }
    return data.charts ?? null
  } catch {
    return null
  }
}

/**
 * Fetch the display name for a single chart by calling /api/mcp/my/charts
 * and searching for the matching id. Returns null if not found or on error.
 * Used by select_chart to resolve a chart_id to its display_name.
 */
async function fetchChartDisplayName(
  principal: Principal,
  chartId: string
): Promise<string | null> {
  const charts = await fetchMyCharts(principal)
  if (!charts) return null
  const match = charts.find((c) => c.id === chartId)
  return match?.display_name ?? null
}

// ── Tool registrations ─────────────────────────────────────────────────────────

/**
 * Register M2 chart-selection tools on the given MCP server.
 * Call once per McpServer instance.
 */
export function registerChartSelectionTools(
  server: McpServer,
  principal: Principal
): void {
  // ── list_my_charts ──────────────────────────────────────────────────────────
  server.tool(
    'list_my_charts',
    'List all charts you are entitled to access. Returns chart names, stable IDs, and 0-indexed labels. Use the chart_id from the response to pass to other chart-scoped tools.',
    {},  // no parameters — "my" is implicit from the authenticated principal
    async () => {
      const charts = await fetchMyCharts(principal)

      if (!charts) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: false,
                error: 'PLATFORM_UNAVAILABLE',
                message: 'Could not retrieve chart list. Platform may be unavailable.',
              }),
            },
          ],
          isError: true,
        }
      }

      if (charts.length === 0) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: true,
                charts: [],
                message: 'No charts found. Ask your administrator to grant you chart access.',
              }),
            },
          ],
        }
      }

      const result = budgetMcpContent(
        {
          ok: true,
          count: charts.length,
          charts: charts.map((c) => ({
            index: c.index,
            chart_id: c.id,
            display_name: c.display_name,
          })),
          usage_hint:
            'Pass chart_id to chart-scoped tools, or use select_chart to validate a choice.',
        },
        'list_my_charts',
      )

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

  // ── select_chart ────────────────────────────────────────────────────────────
  server.tool(
    'select_chart',
    'Validate and select a chart for use in subsequent tool calls. Checks that you are entitled to access the chart, persists the selection to your session, and returns the canonical chart_id with the chart display name. Pass the returned chart_id to other chart-scoped tools.',
    {
      chart_id: z.string().uuid().describe(
        'The UUID of the chart to select. Obtain from list_my_charts.'
      ),
      session_key: z
        .string()
        .optional()
        .describe(
          'Opaque session identifier (e.g. device-id, thread-id). ' +
          'Omit to use your default session. Must match the key used in recall_session.'
        ),
    },
    async ({ chart_id, session_key }) => {
      // M0 entitlement gate — never skip even on "selected" chart
      const authorized = await remoteAuthorize(principal, chart_id, 'view')

      if (!authorized) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: false,
                error: 'AUTHZ_DENIED',
                message: `Access denied to chart ${chart_id}. You are not entitled to access this chart.`,
              }),
            },
          ],
          isError: true,
        }
      }

      // Resolve display_name — use entitled chart list (avoids a separate DB call)
      const displayName = await fetchChartDisplayName(principal, chart_id)
      const name = displayName ?? chart_id  // fall back to UUID only if resolution fails

      // M3: look up current session to detect chart switch (M4) + persist new selection.
      const key = session_key ?? 'default'
      const advisories: string[] = []

      const session = await getOrCreateSession(principal, key)
      const previousChartId = session?.active_chart_id ?? null

      // M4: chart-switch advisory — warn (not block) when switching charts.
      if (previousChartId && previousChartId !== chart_id) {
        advisories.push(
          `You have switched to a different chart from your previous session. ` +
          `Consider starting a new conversation to avoid mixing chart contexts. ` +
          `Previous: ${previousChartId} → New: ${chart_id}.`
        )
      }

      // M3 + R5 W4: persist the newly selected active_chart_id AND resolve/refresh
      // the session pin for it, in one round trip. Failure is non-fatal — the call
      // still returns the selected chart_id even if session/pin persistence fails.
      let sessionPin: unknown = undefined
      let pinJudgmentFlags: string[] | undefined
      if (session) {
        try {
          const pinResult = await persistActiveChartAndPin(principal, key, chart_id)
          if (pinResult.session_pin) {
            sessionPin = pinResult.session_pin
            pinJudgmentFlags = pinResult.judgment_flags
            if (pinJudgmentFlags && pinJudgmentFlags.length > 0) {
              advisories.push(
                `Chart ${chart_id} was rebuilt since your session pin was last set — ` +
                'pin refreshed to the new build.'
              )
            }
          }
        } catch (err: unknown) {
          console.error('[mcp:select_chart] session/pin persist failed', err)
        }
      }

      const result: Record<string, unknown> = {
        ok: true,
        chart_id,
        display_name: name,
        session_key: key,
        message: `Chart selected: ${name}. Pass this chart_id to subsequent tools.`,
      }
      if (sessionPin) {
        result['session_pin'] = sessionPin
      }
      if (pinJudgmentFlags && pinJudgmentFlags.length > 0) {
        result['judgment_flags'] = pinJudgmentFlags
      }
      if (advisories.length > 0) {
        result['advisories'] = advisories
      }

      const budgeted = budgetMcpContent(result, 'select_chart')

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(budgeted, null, 2),
          },
        ],
      }
    }
  )
}
