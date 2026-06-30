/**
 * chart_catalog_resource.ts — M2.3: Charts as MCP resources.
 *
 * Exposes the caller's entitled chart set as MCP resources so compatible
 * clients (Claude Desktop) can render a native chart-picker.
 *
 * Resources:
 *   marsys://chart/{chart_id} — per-chart metadata resource.
 *     List: returns only the caller's entitled charts by display name.
 *     Read: entitlement-gated (M0 gate); returns chart metadata.
 *
 * Entitlement is enforced on EVERY read:
 *   - The list operation calls /api/mcp/my/charts (entitled set only).
 *   - The read handler calls remoteAuthorize before serving any data.
 *   - Selection is convenience; it NEVER bypasses per-call authorization.
 *
 * Chart-agnostic invariants:
 *   - No native chart_id or name appears in this file.
 *
 * M2 chart selection (MCP elevation arc, 2026-07-01).
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'

// ── Environment ────────────────────────────────────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Types ──────────────────────────────────────────────────────────────────────

interface ChartListItem {
  id: string
  display_name: string
  index: number
}

// ── Platform fetch helper ──────────────────────────────────────────────────────

async function fetchMyCharts(principal: Principal): Promise<ChartListItem[]> {
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
    if (!res.ok) return []
    const data = (await res.json()) as { charts?: ChartListItem[] }
    return data.charts ?? []
  } catch {
    return []
  }
}

// ── Resource registration ──────────────────────────────────────────────────────

/**
 * Register the chart catalog resource on the given MCP server.
 * Uses a resource template marsys://chart/{chart_id}.
 * The list callback returns only the caller's entitled charts.
 * The read handler is entitlement-gated (M0 gate).
 */
export function registerChartCatalogResource(
  server: McpServer,
  principal: Principal
): void {
  server.resource(
    'chart',
    new ResourceTemplate('marsys://chart/{chart_id}', {
      list: async () => {
        // Return only the caller's entitled charts — never an unscoped list
        const charts = await fetchMyCharts(principal)
        return {
          resources: charts.map((c) => ({
            uri: `marsys://chart/${c.id}`,
            name: c.display_name,
            description: `Chart ${c.index + 1}: ${c.display_name} (id: ${c.id})`,
            mimeType: 'application/json',
          })),
        }
      },
    }),
    async (uri) => {
      // Extract chart_id from the URI: marsys://chart/{chart_id}
      // uri.host contains the chart_id in the marsys:// scheme
      const uriStr = uri.href
      const match = uriStr.match(/^marsys:\/\/chart\/([0-9a-f-]{36})$/i)
      const chartId = match?.[1]

      if (!chartId) {
        return {
          contents: [
            {
              uri: uriStr,
              mimeType: 'text/plain',
              text: 'Error: chart_id required in URI (marsys://chart/{chart_id})',
            },
          ],
        }
      }

      // M0 entitlement gate — authorize before returning any data
      const authorized = await remoteAuthorize(principal, chartId, 'view')
      if (!authorized) {
        return {
          contents: [
            {
              uri: uriStr,
              mimeType: 'text/plain',
              text: `Error: AUTHZ_DENIED for chart ${chartId}`,
            },
          ],
        }
      }

      // Resolve display name from entitled chart list
      const charts = await fetchMyCharts(principal)
      const chart = charts.find((c) => c.id === chartId)
      const displayName = chart?.display_name ?? chartId

      return {
        contents: [
          {
            uri: uriStr,
            mimeType: 'application/json',
            text: JSON.stringify({
              chart_id: chartId,
              display_name: displayName,
              usage_hint:
                'Pass this chart_id to chart-scoped tools (e.g., holistic_bundle, event_anchors).',
            }),
          },
        ],
      }
    }
  )
}
