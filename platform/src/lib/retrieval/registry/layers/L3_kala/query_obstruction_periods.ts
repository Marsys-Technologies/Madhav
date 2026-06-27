/**
 * query_obstruction_periods — Obstruction Periods (L3 Kāla) — STUBBED-PENDING-DATA
 * ==================================================================================
 * Asset: ka_vighnakara (kala_obstruction) — EMPTY: 0 rows.
 *
 * This tool is stubbed because kala_obstruction contains 0 rows for all charts
 * (as of runtime validation V3). The writer exists but has not populated data.
 *
 * Returns {stubbed: true, reason: "...", data: []} — NOT an error.
 * Do NOT change this to throw. The stub keeps the topology complete so this
 * tool becomes live automatically when data is built.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryObstructionPeriodsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_obstruction_periods',
  type:  'tool',
  layer: 'L3',
  name:  'query_obstruction_periods',

  description: [
    'Returns obstruction periods for a chart from kala_obstruction (ka_vighnakara).',
    'STUBBED-PENDING-DATA: kala_obstruction contains 0 rows as of the current build.',
    'Returns a stub response with data: [] until the ka_vighnakara writer populates data.',
    'When populated, will return periods of planetary obstruction with type, severity,',
    'affected domains, mitigation signals, and temporal bounds.',
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
        reason: 'kala_obstruction table contains 0 rows for this chart. The ka_vighnakara writer has not yet populated data. This tool will return live data when the obstruction writer build is complete.',
        data: [],
        pending_asset: 'ka_vighnakara',
        target_table: 'kala_obstruction',
      },
      is_error: false,
    }
  },
}
