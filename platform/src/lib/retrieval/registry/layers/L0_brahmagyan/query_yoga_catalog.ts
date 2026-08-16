/**
 * L0 retrieval: brahma_yoga_catalog query
 * Tool: marsys://tool/L0/query_yoga_catalog
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryYogaCatalogCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_yoga_catalog',
  type: 'tool',
  layer: 'L0',
  name: 'query_yoga_catalog',
  description:
    'Query the Brahma Yoga Catalog (brahma_yoga_catalog) — 175 canonical yogas with ' +
    'classical activation rules, tradition, domain tags, and classical sources. ' +
    'Use to look up what a yoga means, its activation predicate, and which classical text defines it. ' +
    'Supports search by yoga name, tradition (parashari/jaimini/tajik/lal_kitab/kp/nadi_bhrigu/maharsi), ' +
    'or domain (wealth/career/health/relationship/spirituality/longevity). ' +
    'Returns the weak-tail too — every yoga in the catalog regardless of activation strength.',
  input_schema: {
    yoga_name:  { type: 'string', description: 'Partial match on yoga name (case-insensitive LIKE search).' },
    tradition:  { type: 'string', description: 'Filter by tradition.' },
    domain:     { type: 'string', description: 'Filter by domain tag.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 100 },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Yogas, cross-checked' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      // W4-loop-1 (E-5 group2): tradition/domain were matched case-sensitively (school is
      // stored lowercase 'parashari'; category as raja/dhana/aristha/pancha_mahapurusha/
      // sannyasa/other) so a capitalized tradition or an advertised-but-unstored domain word
      // returned a dishonest blank. Match case-insensitively and emit an honest empty_reason
      // that discloses the real stored vocabulary.
      // F-37: build filter params separately so the count query reuses the same WHERE
      // predicates without LIMIT/OFFSET — pattern from get_condition_composite.ts:87-99.
      const limit  = Math.min((args.limit as number) ?? 100, 500)
      const offset = (args.offset as number) ?? 0
      const filterParams: unknown[] = []
      let whereClause = `WHERE 1=1`
      if (args.yoga_name) { whereClause += ` AND name_en ILIKE $${filterParams.length + 1}`; filterParams.push(`%${args.yoga_name as string}%`) }
      if (args.tradition)  { whereClause += ` AND LOWER(school) = LOWER($${filterParams.length + 1})`; filterParams.push(args.tradition as string) }
      if (args.domain)     { whereClause += ` AND LOWER(category) = LOWER($${filterParams.length + 1})`; filterParams.push(args.domain as string) }
      const np = filterParams.length
      const pageSql  = `SELECT * FROM brahma_yoga_catalog ${whereClause} ORDER BY school, name_en LIMIT $${np + 1} OFFSET $${np + 2}`
      const countSql = `SELECT COUNT(*)::text AS total FROM brahma_yoga_catalog ${whereClause}`
      const [result, countResult] = await Promise.all([
        query<Record<string, unknown>>(pageSql, [...filterParams, limit, offset]),
        query<{ total: string }>(countSql, filterParams),
      ])
      const rows = result.rows ?? []
      const total_matching = Number(countResult.rows[0]?.total ?? 0)
      const filtered = Boolean(args.yoga_name || args.tradition || args.domain)
      return {
        content: {
          rows,
          total_matching,
          more_available: total_matching > rows.length,
          ...(rows.length === 0 && filtered
            ? { empty_reason: `No yogas matched (yoga_name=${(args.yoga_name as string) ?? 'any'}, tradition=${(args.tradition as string) ?? 'any'}, domain=${(args.domain as string) ?? 'any'}). Stored tradition (school): parashari. Stored domain (category): raja, dhana, aristha, pancha_mahapurusha, sannyasa, other.` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
