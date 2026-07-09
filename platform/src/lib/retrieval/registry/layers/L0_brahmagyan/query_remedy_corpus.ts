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
    graha:    { type: 'string', description: 'Filter by target graha abbreviation (SU, MO, MA, ME, JU, VE, SA, RA, KE).' },
    category: { type: 'string', description: 'Remedy category: mantra | gem | yantra | dana | color | fasting | ritual | tantric_heavy.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: DEFAULT_LIMIT },
    fields: { type: 'string', description: "'compact' (default) or 'all' for full raw rows.", enum: ['compact', 'all'] },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'hybrid_retrieval',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 65, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const limit  = Math.min((args.limit as number) ?? DEFAULT_LIMIT, MAX_LIMIT)
      const offset = (args.offset as number) ?? 0
      const includeAll = ((args.fields as string | undefined) ?? 'compact').toLowerCase() === 'all'

      const whereConds: string[] = ['1=1']
      const whereParams: unknown[] = []
      if (args.graha)    { whereParams.push(args.graha as string); whereConds.push(`planet = $${whereParams.length}`) }
      if (args.category) { whereParams.push(args.category as string); whereConds.push(`remedy_type = $${whereParams.length}`) }
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

      return {
        content: {
          rows: result.rows ?? [],
          returned,
          total,
          limit,
          offset,
          fields: includeAll ? 'all' : 'compact',
          truncated: offset + returned < total,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
