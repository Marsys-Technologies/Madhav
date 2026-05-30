/**
 * query_remedial_mantras.ts — MCP Tier 3 surgical primitive: remedial codex lookup.
 *
 * What it does: Returns remedial measures (mantras, gemstones, yantras, devata
 * worship, dinacharya, propitiation rites) from the MARSYS remedial codex,
 * filtered by planet, practice type, or keyword. The codex is stored in the
 * remedial_codex table and pre-indexed from classical sources (BPHS, Phala
 * Deepika, Jataka Parijata).
 *
 * Source: platform/src/lib/retrieve/remedial_codex_query.ts
 * Data: remedial_codex table, migrations/026_remedial_codex.sql
 * Engine: platform/scripts/data/load_remedial_codex.py
 *
 * Practice types:
 *   gemstone   — Ratna (gemstone prescriptions, finger, metal, weight)
 *   mantra     — Vedic and Tantric mantra prescriptions with japa count
 *   yantra     — Geometric yantra forms and installation rites
 *   devata     — Deity worship (devata, day, flower, naivedya)
 *   dinacharya — Daily routine and lifestyle adjustments
 *   propit     — Propitiation rites (daan, havan, charity)
 *
 * When to prefer: Use for "What gemstone should I wear for Saturn?",
 * "What mantra remedies are prescribed for Rahu?", or any remedial/
 * prescription lookup. Prefer holistic_bundle for remedies synthesized
 * against the chart's specific afflictions and dasha context.
 *
 * Output shape preview: {ok, result: {remedies: {planet, practice_type,
 *   prescription, source_ref, classical_authority}[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: query_remedial_mantras({planet: "Saturn", practice_type: "mantra"}) →
 *   {ok: true, result: {remedies: [{planet: "Saturn", practice_type: "mantra",
 *   prescription: "Om Sham Shanicharaya Namah (108x, Saturday)", source_ref: "..."}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

const PRACTICE_TYPES = [
  'gemstone', 'mantra', 'yantra', 'devata', 'dinacharya', 'propit',
] as const

const PLANETS = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu',
] as const

export const QUERY_REMEDIAL_MANTRAS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns remedial measures from the MARSYS remedial codex — mantras, gemstones, ' +
    'yantras, devata worship, dinacharya, and propitiation rites — indexed from classical sources ' +
    '(BPHS, Phala Deepika, Jataka Parijata). Filter by planet, practice type, or keyword.',
  enumSource: [...PLANETS, ...PRACTICE_TYPES] as readonly string[],
  coverageHint: 'remedial_codex table; classical remedial prescriptions from BPHS + secondary texts',
  whenToPrefer:
    'Use for "What gemstone for Saturn?", "Rahu mantra prescriptions", or any remedial codex lookup. ' +
    'Prefer holistic_bundle for remedies synthesized against the chart\'s specific afflictions and dasha.',
})

const QueryRemedialMantrasInputSchema = z.object({
  planet: z.enum(PLANETS).optional().describe(
    'Filter by graha. One of: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.'
  ),
  practice_type: z.enum(PRACTICE_TYPES).optional().describe(
    'Filter by practice type. One of: gemstone (ratna), mantra (japa), yantra, devata (worship), ' +
    'dinacharya (daily routine), propit (propitiation/daan/havan).'
  ),
  house: z.number().int().min(1).max(12).optional().describe(
    'Filter remedies related to a specific house (1–12). Composes into keyword search.'
  ),
  condition: z.string().optional().describe(
    'Astrological condition to search for (e.g., "debilitated Mars", "Rahu affliction"). ' +
    'Composes with house into keyword search.'
  ),
  limit: z.number().int().min(1).max(50).optional().describe(
    'Maximum number of remedial entries to return. Default: 8. Max: 50.'
  ),
})

type QueryRemedialMantrasInput = z.infer<typeof QueryRemedialMantrasInputSchema>

export function registerQueryRemedialMantras(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_remedial_mantras',
    QUERY_REMEDIAL_MANTRAS_DESCRIPTION,
    QueryRemedialMantrasInputSchema.shape,
    async (args: QueryRemedialMantrasInput) => {
      const principal = getPrincipal()

      // Compose keyword from house and/or condition
      const keywordParts: string[] = []
      if (args.house !== undefined) keywordParts.push(`house ${args.house}`)
      if (args.condition) keywordParts.push(args.condition)
      const keyword = keywordParts.length > 0 ? keywordParts.join(' ') : undefined

      const params: Record<string, unknown> = {
        limit: args.limit ?? 8,
      }
      if (args.planet !== undefined) params['planet'] = args.planet
      if (args.practice_type !== undefined) params['practice_type'] = args.practice_type
      if (keyword !== undefined) params['keyword'] = keyword

      const { status, envelope } = await callPlatformPrimitive(
        'remedial_codex_query',
        params,
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }
      return okResult(envelope)
    }
  )
}
