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
      const limit  = Math.min((args.limit as number) ?? 100, 500)
      const offset = (args.offset as number) ?? 0
      const params: unknown[] = [limit, offset]
      let sql = `SELECT * FROM brahma_yoga_catalog WHERE 1=1`
      if (args.yoga_name) { sql += ` AND name_en ILIKE $${params.length + 1}`; params.push(`%${args.yoga_name as string}%`) }
      if (args.tradition)  { sql += ` AND LOWER(school) = LOWER($${params.length + 1})`; params.push(args.tradition as string) }
      if (args.domain)     { sql += ` AND LOWER(category) = LOWER($${params.length + 1})`; params.push(args.domain as string) }
      sql += ` ORDER BY school, name_en LIMIT $1 OFFSET $2`
      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []
      const filtered = Boolean(args.yoga_name || args.tradition || args.domain)
      return {
        content: {
          rows,
          total: rows.length,
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
