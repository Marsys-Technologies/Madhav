/**
 * cluster_atlas.ts — MCP Tier 3 surgical primitive: CLUSTER_ATLAS lookup.
 *
 * What it does: Reads the CLUSTER_ATLAS JSON file from the repository and
 * filters ClusterEntry records by domain, sub_domain, and minimum cluster size.
 * Returns raw cluster rows — cluster_label, dominant_domain, sub_domains,
 * cluster_size_n, confidence, significance, annotation — without synthesis.
 * Tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use cluster_atlas when you need signal clusters from the
 * L2.5 / L3.5 Discovery Layer — groups of co-activating signals with a shared
 * thematic centroid. Prefer over holistic_bundle when the goal is "give me all
 * career-domain clusters above N signals" as a structured list. Prefer
 * pattern_register or resonance_register when you need individual cross-signal
 * patterns or cross-domain bridging entries respectively.
 *
 * Input shape hints:
 *   domain        — optional; filters to clusters whose dominant_domain matches.
 *   sub_domain    — optional; filters to clusters whose sub_domains array contains this value.
 *   min_size      — optional int; exclude clusters smaller than this threshold.
 *   limit         — optional; max clusters to return (default 20, max 100).
 *
 * Output shape preview: {ok, result: {results: ClusterEntry[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: cluster_atlas({domain: "career", min_size: 3}) →
 *   {ok: true, result: {results: [{cluster_id: "CL.001", cluster_label: "...", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const CLUSTER_ATLAS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Reads the CLUSTER_ATLAS JSON file from the L2.5/L3.5 Discovery Layer and ' +
    'filters ClusterEntry records by domain, sub_domain, and minimum cluster size, returning ' +
    'raw cluster rows (cluster_label, dominant_domain, sub_domains, cluster_size_n, confidence, ' +
    'significance, annotation) without synthesis. Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'Discovery Layer signal clusters across all Jyotish domains',
  whenToPrefer:
    'Use cluster_atlas when you need co-activating signal groups from the Discovery Layer. ' +
    'Prefer pattern_register when you need individual detected patterns rather than cluster aggregations. ' +
    'Prefer resonance_register when cross-domain bridging entries (domains_bridged) are needed. ' +
    'Prefer holistic_bundle when interpretation or synthesis is also required.',
})

const ClusterAtlasInputSchema = z.object({
  domain: z.string().optional().describe(
    'Filter to clusters whose dominant_domain matches this value. ' +
    'Examples: "career", "health", "relationships", "spiritual", "wealth".'
  ),
  sub_domain: z.string().optional().describe(
    'Filter to clusters whose sub_domains array contains this value. ' +
    'Broadens the domain filter — a cluster is included if sub_domain appears anywhere in sub_domains.'
  ),
  min_size: z.number().int().min(1).optional().describe(
    'Minimum cluster size (number of signals). Clusters with fewer signals are excluded.'
  ),
  limit: z.number().int().min(1).max(100).optional().default(20).describe(
    'Max clusters to return (default 20, max 100).'
  ),
})

type ClusterAtlasInput = z.infer<typeof ClusterAtlasInputSchema>

export function registerClusterAtlas(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'cluster_atlas',
    CLUSTER_ATLAS_DESCRIPTION,
    ClusterAtlasInputSchema.shape,
    async (args: ClusterAtlasInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'cluster_atlas',
        {
          ...(args.domain ? { domain: args.domain } : {}),
          ...(args.sub_domain ? { sub_domain: args.sub_domain } : {}),
          ...(args.min_size !== undefined ? { min_size: args.min_size } : {}),
          limit: args.limit ?? 20,
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }
      return okResult(envelope)
    }
  )
}
