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

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerListRecentQueries(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'list_recent_queries',

    // ── Tool description (§4.6-standard, ≥100 words) ──────────────────────────
    `What it does: Returns recent MCP call history for the current API key.
Each entry includes trace_id, tool name, source (mcp or mcp_primitive), timestamp,
and a brief query summary. The result is scoped to the calling API key — you see
only your own calls, not other principals' calls.

When to prefer: Use list_recent_queries when you want an audit of what this API
key has called recently, need to find a trace_id from a prior session for follow-up
investigation with get_trace, or want to understand usage patterns and cost behavior
for this key. For inspecting a specific call in full detail, pass the trace_id to
get_trace. For answering chart questions, use holistic_bundle. This tool does not
answer astrological questions — it is purely for MCP usage audit and navigation.

Input shape hints: limit — integer between 1 and 100 (default 20). since — ISO
8601 date string (e.g., "2026-05-01"); defaults to 7 days ago if omitted.

Output shape preview: {ok, result: {queries: [{trace_id, created_at, tool, source,
query_summary}]}, epistemics: {surgical: true}}.

Example: list_recent_queries({limit: 5}) → returns the 5 most recent calls;
list_recent_queries({since: "2026-05-20"}) → all calls since May 20.`,

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
