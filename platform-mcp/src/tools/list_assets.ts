/**
 * list_assets.ts — MCP Tier 4 tool: enumerate supported canonical artifact IDs.
 *
 * Returns the set of canonical_ids that read_asset supports, with their
 * repo-relative paths and status. Callers use this to discover what documents
 * are available before calling read_asset.
 *
 * No params. No auth gate beyond the standard MCP Bearer key (already validated
 * by the server entry point before tool dispatch).
 *
 * Tagged surgical: true — bypasses planner and B.11 floor.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { okResult } from './_envelope.js'
import { KNOWN_CANONICAL_IDS, SAFE_ASSET_MAP } from './read_asset.js'
import type { Principal } from '../types.js'

export const LIST_ASSETS_DESCRIPTION =
  'What it does: Returns the list of canonical artifact IDs supported by read_asset ' +
  '(MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE) ' +
  'with their repo-relative paths. ' +
  'When to prefer: Call this before read_asset if you are unsure which canonical_id ' +
  'to use, or to verify which documents are available in this MCP server instance.'

export function registerListAssets(
  server: McpServer,
  _getPrincipal: () => Principal
): void {
  server.tool(
    'list_assets',

    LIST_ASSETS_DESCRIPTION,

    // No input params — pass empty schema shape.
    {},

    async () => {
      const traceId = crypto.randomUUID()

      const canonical_ids = KNOWN_CANONICAL_IDS.map(id => ({
        id,
        path: SAFE_ASSET_MAP[id],
        status: 'CURRENT',
      }))

      return okResult({
        ok: true,
        trace_id: traceId,
        epistemics: { surgical: true, confidence_band: 'high' },
        result: {
          canonical_ids,
          count: canonical_ids.length,
        },
      })
    }
  )
}
