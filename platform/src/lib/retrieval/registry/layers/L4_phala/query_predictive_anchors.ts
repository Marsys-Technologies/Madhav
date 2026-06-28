/**
 * query_predictive_anchors — Predictive Anchors (L4 Phala)
 * ==========================================================
 * Queries phala_anchors (ph_nimitta) — 150 rows per chart.
 * Returns predictive anchors with 8 derivation axes + 5 elevation fields.
 *
 * Umbrella for the L4 layer — drill further to query_domain_result,
 * query_falsifiers, query_anomaly_flags, query_cleansed_anchors.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPredictiveAnchorsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_predictive_anchors',
  type:  'tool',
  layer: 'L4',
  name:  'query_predictive_anchors',

  description: [
    'Returns predictive anchors for a chart from phala_anchors (ph_nimitta).',
    'Source: phala_anchors (150 rows — the core L4 prediction foundation).',
    'Each anchor carries a magnitude, confidence band, karmic frame, malleability,',
    'and a derivation ledger over its constituent L1/L2/L3 facts.',
    'Filter by domain, event_type, direction, and horizon_tier to focus.',
    'emits_references: signal_id refs back to bodha_msr_signals via anchor provenance.',
    'Drill further: query_domain_result (7-domain result map), query_falsifiers,',
    'query_anomaly_flags, query_cleansed_anchors.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L4/query_domain_result',
    'marsys://tool/L4/query_falsifiers',
  ],

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other).',
    },
    event_type: {
      type: 'string',
      description: 'Filter by event_type (e.g. onset, peak, transition).',
    },
    direction: {
      type: 'string',
      description: 'Filter by direction of the predicted effect.',
    },
    horizon_tier: {
      type: 'string',
      description: 'Filter by horizon tier (e.g. near, mid, far).',
    },
    top_k: {
      type: 'number',
      description: 'Max anchors to return (default: 50, max: 150).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 5,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const domain       = args['domain'] as string | undefined
    const event_type   = args['event_type'] as string | undefined
    const direction    = args['direction'] as string | undefined
    const horizon_tier = args['horizon_tier'] as string | undefined
    const top_k        = Math.min(Number(args['top_k'] ?? 50), 150)

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (domain)       { conds.push(`domain = $${p++}`);       params.push(domain) }
      if (event_type)   { conds.push(`event_type = $${p++}`);   params.push(event_type) }
      if (direction)    { conds.push(`direction = $${p++}`);    params.push(direction) }
      if (horizon_tier) { conds.push(`horizon_tier = $${p++}`); params.push(horizon_tier) }

      params.push(top_k)

      const sql = `
        SELECT anchor_id, domain, event_type, direction, horizon_tier,
               anchor_source, signal_id, convergence_id, discovery_id, bhavishya_id,
               window_start, peak_date, window_end,
               magnitude, magnitude_basis,
               confidence_low, confidence_high, confidence_basis,
               karmic_frame, karmic_note, malleability,
               dasha_consensus_count, ayanamsha_robustness,
               falsifier, source_citation
        FROM phala_anchors
        WHERE ${conds.join(' AND ')}
        ORDER BY magnitude DESC NULLS LAST
        LIMIT $${p}
      `

      const result = await query(sql, params)
      const signalRefs = new Set<string>()
      for (const row of result.rows as Array<{ signal_id?: string }>) {
        if (row.signal_id) signalRefs.add(row.signal_id)
      }

      return {
        content: {
          chart_id,
          anchors:      result.rows,
          anchor_count: result.rows.length,
          signal_id_refs: Array.from(signalRefs),
          filters: { domain, event_type, direction, horizon_tier, top_k },
          drill_next: ['marsys://tool/L4/query_domain_result', 'marsys://tool/L4/query_falsifiers'],
          provenance: { tables: ['phala_anchors'] },
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
