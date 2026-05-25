/**
 * query_cdlm_lookup.ts — MCP Tier 3 surgical primitive: CDLM cross-domain linkage lookup.
 *
 * What it does: Parses CDLM_v1_1.md (81-cell Cross-Domain Linkage Matrix) and returns
 * matching linkage cells filtered by domain_a, domain_b, or signal_id. Returns raw CDLM
 * entries — domain_pair, row_domain, col_domain, linkage_type, strength, direction,
 * valence, signal_ids, key_finding — without synthesis. Tagged surgical: true in the
 * epistemics block.
 *
 * When to prefer: Use query_cdlm_lookup when a query asks about cross-domain interactions,
 * linkage types (feeds, modulates, amplifies, etc.), or which domains a specific MSR signal
 * bridges. Full-dump mode (no params) returns all 81 cells. Prefer holistic_bundle when
 * synthesis or interpretation across the full chart is also required.
 *
 * Input shape hints:
 *   domain_a  — optional; row-domain filter (e.g. "Career"). Case-insensitive substring match.
 *   domain_b  — optional; column-domain filter (e.g. "Wealth"). Case-insensitive substring match.
 *   signal_id — optional; returns only cells whose msr_anchors contain this signal ID (e.g. "MSR.413").
 *
 * Output shape preview: {ok, result: {results: CdlmEntry[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_cdlm_lookup({domain_a: "Career", domain_b: "Wealth"}) →
 *   {ok: true, result: {results: [{domain_pair: "Career→Wealth", linkage_type: "feeds", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_CDLM_LOOKUP_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Parses CDLM_v1_1.md (81-cell Cross-Domain Linkage Matrix) and returns ' +
    'matching linkage cells filtered by domain_a (row), domain_b (column), or signal_id. ' +
    'Returns raw CDLM entries — domain_pair, row_domain, col_domain, linkage_type, strength, ' +
    'direction, valence, signal_ids, key_finding — without synthesis. ' +
    'Full-dump mode (no params) returns all 81 cells. ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: '81-cell CDLM across 9 Jyotish life-domains',
  whenToPrefer:
    'Use query_cdlm_lookup when a query asks about cross-domain interactions, linkage types, ' +
    'or which domains a specific MSR signal bridges. ' +
    'Prefer holistic_bundle when synthesis or interpretation across the full chart is also required. ' +
    'Prefer query_ucn_walk when you need UCN narrative-section context rather than CDLM linkage cells.',
})

const QueryCdlmLookupInputSchema = z.object({
  domain_a: z.string().optional().describe(
    'Row-domain filter (case-insensitive substring match). ' +
    'Examples: "Career", "Wealth", "Health", "Relationships", "Spirit".'
  ),
  domain_b: z.string().optional().describe(
    'Column-domain filter (case-insensitive substring match). ' +
    'Examples: "Career", "Wealth", "Health", "Relationships", "Spirit".'
  ),
  signal_id: z.string().optional().describe(
    'MSR signal ID filter (e.g. "MSR.413"). Returns only cells whose msr_anchors contain this signal.'
  ),
})

type QueryCdlmLookupInput = z.infer<typeof QueryCdlmLookupInputSchema>

export function registerQueryCdlmLookup(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_cdlm_lookup',
    QUERY_CDLM_LOOKUP_DESCRIPTION,
    QueryCdlmLookupInputSchema.shape,
    async (args: QueryCdlmLookupInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_cdlm_lookup',
        {
          ...(args.domain_a ? { domain_a: args.domain_a } : {}),
          ...(args.domain_b ? { domain_b: args.domain_b } : {}),
          ...(args.signal_id ? { signal_id: args.signal_id } : {}),
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
