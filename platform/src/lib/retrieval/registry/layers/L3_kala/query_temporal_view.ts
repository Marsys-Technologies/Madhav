/**
 * query_temporal_view — Temporal View (L3 Kāla) — STUBBED-PENDING-DATA
 * ======================================================================
 * Asset: ka_kala_darshana (kala_darshana) — EMPTY: 0 rows.
 *
 * This tool is stubbed because kala_darshana contains 0 rows for all charts
 * (as of runtime validation V3). The writer exists but has not populated data.
 *
 * Returns {stubbed: true, reason: "...", data: []} — NOT an error.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryTemporalViewCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_temporal_view',
  type:  'tool',
  layer: 'L3',
  name:  'query_temporal_view',

  description: [
    'Returns the temporal Kāla-Darshana view for a chart from kala_darshana (ka_kala_darshana).',
    'STUBBED-PENDING-DATA: kala_darshana contains 0 rows as of the current build.',
    'Returns a stub response with data: [] until the ka_kala_darshana writer populates data.',
    'When populated, will return the integrated temporal view combining dasha, gochara,',
    'and convergence layers into a unified timeline visualization surface.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
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
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  false,
    },
    bulk_context: {
      pre_fetch_priority: 50,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    return {
      content: {
        chart_id,
        stubbed: true,
        reason: 'kala_darshana table contains 0 rows for this chart. The ka_kala_darshana writer has not yet populated data. This tool will return live data when the temporal view writer build is complete.',
        data: [],
        pending_asset: 'ka_kala_darshana',
        target_table: 'kala_darshana',
      },
      is_error: false,
    }
  },
}
