/**
 * L0 retrieval: brahma_remedy_corpus query
 * Tool: marsys://tool/L0/query_remedy_corpus
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

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
    'Returns every remedy without truncation — strength/selection happens at serve-time.',
  input_schema: {
    graha:    { type: 'string', description: 'Filter by target graha abbreviation (SU, MO, MA, ME, JU, VE, SA, RA, KE).' },
    category: { type: 'string', description: 'Remedy category: mantra | gem | yantra | dana | color | fasting | ritual | tantric_heavy.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 100 },
  },
  required_inputs: [],
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 65, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const limit  = Math.min((args.limit as number) ?? 100, 500)
      const offset = (args.offset as number) ?? 0
      const params: unknown[] = [limit, offset]
      let sql = `SELECT * FROM brahma_remedy_corpus WHERE 1=1`
      if (args.graha)    { sql += ` AND target_graha = $${params.length + 1}`; params.push(args.graha as string) }
      if (args.category) { sql += ` AND remedy_category = $${params.length + 1}`; params.push(args.category as string) }
      sql += ` ORDER BY target_graha, remedy_category LIMIT $1 OFFSET $2`
      const result = await query<Record<string, unknown>>(sql, params)
      return { content: { rows: result.rows ?? [], total: result.rows?.length ?? 0 }, is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
