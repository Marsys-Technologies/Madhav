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
 * or "find the trace_id from the ask_madhav call I made yesterday." For inspecting
 * a specific call in detail, follow up with get_trace(trace_id). For current chart
 * analysis, use ask_madhav.
 *
 * Input: limit (default 20, max 100), since (ISO date string, default 7 days ago).
 * Output: {ok, result: {queries: [{trace_id, created_at, tool, source, query_summary}]}}.
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerListRecentQueries(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=list_recent_queries.d.ts.map