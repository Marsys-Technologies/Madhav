/**
 * query_remedies_prescribed.ts — MCP Tier 3 surgical primitive: remedial prescription lookup.
 *
 * What it does: Cross-references natal chart conditions with the remedial codex.
 * Builds a composite search query from affliction/planet/house/condition params,
 * calls the remedial_codex_query engine (via query_remedial_mantras primitive),
 * optionally enriches with chart_facts remedy/strength rows for the planet,
 * detects remedy_type from content keywords, filters by type, and returns
 * up to 10 structured remedy results.
 *
 * Algorithm:
 *   1. Build search query: `${affliction} ${planet} house ${house} ${condition} remedy mantra gem`.trim()
 *   2. Call remedial_codex_query via callPlatformPrimitive (planet + keyword + limit).
 *   3. If planet is provided, call query_chart_facts for remedy/strength rows.
 *   4. Merge results; detect remedy_type from content keywords.
 *   5. Filter by remedy_type if not "all". Return top 10.
 *
 * Keyword → remedy_type detection:
 *   "mantra" → mantra
 *   "gem" | "gemstone" | "ratna" → gem
 *   "ritual" | "puja" | "homa" → ritual
 *   "donate" | "charity" | "daan" → charity
 *   (no match) → mantra (default)
 *
 * TR-P8-S2: new MCP tool (final session, v1.0 close).
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

// ── Description ───────────────────────────────────────────────────────────────

const QUERY_REMEDIES_PRESCRIBED_DESCRIPTION =
  'Cross-references natal chart conditions with the MARSYS remedial codex. ' +
  'Accepts affliction description, planet name, house number, free-text condition, ' +
  'and remedy_type filter ("mantra", "gem", "ritual", "charity", "all"). ' +
  'Retrieves L4 remedial prescriptions from the rag_chunks corpus and optionally ' +
  'chart_facts remedy/strength rows for the planet. Detects remedy_type from ' +
  'content keywords (mantra/gem/gemstone/ratna/ritual/puja/homa/donate/charity/daan). ' +
  'Returns up to 10 structured results with condition, remedy_type, remedy_text, ' +
  'timing, classical_source, and relevance_score. ' +
  'Use when the native needs planetary propitiation or remedial protocol recommendations.'

// ── Schema ────────────────────────────────────────────────────────────────────

const QueryRemediesPrescribedInputSchema = z.object({
  affliction: z.string().optional().describe(
    'Description of the affliction or astrological condition requiring remedy, ' +
    'e.g. "Saturn afflicts 1H", "debilitated Mars", "Rahu-Ketu axis on 7H".'
  ),
  planet: z.string().optional().describe(
    'Planet name for which to retrieve remedies, e.g. "Saturn", "Rahu", "Mars".'
  ),
  house: z.number().int().min(1).max(12).optional().describe(
    'Afflicted or relevant house number (1–12).'
  ),
  condition: z.string().optional().describe(
    'Free-text condition query for RAG search, ' +
    'e.g. "Ketu affliction", "neecha bhanga raja yoga", "Saturn transit 7th house".'
  ),
  remedy_type: z.enum(['mantra', 'gem', 'ritual', 'charity', 'all']).default('all').describe(
    'Filter results by remedy type. "all" returns all types. Default: "all".'
  ),
  tier: z.string().optional().describe(
    'Audience tier override. Defaults to the caller\'s authenticated tier.'
  ),
})

type QueryRemediesPrescribedInput = z.infer<typeof QueryRemediesPrescribedInputSchema>

// ── Types ─────────────────────────────────────────────────────────────────────

type RemedyType = 'mantra' | 'gem' | 'ritual' | 'charity' | 'unknown'

interface RemedyResult {
  condition: string
  remedy_type: RemedyType
  remedy_text: string
  timing: string | null
  classical_source: string | null
  relevance_score: number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Detect remedy type from content string using keyword matching.
 * Priority order: mantra, gem/ratna, ritual/puja/homa, charity/daan.
 */
function detectRemedyType(content: string): RemedyType {
  const lower = content.toLowerCase()
  if (lower.includes('mantra') || lower.includes('japa') || lower.includes('stotra')) {
    return 'mantra'
  }
  if (lower.includes('gem') || lower.includes('gemstone') || lower.includes('ratna')) {
    return 'gem'
  }
  if (lower.includes('ritual') || lower.includes('puja') || lower.includes('homa') ||
      lower.includes('yagna') || lower.includes('yajna')) {
    return 'ritual'
  }
  if (lower.includes('donate') || lower.includes('charity') || lower.includes('daan') ||
      lower.includes('dana')) {
    return 'charity'
  }
  // Default: unknown (not classified) — will be included in "all" filter
  return 'unknown'
}

/**
 * Extract a string field from a row object, trying multiple field name aliases.
 */
function extractStr(row: Record<string, unknown>, ...fields: string[]): string | null {
  for (const f of fields) {
    const v = row[f]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return null
}

/**
 * Unwrap the envelope's result data, supporting both ToolBundle and direct shapes.
 */
function unwrapResult(envelope: Record<string, unknown>): unknown {
  const result = envelope['result']
  if (!result || typeof result !== 'object') return null
  const r = result as Record<string, unknown>

  // ToolBundle pattern: result.results[0].content (JSON string)
  const bundleResults = r['results'] as Array<{ content: unknown }> | undefined
  if (Array.isArray(bundleResults) && bundleResults.length > 0) {
    const raw = bundleResults[0]!.content
    if (typeof raw === 'string') {
      try { return JSON.parse(raw) } catch { /* fall through */ }
    }
    if (raw !== null && raw !== undefined) return raw
  }

  return r
}

/**
 * Extract remedy chunks from a remedial_codex_query response.
 * Supports both `chunks` array and `rows` array shapes.
 */
function extractRemedyChunks(data: unknown): unknown[] {
  if (!data || typeof data !== 'object') return []
  const d = data as Record<string, unknown>
  if (Array.isArray(d['chunks'])) return d['chunks']
  if (Array.isArray(d['rows'])) return d['rows']
  if (Array.isArray(d['results'])) return d['results']
  return []
}

/**
 * Extract chart_facts remedy/strength rows from a query_chart_facts response.
 */
function extractChartFactsRemedyRows(data: unknown): unknown[] {
  if (!data || typeof data !== 'object') return []
  const d = data as Record<string, unknown>

  // rows_by_category shape
  const rbc = d['rows_by_category'] as Record<string, unknown[]> | undefined
  if (rbc) {
    const rows: unknown[] = []
    for (const cat of ['remedy', 'strength', 'weakness']) {
      if (Array.isArray(rbc[cat])) rows.push(...rbc[cat])
    }
    return rows
  }

  if (Array.isArray(d['rows'])) return d['rows']
  return []
}

/**
 * Convert a raw chunk/row into a RemedyResult.
 * chunk_id, content, classical_source extracted; timing from metadata or timing field.
 */
function rowToRemedyResult(
  row: Record<string, unknown>,
  idx: number,
  totalCount: number,
): RemedyResult {
  const content = extractStr(row, 'content', 'text', 'value_text', 'description') ?? ''
  const remedyType = detectRemedyType(content)

  // Condition label from row fields or a constructed description
  const conditionLabel =
    extractStr(row, 'condition', 'affliction', 'planet', 'category_detail', 'yoga_name') ??
    extractStr(row, 'category', 'doc_type') ??
    'remedial prescription'

  // Timing from row fields
  const timing =
    extractStr(row, 'timing', 'time', 'muhurta', 'when') ?? null

  // Classical source citation
  const classicalSource =
    extractStr(row, 'classical_source', 'source', 'chunk_id', 'text_id', 'text_key') ?? null

  // Relevance score: use similarity if present, otherwise compute positional decay
  let relevanceScore: number
  const simVal = row['similarity'] ?? row['score'] ?? row['relevance_score']
  if (typeof simVal === 'number' && simVal >= 0 && simVal <= 1) {
    relevanceScore = Math.round(simVal * 100) / 100
  } else {
    // Positional decay: first result = 0.95, decays by 0.05 per rank, floor 0.50
    relevanceScore = Math.max(0.5, 0.95 - idx * (0.45 / Math.max(totalCount - 1, 1)))
    relevanceScore = Math.round(relevanceScore * 100) / 100
  }

  return {
    condition: conditionLabel,
    remedy_type: remedyType,
    remedy_text: content || 'No remedy text available',
    timing,
    classical_source: classicalSource,
    relevance_score: relevanceScore,
  }
}

// ── MCP tool registration ─────────────────────────────────────────────────────

export function registerQueryRemediesPrescribed(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_remedies_prescribed',
    QUERY_REMEDIES_PRESCRIBED_DESCRIPTION,
    QueryRemediesPrescribedInputSchema.shape,
    async (args: QueryRemediesPrescribedInput) => {
      const principal = getPrincipal()

      // ── Step 1: Build composite search query ─────────────────────────────────
      const queryParts: string[] = []
      if (args.affliction) queryParts.push(args.affliction)
      if (args.planet) queryParts.push(args.planet)
      if (args.house !== undefined) queryParts.push(`house ${args.house}`)
      if (args.condition) queryParts.push(args.condition)
      queryParts.push('remedy mantra gem')
      const afflictionQuery = queryParts.join(' ').trim()

      // ── Step 2: Call remedial_codex_query via platform primitive ─────────────
      const remedialParams: Record<string, unknown> = {
        limit: 12, // fetch more than 10 so we can filter then truncate
      }
      if (args.planet) remedialParams['planet'] = args.planet
      if (args.house !== undefined || args.affliction || args.condition) {
        const keywordParts: string[] = []
        if (args.house !== undefined) keywordParts.push(`house ${args.house}`)
        if (args.affliction) keywordParts.push(args.affliction)
        if (args.condition) keywordParts.push(args.condition)
        if (keywordParts.length > 0) {
          remedialParams['keyword'] = keywordParts.join(' ')
        }
      }

      const remedialCall = await callPlatformPrimitive(
        'remedial_codex_query',
        remedialParams,
        principal,
      )

      // Hard error from remedial codex — propagate up
      if (!remedialCall.envelope.ok && remedialCall.status >= 400) {
        return errorResult(remedialCall.envelope as unknown as Record<string, unknown>)
      }

      // ── Step 3: Optionally fetch chart_facts remedy/strength rows for planet ──
      let chartFactsRows: unknown[] = []
      if (args.planet) {
        try {
          const cfCall = await callPlatformPrimitive(
            'query_chart_facts',
            {
              categories: ['remedy', 'strength'],
              planet: args.planet,
              limit: 5,
            },
            principal,
          )
          if (cfCall && cfCall.envelope && cfCall.envelope.ok && cfCall.status < 400) {
            const cfData = unwrapResult(cfCall.envelope as unknown as Record<string, unknown>)
            chartFactsRows = extractChartFactsRemedyRows(cfData)
          }
        } catch {
          // chart_facts enrichment is optional — swallow errors; remedial results still returned
        }
      }

      // ── Step 4: Merge and convert raw results ─────────────────────────────────
      const remedialData = unwrapResult(remedialCall.envelope as unknown as Record<string, unknown>)
      const remedialChunks = extractRemedyChunks(remedialData)

      const allRawRows = [...remedialChunks, ...chartFactsRows]

      // ── Step 5: Convert to RemedyResult structs and detect remedy_type ────────
      const allResults: RemedyResult[] = allRawRows
        .filter(r => r && typeof r === 'object')
        .map((r, idx) =>
          rowToRemedyResult(r as Record<string, unknown>, idx, allRawRows.length),
        )

      // ── Step 6: Filter by remedy_type if not "all" ────────────────────────────
      // Note: remedy_type defaults to "all" via Zod schema; guard against undefined
      // in case handler is invoked outside Zod parsing (tests, direct calls).
      const remedyTypeFilter = args.remedy_type ?? 'all'
      const filtered =
        remedyTypeFilter === 'all'
          ? allResults
          : allResults.filter(r => r.remedy_type === remedyTypeFilter)

      // ── Step 7: Return top 10 ─────────────────────────────────────────────────
      const top10 = filtered.slice(0, 10)

      return okResult({
        ok: true,
        affliction_query: afflictionQuery,
        results: top10,
        result_count: top10.length,
        epistemics: { surgical: true },
      })
    },
  )
}
