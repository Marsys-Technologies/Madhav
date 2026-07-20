/**
 * query_vastu_directions — L0 Brahmagyan Vastu direction-graha reference
 * ==========================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_vastu_directions`, 8 rows). Serves the classical Vastu 8-direction →
 * ruling-graha / element / colour reference (Mayamata Ch.6; Brihat Samhita
 * — 284_bg_vastu_directions.sql). Distinct from the already-served L1
 * `get_vastu_directions` tool, which serves the per-chart COMPUTED
 * ga_vastu_planet_direction_map rollup — this table is the underlying
 * chart-agnostic classical reference those computed rows draw on.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryVastuDirectionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_vastu_directions',
  type:  'tool',
  layer: 'L0',
  name:  'query_vastu_directions',

  description: [
    'Query the classical Vastu direction reference (bg_vastu_directions, 8 rows — Mayamata',
    'Ch.6). Each row: direction, direction_deg, ruling_graha, secondary_graha,',
    'favorable_color, element, classical_citation. Filter by direction or ruling_graha.',
    'Global classical reference — no chart_id needed. Distinct from the per-chart computed',
    "vastu direction-impact map (get_vastu_directions, L1) — this is the underlying",
    'chart-agnostic classical direction-graha reference table.',
  ].join(' '),

  input_schema: {
    direction:    { type: 'string', description: 'Filter by direction (e.g. "Northeast"). Omit for all 8.' },
    ruling_graha: { type: 'string', description: 'Filter by ruling_graha (case-insensitive). Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 15, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const direction    = args['direction'] ? String(args['direction']) : null
    const rulingGraha  = args['ruling_graha'] ? String(args['ruling_graha']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (direction)   { filters.push(`LOWER(direction) = LOWER($${p++})`); params.push(direction) }
    if (rulingGraha) { filters.push(`LOWER(ruling_graha) = LOWER($${p++})`); params.push(rulingGraha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT direction, direction_deg, ruling_graha, secondary_graha, favorable_color, element, classical_citation
      FROM bg_vastu_directions
      WHERE ${where}
      ORDER BY direction_deg`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { direction, ruling_graha: rulingGraha },
          ...(result.rows.length === 0
            ? { empty_reason: `No vastu-direction rows matched (direction=${direction ?? 'any'}, ruling_graha=${rulingGraha ?? 'any'}).` }
            : {}),
          disclaimer: "Classical direction-graha reference only — not any chart's computed vastu impact map.",
          provenance: { tables: ['bg_vastu_directions'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
