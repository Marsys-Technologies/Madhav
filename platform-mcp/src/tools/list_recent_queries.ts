/**
 * list_recent_queries.ts — MCP Tier 5 observability tool: recent query history.
 *
 * Returns a list of recent MCP calls made by the current API key. Each entry
 * includes the trace_id (for follow-up get_trace calls), the tool name, source
 * (mcp or mcp_primitive), timestamp, and a summary of the query.
 *
 * Useful for auditing what this API key has called recently, understanding cost
 * patterns, and retrieving trace_ids from prior sessions for investigation.
 *
 * When to prefer: Use list_recent_queries when you want an overview of recent
 * MCP activity for this API key — e.g., "what have I called in the last 7 days?"
 * or "find the trace_id from the holistic_bundle call I made yesterday." For inspecting
 * a specific call in detail, follow up with get_trace(trace_id). For current chart
 * analysis, use holistic_bundle.
 *
 * Input: limit (default 20, max 100), since (ISO date string, default 7 days ago).
 * Output: {ok, result: {queries: [{trace_id, created_at, tool, source, query_summary}]}}.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformRecent } from '../client.js'
import type { Principal } from '../types.js'
import { okResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const LIST_RECENT_QUERIES_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns recent MCP call history for the current API key — ' +
    'each entry includes trace_id, tool name, source (mcp or mcp_primitive), timestamp, and a brief query summary.',
  whenToPrefer:
    'Use when you want an audit of what this API key has called recently, ' +
    'or need to find a trace_id from a prior session for follow-up investigation with get_trace. ' +
    'Do not use for answering chart questions — use holistic_bundle for that.',
})

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerListRecentQueries(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'list_recent_queries',

    LIST_RECENT_QUERIES_DESCRIPTION,

    // ── Input schema ──────────────────────────────────────────────────────────
    {
      limit: z
        .number()
        .int()
        .min(1)
        .max(100)
        .optional()
        .describe(
          'Number of results to return (default 20, max 100). ' +
          'Results are ordered by most recent first.'
        ),
      since: z
        .string()
        .optional()
        .describe(
          'ISO 8601 date string to filter results from (e.g., "2026-05-01"). ' +
          'Defaults to 7 days ago if not provided.'
        ),
    },

    // ── Handler ────────────────────────────────────────────────────────────────
    async ({ limit, since }) => {
      const principal = getPrincipal()

      const result = await callPlatformRecent(
        { limit, since },
        principal
      )

      if (!result.envelope.ok) {
        const errEnv = result.envelope
        const errorMsg = 'error' in errEnv
          ? `${errEnv.error.class}: ${errEnv.error.message}`
          : 'Unknown error from platform recent endpoint'
        return {
          content: [{ type: 'text' as const, text: `Error: ${errorMsg}` }],
          isError: true,
        }
      }

      return okResult(result.envelope)
    }
  )
}
