/**
 * concept_locate — resolve free-text concept names to a serving category/tool (C3/Task 1)
 * ================================================================================
 * Elevation Campaign v2.1, STREAM α Lane-H, Task 1. Resolves a caller's free-text term
 * ("Gulika", "sphuta", "mangal shadbala") to its true serving `fact_category`(ies) and the
 * MCP tool that serves them, using the seeded `concept_aliases.ts` table.
 *
 * ABSENCE PROTOCOL (Task 2 / EL-07): this capability's `resolved: false` path IS the
 * concept-resolver MISS the Absence Protocol requires before any served string may claim
 * ontological absence ("not in your data" / "doesn't exist"). Any tool that wants to make
 * such a claim should call this capability (or its MCP-facing `concept_locate` tool) first
 * and cite the miss — see `empty_reason` below, which names exactly what was checked
 * (N seed aliases + M live fact_category values) rather than asserting absence unconditionally.
 *
 * SATYA-ŚEṢA W1 (SATYA_SHESHA_BRIEF_v1_0.md §2): the same two-pass resolution logic (seed
 * alias table, then live fact_category substring fallback) is now ALSO available as a shared,
 * chart-scoped function in `resolve_concept.ts` (`resolveConceptWithLiveFallback`), so
 * `chart_facts_query` and sibling query-shaped tools can build the SAME honest
 * `resolver_suggestion` on a bare empty. This handler's own response shape is left exactly as
 * it was (byte-for-byte) to avoid any regression on an already-verified-live tool — it is not
 * refactored to delegate, deliberately, to keep this change zero-risk to concept_locate's
 * existing callers/tests.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { resolveConceptAlias, CONCEPT_ALIASES } from './concept_aliases'

const DEFAULT_SCHEMA_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** Live fact_category list, for the fallback direct-match pass and for an honest miss count.
 *  Cheap (chart_facts has ~600 category/subject groups but far fewer distinct categories —
 *  DISTINCT alone, no grouping needed here) and short-cacheable at the route layer via
 *  llm_hints.agentic.cacheable, same as get_database_schema. */
async function liveFactCategories(chartId: string): Promise<string[]> {
  const result = await query<{ fact_category: string }>(
    `SELECT DISTINCT fact_category FROM chart_facts WHERE chart_id = $1 ORDER BY fact_category`,
    [chartId],
  )
  return result.rows.map(r => r.fact_category)
}

export const conceptLocateCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/concept_locate',
  type: 'tool',
  layer: 'L1',
  name: 'concept_locate',
  description: [
    'Resolve a free-text concept name (English or Sanskrit, e.g. "Gulika", "sphuta",',
    '"panchanga", "mangal shadbala") to the real fact_category value(s) it serves through and',
    'the MCP tool that serves them (query_chart_facts / chart_facts_query, or a dedicated face',
    'like get_dignity/get_strength when the category maps to one). Tries the seeded alias table',
    'first, then falls back to a direct substring match against the live fact_category list.',
    'Returns an HONEST MISS (resolved:false, empty_reason naming exactly what was checked) when',
    'nothing matches — never a silent empty result. Use this before phrasing any answer as',
    '"not in the data" / "doesn\'t exist" (Absence Protocol, EL-07).',
  ].join(' '),
  input_schema: {
    query: { type: 'string', description: 'Free-text concept name to resolve.', required: true },
    chart_id: { type: 'string', description: 'Chart UUID for the live-category fallback pass. Defaults to the canonical chart.' },
  },
  required_inputs: ['query'],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-ORIENT',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 35, always_include: false },
  },
  density_contract: {
    paginated: false,
    facets: ['query', 'chart_id'],
    empty_reason: true,
  },
  async handler(args, _ctx) {
    try {
      const q = (args.query as string | undefined) ?? ''
      if (!q.trim()) {
        return { content: { error: 'query is required' }, is_error: true }
      }
      const chartId = (args.chart_id as string | undefined) ?? DEFAULT_SCHEMA_CHART_ID

      // Pass 1 — seeded alias table (cheap, in-memory, no DB round trip).
      const aliasResult = resolveConceptAlias(q)
      if (aliasResult.resolved) {
        return {
          content: {
            resolved: true,
            query: q,
            matched_alias: aliasResult.matched_alias,
            concept_id: aliasResult.concept_id,
            fact_categories: aliasResult.fact_categories,
            resolved_via: aliasResult.resolved_via,
            serving_tool: 'query_chart_facts (chart_facts_query) with categories:<fact_categories above>, or the dedicated face named in fact_categories if one exists (e.g. get_dignity, get_strength, get_avasthas).',
          },
          is_error: false,
        }
      }

      // Pass 2 — direct substring match against the LIVE fact_category list (catches real
      // category names the seed alias table hasn't been extended to cover yet).
      const liveCategories = await liveFactCategories(chartId)
      const qLower = q.trim().toLowerCase()
      const directMatches = liveCategories.filter(c => c.toLowerCase().includes(qLower) || qLower.includes(c.toLowerCase()))
      if (directMatches.length > 0) {
        return {
          content: {
            resolved: true,
            query: q,
            matched_alias: null,
            concept_id: directMatches[0],
            fact_categories: directMatches,
            resolved_via: 'direct_category_match',
            serving_tool: 'query_chart_facts (chart_facts_query) with categories:<fact_categories above>.',
          },
          is_error: false,
        }
      }

      // Genuine MISS — the resolver actually ran both passes and found nothing. This is the
      // signal the Absence Protocol (Task 2/EL-07) requires before any caller may phrase a
      // response as ontological absence, and the shape names exactly what was checked.
      return {
        content: {
          resolved: false,
          query: q,
          matched_alias: null,
          concept_id: null,
          fact_categories: [],
          resolved_via: 'miss',
          empty_reason: `No concept alias or live fact_category matched "${q}" — checked ${CONCEPT_ALIASES.length} seed alias entries and ${liveCategories.length} live fact_category values for chart_id ${chartId}. This is a resolver MISS, not a claim that "${q}" categorically does not exist anywhere in Jyotish — only that it is not reachable under this name in the live schema today. Try get_database_schema to browse the full category/subject substrate, or rephrase with a more specific term.`,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
