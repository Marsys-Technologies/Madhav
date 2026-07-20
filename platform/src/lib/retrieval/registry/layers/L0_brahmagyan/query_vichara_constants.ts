/**
 * query_vichara_constants — L0 Brahmagyan vichara ratification-constants reference
 * ====================================================================================
 * W2b dark-set wiring, Batch 2 (TABLE_CONCEPT_DISPOSITIONS_v2_0.md borderline
 * SERVE-gap set, `brahma_vichara_constants`, 7 rows). Serves the "registry
 * data, not literals" vichara ratification constants (ratification_step,
 * ratification_clamp — 435_ga_vichara.sql). Zero live TS reader found; a
 * documented DOCTRINE_CAMPAIGN_DESIGN-cited config table, judgment-call
 * per the disposition doc, wired per the ruling's default-bias.
 *
 * Global reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryVicharaConstantsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_vichara_constants',
  type:  'tool',
  layer: 'L0',
  name:  'query_vichara_constants',

  description: [
    'Query the vichara ratification-constants registry (brahma_vichara_constants, 7 rows).',
    'Each row: constant_key, value_jsonb, citation, version, updated_at. Filter by',
    'constant_key. Global reference — no chart_id needed. Registry data (ratification',
    'steps/clamps for the chart_vichara family), not hand-copied literals.',
  ].join(' '),

  input_schema: {
    constant_key: { type: 'string', description: 'Filter by exact constant_key. Omit for all 7.' },
  },

  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 10, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const constantKey = args['constant_key'] ? String(args['constant_key']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (constantKey) { filters.push(`constant_key = $${p++}`); params.push(constantKey) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT constant_key, value_jsonb, citation, version, updated_at
      FROM brahma_vichara_constants
      WHERE ${where}
      ORDER BY constant_key`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { constant_key: constantKey },
          ...(result.rows.length === 0
            ? { empty_reason: `No vichara-constant rows matched (constant_key=${constantKey ?? 'any'}).` }
            : {}),
          disclaimer: 'Registry-managed ratification constants for the chart_vichara family — not hand-copied literals.',
          provenance: { tables: ['brahma_vichara_constants'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
