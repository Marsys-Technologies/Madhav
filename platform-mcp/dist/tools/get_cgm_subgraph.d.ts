/**
 * get_cgm_subgraph.ts — MCP Tier 3 surgical primitive: CGM topology traversal.
 *
 * What it does: Traverses the Cross-Domain Linkage Matrix (CGM) graph starting
 * from a seed node and returns a subgraph of connected nodes up to N hops. The
 * CGM encodes cross-domain signal linkages — how a career signal connects to a
 * health signal via a shared planetary ruler, or how a spiritual theme amplifies
 * a relationship pattern. Traversal returns nodes (signal IDs), edges (link types
 * and weights), and summary metadata. Tagged surgical: true; bypasses synthesis.
 *
 * When to prefer: Use get_cgm_subgraph when you want to map the topology of how
 * signals connect across domains — e.g., "what signals are connected to SIG.MSR.234
 * within 2 hops?" Prefer ask_madhav when you want the cross-domain connections
 * synthesized into a holistic answer. Prefer query_signals for flat signal lookups
 * without graph structure.
 *
 * Input shape hints:
 *   node_id — required; a signal ID (e.g. "SIG.MSR.234"), domain node ID,
 *     or CGM entity ID as the traversal seed.
 *   hops — optional integer (1–5); traversal depth (default 2).
 *   edge_types — optional array; filter to specific edge types. Examples:
 *     "amplifies", "contradicts", "shares_ruler", "temporal_co-activation".
 *
 * Output shape preview: {ok, result: {nodes: CgmNode[], edges: CgmEdge[]},
 *   trace_id, epistemics: {surgical: true}}.
 *
 * Example: get_cgm_subgraph({node_id: "SIG.MSR.234", hops: 2}) →
 *   {ok: true, result: {nodes: [{id: "SIG.MSR.234", domain: "career"}, ...],
 *   edges: [{from: "SIG.MSR.234", to: "SIG.MSR.512", type: "amplifies", weight: 0.8}]}, ...}
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerGetCgmSubgraph(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=get_cgm_subgraph.d.ts.map