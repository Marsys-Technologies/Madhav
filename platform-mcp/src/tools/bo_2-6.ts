/**
 * bo_2-6.ts — MCP tool: query_remediation
 * Layer L2 · Wave 2 · Asset BO-2-6 (bodha.remediation)
 *
 * Exposes the bodha.remediation table as an MCP-callable tool.
 *
 * Tool: query_remediation(chart_id, domain?)
 *   → remedies with L0 citation (BPHS chapter/verse or concordance rule_id)
 *
 * Depends on:
 *   - BO-2-1 (bodha.signals): bodha_signals table
 *   - BO-2-2 (bodha.graph): bodha_graph table (contradiction hubs)
 *   - BG-0-7 (brahmagyan.concordance): concordance_lookup (L0 rule source)
 *
 * FORENSIC ground: Abhisek Mohanty, 1984-02-05 10:43 IST Bhubaneswar.
 * At least 1 remedy row for the native chart must be grounded to BPHS/concordance.
 *
 * Architecture:
 *   MCP tool → callPlatformPrimitive('/api/mcp/primitives/query_remediation')
 *   → platform route → bodha_remediation DB table
 *
 * surgical: true (pure retrieval; no LLM calls)
 */

import { z } from 'zod'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'

// ── Input schema ───────────────────────────────────────────────────────────────

export const QueryRemediationInputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to retrieve remediation for. ' +
      'Use the native chart ID (Abhisek Mohanty: 1984-02-05 10:43 IST Bhubaneswar).'
    ),
  domain: z
    .string()
    .optional()
    .describe(
      'Optional Jyotish domain filter. Narrows results to contradiction hubs in that domain. ' +
      'Examples: "career", "health", "relationship", "finance", "dharma". ' +
      'Omit to return remedies across all domains.'
    ),
  limit: z
    .number()
    .int()
    .min(1)
    .max(100)
    .default(50)
    .describe('Maximum number of remedy rows to return. Default 50.'),
})

export type QueryRemediationInput = z.infer<typeof QueryRemediationInputSchema>

// ── Output shape (documented; actual shape comes from the platform) ────────────

/**
 * One remedy row returned by query_remediation.
 *
 * source_citation always traces to a BPHS chapter/verse or L0 concordance rule_id:
 *   - format "BPHS.<chapter>.<verses>" (e.g. BPHS.25.41-56)
 *   - or a concordance_lookup.source_citation value
 *
 * source_l0_rule_id traces to concordance_lookup.id or a BPHS-FALLBACK-* key,
 * both of which resolve to BPHS canonical source material.
 */
export interface RemediationRow {
  contradiction_hub_id: string
  hub_label: string | null
  domain: string | null
  edge_count: number
  contradicting_signal_ids: string[]
  remedy_type: 'mantra' | 'charity' | 'gemstone' | 'ritual'
  remedy_text: string
  source_l0_rule_id: string
  source_citation: string
  asset_version: string
  computed_at: string
}

export interface QueryRemediationResult {
  chart_id: string
  domain_filter: string | null
  remedies: RemediationRow[]
  total_count: number
  forensic_grounded: boolean
  asset: string
  asset_version: string
}

// ── Tool description ───────────────────────────────────────────────────────────

export const QUERY_REMEDIATION_DESCRIPTION =
  'Returns per-contradiction-hub classical remedies for a Jyotish chart ' +
  '(bodha.remediation / BO-2-6). ' +
  'Each remedy is grounded to a BPHS chapter/verse or L0 concordance rule_id (BG-0-7). ' +
  'A contradiction hub is a signal node in bodha_graph (BO-2-2) that participates in ' +
  '≥1 contradict edge — the remedy maps the classical resolution to that specific contradiction. ' +
  'source_citation format: BPHS.<chapter>.<verses> (e.g. BPHS.25.41-56). ' +
  'source_l0_rule_id links back to concordance_lookup.id when concordance data is seeded, ' +
  'or to a BPHS-FALLBACK-* key that encodes the same BPHS chapter pointer. ' +
  'Use domain parameter to narrow to a single Jyotish domain (career/health/relationship/…). ' +
  'surgical: true — pure retrieval, no LLM synthesis.'

// ── Tool handler ───────────────────────────────────────────────────────────────

/**
 * query_remediation MCP tool handler.
 *
 * Delegates to /api/mcp/primitives/query_remediation on the platform service.
 * Returns the platform's McpEnvelope directly.
 *
 * Error contract:
 *   - If upstream tables are missing (BO-2-1/2-2/BG-0-7 not yet built) the
 *     platform returns an error envelope with class "not_found"; we pass it through.
 *   - If chart_id has no graph data yet, returns an empty remedies array (not an error).
 */
export async function handleQueryRemediation(
  input: QueryRemediationInput,
  principal: Principal
): Promise<unknown> {
  const params: Record<string, unknown> = {
    chart_id: input.chart_id,
    limit: input.limit,
  }
  if (input.domain) {
    params['domain'] = input.domain
  }

  const result = await callPlatformPrimitive('query_remediation', params, principal)
  return result.envelope
}

// ── MCP server registration helper ────────────────────────────────────────────

/**
 * Register the query_remediation tool on an McpServer instance.
 *
 * Usage in server.ts:
 *   import { registerQueryRemediationTool } from './tools/bo_2-6.js'
 *   registerQueryRemediationTool(server, principal)
 *
 * The tool is surgical (pure retrieval) and appropriate for all principal tiers.
 */
export function registerQueryRemediationTool(
  server: { tool: (name: string, description: string, schema: Record<string, unknown>, handler: (args: unknown) => Promise<unknown>) => void },
  principal: Principal
): void {
  server.tool(
    'query_remediation',
    QUERY_REMEDIATION_DESCRIPTION,
    {
      chart_id: z.string().uuid().describe(
        'UUID of the chart. Use native chart ID for Abhisek Mohanty (1984-02-05 10:43 IST Bhubaneswar).'
      ),
      domain: z.string().optional().describe(
        'Jyotish domain filter: career | health | relationship | finance | dharma | …'
      ),
      limit: z.number().int().min(1).max(100).default(50).describe(
        'Max remedy rows. Default 50.'
      ),
    },
    async (args: unknown) => {
      const parsed = QueryRemediationInputSchema.parse(args)
      return handleQueryRemediation(parsed, principal)
    }
  )
}
