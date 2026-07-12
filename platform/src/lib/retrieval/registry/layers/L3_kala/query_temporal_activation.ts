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
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'

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
      description: "Ayanamsha filter (default: 'lahiri_chitrapaksha').",
    },
    date_from: {
      type: 'string',
      description: 'Start of date range (ISO 8601: YYYY-MM-DD). Default: today.',
    },
    date_to: {
      type: 'string',
      description: 'End of date range (ISO 8601: YYYY-MM-DD). Default: 1 year from today.',
    },
    as_of: {
      type: 'string',
      description: 'Point-in-time date (ISO 8601: YYYY-MM-DD). When set, returns only the ' +
        'activation windows CONTAINING this instant (activation_start <= as_of <= activation_end) ' +
        'and overrides date_from/date_to. Use for "what is active on <date>?" questions.',
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
      description: 'Minimum orb_strength threshold (0..1, default: 0).',
    },
    domain: {
      type: 'string',
      description: 'Filter to activations whose signal (bodha_msr_signals.domains_affected_array) ' +
        'contains this domain (e.g. "career", "wealth", "relationship", "health"). Optional.',
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

    const ayanamsha_id        = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    // WP-1.3(e): track whether the caller supplied an explicit window so the echo can
    // honestly disclose when a default (today..+1y) was silently applied.
    const explicitFrom        = args['date_from'] !== undefined && args['date_from'] !== null
    const explicitTo          = args['date_to'] !== undefined && args['date_to'] !== null
    const as_of               = args['as_of'] as string | undefined
    const date_from           = (args['date_from'] as string | undefined) ?? new Date().toISOString().split('T')[0]
    const date_to             = (args['date_to'] as string | undefined) ?? new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0]
    const signal_ids          = args['signal_ids'] as string[] | undefined
    const top_k               = Math.min(Number(args['top_k'] ?? 50), 500)
    const min_strength        = Number(args['min_activation_strength'] ?? 0)
    const domain              = args['domain'] as string | undefined

    try {
      const actConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const actParams: unknown[] = [chart_id, ayanamsha_id]
      let ap = 3

      // WP-1.3(e): as_of is a point-in-time query — the window must CONTAIN the instant.
      // It overrides the range (and its today..+1y default) entirely.
      if (as_of) {
        actConds.push(`activation_start <= $${ap++}`)
        actParams.push(as_of)
        actConds.push(`activation_end >= $${ap++}`)
        actParams.push(as_of)
      } else {
        if (date_from) {
          actConds.push(`activation_end >= $${ap++}`)
          actParams.push(date_from)
        }
        if (date_to) {
          actConds.push(`activation_start <= $${ap++}`)
          actParams.push(date_to)
        }
      }
      if (signal_ids && signal_ids.length > 0) {
        const phs = signal_ids.map(() => `$${ap++}`).join(', ')
        actConds.push(`signal_id IN (${phs})`)
        actParams.push(...signal_ids)
      }
      if (min_strength > 0) {
        actConds.push(`orb_strength >= $${ap++}`)
        actParams.push(min_strength)
      }
      if (domain) {
        actConds.push(
          `EXISTS (SELECT 1 FROM bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id AND $${ap++} = ANY(ms.domains_affected_array))`
        )
        actParams.push(domain)
      }
      actParams.push(top_k)
      const topKPh = `$${ap++}`

      const activationSql = `
        SELECT id, signal_id, ayanamsha_id, signature_class,
               activation_start, activation_end, activation_peak_date,
               orb_strength, convergence_score, dasha_activation_proximity_score,
               active_dasha_periods_jsonb, activation_predicted_dates_jsonb,
               source_citation
        FROM kala_activation
        WHERE ${actConds.join(' AND ')}
        ORDER BY orb_strength DESC NULLS LAST, activation_start
        LIMIT ${topKPh}
      `

      const activations = await query<Record<string, unknown>>(activationSql, actParams)

      // Predicates link to activations by signal_id (+ signature_class), not an
      // activation_id FK. Fetch predicates for the signals in the returned set.
      const predSignalIds = [...new Set(
        (activations.rows as Array<{ signal_id?: string }>)
          .map(r => r.signal_id).filter(Boolean) as string[]
      )]

      let predicates: unknown[] = []
      if (predSignalIds.length > 0) {
        const predPhs = predSignalIds.map((_, i) => `$${i + 3}`).join(', ')
        const predSql = `
          SELECT id, signal_id, ayanamsha_id, signature_class,
                 dasha_eligibility_rule_jsonb, transit_trigger_jsonb,
                 strength_affliction_hook_jsonb, derivation_ledger_jsonb,
                 template_version
          FROM kala_activation_predicates
          WHERE chart_id = $1
            AND ayanamsha_id = $2
            AND signal_id IN (${predPhs})
        `
        const predResult = await query<Record<string, unknown>>(predSql, [chart_id, ayanamsha_id, ...predSignalIds])
        predicates = predResult.rows
      }

      // Collect signal_id references
      const signalRefs = [...new Set(
        (activations.rows as Array<{ signal_id?: string }>).map(r => r.signal_id).filter(Boolean) as string[]
      )]

      // WP-1.3(e): honest-empty disclosure. When the date filter yields nothing, an LLM
      // consumer cannot tell "no windows in this range" from R-45 "the writer emits no
      // activation dates yet" (WP-2.1 populates them at W2). Run one bounded COUNT aggregate
      // (single row, not a dump) to classify the empty and disclose the reason.
      let empty_reason: string | null = null
      let awaiting_activation_dates = false
      if (activations.rows.length === 0) {
        const disc = await query<{ total: number; dated: number }>(
          `SELECT COUNT(*)::int AS total, COUNT(activation_start)::int AS dated
             FROM kala_activation
            WHERE chart_id = $1 AND ayanamsha_id = $2`,
          [chart_id, ayanamsha_id],
        )
        const total = Number(disc.rows[0]?.total ?? 0)
        const dated = Number(disc.rows[0]?.dated ?? 0)
        if (total === 0) {
          empty_reason =
            `No activation rows exist for chart ${chart_id} at ayanamsha '${ayanamsha_id}'. ` +
            `The L3 Kāla activation asset (ka_kalasutra) may not be built for this chart, or the ` +
            `ayanamsha_id does not match a built variant.`
        } else if (dated === 0) {
          awaiting_activation_dates = true
          empty_reason =
            `PENDING-W3 (honest empty, not an error): ${total} activation rows exist for this ` +
            `chart/ayanamsha but none carry activation_start/activation_end dates yet (R-45). ` +
            `Temporal windowing therefore returns empty until WP-2.1 (the ka_kalasutra writer half, ` +
            `Wave 2) populates activation dates. The serving side honored your date filter correctly; ` +
            `there is simply no dated data to place in a window.`
        } else {
          const window = as_of ? `as_of point ${as_of}` : `date range ${date_from}..${date_to}`
          empty_reason =
            `No activation windows overlap the requested ${window}. ${dated} dated activation rows ` +
            `exist for this chart/ayanamsha outside that filter — widen the window (or drop the date ` +
            `filter) to see them.`
        }
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          activations:       activations.rows,
          activation_count:  activations.rows.length,
          predicates,
          predicate_count:   predicates.length,
          signal_id_refs:    signalRefs,
          filters: { date_from, date_to, as_of: as_of ?? null, signal_ids, top_k, min_strength, domain: domain ?? null },
          // WP-1.3(e): explicit, always-present echo of the date filter actually applied,
          // including whether the range fell back to its today..+1y default.
          date_filter: {
            mode:            as_of ? 'point_in_time' : 'range',
            as_of:           as_of ?? null,
            date_from:       as_of ? null : date_from,
            date_to:         as_of ? null : date_to,
            range_defaulted: !as_of && !explicitFrom && !explicitTo,
            honored:         true,
          },
          empty_reason,
          awaiting_activation_dates,
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
