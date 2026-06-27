/**
 * query_signal_families — Signal Family Registry (L5 Mīmāṃsā)
 * ==============================================================
 * Queries mimamsa_signal_families (mi_kula) — global catalog, no chart_id.
 * Returns signal-family registry + negative-control battery.
 *
 * scope: 'global' — no chart_id required or meaningful.
 * emits_references: false — returns family catalog data directly.
 * Chart-agnostic: this is a global reference tool (principle #14 N/A for global scope).
 */

import type { CapabilityDescriptor } from '../../types'

export const querySignalFamiliesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_signal_families',
  type:  'tool',
  layer: 'L5',
  name:  'query_signal_families',

  description: [
    'Returns the signal-family registry from mimamsa_signal_families (mi_kula).',
    'Global scope — not chart-specific. Returns all signal families + negative-control battery.',
    'Signal families define the structural groupings (yoga, dosha, karaka_alignment, etc.)',
    'along with their negative controls (inverse predictions used for calibration testing).',
    'Used by the L5 calibration harness. No chart_id required.',
  ].join(' '),

  scope: 'global',
  archetype: 'calibration',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'quality',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  input_schema: {
    family_name: {
      type: 'string',
      description: 'Filter by specific family name.',
    },
    include_negative_controls: {
      type: 'boolean',
      description: 'Include negative control battery rows (default: true).',
    },
    top_k: {
      type: 'number',
      description: 'Max families to return (default: all, max: 200).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 40 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const family_name         = args['family_name'] as string | undefined
    const include_neg_ctrl    = args['include_negative_controls'] !== false
    const top_k               = Math.min(Number(args['top_k'] ?? 200), 200)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const conds: string[] = []
      const params: unknown[] = []
      let p = 1

      if (family_name)     { conds.push(`family_name = $${p++}`); params.push(family_name) }
      if (!include_neg_ctrl) { conds.push(`is_negative_control = false`) }

      const where = conds.length > 0 ? `WHERE ${conds.join(' AND ')}` : ''
      params.push(top_k)

      const sql = `
        SELECT family_id, family_name, family_class, description,
               is_negative_control, negative_control_of,
               expected_direction, classical_source, created_at
        FROM mimamsa_signal_families
        ${where}
        ORDER BY family_class, family_name
        LIMIT $${p}
      `

      const result = await db.query(sql, params)

      return {
        content: {
          signal_families:  result.rows,
          family_count:     result.rows.length,
          filters: { family_name, include_negative_controls: include_neg_ctrl, top_k },
          provenance: { tables: ['mimamsa_signal_families'] },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err) },
        is_error: true,
      }
    }
  },
}
