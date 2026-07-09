/**
 * query_predictions — Prediction Log (L5 Mīmāṃsā)
 * ==================================================
 * Queries mimamsa_predictions (mi_bhavisya) — 50 rows per chart (sparse, by design).
 * Returns logged predictions with confidence, falsifiers, and outcome status.
 *
 * emits_references: true (prediction_id → ph_pramana L4 falsifier refs).
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPredictionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_predictions',
  type:  'tool',
  layer: 'L5',
  name:  'query_predictions',

  description: [
    'Returns logged predictions for a chart from mimamsa_predictions (mi_bhavisya).',
    'Source: mimamsa_predictions (50 rows per chart — sparse, early-stage L5 population).',
    'Each prediction carries: outcome_claim, confidence band, falsifier_jsonb, lifecycle_status',
    '(pending|confirmed|denied|expired), and domain.',
    'emits_references: prediction_id references link to ph_pramana (L4 via source_pramana_id).',
    'Filter by lifecycle_status to review confirmed/denied predictions.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    prediction_id: {
      type: 'string',
      description: 'Filter by specific prediction_id.',
    },
    lifecycle_status: {
      type: 'string',
      description: 'Filter by lifecycle status.',
      enum: ['pending', 'confirmed', 'denied', 'expired'],
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 12 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const prediction_id    = args['prediction_id'] as string | undefined
    const lifecycle_status = args['lifecycle_status'] as string | undefined
    const domain           = args['domain'] as string | undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (prediction_id)    { conds.push(`prediction_id = $${p++}`);    params.push(prediction_id) }
      if (lifecycle_status) { conds.push(`lifecycle_status = $${p++}`); params.push(lifecycle_status) }
      if (domain)           { conds.push(`domain = $${p++}`);          params.push(domain) }

      const sql = `
        SELECT prediction_id, source_pramana_id, domain, outcome_claim,
               confidence_band, magnitude_expected, lifecycle_status,
               observation_window, eval_date, falsifier_jsonb, base_rate,
               driving_signals, emitted_at, created_at
        FROM mimamsa_predictions
        WHERE ${conds.join(' AND ')}
        ORDER BY confidence_band DESC NULLS LAST, created_at DESC
      `

      const result = await query(sql, params)
      const predictionRefs = (result.rows as Array<{ prediction_id?: string }>)
        .map(r => r.prediction_id).filter(Boolean) as string[]

      // R5.1 C2 item 4 (posterior cardinality + base_rate_source stamping). `base_rate` here
      // is populated by mi_pramana.py's _load_base_rates() — a flat per-event-class prior
      // read from `brahma_event_ontology.base_rate` (NOT the age-banded `base_rate_by_age`
      // vector L4 ph_nimitta uses for phala_anchors.posterior — a different, coarser prior
      // for a different purpose: the climatology-null Brier baseline). Falls back to an
      // uninformative 0.10 when the event class has no ontology row. Stamped per row so a
      // caller never has to guess which of the two ontology-derived base rates this is, or
      // assume a floor when the source is genuinely unresolvable.
      const predictionsWithProvenance = (result.rows as Array<Record<string, unknown>>).map(row => {
        const baseRate = row['base_rate'] as number | null
        return {
          ...row,
          base_rate_provenance: baseRate == null ? null : {
            source: 'brahma_event_ontology.base_rate (flat per-event-class prior; distinct from the age-banded base_rate_by_age vector L4 phala_anchors.posterior uses)',
            fallback_value: 0.10,
            // Heuristic flag only — 0.10 could also be a genuine ontology value, not proof of
            // the fallback path having fired for this row.
            matches_fallback_value: baseRate === 0.10,
            cardinality: null,
            cardinality_note: 'base_rate is a prior lookup, not a sample-fit statistic — no N of observations underlies this value.',
          },
        }
      })

      return {
        content: {
          chart_id,
          predictions:      predictionsWithProvenance,
          prediction_count: result.rows.length,
          prediction_id_refs: [...new Set(predictionRefs)],
          sparse_note:      'mimamsa_predictions: 50 rows — sparse early L5 population. Population grows with calibration cycles.',
          filters: { prediction_id, lifecycle_status, domain },
          provenance: { tables: ['mimamsa_predictions'] },
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
