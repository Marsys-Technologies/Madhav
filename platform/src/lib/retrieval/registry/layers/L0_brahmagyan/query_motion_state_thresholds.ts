/**
 * query_motion_state_thresholds — L0 Brahmagyan motion-state reference
 * ========================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_motion_state_thresholds`, 27 rows). Serves the classical per-graha
 * speed thresholds that define motion state (vakra/anuvakra/manda/sama/
 * atichara) — the reference thresholds only, not any chart's computed
 * per-graha motion state (that lives in chart_facts). Same migration file
 * as bg_dignity_reference (250_bg_dignity_reference.sql).
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryMotionStateThresholdsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_motion_state_thresholds',
  type:  'tool',
  layer: 'L0',
  name:  'query_motion_state_thresholds',

  description: [
    'Query the classical graha motion-state speed-threshold reference',
    '(bg_motion_state_thresholds, 27 rows). motion_state one of vakra (retrograde), anuvakra',
    '(station/slow), manda (slow), sama (normal), atichara (fast); threshold_type one of',
    'below|above|range|always, with speed_threshold_low/high in degrees/day and a',
    'typical_speed_dps reference value. Filter by graha or motion_state. Global classical',
    'reference — no chart_id needed; returns THRESHOLDS only, not any chart\'s actual',
    'computed motion state (that lives in chart_facts / ephemeris).',
  ].join(' '),

  input_schema: {
    graha:        { type: 'string', description: 'Filter by graha (case-insensitive, e.g. "Mars"). Omit for all.' },
    motion_state: { type: 'string', description: 'Filter by motion_state (vakra|anuvakra|manda|sama|atichara). Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 25, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const graha       = args['graha'] ? String(args['graha']) : null
    const motionState = args['motion_state'] ? String(args['motion_state']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (graha)       { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
    if (motionState) { filters.push(`LOWER(motion_state) = LOWER($${p++})`); params.push(motionState) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, motion_state, speed_threshold_low, speed_threshold_high, threshold_type,
             typical_speed_dps, classical_citation, notes
      FROM bg_motion_state_thresholds
      WHERE ${where}
      ORDER BY graha, motion_state`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { graha, motion_state: motionState },
          ...(result.rows.length === 0
            ? { empty_reason: `No motion-state threshold rows matched (graha=${graha ?? 'any'}, motion_state=${motionState ?? 'any'}).` }
            : {}),
          disclaimer: 'Reference speed thresholds only — not a computed per-chart motion-state verdict.',
          provenance: { tables: ['bg_motion_state_thresholds'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
