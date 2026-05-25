/**
 * contradiction_register.ts — MCP Tier 3 surgical primitive: CONTRADICTION_REGISTER lookup.
 *
 * What it does: Reads the CONTRADICTION_REGISTER JSON file from the repository and
 * filters ContradictionEntry records by domain and contradiction_class. Returns raw
 * contradiction rows — hypothesis_text, mechanism, domains_implicated, signals_in_conflict,
 * resolution_options, contradiction_class — without synthesis.
 * Tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use contradiction_register when you need known contradictions and
 * tensions from the L2.5 Discovery Layer — cases where signals point in opposing
 * directions or classical schools disagree. Prefer over holistic_bundle when the
 * goal is "surface all contradictions in the career domain" as a structured list.
 * Prefer pattern_register for co-activating convergent patterns rather than
 * contradictions.
 *
 * Input shape hints:
 *   domain               — optional; filters to contradictions implicating this domain.
 *   contradiction_class  — optional; e.g. "inter-system", "intra-system", "temporal".
 *   limit                — optional; max contradictions to return (default 20, max 100).
 *
 * Output shape preview: {ok, result: {results: ContradictionEntry[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: contradiction_register({domain: "career", contradiction_class: "inter-system"}) →
 *   {ok: true, result: {results: [{contradiction_id: "CON.001", hypothesis_text: "...", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const CONTRADICTION_REGISTER_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Reads the CONTRADICTION_REGISTER JSON file from the L2.5 Discovery Layer and ' +
    'filters ContradictionEntry records by domain and contradiction_class, returning raw ' +
    'contradiction rows (hypothesis_text, mechanism, domains_implicated, signals_in_conflict, ' +
    'resolution_options, contradiction_class) without synthesis. ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'Discovery Layer contradictions and signal tensions across all Jyotish domains',
  whenToPrefer:
    'Use contradiction_register when you need known contradictions where signals point in opposing directions. ' +
    'Prefer pattern_register for convergent cross-signal patterns. ' +
    'Prefer cluster_atlas for signal groupings by dominant domain. ' +
    'Prefer holistic_bundle when interpretation or synthesis is also required.',
})

const ContradictionRegisterInputSchema = z.object({
  domain: z.string().optional().describe(
    'Filter to contradictions whose domains_implicated array contains this value. ' +
    'Examples: "career", "health", "relationships", "spiritual", "wealth".'
  ),
  contradiction_class: z.string().optional().describe(
    'Filter by contradiction class. ' +
    'Examples: "inter-system" (schools disagree), "intra-system" (same school contradicts itself), "temporal" (signals conflict at different times).'
  ),
  limit: z.number().int().min(1).max(100).optional().default(20).describe(
    'Max contradictions to return (default 20, max 100).'
  ),
})

type ContradictionRegisterInput = z.infer<typeof ContradictionRegisterInputSchema>

export function registerContradictionRegister(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'contradiction_register',
    CONTRADICTION_REGISTER_DESCRIPTION,
    ContradictionRegisterInputSchema.shape,
    async (args: ContradictionRegisterInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'contradiction_register',
        {
          ...(args.domain ? { domain: args.domain } : {}),
          ...(args.contradiction_class ? { contradiction_class: args.contradiction_class } : {}),
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
