/**
 * flag_disagreement.ts — MCP tool: flag a disagreement to the MARSYS governance register.
 *
 * Tier 6 — Write tool (MCP-4-S1). Formal governance channel for MCP callers.
 *
 * Tool description (§4.6-standard, ≥100 words, 5 blocks):
 *
 * What it does: Logs a formal disagreement to the MARSYS-JIS governance
 * register (mcp_disagreements table, mirroring DISAGREEMENT_REGISTER_v1_0.md
 * §2 schema). Use this tool when you detect a contradiction between MARSYS
 * outputs and your own assessment, between two signal readings from different
 * sessions, or when a structural inconsistency arises that cannot be silently
 * resolved. This is a formal governance channel: the native reviews open
 * entries and may promote significant ones to the markdown register as
 * full DR entries (DIS.NNN). Silent overwriting of contradictions is
 * forbidden per CLAUDE.md §K and ND.1.
 *
 * When to prefer: Use this tool when you encounter any of these situations:
 * (1) An MSR signal contradicts FORENSIC L1 data (class: "factual").
 * (2) Two holistic_bundle responses on the same question yield conflicting
 *     conclusions in the same session (class: "output_conflict").
 * (3) This MARSYS session's output conflicts with a prior session's finding
 *     that you have context about (class: "interpretive").
 * (4) A structural scope issue: the question cannot be answered because the
 *     instrument doesn't cover the relevant domain (class: "structural").
 * Do NOT use for minor uncertainty — only for genuine, irresolvable conflicts.
 *
 * Input shape hints:
 *   class          — one of: factual, interpretive, structural, mirror_desync,
 *                    scope, output_conflict, version_disagreement,
 *                    scope_disagreement, closure_disagreement. Use "factual"
 *                    for L1 data conflicts, "interpretive" for synthesis
 *                    conflicts, "structural" for architecture/scope issues.
 *   description    — 2–5 sentences: what the disagreement is, when noticed,
 *                    why it cannot be silently resolved. Be specific — cite
 *                    signal IDs (SIG.MSR.NNN), FORENSIC sections, or session IDs.
 *   source_session — a label for the current session context so the native
 *                    can trace where the disagreement was noticed.
 *   proposed_resolution — optional: what you think should happen. The native
 *                    makes the final call, but your recommendation is useful.
 *
 * Output shape preview:
 *   {ok: true, result: {disagreement_id: "DIS.MCP.XXXXXXXX"}, trace_id, epistemics}
 *
 * Example:
 *   flag_disagreement({
 *     class: "factual",
 *     description: "SIG.MSR.377 asserts Muntha in Gemini 3H but FORENSIC §22 records Muntha = Libra 7H (lord Venus). The MSR signal's signal_name and body are internally inconsistent AND contradict L1. Cannot be silently resolved — MSR.377 is load-bearing in this query's predictive synthesis.",
 *     source_session: "Cowork_career_query_2026-05-21",
 *     proposed_resolution: "Correct SIG.MSR.377 to Libra 7H per FORENSIC §22 authority (B.8 / B.1). Re-run drift and schema validators."
 *   })
 *   → {ok: true, result: {disagreement_id: "DIS.MCP.B7F2A9C3"}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformWrites } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

// ── Input schema ──────────────────────────────────────────────────────────────

const DisagreementClassSchema = z.enum([
  'factual',
  'interpretive',
  'structural',
  'mirror_desync',
  'scope',
  'output_conflict',
  'version_disagreement',
  'scope_disagreement',
  'closure_disagreement',
  'l3_zero_supports',
  'panel_divergence',
  'school_disagreement',
  'acceptance_rate_anomaly',
])

const FlagDisagreementInputSchema = z.object({
  class: DisagreementClassSchema.describe(
    'Disagreement class from DISAGREEMENT_REGISTER §1. ' +
    'Use "factual" for L1 data conflicts, "interpretive" for synthesis conflicts, ' +
    '"structural" for architecture/scope issues, "output_conflict" for inter-session conflicts.'
  ),
  description: z
    .string()
    .describe(
      '2–5 sentences: what the disagreement is, when noticed, and why it cannot be silently resolved. ' +
      'Cite signal IDs (SIG.MSR.NNN), FORENSIC sections, or session IDs for traceability.'
    ),
  source_session: z
    .string()
    .describe('Label for the current session context (e.g. "Cowork_career_2026-05-21").'),
  proposed_resolution: z
    .string()
    .optional()
    .describe('Optional: your recommended resolution for native review.'),
})

type FlagDisagreementInput = z.infer<typeof FlagDisagreementInputSchema>

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the flag_disagreement MCP tool.
 *
 * @param server       The McpServer instance.
 * @param getPrincipal Callback that returns the resolved principal for this request.
 */
export function registerFlagDisagreement(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'flag_disagreement',
    'Flag a governance disagreement to the MARSYS-JIS register. Use when you detect ' +
    'a contradiction between MSR signals and FORENSIC L1 data, between two synthesis ' +
    'outputs, or any irresolvable conflict. This is a formal channel — the native ' +
    'reviews entries. Returns disagreement_id for tracking.',
    FlagDisagreementInputSchema.shape,
    async (input: FlagDisagreementInput) => {
      const principal = getPrincipal()

      // T.1: flag_disagreement is a governance write tool restricted to super_admin.
      // Acharya and client tiers can note conflicts in their responses but cannot
      // write to the formal governance register — that requires operator trust.
      if (principal.audience_tier !== 'super_admin') {
        return errorResult({
          ok: false,
          error: {
            class: 'TIER_FORBIDDEN',
            message: 'flag_disagreement requires super_admin tier. ' +
              'Acharya/client callers: note the conflict in your response instead.',
          },
        })
      }

      const result = await callPlatformWrites(
        'flag_disagreement',
        {
          entry: {
            class: input.class,
            description: input.description,
            source_session: input.source_session,
            proposed_resolution: input.proposed_resolution ?? null,
          },
        },
        principal
      )

      if (!result.envelope.ok) {
        return errorResult(result.envelope)
      }

      return okResult(result.envelope)
    }
  )
}
