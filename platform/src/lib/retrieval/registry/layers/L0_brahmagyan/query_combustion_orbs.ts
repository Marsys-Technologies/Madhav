/**
 * query_combustion_orbs — L0 Brahmagyan combustion-orb reference
 * =================================================================
 * W2 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_combustion_orbs`, 8 rows). Serves the classical combustion (asta) orb
 * thresholds per graha — the degree-from-Sun distances at which a graha is
 * considered combust / deep-combust (Saravali Ch.6 / BPHS Ch.3). Same migration
 * file (250_bg_dignity_reference.sql) as `bg_dignity_reference` and
 * `bg_graha_naisargika_friendship` (sibling W2 dark-set item, this same wave).
 * Sun has no row (never combust).
 *
 * Global classical reference — no chart_id needed. This table stores the
 * REFERENCE THRESHOLDS only, not any chart's actual per-planet combustion
 * verdict (that computed verdict lives in `ga_condition_composite` /
 * chart_facts — a separate SERVE-gap item this wave did not wire).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryCombustionOrbsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_combustion_orbs',
  type:  'tool',
  layer: 'L0',
  name:  'query_combustion_orbs',

  description: [
    'Query the classical combustion (asta) orb reference (bg_combustion_orbs, 8 rows —',
    'Saravali Ch.6 / BPHS Ch.3). orb_degrees is the outer threshold (planet enters combustion',
    'within this many degrees of the Sun); deep_orb_degrees is the tighter inner threshold',
    '(deep/severe combustion). Sun itself has no row (never combust). Filter by graha.',
    'Global classical reference — no chart_id needed; returns THRESHOLDS only, not any',
    "chart's actual combust/not-combust verdict (that lives in computed chart_facts).",
  ].join(' '),

  input_schema: {
    graha: { type: 'string', description: 'Filter by graha (case-insensitive, e.g. "Mercury"). Omit for all 8.' },
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
    bulk_context: { pre_fetch_priority: 30, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const graha = args['graha'] ? String(args['graha']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (graha) { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, orb_degrees, deep_orb_degrees, retrograde_note, classical_citation
      FROM bg_combustion_orbs
      WHERE ${where}
      ORDER BY graha`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { graha },
          ...(result.rows.length === 0
            ? { empty_reason: `No combustion-orb rows matched (graha=${graha ?? 'any'}). Note: Sun never has a row (never combust).` }
            : {}),
          disclaimer: 'Reference thresholds only — not a computed combust/not-combust verdict for any chart.',
          provenance: { tables: ['bg_combustion_orbs'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
