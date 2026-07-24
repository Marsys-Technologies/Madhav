/**
 * query_predictive_anchors — Predictive Anchors (L4 Phala)
 * ==========================================================
 * Queries phala_anchors (ph_nimitta) — 150 rows per chart.
 * Returns predictive anchors with 8 derivation axes + 5 elevation fields.
 *
 * Umbrella for the L4 layer — drill further to query_domain_result,
 * query_falsifiers, query_anomaly_flags, query_cleansed_anchors.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPredictiveAnchorsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_predictive_anchors',
  type:  'tool',
  layer: 'L4',
  name:  'query_predictive_anchors',

  description: [
    'Returns predictive anchors for a chart from phala_anchors (ph_nimitta).',
    'Source: phala_anchors (150 rows — the core L4 prediction foundation).',
    'Each anchor carries a magnitude, confidence band, karmic frame, malleability,',
    'and a derivation ledger over its constituent L1/L2/L3 facts.',
    'Filter by domain, event_type, direction, and horizon_tier to focus.',
    'emits_references: signal_id refs back to bodha_msr_signals via anchor provenance.',
    'Drill further: query_domain_result (7-domain result map), query_falsifiers,',
    'query_anomaly_flags, query_cleansed_anchors.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L4/query_domain_result',
    'marsys://tool/L4/query_falsifiers',
  ],

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other).',
    },
    event_type: {
      type: 'string',
      description: 'Filter by event_type (e.g. onset, peak, transition).',
    },
    direction: {
      type: 'string',
      description: 'Filter by direction of the predicted effect.',
    },
    horizon_tier: {
      type: 'string',
      description: 'Filter by horizon tier (e.g. near, mid, far).',
    },
    top_k: {
      type: 'number',
      description: 'Max anchors to return (default: 50, max: 150).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 5,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const domain       = args['domain'] as string | undefined
    const event_type   = args['event_type'] as string | undefined
    const direction    = args['direction'] as string | undefined
    const horizon_tier = args['horizon_tier'] as string | undefined
    const top_k        = Math.min(Number(args['top_k'] ?? 50), 150)

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (domain)       { conds.push(`domain = $${p++}`);       params.push(domain) }
      if (event_type)   { conds.push(`event_type = $${p++}`);   params.push(event_type) }
      if (direction)    { conds.push(`direction = $${p++}`);    params.push(direction) }
      if (horizon_tier) { conds.push(`horizon_tier = $${p++}`); params.push(horizon_tier) }

      params.push(top_k)

      const sql = `
        SELECT anchor_id, domain, event_type, direction, horizon_tier,
               anchor_source, signal_id, convergence_id, discovery_id, bhavishya_id,
               to_char(window_start, 'YYYY-MM-DD') AS window_start,
               to_char(peak_date, 'YYYY-MM-DD')    AS peak_date,
               to_char(window_end, 'YYYY-MM-DD')   AS window_end,
               magnitude, magnitude_basis,
               confidence_low, confidence_high, confidence_basis,
               karmic_frame, karmic_note, malleability,
               dasha_consensus_count, ayanamsha_robustness,
               falsifier, source_citation,
               posterior, lift_vector_jsonb
        FROM phala_anchors
        WHERE ${conds.join(' AND ')}
        ORDER BY magnitude DESC NULLS LAST
        LIMIT $${p}
      `

      const result = await query(sql, params)
      const signalRefs = new Set<string>()
      for (const row of result.rows as Array<{ signal_id?: string }>) {
        if (row.signal_id) signalRefs.add(row.signal_id)
      }

      // §N.6 Serving Density Principle (T-5 fix, A-6/B-1): an empty `anchors` array must
      // NEVER be a silent empty. Distinguish (a) a genuine filter miss (the chart HAS
      // anchors, just none match this domain/event_type/direction/horizon_tier), from
      // (b) a genuinely empty backing set for this chart (the CR-66 degenerate-build
      // condition), from (c) an unreachable backing table. We resolve which by counting
      // the chart's total anchors once, only when the filtered result is empty — an
      // honest, non-fabricated disclosure — and cite the open CR so a caller can never
      // read the empty as "no predictions exist for this native."
      let empty_reason: string | null = null
      let known_gap: string | null = null
      let backing_data_reachable = true
      if (result.rows.length === 0) {
        const hasFilter = Boolean(domain || event_type || direction || horizon_tier)
        let chartTotal = -1
        try {
          const totalRes = await query(
            'SELECT count(*)::int AS n FROM phala_anchors WHERE chart_id = $1',
            [chart_id],
          )
          chartTotal = Number((totalRes.rows[0] as { n?: number } | undefined)?.n ?? 0)
        } catch {
          chartTotal = -1
        }
        if (chartTotal < 0) {
          backing_data_reachable = false
          empty_reason = 'phala_anchors count for this chart could not be read on this call — backing data may be unreachable; this empty is NOT a confirmed zero-prediction result.'
        } else if (chartTotal === 0) {
          empty_reason = 'phala_anchors has zero rows for this chart — the L4 predictive-anchor build (ph_nimitta) has not produced anchors for this native, or the build is degenerate. This is a known data gap, not a fabricated empty.'
          known_gap = 'CR-66'
        } else if (hasFilter) {
          empty_reason = `phala_anchors has ${chartTotal} anchor(s) for this chart, but none match the requested filter (domain=${domain ?? '∅'}, event_type=${event_type ?? '∅'}, direction=${direction ?? '∅'}, horizon_tier=${horizon_tier ?? '∅'}). Drop or widen the filter to see the chart's anchors — an honest filter miss, not a fabricated empty.`
          known_gap = 'CR-66'
        } else {
          empty_reason = `phala_anchors reports ${chartTotal} anchor(s) for this chart but the primary query returned none — unexpected; treat as an honest empty pending investigation, not a confirmed zero.`
        }
      }

      // R5.1 C2 item 4 (posterior cardinality + base_rate_source stamping — seal §6 /
      // lift_vector provenance). `posterior`/`lift_vector_jsonb` (migration 398, BA-P5B) are
      // a DETERMINISTIC product model — posterior = base_rate × promise_lift ×
      // activation_lift × trigger_lift × ayanamsha_robustness_modifier — NOT a frequentist
      // estimate fit from N observed outcomes. Per B.10, we do not invent a fake "n" for a
      // model that has none; instead every anchor row gets an honest `posterior_provenance`
      // block naming (a) the real, current base_rate source (services/ph_nimitta/base_rate.py,
      // JL-009 closed 2026-07-07: brahma_event_ontology.base_rate_by_age, row-normalized to
      // the anchor's own predicted-date age band, uniform 0.20 fallback when the vector/dates
      // are unavailable), and (b) the explicit, non-fabricated cardinality floor — this
      // model has no sample-size analog; the empirically-calibrated analog with a genuine
      // n_observations lives at L5 query_calibration's mimamsa_multipliers. Anchors written
      // before BA-P5B (posterior/lift_vector_jsonb null) get an honest null block, never a
      // backfilled guess.
      const anchorsWithProvenance = (result.rows as Array<Record<string, unknown>>).map(row => {
        const liftVector = row['lift_vector_jsonb'] as Record<string, unknown> | null
        const posterior = row['posterior'] as number | null
        if (posterior == null || liftVector == null) {
          return {
            ...row,
            posterior_provenance: null,
            posterior_provenance_note: 'posterior/lift_vector_jsonb not computed for this anchor (pre-BA-P5B row or backfill pending) — no cardinality/base_rate_source to report.',
          }
        }
        return {
          ...row,
          posterior_provenance: {
            model: 'deterministic_product_lift',
            model_formula: 'posterior = base_rate × promise_lift × activation_lift × trigger_lift × ayanamsha_robustness_modifier',
            cardinality: null,
            cardinality_note: 'Not a sample-fit statistic — this posterior has no underlying N of observed outcomes to report (never fabricated). The empirically-calibrated analog with a genuine n_observations is L5 query_calibration (mimamsa_multipliers).',
            base_rate_source: 'brahma_event_ontology.base_rate_by_age, row-normalized to sum 1.0 (JL-009 closed 2026-07-07), looked up for the age band containing this anchor’s predicted date (peak_date, else window_start) relative to the native’s birth date. Falls back to the uniform age prior (0.20, 1-of-5-bands) when the ontology vector or a usable date is unavailable for this anchor — never a fabricated non-uniform value.',
            base_rate_value: liftVector['base_rate'] ?? null,
            // Heuristic only (0.20 == the uniform fallback value, but a genuinely age-banded
            // lookup could also legitimately resolve to 0.20) — labeled as such, never
            // asserted as a confirmed fact about which path this specific row took.
            base_rate_matches_uniform_fallback_value: typeof liftVector['base_rate'] === 'number' ? liftVector['base_rate'] === 0.2 : null,
          },
        }
      })

      return {
        content: {
          chart_id,
          anchors:      anchorsWithProvenance,
          anchor_count: result.rows.length,
          empty_reason,
          known_gap,
          signal_id_refs: Array.from(signalRefs),
          filters: { domain, event_type, direction, horizon_tier, top_k },
          drill_next: ['marsys://tool/L4/query_domain_result', 'marsys://tool/L4/query_falsifiers'],
          provenance: { tables: ['phala_anchors'], backing_data_reachable },
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
