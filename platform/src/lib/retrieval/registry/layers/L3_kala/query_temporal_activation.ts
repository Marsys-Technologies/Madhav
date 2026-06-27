/**
 * query_temporal_activation — Temporal Activation (L3 Kāla)
 * ===========================================================
 * Queries the two core L3 activation tables:
 *   - kala_activation (ka_kalasutra): 66,738 rows — activation windows per signal
 *   - kala_activation_predicates (ka_yojaka): 66,738 rows — predicate conditions
 *
 * Umbrella tool for the L3 timing layer — returns activation windows for signals
 * in a date range, with corresponding predicate conditions.
 * emits_references: true (signal_id back to bo_laksana / bodha_msr_signals).
 *
 * Anchor-to-D1-and-Moon mandate: accepts ayanamsha_id filter.
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryTemporalActivationCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_temporal_activation',
  type:  'tool',
  layer: 'L3',
  name:  'query_temporal_activation',

  description: [
    'Returns temporal activation windows and predicate conditions for a chart.',
    'Sources: kala_activation (66,738 rows per chart) and kala_activation_predicates (66,738 rows).',
    'Filter by date range, signal_ids, and ayanamsha_id.',
    'Returns signal_id references back to bodha_msr_signals for downstream hydration.',
    'Drill further with query_convergence_windows (temporal convergence scoring) and',
    'query_life_arc (biographical chapter structure).',
    'This is the primary temporal entry point — call before any time-specific reading.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',  // L-TIMING (kala layer) maps to L-SIGNAL in D1 types.ts
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L3/query_convergence_windows',
    'marsys://tool/L3/query_life_arc',
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
    date_from: {
      type: 'string',
      description: 'Start of date range (ISO 8601: YYYY-MM-DD). Default: today.',
    },
    date_to: {
      type: 'string',
      description: 'End of date range (ISO 8601: YYYY-MM-DD). Default: 1 year from today.',
    },
    signal_ids: {
      type: 'array',
      description: 'Optional filter: only return activations for these signal_ids (from bodha_msr_signals).',
      items: { type: 'string' },
    },
    top_k: {
      type: 'number',
      description: 'Max activation rows to return (default: 50, max: 500).',
    },
    min_activation_strength: {
      type: 'number',
      description: 'Minimum activation_strength threshold (0..1, default: 0).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'medium',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 8,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id        = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const date_from           = (args['date_from'] as string | undefined) ?? new Date().toISOString().split('T')[0]
    const date_to             = (args['date_to'] as string | undefined) ?? new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0]
    const signal_ids          = args['signal_ids'] as string[] | undefined
    const top_k               = Math.min(Number(args['top_k'] ?? 50), 500)
    const min_strength        = Number(args['min_activation_strength'] ?? 0)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const actConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const actParams: unknown[] = [chart_id, ayanamsha_id]
      let ap = 3

      if (date_from) {
        actConds.push(`window_end >= $${ap++}`)
        actParams.push(date_from)
      }
      if (date_to) {
        actConds.push(`window_start <= $${ap++}`)
        actParams.push(date_to)
      }
      if (signal_ids && signal_ids.length > 0) {
        const phs = signal_ids.map(() => `$${ap++}`).join(', ')
        actConds.push(`signal_id IN (${phs})`)
        actParams.push(...signal_ids)
      }
      if (min_strength > 0) {
        actConds.push(`activation_strength >= $${ap++}`)
        actParams.push(min_strength)
      }
      actParams.push(top_k)
      const topKPh = `$${ap++}`

      const activationSql = `
        SELECT activation_id, signal_id, window_start, window_end,
               activation_strength, activation_type, dasha_lord, antardasha_lord,
               pratyantar_lord, trigger_type, domain_primary, ayanamsha_id
        FROM kala_activation
        WHERE ${actConds.join(' AND ')}
        ORDER BY activation_strength DESC NULLS LAST, window_start
        LIMIT ${topKPh}
      `

      const activations = await db.query(activationSql, actParams)
      const activationIds = (activations.rows as Array<{ activation_id?: string }>)
        .map(r => r.activation_id).filter(Boolean) as string[]

      // Fetch predicates for the activation rows returned
      let predicates: unknown[] = []
      if (activationIds.length > 0) {
        const predPhs = activationIds.map((_, i) => `$${i + 2}`).join(', ')
        const predSql = `
          SELECT predicate_id, activation_id, predicate_type, predicate_expression,
                 predicate_weight, condition_met, checked_at
          FROM kala_activation_predicates
          WHERE chart_id = $1
            AND activation_id IN (${predPhs})
          ORDER BY predicate_weight DESC NULLS LAST
        `
        const predResult = await db.query(predSql, [chart_id, ...activationIds])
        predicates = predResult.rows
      }

      // Collect signal_id references
      const signalRefs = [...new Set(
        (activations.rows as Array<{ signal_id?: string }>).map(r => r.signal_id).filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id,
          ayanamsha_id,
          activations:       activations.rows,
          activation_count:  activations.rows.length,
          predicates,
          predicate_count:   predicates.length,
          signal_id_refs:    signalRefs,
          filters: { date_from, date_to, signal_ids, top_k, min_strength },
          drill_next: [
            'marsys://tool/L3/query_convergence_windows',
            'marsys://tool/L3/query_life_arc',
          ],
          provenance: {
            tables: ['kala_activation', 'kala_activation_predicates'],
          },
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
