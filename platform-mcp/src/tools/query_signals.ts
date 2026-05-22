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

const QuerySignalsInputSchema = z.object({
  domain: z.string().optional().describe(
    'Jyotish domain filter. Examples: "career", "health", "relationships", "spiritual".'
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
    'What it does: Queries the MSR signal corpus (499+ astrological signals) with structured ' +
    'filters and returns raw signal rows without synthesis. ' +
    'When to prefer: Use for "give me all forward-looking career signals" style queries. ' +
    'Prefer holistic_bundle when interpretation or cross-domain synthesis is also needed. ' +
    'Input shape hints: all params optional; domain filters by Jyotish domain; ' +
    'dasha_lord filters by activating dasha; min_confidence is a 0–1 float; ' +
    'forward_looking:true limits to prospective signals. ' +
    'Output shape preview: {ok, result: {signals: MsrSignalRow[]}, trace_id, epistemics: {surgical: true}}. ' +
    'Example: query_signals({domain: "career", forward_looking: true}) → raw MSR signal rows.',
    QuerySignalsInputSchema.shape,
    async (args: QuerySignalsInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_signals',
        {
          ...(args.domain ? { domain: args.domain } : {}),
          ...(args.planet ? { planet: args.planet } : {}),
          ...(args.dasha_lord ? { dasha_lord: args.dasha_lord } : {}),
          ...(args.min_confidence !== undefined ? { min_confidence: args.min_confidence } : {}),
          ...(args.forward_looking !== undefined ? { forward_looking: args.forward_looking } : {}),
          limit: args.limit ?? 50,
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
