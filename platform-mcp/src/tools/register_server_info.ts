/**
 * tools/register_server_info.ts — EL-13 (tool-catalog caching).
 *
 * A global, chart-agnostic, no-entitlement tool exposing this MCP server's own metadata:
 * name/version, and (EL-13) `catalog_version` + `tools_changed_at` so a client can cache the
 * tool catalog across sessions instead of re-listing it every time, and know reliably when it
 * must invalidate that cache. See resources/mcp_catalog_version.ts for the version/timestamp
 * derivation and its honesty caveats (B.10 — tools_changed_at is best-effort, never fabricated).
 *
 * Registered BEFORE applyProfileGate in server.ts (same reasoning as prashna_ask/
 * prashna_status): server metadata must be reachable under every MCP surface profile
 * (full/compact/consult), not just the ones the generated MCP_SURFACE_PROFILES manifest lists
 * it under — a 'consult'-profile client still needs to detect catalog staleness.
 *
 * `client_catalog_version` (optional input) mirrors register_vidhi_plan.ts's
 * `client_catalog_version` handshake: when a caller presents its cached version and it no
 * longer matches the live one, the response flags `stale: true` AND (if the SDK transport is
 * connected) emits a `notifications/tools/list_changed` on this request's server, so a
 * compliant host re-fetches tools/resources/prompts (SDK support for this notification is
 * CONFIRMED — see server.sendToolListChanged(), already used by
 * resources/vidhi/capability_version.ts's notifyIfCapabilityStale).
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import {
  MCP_CATALOG_VERSION, MCP_CATALOG_TOOL_COUNT,
  MCP_CATALOG_TOOLS_CHANGED_AT, MCP_CATALOG_TOOLS_CHANGED_AT_NOTE,
  notifyIfCatalogStale,
} from '../resources/mcp_catalog_version.js'

export const MCP_SERVER_NAME = 'marsys-jis'
export const MCP_SERVER_VERSION = '1.0.0'

export function registerServerInfoTool(server: McpServer): void {
  server.tool(
    'mcp_server_info',
    'Server + tool-catalog metadata for this MCP server. EL-13: pass your cached ' +
      '`client_catalog_version` to check staleness in the same call — the response reports ' +
      '`stale` and, when stale, emits a `tools/list_changed` notification so a compliant host ' +
      're-fetches the tool list. `catalog_version` is the field to CACHE and compare on your ' +
      'next session; `tools_changed_at` is a best-effort, non-authoritative timestamp (see ' +
      '`tools_changed_at_note` for its caveats) — never treat it as precise.',
    {
      client_catalog_version: z.string().optional().describe(
        'Your cached catalog_version from a prior call. If it no longer matches the live ' +
          'value, the response flags `stale: true` and a tools/list_changed notification is sent.'),
    },
    async (args) => {
      const { client_catalog_version } = args as { client_catalog_version?: string }
      const staleness = notifyIfCatalogStale(client_catalog_version, server)
      const payload = {
        name: MCP_SERVER_NAME,
        version: MCP_SERVER_VERSION,
        catalog_version: MCP_CATALOG_VERSION,
        tool_count: MCP_CATALOG_TOOL_COUNT,
        tools_changed_at: MCP_CATALOG_TOOLS_CHANGED_AT,
        tools_changed_at_note: MCP_CATALOG_TOOLS_CHANGED_AT_NOTE,
        stale: staleness.stale,
        list_changed_notified: staleness.notified,
      }
      const json = JSON.stringify(payload)
      return {
        structuredContent: { type: 'object' as const, object: payload },
        content: [{ type: 'text' as const, text: json }],
      }
    }
  )
}
