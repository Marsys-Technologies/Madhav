/**
 * pattern_register.ts — MCP Tier 3 surgical primitive: PATTERN_REGISTER lookup.
 *
 * What it does: Reads the PATTERN_REGISTER JSON file from the repository and
 * filters PatternEntry records by domain and keyword. Returns raw pattern rows
 * — claim_text, mechanism, domain, confidence, significance, forward-looking
 * flag, and time-indexed falsifier — without synthesis.
 * Tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use pattern_register when you need detected cross-signal
 * patterns from the L2.5 Discovery Layer. Prefer over holistic_bundle when the
 * goal is "give me all forward-looking career patterns" as a structured list.
 * Prefer resonance_register when you need cross-domain resonance entries that
 * bridge multiple domains simultaneously.
 *
 * Input shape hints:
 *   domain       — optional; e.g. "career", "health", "relationships".
 *   keyword      — optional; filters by substring match on claim_text or mechanism.
 *   min_confidence — optional float 0.0–1.0; exclude patterns below this threshold.
 *   limit        — optional; max patterns to return (default 50, max 200).
 *
 * Output shape preview: {ok, result: {results: PatternEntry[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: pattern_register({domain: "career", min_confidence: 0.7}) →
 *   {ok: true, result: {results: [{pattern_id: "PAT.001", domain: "career", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const PATTERN_REGISTER_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Reads the PATTERN_REGISTER JSON file from the L2.5 Discovery Layer and ' +
    'filters PatternEntry records by domain and keyword, returning raw pattern rows ' +
    '(claim_text, mechanism, domain, confidence, significance, forward_looking, falsifier) ' +
    'without synthesis. Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'Discovery Layer patterns across all Jyotish domains',
  whenToPrefer:
    'Use pattern_register when you need detected cross-signal patterns from the Discovery Layer. ' +
    'Prefer resonance_register when cross-domain bridging entries (domains_bridged) are needed. ' +
    'Prefer holistic_bundle when interpretation or synthesis is also required.',
})

const PatternRegisterInputSchema = z.object({
  domain: z.string().optional().describe(
    'Jyotish domain filter. Examples: "career", "health", "relationships", "spiritual", "wealth".'
  ),
  keyword: z.string().optional().describe(
    'Substring filter applied to claim_text and mechanism fields. Case-insensitive.'
  ),
  min_confidence: z.number().min(0).max(1).optional().describe(
    'Minimum confidence threshold (0.0–1.0). Patterns below this level are excluded.'
  ),
  limit: z.number().int().min(1).max(200).optional().default(50).describe(
    'Max patterns to return (default 50, max 200).'
  ),
})

type PatternRegisterInput = z.infer<typeof PatternRegisterInputSchema>

export function registerPatternRegister(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'pattern_register',
    PATTERN_REGISTER_DESCRIPTION,
    PatternRegisterInputSchema.shape,
    async (args: PatternRegisterInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'pattern_register',
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
