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

export const queryPredictiveAnchorsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_predictive_anchors',
  type:  'tool',
  layer: 'L4',
  name:  'query_predictive_anchors',

  description: [
    'Returns predictive anchors for a chart from phala_anchors (ph_nimitta).',
    'Source: phala_anchors (150 rows — the core L4 prediction foundation).',
    'Each anchor has 8 derivation axes (natal, dasha, gochara, divisional,',
    'strength, karaka, yoga, convergence) and 5 elevation fields.',
    'Filter by domain and derivation_axis to focus on specific anchor classes.',
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
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'LAHIRI').",
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other).',
    },
    derivation_axis: {
      type: 'string',
      description: "Filter by derivation axis: 'natal'|'dasha'|'gochara'|'divisional'|'strength'|'karaka'|'yoga'|'convergence'.",
      enum: ['natal', 'dasha', 'gochara', 'divisional', 'strength', 'karaka', 'yoga', 'convergence'],
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

    const ayanamsha_id    = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const domain          = args['domain'] as string | undefined
    const derivation_axis = args['derivation_axis'] as string | undefined
    const top_k           = Math.min(Number(args['top_k'] ?? 50), 150)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (domain)          { conds.push(`domain = $${p++}`);           params.push(domain) }
      if (derivation_axis) { conds.push(`derivation_axis = $${p++}`);  params.push(derivation_axis) }

      params.push(top_k)

      const sql = `
        SELECT anchor_id, domain, derivation_axis,
               anchor_statement, signal_id_refs,
               natal_axis_score, dasha_axis_score, gochara_axis_score,
               divisional_axis_score, strength_axis_score,
               karaka_axis_score, yoga_axis_score, convergence_axis_score,
               elevation_primary, elevation_secondary,
               anchor_weight, anchor_confidence,
               classical_warrant, ayanamsha_id
        FROM phala_anchors
        WHERE ${conds.join(' AND ')}
        ORDER BY anchor_weight DESC NULLS LAST
        LIMIT $${p}
      `

      const result = await db.query(sql, params)
      const signalRefs = new Set<string>()
      for (const row of result.rows as Array<{ signal_id_refs?: string[] }>) {
        if (row.signal_id_refs) {
          for (const id of row.signal_id_refs) signalRefs.add(id)
        }
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          anchors:      result.rows,
          anchor_count: result.rows.length,
          signal_id_refs: Array.from(signalRefs),
          filters: { domain, derivation_axis, top_k },
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
