/**
 * query_domain_result — Domain Result Map (L4 Phala)
 * ====================================================
 * Queries phala_phaladesa (ph_phaladesa) — 7 rows per chart (one per domain).
 * Returns B.11-compliant domain result declaration rows.
 *
 * Note: 7 rows total — by design (one row per domain). This is SPARSE but complete.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryDomainResultCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_domain_result',
  type:  'tool',
  layer: 'L4',
  name:  'query_domain_result',

  description: [
    'Returns the L4 domain result map for a chart from phala_phaladesa (ph_phaladesa).',
    'Source: phala_phaladesa (7 rows — one per life domain, by design).',
    'Each row is a B.11-compliant domain result declaration covering:',
    'anchor inventory count, spillover coverage, mitigation coverage, muhurta coverage.',
    'Returns all 7 domains by default; filter by domain for a specific one.',
    'NOTE: 7 total rows is by design — one row per domain per chart. Expected sparse count.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'LAHIRI').",
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other). Omit for all 7.',
      enum: ['career', 'wealth', 'relationship', 'health', 'character', 'spirituality', 'other'],
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 6 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const domain       = args['domain'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (domain) { conds.push(`domain = $${p++}`); params.push(domain) }

      const sql = `
        SELECT phaladesa_id, domain, anchor_count,
               spillover_coverage_pct, mitigation_coverage_pct,
               muhurta_coverage_pct, anchor_id_refs,
               result_summary, confidence_band,
               b11_compliance_flag, ayanamsha_id
        FROM phala_phaladesa
        WHERE ${conds.join(' AND ')}
        ORDER BY domain
      `

      const result = await db.query(sql, params)
      const anchorRefs = new Set<string>()
      for (const row of result.rows as Array<{ anchor_id_refs?: string[] }>) {
        if (row.anchor_id_refs) {
          for (const id of row.anchor_id_refs) anchorRefs.add(id)
        }
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          domain_results:  result.rows,
          domain_count:    result.rows.length,
          anchor_id_refs:  Array.from(anchorRefs),
          design_note:     '7 rows is by design — one per domain. Sparse count is expected.',
          filters: { domain },
          provenance: { tables: ['phala_phaladesa'] },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id },
        is_error: true,
      }
    }
  },
}
