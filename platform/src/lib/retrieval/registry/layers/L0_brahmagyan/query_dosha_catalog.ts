/**
 * L0 retrieval: brahma_dosha_catalog query
 * Tool: marsys://tool/L0/query_dosha_catalog
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const DEFAULT_LIMIT = 79
const MAX_LIMIT = 200

export const queryDoshaCatalogCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_dosha_catalog',
  type: 'tool',
  layer: 'L0',
  name: 'query_dosha_catalog',
  description:
    'Query the Brahma Dosha Catalog (brahma_dosha_catalog) — 79 canonical doshas with ' +
    'classical activation rules, severity tiers, cancellation conditions, and classical sources. ' +
    'Use to look up what a dosha means, how it is cancelled (neechabhanga-style conditions), ' +
    'and which text defines it. ' +
    'Covers Manglik dosha, Kala Sarpa dosha, Pitra dosha, Guru Chandala, Grahan dosha, ' +
    'Kemdruma, Daridra, and 72 more. ' +
    'An unfiltered request defaults to all 79 entries. Paginated requests disclose the true matching total and returned count.',
  input_schema: {
    dosha_name:   { type: 'string', description: 'Partial match on dosha name.' },
    severity:     { type: 'string', description: 'Filter to doshas that define a given severity grade key in severity_grades (e.g. mild | moderate | severe).' },
    domain:       { type: 'string', description: 'Filter by domain tag.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: DEFAULT_LIMIT },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 68, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      // The canonical catalog has 79 entries. Its public contract promises an
      // unfiltered browse is complete, so keep the default aligned with that
      // catalog size rather than silently serving a 50-row first page.
      const limit  = Math.min((args.limit as number) ?? DEFAULT_LIMIT, MAX_LIMIT)
      const offset = (args.offset as number) ?? 0
      const filterParams: unknown[] = []
      let whereClause = `WHERE 1=1`
      if (args.dosha_name) {
        // name_en alone (e.g. 'Manglik Dosha', 'Kuja Dosha (from Moon)') misses common
        // colloquial spellings whose substrings don't literally occur in name_en — the
        // classic trap is 'mangal', which is NOT a substring of 'Manglik' (no second 'a').
        // Broaden to name_sa + canonical_id, and expand known synonym groups so a search
        // on any member of a group matches catalog rows carrying any other member.
        const raw = (args.dosha_name as string).trim().toLowerCase()
        const synonymGroups = [['mangal', 'manglik', 'kuja']]
        const terms = new Set<string>([raw])
        for (const group of synonymGroups) {
          if (group.some((t) => raw.includes(t) || t.includes(raw))) {
            for (const t of group) terms.add(t)
          }
        }
        const clauses: string[] = []
        for (const term of terms) {
          const idx = filterParams.length + 1
          clauses.push(`(name_en ILIKE $${idx} OR name_sa ILIKE $${idx} OR canonical_id ILIKE $${idx})`)
          filterParams.push(`%${term}%`)
        }
        whereClause += ` AND (${clauses.join(' OR ')})`
      }
      if (args.severity) { whereClause += ` AND severity_grades ? $${filterParams.length + 1}`; filterParams.push(args.severity as string) }
      if (args.domain)   { whereClause += ` AND category = $${filterParams.length + 1}`; filterParams.push(args.domain as string) }
      const pageSql = `SELECT * FROM brahma_dosha_catalog ${whereClause} ` +
        `ORDER BY category, name_en LIMIT $${filterParams.length + 1} OFFSET $${filterParams.length + 2}`
      const countSql = `SELECT COUNT(*)::text AS total FROM brahma_dosha_catalog ${whereClause}`
      const [result, countResult] = await Promise.all([
        query<Record<string, unknown>>(pageSql, [...filterParams, limit, offset]),
        query<{ total: string }>(countSql, filterParams),
      ])
      const rows = result.rows ?? []
      const total = Number(countResult.rows?.[0]?.total ?? rows.length)
      const returned = rows.length
      return {
        content: {
          rows,
          returned,
          total,
          limit,
          offset,
          truncated: offset + returned < total,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
