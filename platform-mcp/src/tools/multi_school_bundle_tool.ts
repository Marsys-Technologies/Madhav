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

const SCHOOLS = ['parashara', 'jaimini', 'kp', 'tajaka'] as const

const MultiSchoolBundleInputSchema = z.object({
  claim: z.string().min(10).describe(
    'Astrological claim to verify across schools. State as a declarative sentence. ' +
    'Example: "Saturn in 10th house delays career until 36" or ' +
    '"Moon-Ketu conjunction in 4th house indicates maternal separation theme".'
  ),
  schools: z.array(z.enum(SCHOOLS)).optional().describe(
    'Schools to include. Defaults to all four: parashara, jaimini, kp, tajaka. ' +
    'All four school evidence sets (including KP and Tajaka) are fully populated as of MCPT v3.3.'
  ),
})

type MultiSchoolBundleInput = z.infer<typeof MultiSchoolBundleInputSchema>

export function registerMultiSchoolBundle(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'multi_school_bundle',

    `What it does: Runs a parallel multi-school convergence check on an astrological claim.
Fires: (1) cross_school_lookup to get stance + citation per school; (2) per-school
targeted evidence queries (Parashara → MSR signals, Jaimini → strength_extra chart_facts,
KP → kp_cusp chart_facts, Tajaka → varshphal chart_facts); (3) read_classical_text for
the most-cited classical reference from the lookup result. All tasks run concurrently with
8-second per-tool timeouts and error isolation. All four school evidence sets are fully
populated (MCPT v3.3 complete). Results
cached 5 minutes.

When to prefer: Use multi_school_bundle when the question explicitly concerns whether
Parashara, Jaimini, KP, and Tajaka schools agree or disagree on a specific rule or
claim. Prefer holistic_bundle when you want the multi-school data synthesized alongside the
native's actual signals. Prefer query_signals + cross_school_lookup directly when you
need raw school-level data without the bundle orchestration.

Input shape: claim (required declarative sentence), schools (optional subset).

Output shape: { ok: true, bundle_name: "multi_school_bundle", served_from_cache: bool,
claim, schools, bundle_entries: [{sub_tool, errored, data, rows_returned, latency_ms}...],
provenance: {sub_tools_fired, sub_tools_errored, convergence_score?: float} }.

Example: multi_school_bundle({ claim: "Saturn aspects 7th house lord damages partnerships" })
→ bundle_entries has cross_school_lookup + 4 per-school evidence entries + optional
classical text read; provenance.convergence_score from cross_school_lookup.`,

    MultiSchoolBundleInputSchema.shape,

    async (input: MultiSchoolBundleInput) => {
      const principal = getPrincipal()

      const envelope = await executeMultiSchoolBundle(
        {
          claim: input.claim,
          schools: input.schools,
          tier: principal.audience_tier,
          chart_id: undefined,
        },
        principal
      )

      return okResult(envelope)
    }
  )
}
