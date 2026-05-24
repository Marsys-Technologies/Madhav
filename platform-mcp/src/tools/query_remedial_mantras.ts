/**
 * query_remedial_mantras.ts — MCP Tier 3 surgical primitive: remedial codex RAG filter.
 *
 * What it does: Queries rag_chunks where doc_type='l4_remedial', returning L4 remedial
 * prescriptions — planetary propitiation, gemology, mantra, yantra, devata, lifestyle
 * protocols. Filters by planet name, house, and/or free-text condition keyword.
 *
 * Source engine: platform/src/lib/retrieve/remedial_codex_query.ts
 * DB table:      rag_chunks (WHERE doc_type = 'l4_remedial')
 *
 * TR-P4-S1: new MCP wrapper.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

const QUERY_REMEDIAL_MANTRAS_DESCRIPTION =
  'Remedial codex RAG lookup. Returns L4 remedial prescriptions — planetary propitiation, ' +
  'gemology, mantra, yantra, devata, and lifestyle protocols — from the rag_chunks corpus ' +
  '(doc_type = l4_remedial). Filter by planet (e.g. "Saturn"), house (1–12), and/or ' +
  'a free-text condition query (e.g. "debilitated Mars", "Rahu in 7th"). ' +
  'At least one of planet, house, or condition should be provided for meaningful results. ' +
  'Returns up to 8 chunks by default (max 20). Each chunk carries content + chunk_id.'

const QueryRemedialMantrasInputSchema = z.object({
  planet: z.string().optional().describe(
    "Planet name to filter remedies for, e.g. 'Saturn', 'Mars', 'Rahu'."
  ),
  house: z.number().int().min(1).max(12).optional().describe(
    'House number (1–12) to include in the query, e.g. 7 → filters for "house 7" remedies.'
  ),
  condition: z.string().optional().describe(
    "Free-text condition query, e.g. 'debilitated Mars', 'Ketu affliction', 'neecha bhanga'."
  ),
  limit: z.number().int().min(1).max(20).optional().default(8).describe(
    'Max number of chunks to return (default 8, max 20).'
  ),
  tier: z.string().optional().default('super_admin'),
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

      // Build a combined keyword query from planet, house, condition.
      // The underlying remedial_codex_query engine accepts: planet, keyword, limit.
      // We pass `planet` directly and compose a `keyword` from house + condition.
      const keywordParts: string[] = []
      if (args.house !== undefined) keywordParts.push(`house ${args.house}`)
      if (args.condition) keywordParts.push(args.condition)
      const keyword = keywordParts.length > 0 ? keywordParts.join(' ') : undefined

      const params: Record<string, unknown> = {
        limit: args.limit ?? 8,
      }
      if (args.planet) params['planet'] = args.planet
      if (keyword) params['keyword'] = keyword

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
