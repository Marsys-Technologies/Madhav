/** Global metadata for this request's post-gate served descriptors; no tool-call authority. */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import {
  captureServedCatalog, SERVED_CATALOG_UNAVAILABLE, type ServedCatalogReader, type ServedCatalogSnapshot,
  RETRIEVAL_REGISTRY_PROFILE_TOTAL, RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT,
  MCP_CATALOG_TOOLS_CHANGED_AT, MCP_CATALOG_TOOLS_CHANGED_AT_NOTE,
  notifyIfCatalogStale,
} from '../resources/mcp_catalog_version.js'

export const MCP_SERVER_NAME = 'marsys-jis'
export const MCP_SERVER_VERSION = '1.0.0'

export function registerServerInfoTool(
  server: McpServer,
  readCatalog: ServedCatalogReader = () => captureServedCatalog(server),
): void {
  server.tool(
    'mcp_server_info',
    'Server + tool-catalog metadata for this MCP server. EL-13: pass your cached ' +
      '`client_catalog_version` to check staleness in the same call — the response reports ' +
      '`stale` and, when stale, emits a `tools/list_changed` notification so a compliant host ' +
      're-fetches the tool list. `catalog_version` is the field to CACHE and compare on your ' +
      'next session; `tools_changed_at` is null unless an attributable served change time exists (see ' +
      '`tools_changed_at_note` for its caveats) — never treat it as precise. `tool_count` is ' +
      'measured live from this request\'s own tool descriptors and equals the length of your ' +
      'tools/list response; `retrieval_registry_profile_total` is a dated build-time figure ' +
      'over a different population and is NOT the served catalog size.',
    {
      client_catalog_version: z.string().optional().describe(
        'Your cached catalog_version from a prior call. If it no longer matches the live ' +
          'value, the response flags `stale: true` and a tools/list_changed notification is sent.'),
    },
    async (args) => {
      const { client_catalog_version } = args as { client_catalog_version?: string }
      let served: ServedCatalogSnapshot
      try { served = readCatalog() } catch { served = { ok: false, code: SERVED_CATALOG_UNAVAILABLE } }
      if (!served || !served.ok) {
        const unavailable = {
          error: { code: SERVED_CATALOG_UNAVAILABLE, message: 'Served tool catalog is unavailable.' },
          tool_count: null, catalog_version: null, stale: null, list_changed_notified: false,
        }
        return {
          isError: true,
          structuredContent: { type: 'object' as const, object: unavailable },
          content: [{ type: 'text' as const, text: JSON.stringify(unavailable) }],
        }
      }
      const staleness = await notifyIfCatalogStale(client_catalog_version, served, server)
      const payload = {
        name: MCP_SERVER_NAME,
        version: MCP_SERVER_VERSION,
        catalog_version: served.version,
        tool_count: served.count,
        tool_count_note: 'Exact SDK1.29 tools/list descriptor projection after all request gates; profile-scoped.',
        retrieval_registry_profile_total: RETRIEVAL_REGISTRY_PROFILE_TOTAL,
        retrieval_registry_profile_generated_at: RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT,
        retrieval_registry_profile_note:
          'Size of the retrieval registry\'s `full` MCP projection as recorded in the ' +
          'generated manifest at `retrieval_registry_profile_generated_at` — a BUILD-TIME ' +
          'figure over a DIFFERENT population from the served MCP catalog, not live ' +
          'telemetry. Until 2026-07-30 this number was served as `tool_count`; it was ' +
          'measured at 152 while tools/list returned 124, overlapping by 15 names. Use ' +
          '`tool_count` for "how many tools can I call".',
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
