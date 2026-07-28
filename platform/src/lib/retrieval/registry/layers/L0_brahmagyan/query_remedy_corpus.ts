/**
 * L0 retrieval: brahma_remedy_corpus query
 * Tool: marsys://tool/L0/query_remedy_corpus
 *
 * R5.3 B3 bounded-fix #1 (query_remedies 106KB, reproduced live at 105,935 bytes):
 * root cause was here, not the MCP proxy — `SELECT *` with no column projection and a
 * default limit=100 shipped up to 100 full-width corpus rows (many bulky/mostly-null
 * columns: ingredients_jsonb, timing_rules_jsonb, contraindications, etc.) as one giant
 * JSON string. Fix: (1) default limit lowered 100 -> 20 (still generous for an
 * unfiltered global browse; max stays 500 for callers that explicitly ask for more);
 * (2) SELECT * replaced with a curated default column list — heavy/mostly-null columns
 * dropped from the default projection, recoverable via fields='all' or read_remedy
 * (remedy_id) for full single-row detail; (3) `total` now reports the true
 * WHERE-matching corpus count (cheap COUNT(*) with the same predicate) distinct from
 * `returned` (the actual row count shipped), so callers know they're seeing a slice and
 * can page via offset/graha/category instead of raising limit.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const DEFAULT_LIMIT = 20
const MAX_LIMIT = 500

const COMPACT_COLUMNS = [
  'remedy_id', 'planet', 'remedy_type', 'category', 'deity',
  'prescription_text', 'mantra_text', 'source_canonical_id', 'source_citation',
  'cost_tier', 'confidence',
].join(', ')

export const queryRemedyCorpusCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_remedy_corpus',
  type: 'tool',
  layer: 'L0',
  name: 'query_remedy_corpus',
  description:
    'Query the Brahma Remedy Corpus (brahma_remedy_corpus) — 266 classical remedies with ' +
    'graha target, remedy category, classical sources, and dosage / application instructions. ' +
    'Remedy categories: mantra | gem | yantra | dana (charity) | color | fasting | ritual | tantric_heavy. ' +
    'Use to look up prescribed remedies for a specific weak/afflicted graha ' +
    '(the bo_upaya writer grounds all recommendations against this corpus). ' +
    `Default response is a compact per-row projection (limit=${DEFAULT_LIMIT}); pass ` +
    "fields='all' for full-width rows (ingredients_jsonb, timing_rules_jsonb, " +
    'contraindications, etc.) or use read_remedy(remedy_id) for single-record full detail. ' +
    '`total` is the true count of corpus rows matching the filter, independent of how many were returned.',
  input_schema: {
    planet:   { type: 'string', description: 'Filter by target graha full name (case-insensitive, e.g. "Venus", "Saturn"). `graha` accepted as an alias.' },
    graha:    { type: 'string', description: 'Alias of `planet` (graha name; case-insensitive).' },
    domain:   { type: 'string', description: 'Filter by life domain (ILIKE, e.g. career, health, marriage).' },
    category: { type: 'string', description: 'Remedy category (case-insensitive; plural forms accepted): mantra(s) | gemstone(s) | charity | puja | vrata | yantra(s) | homa | japa | behavioral | ayurvedic.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: DEFAULT_LIMIT },
    top_k:  { type: 'number', description: 'Alias of `limit`.' },
    fields: { type: 'string', description: "'compact' (default) or 'all' for full raw rows.", enum: ['compact', 'all'] },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'hybrid_retrieval',
  emits_references: false,
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Remedial tradition' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 65, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      // W4-loop-1 (E-5 group2, WORST bug): this handler only ever read `graha` and matched
      // `planet = $` exactly, while its LLM-facing callers (query_remedies / ref_remedies_get /
      // ref_remedies_search) send `planet` (full name e.g. "Venus"), `domain`, `category`, and
      // `top_k`. The result: planet=Venus was silently ignored and all 266 rows were returned
      // (JUPITER first, alphabetical) — an actively-misleading filter-lie. Now honors planet
      // (case-insensitive; graha kept as an alias), domain (ILIKE), category (case-insensitive,
      // matched against BOTH remedy_type[singular] and category, plural→singular normalized),
      // and top_k (as a limit alias). Emits empty_reason on a genuine empty match.
      const rawLimit = (args.limit as number | undefined) ?? (args.top_k as number | undefined)
      const limit  = Math.min(rawLimit ?? DEFAULT_LIMIT, MAX_LIMIT)
      const offset = (args.offset as number) ?? 0
      const includeAll = ((args.fields as string | undefined) ?? 'compact').toLowerCase() === 'all'

      const planetArg = (args.planet as string | undefined) ?? (args.graha as string | undefined)
      const categoryArg = args.category as string | undefined
      const domainArg = args.domain as string | undefined
      // remedy category vocabulary: the corpus stores singular remedy_type ('gemstone',
      // 'mantra', 'yantra', ...) — normalize common plural request forms.
      const catNorm = categoryArg
        ? categoryArg.trim().toLowerCase().replace(/s$/, '')
        : undefined

      const whereConds: string[] = ['1=1']
      const whereParams: unknown[] = []
      if (planetArg)  { whereParams.push(planetArg); whereConds.push(`LOWER(planet) = LOWER($${whereParams.length})`) }
      if (catNorm)    { whereParams.push(catNorm); whereConds.push(`(LOWER(remedy_type) = $${whereParams.length} OR LOWER(category) = $${whereParams.length})`) }
      if (domainArg)  { whereParams.push(`%${domainArg}%`); whereConds.push(`domain ILIKE $${whereParams.length}`) }
      const whereClause = whereConds.join(' AND ')

      const selectCols = includeAll ? '*' : COMPACT_COLUMNS
      const dataParams = [...whereParams, limit, offset]
      const sql = `SELECT ${selectCols} FROM brahma_remedy_corpus WHERE ${whereClause} ` +
        `ORDER BY planet, remedy_type LIMIT $${dataParams.length - 1} OFFSET $${dataParams.length}`

      const countSql = `SELECT COUNT(*)::int AS total FROM brahma_remedy_corpus WHERE ${whereClause}`

      const [result, countResult] = await Promise.all([
        query<Record<string, unknown>>(sql, dataParams),
        query<{ total: number }>(countSql, whereParams),
      ])

      const total = countResult.rows?.[0]?.total ?? result.rows?.length ?? 0
      const returned = result.rows?.length ?? 0

      const anyFilter = Boolean(planetArg || catNorm || domainArg)
      return {
        content: {
          rows: result.rows ?? [],
          returned,
          total,
          limit,
          offset,
          fields: includeAll ? 'all' : 'compact',
          truncated: offset + returned < total,
          filters_applied: { planet: planetArg ?? null, category: categoryArg ?? null, domain: domainArg ?? null },
          ...(total === 0 && anyFilter
            ? { empty_reason: `No remedies matched (planet=${planetArg ?? 'any'}, category=${categoryArg ?? 'any'}, domain=${domainArg ?? 'any'}). The corpus stores planet as lowercase full names and remedy_type as singular (mantra/gemstone/yantra/charity/puja/vrata/homa/japa/behavioral/ayurvedic).` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
