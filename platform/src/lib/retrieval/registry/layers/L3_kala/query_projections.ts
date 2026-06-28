/**
 * query_projections — Forward Projections (L3 Kāla)
 * ===================================================
 * Queries kala_bhavishya (ka_bhavishya_lekha) — 50 rows per chart.
 * Returns probabilistic forward projections with domain labels,
 * peak_date / window bounds, falsifiability hooks, and source chains.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import { query } from '@/lib/db/client'
import type { CapabilityDescriptor } from '../../types'

export const queryProjectionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_projections',
  type:  'tool',
  layer: 'L3',
  name:  'query_projections',

  description: [
    'Returns probabilistic forward projections for a chart from kala_bhavishya.',
    'Source: kala_bhavishya (50 rows — spanning multiple years and domains).',
    'Each projection carries: domain, probability_tier, peak_date, window_start/window_end,',
    'falsifiability hook, source_chain, effective_score, and narrative.',
    'Filter by probability_tier: tier_1_high (≥0.65), tier_2_moderate (0.40–0.65),',
    'tier_3_speculative (<0.40).',
    'emits_references: returns signal_id references linkable to bo_laksana / ph_pramana (L4).',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
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
    horizon_years: {
      type: 'number',
      description: 'Filter projections whose peak_date falls within this many years from today (default: 3).',
    },
    probability_tier: {
      type: 'string',
      description: 'Filter by probability tier.',
      enum: ['tier_1_high', 'tier_2_moderate', 'tier_3_speculative'],
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 18,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const horizon_years   = Number(args['horizon_years'] ?? 3)
    const probability_tier = args['probability_tier'] as string | undefined
    const domain          = args['domain'] as string | undefined

    const horizon_date = new Date()
    horizon_date.setFullYear(horizon_date.getFullYear() + horizon_years)

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      // The projection's temporal anchor is peak_date (kala_bhavishya has no
      // projection_date / horizon_years columns).
      if (horizon_years > 0) {
        conds.push(`peak_date <= $${p++}`)
        params.push(horizon_date.toISOString().split('T')[0])
      }
      if (probability_tier) { conds.push(`probability_tier = $${p++}`); params.push(probability_tier) }
      if (domain)           { conds.push(`domain = $${p++}`);           params.push(domain) }

      const sql = `
        SELECT id, projection_rank, domain, probability_tier, effective_score,
               peak_date, window_start, window_end, narrative,
               falsifiability, convergence_id, signal_id, source_chain,
               outcome_recorded, outcome_notes, source_citation, computed_at
        FROM kala_bhavishya
        WHERE ${conds.join(' AND ')}
        ORDER BY probability_tier, projection_rank
      `

      const result = await query(sql, params)

      // signal_id is a scalar per row (not an array); collect distinct refs.
      const signalRefs = new Set<string>()
      for (const row of result.rows as Array<{ signal_id?: string }>) {
        if (row.signal_id) signalRefs.add(row.signal_id)
      }

      return {
        content: {
          chart_id,
          projections:      result.rows,
          projection_count: result.rows.length,
          signal_id_refs:   Array.from(signalRefs),
          filters: { horizon_years, probability_tier, domain },
          provenance: { tables: ['kala_bhavishya'] },
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
