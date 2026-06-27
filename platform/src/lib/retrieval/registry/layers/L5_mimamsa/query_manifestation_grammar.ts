/**
 * query_manifestation_grammar — Manifestation Grammar (L5 Mīmāṃsā)
 * ===================================================================
 * Queries mimamsa_manifestation_grammar (mi_sambandha) — count unknown, per_chart.
 * Returns per-native grammar of how each signal/house/karaka expresses:
 *   structural cells (classical prediction) + empirical cells (observed expression).
 *
 * emits_references: true (signal_id back to bo_laksana/bodha_msr_signals).
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryManifestationGrammarCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_manifestation_grammar',
  type:  'tool',
  layer: 'L5',
  name:  'query_manifestation_grammar',

  description: [
    'Returns the manifestation grammar for a chart from mimamsa_manifestation_grammar (mi_sambandha).',
    'Per-native grammar: how each signal/house/karaka actually expresses in this chart.',
    'Two cell types: structural (classical prediction) and empirical (observed expression).',
    'Useful for calibrating interpretation models against lived reality.',
    'emits_references: signal_id references back to bodha_msr_signals.',
    'Filter by signal_family or house to narrow scope.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
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
    signal_family: {
      type: 'string',
      description: 'Filter by signal family (yoga, dosha, karaka_alignment, composite_state, etc.).',
    },
    house: {
      type: 'number',
      description: 'Filter by house (1–12).',
    },
    cell_type: {
      type: 'string',
      description: "Filter by cell type: 'structural'|'empirical'.",
      enum: ['structural', 'empirical'],
    },
    top_k: {
      type: 'number',
      description: 'Max rows to return (default: 50, max: 500).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 15 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const signal_family = args['signal_family'] as string | undefined
    const house         = args['house'] !== undefined ? Number(args['house']) : undefined
    const cell_type     = args['cell_type'] as string | undefined
    const top_k         = Math.min(Number(args['top_k'] ?? 50), 500)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (signal_family) { conds.push(`signal_family = $${p++}`); params.push(signal_family) }
      if (house !== undefined) { conds.push(`house = $${p++}`); params.push(house) }
      if (cell_type) { conds.push(`cell_type = $${p++}`); params.push(cell_type) }

      params.push(top_k)

      const sql = `
        SELECT grammar_id, signal_family, house, karaka,
               cell_type, structural_prediction, empirical_expression,
               alignment_score, signal_id_ref, lel_event_id,
               recorded_at
        FROM mimamsa_manifestation_grammar
        WHERE ${conds.join(' AND ')}
        ORDER BY alignment_score DESC NULLS LAST
        LIMIT $${p}
      `

      const result = await db.query(sql, params)
      const signalRefs = [...new Set(
        (result.rows as Array<{ signal_id_ref?: string }>).map(r => r.signal_id_ref).filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id,
          grammar_rows:  result.rows,
          row_count:     result.rows.length,
          signal_id_refs: signalRefs,
          filters: { signal_family, house, cell_type, top_k },
          provenance: { tables: ['mimamsa_manifestation_grammar'] },
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
