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
 * within 2 hops?" Prefer holistic_bundle when you want the cross-domain connections
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

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'

const GetCgmSubgraphInputSchema = z.object({
  node_id: z.string().describe(
    'Seed node for graph traversal. Examples: "SIG.MSR.234", domain node ID, or CGM entity ID.'
  ),
  hops: z.number().int().min(1).max(5).optional().default(2).describe(
    'Traversal depth in graph hops (default 2, max 5).'
  ),
  edge_types: z.array(z.string()).optional().describe(
    'Filter to specific edge types. Examples: "amplifies", "contradicts", ' +
    '"shares_ruler", "temporal_co-activation".'
  ),
})

type GetCgmSubgraphInput = z.infer<typeof GetCgmSubgraphInputSchema>

export function registerGetCgmSubgraph(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'get_cgm_subgraph',
    'What it does: Traverses the Cross-Domain Linkage Matrix (CGM) from a seed node ' +
    'and returns a subgraph of connected signals/domains up to N hops, with edges ' +
    'typed by link relationship (amplifies, contradicts, shares_ruler, etc.). ' +
    'When to prefer: Use to map cross-domain signal topology ("what connects to SIG.MSR.234?"). ' +
    'Prefer holistic_bundle when the cross-domain connections need to be synthesized into a holistic answer. ' +
    'Input shape hints: node_id (required) is the seed — a signal ID or CGM entity ID; ' +
    'hops (default 2) controls traversal depth (max 5); edge_types is an optional filter array. ' +
    'Output shape preview: {ok, result: {nodes: CgmNode[], edges: CgmEdge[]}, trace_id, epistemics: {surgical: true}}. ' +
    'Example: get_cgm_subgraph({node_id: "SIG.MSR.234", hops: 2}) → subgraph of 2-hop neighbors.',
    GetCgmSubgraphInputSchema.shape,
    async (args: GetCgmSubgraphInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'get_cgm_subgraph',
        {
          node_id: args.node_id,
          hops: args.hops ?? 2,
          ...(args.edge_types ? { edge_types: args.edge_types } : {}),
        },
        principal
      )
      const text = JSON.stringify(envelope, null, 2)
      return {
        content: [{ type: 'text' as const, text }],
        isError: !envelope.ok || status >= 400,
      }
    }
  )
}
