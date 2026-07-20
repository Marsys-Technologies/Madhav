/**
 * query_vastu_direction_remedials — L0 Brahmagyan Vastu remedy reference
 * ==========================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_vastu_direction_remedials`, 24 rows). Serves the classical per-direction
 * Vastu remedy reference (colour/symbol/material/space guidance — Brihat
 * Samhita Ch.53; Mayamata Ch.6 — 284_bg_vastu_directions.sql). FK sibling of
 * bg_vastu_directions (same migration, this wave).
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryVastuDirectionRemedialsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_vastu_direction_remedials',
  type:  'tool',
  layer: 'L0',
  name:  'query_vastu_direction_remedials',

  description: [
    'Query the classical Vastu direction-remedy reference (bg_vastu_direction_remedials,',
    '24 rows — Brihat Samhita Ch.53 / Mayamata Ch.6). Each row: direction, remedy_type',
    '(color|symbol|material|space), remedy_description, classical_citation. Filter by',
    'direction or remedy_type. Global classical reference — no chart_id needed.',
  ].join(' '),

  input_schema: {
    direction:   { type: 'string', description: 'Filter by direction (e.g. "Southwest"). Omit for all.' },
    remedy_type: { type: 'string', description: 'Filter by remedy_type (color|symbol|material|space). Omit for all.' },
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
    const direction  = args['direction'] ? String(args['direction']) : null
    const remedyType = args['remedy_type'] ? String(args['remedy_type']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (direction)  { filters.push(`LOWER(direction) = LOWER($${p++})`); params.push(direction) }
    if (remedyType) { filters.push(`LOWER(remedy_type) = LOWER($${p++})`); params.push(remedyType) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT direction, remedy_type, remedy_description, classical_citation
      FROM bg_vastu_direction_remedials
      WHERE ${where}
      ORDER BY direction, remedy_type`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { direction, remedy_type: remedyType },
          ...(result.rows.length === 0
            ? { empty_reason: `No vastu-remedy rows matched (direction=${direction ?? 'any'}, remedy_type=${remedyType ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical Vastu remedy reference only — general guidance, not a prescription for any specific chart.',
          provenance: { tables: ['bg_vastu_direction_remedials'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
