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
import { query } from '@/lib/db/client'

export const queryDomainResultCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_domain_result',
  type:  'tool',
  layer: 'L4',
  name:  'query_domain_result',

  description: [
    'Returns the L4 domain result map for a chart from phala_phaladesa (ph_phaladesa).',
    'Source: phala_phaladesa (7 rows — one per life domain, by design).',
    'Each row is a B.11-compliant domain result declaration covering:',
    'anchor inventory count, clean/staged/anomaly counts, incoming spillover,',
    'mitigation availability, and muhurta availability.',
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

    const domain = args['domain'] as string | undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (domain) { conds.push(`domain = $${p++}`); params.push(domain) }

      const sql = `
        SELECT phaladesa_id, domain, anchor_count, clean_anchor_count,
               staged_revision_count, anomaly_flag_count, top_anchor_id,
               to_char(prediction_window_start, 'YYYY-MM-DD') AS prediction_window_start,
               to_char(prediction_window_end, 'YYYY-MM-DD')   AS prediction_window_end,
               to_char(peak_date, 'YYYY-MM-DD')               AS peak_date,
               magnitude, confidence_low, confidence_high, malleability,
               incoming_spillover_count, mitigation_available, muhurta_available,
               pramana_window_status, evidence_type, narration_status,
               source_citation
        FROM phala_phaladesa
        WHERE ${conds.join(' AND ')}
        ORDER BY domain
      `

      const result = await query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ top_anchor_id?: string }>)
          .map(r => r.top_anchor_id)
          .filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id,
          domain_results:  result.rows,
          domain_count:    result.rows.length,
          anchor_id_refs:  anchorRefs,
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
