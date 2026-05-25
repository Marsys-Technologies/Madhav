/**
 * resonance_register.ts — MCP Tier 3 surgical primitive: RESONANCE_REGISTER lookup.
 *
 * What it does: Reads the RESONANCE_REGISTER JSON file from the repository and
 * filters ResonanceEntry records by domain and keyword. Returns raw resonance rows
 * — claim_text, mechanism, domains_bridged, confidence, significance, forward-looking
 * flag, and time-indexed falsifier — without synthesis.
 * Tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use resonance_register when you need cross-domain resonance
 * entries from the L2.5 Discovery Layer that explicitly bridge multiple Jyotish
 * domains. Prefer over pattern_register when the query is about multi-domain
 * intersection rather than single-domain patterns. Prefer holistic_bundle when
 * interpretation or synthesis is also required.
 *
 * Input shape hints:
 *   domain       — optional; filter entries where domains_bridged includes this domain.
 *   keyword      — optional; filters by substring match on claim_text or mechanism.
 *   min_confidence — optional float 0.0–1.0; exclude resonances below this threshold.
 *   limit        — optional; max resonances to return (default 50, max 200).
 *
 * Output shape preview: {ok, result: {results: ResonanceEntry[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: resonance_register({domain: "career", min_confidence: 0.7}) →
 *   {ok: true, result: {results: [{resonance_id: "RES.001", domains_bridged: ["career", "spiritual"], ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const RESONANCE_REGISTER_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Reads the RESONANCE_REGISTER JSON file from the L2.5 Discovery Layer and ' +
    'filters ResonanceEntry records by domain (domains_bridged includes match) and keyword, ' +
    'returning raw resonance rows (claim_text, mechanism, domains_bridged, confidence, ' +
    'significance, forward_looking, falsifier) without synthesis. ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'Cross-domain resonance entries bridging multiple Jyotish domains',
  whenToPrefer:
    'Use resonance_register when the query is about multi-domain intersection rather than ' +
    'single-domain patterns. Prefer pattern_register for single-domain pattern entries. ' +
    'Prefer holistic_bundle when cross-domain synthesis or interpretation is also required.',
})

const ResonanceRegisterInputSchema = z.object({
  domain: z.string().optional().describe(
    'Jyotish domain filter — returns entries where domains_bridged includes this domain. ' +
    'Examples: "career", "health", "relationships", "spiritual", "wealth".'
  ),
  keyword: z.string().optional().describe(
    'Substring filter applied to claim_text and mechanism fields. Case-insensitive.'
  ),
  min_confidence: z.number().min(0).max(1).optional().describe(
    'Minimum confidence threshold (0.0–1.0). Resonances below this level are excluded.'
  ),
  limit: z.number().int().min(1).max(200).optional().default(50).describe(
    'Max resonances to return (default 50, max 200).'
  ),
})

type ResonanceRegisterInput = z.infer<typeof ResonanceRegisterInputSchema>

export function registerResonanceRegister(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'resonance_register',
    RESONANCE_REGISTER_DESCRIPTION,
    ResonanceRegisterInputSchema.shape,
    async (args: ResonanceRegisterInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'resonance_register',
        {
          ...(args.domain ? { domain: args.domain } : {}),
          ...(args.keyword ? { keyword: args.keyword } : {}),
          ...(args.min_confidence !== undefined ? { min_confidence: args.min_confidence } : {}),
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
