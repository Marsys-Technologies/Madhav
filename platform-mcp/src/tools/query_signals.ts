/**
 * query_signals.ts — MCP Tier 3 surgical primitive: MSR signal corpus lookup.
 *
 * What it does: Queries the MSR (Master Signal Register) corpus of 499+ astrological
 * signals with structured filters. Returns raw signal rows — domain, valence, dasha
 * activations, confidence, significance, forward-looking flag, and signal text. This
 * is a direct L2.5 data read that bypasses the planner and synthesis stages. Tagged
 * surgical: true in the epistemics block.
 *
 * When to prefer: Use query_signals when you need raw signal data from the MSR corpus
 * rather than synthesized prose. Prefer over holistic_bundle when the goal is "give me
 * all forward-looking signals in the career domain" as a structured list. Prefer
 * holistic_bundle when interpretation or cross-domain synthesis is also required.
 *
 * Input shape hints:
 *   domain — optional; e.g. "career", "health", "relationships", "spiritual".
 *   planet — optional; filter to signals involving a specific planet.
 *   dasha_lord — optional; filter to signals activated by a specific dasha lord.
 *   min_confidence — optional float 0.0–1.0; filter to signals above this threshold.
 *   forward_looking — optional boolean; true = only prospective signals.
 *   limit — optional; max signals to return (default 50).
 *
 * Output shape preview: {ok, result: {signals: MsrSignalRow[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_signals({domain: "career", forward_looking: true, min_confidence: 0.8}) →
 *   {ok: true, result: {signals: [{signal_id: "SIG.MSR.234", domain: "career", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

// Unit 3.dejudge (2026-05-28): query-time judgment removed.
//
// Previously this MCP tool re-applied the same LL.1 / finance-floor / Pancha-MP
// post-processing that the portal msr_sql tool applied, so a clean signal that
// fell below the 0.6 default (or 0.35 finance/wealth) floor was silently
// dropped twice — once on the portal side and again here. Audit §6-A.
//
// Both removals land in the same wave so the channels stay identical.
//
// Ranking and salience now live in the L2.5 computed coefficient
// (deterministic_strength, verification_certainty, computed_salience — three
// distinct columns added in 2a.1 / migration 086) and in the serve-time panel,
// not in this query-time tool.

export const QUERY_SIGNALS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries the MSR signal corpus (499+ astrological signals) with structured ' +
    'filters (domain, domains[], planet, dasha_lord, min_confidence, forward_looking, valence, temporal_activation) ' +
    'and returns raw signal rows without synthesis.',
  coverageHint: '499+ signals across all Jyotish domains',
  whenToPrefer:
    'Use for "give me all forward-looking career signals" style queries. ' +
    'Prefer holistic_bundle when interpretation or cross-domain synthesis is also needed. ' +
    'Prefer query_chart_facts for raw chart-fact rows rather than MSR signals.',
})

const QuerySignalsInputSchema = z.object({
  domain: z.string().optional().describe(
    'Jyotish domain filter. Examples: "career", "health", "relationships", "spiritual".'
  ),
  domains: z.array(z.string()).optional().describe(
    'Multiple domain filters. When provided, returns signals matching any of the listed domains. ' +
    'Prefer this over repeated single-domain calls.'
  ),
  planet: z.string().optional().describe('Filter to signals involving a specific planet.'),
  dasha_lord: z.string().optional().describe(
    'Filter to signals activated by a specific dasha lord (e.g. "Saturn", "Ketu").'
  ),
  min_confidence: z.number().min(0).max(1).optional().describe(
    'Minimum confidence threshold (0.0–1.0). Returns signals at or above this level.'
  ),
  forward_looking: z.boolean().optional().describe(
    'If true, return only prospective (forward-looking) signals.'
  ),
  valence: z.enum(['benefic', 'malefic', 'context-dependent']).optional().describe(
    'Filter by signal valence. "benefic" = helpful/positive outcomes; "malefic" = challenging/difficult; "context-dependent" = mixed or situational.'
  ),
  temporal_activation: z.enum(['permanent', 'dasha_tied', 'transit_tied']).optional().describe(
    'Filter by activation pattern. "permanent" = natal, always active; "dasha_tied" = active only in specific dasha periods; "transit_tied" = active only during specific transits.'
  ),
  limit: z.number().int().min(1).max(500).optional().default(50).describe(
    'Max signals to return (default 50, max 500).'
  ),
})

type QuerySignalsInput = z.infer<typeof QuerySignalsInputSchema>

export function registerQuerySignals(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_signals',
    QUERY_SIGNALS_DESCRIPTION,
    QuerySignalsInputSchema.shape,
    async (args: QuerySignalsInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_signals',
        {
          ...(args.domain ? { domain: args.domain } : {}),
          ...(args.domains && args.domains.length > 0 ? { domains: args.domains } : {}),
          ...(args.planet ? { planet: args.planet } : {}),
          ...(args.dasha_lord ? { dasha_lord: args.dasha_lord } : {}),
          ...(args.min_confidence !== undefined ? { min_confidence: args.min_confidence, confidence_floor: args.min_confidence } : {}),
          ...(args.forward_looking !== undefined ? { forward_looking: args.forward_looking } : {}),
          ...(args.valence !== undefined ? { valence: [args.valence] } : {}),
          ...(args.temporal_activation !== undefined ? { temporal_activation: [args.temporal_activation] } : {}),
          limit: args.limit ?? 50,
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // Unit 3.dejudge (2026-05-28): no client-side calibration. The platform
      // primitive `query_signals` (portal msr_sql) already returns the
      // never-dropped signal set with its native confidence + significance
      // columns. Salience now belongs to the L2.5 computed coefficient and the
      // serve-time panel — both downstream of this tool.
      return okResult(envelope)
    }
  )
}
