/**
 * msr_sql.ts — MCP Tier 3 surgical primitive: MSR signal corpus SQL lookup.
 *
 * What it does: Queries the MSR (Master Signal Register) Cloud SQL table directly
 * with structured filters — domain, forward_looking, confidence_floor, signal_type,
 * chart_id — and returns raw signal rows ranked by confidence × significance.
 * This is a direct L2.5 data read that bypasses the planner and synthesis stages.
 * Tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use msr_sql when you need the full SQL-layer filter set —
 * confidence_floor, signal_type, chart_id UUID scoping. Prefer query_signals when
 * you need domain/planet/dasha_lord/valence filters with LL.1 calibration applied
 * client-side. Prefer holistic_bundle when cross-domain synthesis or interpretation
 * is also required.
 *
 * Input shape hints:
 *   domain — optional; e.g. "career", "health", "relationships".
 *   domains — optional array; filter to signals in any of the listed domains.
 *   forward_looking — optional boolean; true = only prospective signals.
 *   confidence_floor — optional float 0.0–1.0; filter to signals at or above this level.
 *   chart_id — optional UUID; scope to a specific chart (defaults to native chart).
 *   signal_type — optional; e.g. "yoga", "aspect", "transit".
 *   limit — optional; max signals to return (default 50, max 500).
 *
 * Output shape preview: {ok, result: {results: ToolBundleResult[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: msr_sql({domain: "career", forward_looking: true, confidence_floor: 0.7}) →
 *   {ok: true, result: {results: [{signal_id: "SIG.MSR.234", domain: "career", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const MSR_SQL_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries the MSR signal corpus Cloud SQL table directly with structured ' +
    'filters (domain, domains[], forward_looking, confidence_floor, chart_id UUID, signal_type, limit) ' +
    'and returns raw signal rows ranked by confidence × significance without synthesis. ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: '573+ signals across all Jyotish domains in the MSR corpus',
  whenToPrefer:
    'Use msr_sql when you need full SQL-layer filter control — confidence_floor, signal_type, chart_id scoping. ' +
    'Prefer query_signals when domain/planet/dasha_lord/valence filters with LL.1 calibration are needed. ' +
    'Prefer holistic_bundle when cross-domain synthesis or interpretation is also required.',
})

const MsrSqlInputSchema = z.object({
  domain: z.string().optional().describe(
    'Jyotish domain filter. Examples: "career", "health", "relationships", "spiritual", "wealth".'
  ),
  domains: z.array(z.string()).optional().describe(
    'Multiple domain filters. When provided, returns signals matching any of the listed domains. ' +
    'Prefer this over repeated single-domain calls. Finance/wealth domains use a lower confidence floor (0.35).'
  ),
  forward_looking: z.boolean().optional().describe(
    'If true, return only prospective (forward-looking) signals.'
  ),
  confidence_floor: z.number().min(0).max(1).optional().describe(
    'Minimum confidence threshold (0.0–1.0). Signals at or above this level are returned. ' +
    'Default: 0.6 globally; 0.35 for finance/wealth domains.'
  ),
  chart_id: z.string().uuid().optional().describe(
    'UUID of a specific chart to scope the query to. Defaults to the native chart (Abhisek Mohanty).'
  ),
  signal_type: z.string().optional().describe(
    'Filter by signal type. Examples: "yoga", "aspect", "transit", "planetary_strength".'
  ),
  limit: z.number().int().min(1).max(500).optional().default(50).describe(
    'Max signals to return (default 50, max 500).'
  ),
})

type MsrSqlInput = z.infer<typeof MsrSqlInputSchema>

export function registerMsrSql(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'msr_sql',
    MSR_SQL_DESCRIPTION,
    MsrSqlInputSchema.shape,
    async (args: MsrSqlInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'msr_sql',
        {
          ...(args.domain ? { domain: args.domain } : {}),
          ...(args.domains && args.domains.length > 0 ? { domains: args.domains } : {}),
          ...(args.forward_looking !== undefined ? { forward_looking: args.forward_looking } : {}),
          ...(args.confidence_floor !== undefined ? { confidence_floor: args.confidence_floor } : {}),
          ...(args.chart_id ? { chart_id: args.chart_id } : {}),
          ...(args.signal_type ? { signal_type: [args.signal_type] } : {}),
          limit: args.limit ?? 50,
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
