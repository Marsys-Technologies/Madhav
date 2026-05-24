/**
 * cross_school_lookup.ts — MCP Tier 3 surgical primitive: cross-school convergence check.
 *
 * What it does: Checks an astrological claim or rule against multiple Jyotish schools
 * — Parashara (primary), Jaimini, KP, and Tajaka — and returns where they agree,
 * disagree, or are silent on the claim. Returns a structured convergence report per
 * school with source citations and a convergence score. Bypasses planner and synthesis;
 * tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use cross_school_lookup when the question is explicitly about
 * multi-school convergence ("Do all four schools agree that 7th lord in 6th house
 * indicates partnership stress?"). Prefer holistic_bundle when you want the multi-school
 * data synthesized alongside the native's actual chart signals. Prefer query_signals
 * to retrieve signals already tagged with school convergence fields.
 *
 * Input shape hints:
 *   claim — required; the astrological claim to test across schools. Phrase as a
 *     declarative statement: "Saturn in 10th house delays career until 36" or
 *     "Moon-Ketu conjunction in 4th house indicates maternal separation theme".
 *   schools — optional array; which schools to check. Defaults to all four.
 *     Valid values: "parashara", "jaimini", "kp", "tajaka".
 *
 * Output shape preview: {ok, result: {convergence_score: float, school_positions:
 *   {school: string, stance: "agree"|"disagree"|"silent", citation: string}[]},
 *   trace_id, epistemics: {surgical: true}}.
 *
 * Example: cross_school_lookup({claim: "Saturn in 10th house delays career until 36"}) →
 *   {convergence_score: 0.75, school_positions: [{school: "parashara", stance: "agree",
 *   citation: "Brihat Parashara Hora Shastra ch. 24"}, ...]}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

const SCHOOLS = ['parashara', 'jaimini', 'kp', 'tajaka'] as const

export const CROSS_SCHOOL_LOOKUP_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Checks an astrological claim against Parashara, Jaimini, KP, and Tajaka ' +
    'and returns where each school agrees, disagrees, or is silent, with a convergence score (0–1).',
  enumSource: SCHOOLS,
  coverageHint: 'All four school evidence sets fully populated (MCPT v3.3)',
  whenToPrefer:
    'Use when the question is explicitly about multi-school convergence on a rule or claim. ' +
    'Prefer multi_school_bundle when you also want per-school evidence queries and classical text references. ' +
    'Prefer query_signals to find signals already tagged with school convergence metadata.',
  tierAccess: 'super_admin + acharya. Multi-school analysis is acharya-grade.',
})

const CrossSchoolLookupInputSchema = z.object({
  claim: z.string().describe(
    'Astrological claim to verify across schools. State as a declarative sentence: ' +
    '"Saturn in 10th house delays career until 36" or ' +
    '"Moon-Ketu conjunction in 4th house indicates maternal separation theme".'
  ),
  schools: z.array(z.enum(SCHOOLS)).optional().describe(
    'Schools to check. Defaults to all four: parashara, jaimini, kp, tajaka.'
  ),
})

type CrossSchoolLookupInput = z.infer<typeof CrossSchoolLookupInputSchema>

export function registerCrossSchoolLookup(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'cross_school_lookup',
    CROSS_SCHOOL_LOOKUP_DESCRIPTION,
    CrossSchoolLookupInputSchema.shape,
    async (args: CrossSchoolLookupInput) => {
      const principal = getPrincipal()
      // Bug fix (TR-P2-S2 / C3): the platform primitive resolves the lookup topic via
      // params.topic (falling back to plan.query_text if absent). Passing only
      // { claim: ... } caused the primitive to always query using the static fallback
      // string "surgical_primitive:cross_school_lookup" instead of the user's claim.
      // Fix: forward the claim as both `topic` (the param the primitive reads) and
      // `claim` (preserved for documentation / future primitive upgrades).
      const { status, envelope } = await callPlatformPrimitive(
        'cross_school_lookup',
        {
          topic: args.claim,
          claim: args.claim,
          ...(args.schools ? { schools: args.schools } : {}),
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // Augment the platform response with the static Nadi/BNN/Yogini note.
      // These three schools are not represented in the corpus (school_convergence_index
      // covers only parashari, jaimini, kp, tajaka). Their coverage defaults to silent
      // for every signal. We surface this as a first-class field so callers are not
      // misled into thinking absent coverage means silent-but-checked.
      const baseResult = typeof envelope.result === 'object' && envelope.result !== null
        ? envelope.result as Record<string, unknown>
        : { raw: envelope.result }

      // Add school_count to each result entry: count of entries sharing the same school name.
      // Results arrive as a flat array; we compute per-school frequency and annotate each entry.
      const rawResults = Array.isArray(baseResult['results']) ? baseResult['results'] as unknown[] : []
      // Build per-school count map
      const schoolFreq: Record<string, number> = {}
      for (const entry of rawResults) {
        const e = entry as Record<string, unknown>
        const schoolName = typeof e['school'] === 'string'
          ? e['school']
          : (() => {
              try {
                const parsed = JSON.parse(e['content'] as string) as Record<string, unknown>
                return typeof parsed['school'] === 'string' ? parsed['school'] : '__unknown__'
              } catch { return '__unknown__' }
            })()
        schoolFreq[schoolName] = (schoolFreq[schoolName] ?? 0) + 1
      }
      // Annotate each entry with school_count
      const annotatedResults = rawResults.map(entry => {
        const e = entry as Record<string, unknown>
        const schoolName = typeof e['school'] === 'string'
          ? e['school']
          : (() => {
              try {
                const parsed = JSON.parse(e['content'] as string) as Record<string, unknown>
                return typeof parsed['school'] === 'string' ? parsed['school'] : '__unknown__'
              } catch { return '__unknown__' }
            })()
        return { ...e, school_count: schoolFreq[schoolName] ?? 1 }
      })

      const augmented = {
        ...envelope,
        result: {
          ...baseResult,
          results: annotatedResults,
          unrepresented_schools: ['nadi', 'bnn', 'yogini'] as const,
          unrepresented_schools_note:
            'These schools are not in the corpus; their coverage defaults to silent for all signals.',
        },
      }

      return okResult(augmented)
    }
  )
}
