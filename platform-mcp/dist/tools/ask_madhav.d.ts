/**
 * ask_madhav.ts — MCP tool: end-to-end MARSYS-JIS pipeline.
 *
 * Tier 1 tool (MCP_BRIEF §4.1). Runs the full pipeline: planner → arbitrate
 * → compose_bundle → retrieval → synthesis. Returns a synthesized answer with
 * citations, trace ID, synthesis audit, suggested follow-ups, and epistemics.
 *
 * Tool description is a PLACEHOLDER in this session (~30 words).
 * Full §4.6-standard description (120–180 words, 5 blocks) authors in MCP-2-S2.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
/**
 * Register the ask_madhav MCP tool on the given server.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export declare function registerAskMadhav(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=ask_madhav.d.ts.map