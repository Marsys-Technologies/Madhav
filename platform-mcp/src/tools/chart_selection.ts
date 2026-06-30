/**
 * chart_selection.ts — M2: list_my_charts + select_chart MCP tools.
 *
 * M2.1 — list_my_charts:
 *   Returns the caller's entitled chart set by display name + stable id + 0-indexed label.
 *   Never returns raw-UUID-only output. Calls /api/mcp/my/charts on the platform
 *   (which calls getEntitledCharts internally).
 *
 * M2.2 — select_chart:
 *   Validates a chosen chart_id is entitled (calls remoteAuthorize).
 *   Returns the canonical chart_id + display_name for use in subsequent tool calls.
 *   Param-carried selection works statelessly (M3 will add session persistence).
 *
 * Selection NEVER weakens the per-call entitlement gate:
 *   - Every chart-scoped tool still calls remoteAuthorize before serving data.
 *   - select_chart merely validates + resolves the chart_id ergonomically.
 *
 * Chart-agnostic invariants:
 *   - No native chart_id or name appears in this file.
 *   - list_my_charts takes no chart_id param.
 *
 * M2 chart selection (MCP elevation arc, 2026-07-01).
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'

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

      const result = {
        ok: true,
        count: charts.length,
        charts: charts.map((c) => ({
          index: c.index,
          chart_id: c.id,
          display_name: c.display_name,
        })),
        usage_hint:
          'Pass chart_id to chart-scoped tools, or use select_chart to validate a choice.',
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

  // ── select_chart ────────────────────────────────────────────────────────────
  server.tool(
    'select_chart',
    'Validate and select a chart for use in subsequent tool calls. Checks that you are entitled to access the chart and returns the canonical chart_id with the chart display name. Pass the returned chart_id to other chart-scoped tools.',
    {
      chart_id: z.string().uuid().describe(
        'The UUID of the chart to select. Obtain from list_my_charts.'
      ),
    },
    async ({ chart_id }) => {
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

      // M3: persist active_chart_id to mcp_sessions
      // TODO: once M3 session store is live, persist:
      //   await persistActiveChart(sessionId, principal.user_uid, chart_id)
      // For now: param-carried selection (caller passes chart_id to each tool).

      const name = displayName ?? chart_id  // fall back to UUID only if resolution fails

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify({
              ok: true,
              chart_id,
              display_name: name,
              message: `Chart selected: ${name}. Pass this chart_id to subsequent tools.`,
            }),
          },
        ],
      }
    }
  )
}
