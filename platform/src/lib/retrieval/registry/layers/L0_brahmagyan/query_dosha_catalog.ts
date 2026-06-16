/**
 * L0 retrieval: brahma_dosha_catalog query
 * Tool: marsys://tool/L0/query_dosha_catalog
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryDoshaCatalogCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_dosha_catalog',
  type: 'tool',
  layer: 'L0',
  name: 'query_dosha_catalog',
  description:
    'Query the Brahma Dosha Catalog (brahma_dosha_catalog) — 50 canonical doshas with ' +
    'classical activation rules, severity tiers, cancellation conditions, and classical sources. ' +
    'Use to look up what a dosha means, how it is cancelled (neechabhanga-style conditions), ' +
    'and which text defines it. ' +
    'Covers Manglik dosha, Kala Sarpa dosha, Pitra dosha, Guru Chandala, Grahan dosha, ' +
    'Kemdruma, Daridra, and 43 more. ' +
    'Returns all 50 entries with no truncation.',
  input_schema: {
    dosha_name:   { type: 'string', description: 'Partial match on dosha name.' },
    severity:     { type: 'string', description: 'Filter by severity tier: high | medium | low.' },
    domain:       { type: 'string', description: 'Filter by domain tag.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 50 },
  },
  required_inputs: [],
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 68, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const limit  = Math.min((args.limit as number) ?? 50, 200)
      const offset = (args.offset as number) ?? 0
      const params: unknown[] = [limit, offset]
      let sql = `SELECT * FROM brahma_dosha_catalog WHERE 1=1`
      if (args.dosha_name) { sql += ` AND dosha_name ILIKE $${params.length + 1}`; params.push(`%${args.dosha_name as string}%`) }
      if (args.severity)   { sql += ` AND severity_tier = $${params.length + 1}`; params.push(args.severity as string) }
      if (args.domain)     { sql += ` AND $${params.length + 1} = ANY(domain_tags)`; params.push(args.domain as string) }
      sql += ` ORDER BY severity_tier, dosha_name LIMIT $1 OFFSET $2`
      const result = await query<Record<string, unknown>>(sql, params)
      return { content: { rows: result.rows ?? [], total: result.rows?.length ?? 0 }, is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
