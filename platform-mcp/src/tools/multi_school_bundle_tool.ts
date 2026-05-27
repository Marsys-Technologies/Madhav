/**
 * multi_school_bundle_tool.ts — MCP Tier 2 bundle: cross-school convergence.
 *
 * Registers multi_school_bundle as an MCP tool. Delegates to the bundle executor
 * which runs cross_school_lookup + per-school evidence queries in parallel + reads
 * the most-cited classical text. Same error-isolation semantics as holistic_bundle.
 *
 * MCPT v3.1.0-S2
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { executeMultiSchoolBundle } from '../bundles/multi_school_bundle.js'
import type { Principal } from '../types.js'
import { okResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

const SCHOOLS = ['parashara', 'jaimini', 'kp', 'tajaka'] as const

export const MULTI_SCHOOL_BUNDLE_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Runs a parallel multi-school convergence check on an astrological claim — ' +
    'fires cross_school_lookup, per-school evidence queries (Parashara/Jaimini/KP/Tajaka), ' +
    'and reads the most-cited classical text reference, all concurrently.',
  enumSource: SCHOOLS,
  coverageHint: 'All four school evidence sets fully populated (MCPT v3.3); results cached 5 minutes',
  whenToPrefer:
    'Use when the question explicitly concerns whether all four schools agree or disagree on a claim. ' +
    'Prefer holistic_bundle when you want multi-school data synthesized alongside the native\'s actual signals. ' +
    'Prefer cross_school_lookup directly for a lightweight stance-only check without per-school evidence.',
})

// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
const MultiSchoolBundleInputSchema = z.object({
  // Accepts `claim` (new) or `topic` (old callers). Handler normalizes to `claim`.
  claim: z.string().optional().describe(
    'Astrological claim to verify across schools. State as a declarative sentence. ' +
    'Example: "Saturn in 10th house delays career until 36" or ' +
    '"Moon-Ketu conjunction in 4th house indicates maternal separation theme".'
  ),
  topic: z.string().optional().describe('Backward-compat alias for claim.'),
  schools: z.array(z.enum(SCHOOLS)).optional().describe(
    'Schools to include. Defaults to all four: parashara, jaimini, kp, tajaka. ' +
    'All four school evidence sets (including KP and Tajaka) are fully populated as of MCPT v3.3.'
  ),
})

// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
// Compat schema with transform+refine for tests — normalises topic → claim (min 10 chars).
export const MultiSchoolBundleCompatSchema = MultiSchoolBundleInputSchema.transform(i => ({
  ...i,
  claim: i.claim ?? i.topic ?? '',
})).refine(i => i.claim.length >= 10, {
  message: 'claim (or topic) must be at least 10 characters',
})

type MultiSchoolBundleInput = z.infer<typeof MultiSchoolBundleInputSchema>

export function registerMultiSchoolBundle(
  server: McpServer,
  getPrincipal: () => Principal,
  descriptionOverride?: string
): void {
  server.tool(
    'multi_school_bundle',

    descriptionOverride ?? MULTI_SCHOOL_BUNDLE_DESCRIPTION,

    MultiSchoolBundleInputSchema.shape,

    async (input: MultiSchoolBundleInput) => {
      const principal = getPrincipal()
      // --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
      const claim = input.claim ?? input.topic ?? ''

      const envelope = await executeMultiSchoolBundle(
        {
          claim,
          schools: input.schools,
          tier: '', // audience_tier excised; cache+audit keep field for back-compat (Stream A 3.tier_excision 2026-05-28).
          chart_id: undefined,
        },
        principal
      )

      return okResult(envelope)
    }
  )
}
