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

export const queryPredictionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_predictions',
  type:  'tool',
  layer: 'L5',
  name:  'query_predictions',

  description: [
    'Returns logged predictions for a chart from mimamsa_predictions (mi_bhavisya).',
    'Source: mimamsa_predictions (50 rows per chart — sparse, early-stage L5 population).',
    'Each prediction carries: confidence band, falsifiers, outcome_status',
    '(pending|confirmed|disconfirmed|expired), and domain.',
    'emits_references: prediction_id references link to ph_pramana (L4 falsifiers).',
    'Filter by outcome_status to review confirmed/disconfirmed predictions.',
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
    outcome_status: {
      type: 'string',
      description: 'Filter by outcome status.',
      enum: ['pending', 'confirmed', 'disconfirmed', 'expired'],
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

    const prediction_id  = args['prediction_id'] as string | undefined
    const outcome_status = args['outcome_status'] as string | undefined
    const domain         = args['domain'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (prediction_id)  { conds.push(`prediction_id = $${p++}`); params.push(prediction_id) }
      if (outcome_status) { conds.push(`outcome_status = $${p++}`); params.push(outcome_status) }
      if (domain)         { conds.push(`domain = $${p++}`);         params.push(domain) }

      const sql = `
        SELECT prediction_id, domain, prediction_statement,
               confidence_band, outcome_status, outcome_recorded_at,
               falsifier_id_ref, horizon_date, source_anchor_ids,
               reviewer_notes, created_at
        FROM mimamsa_predictions
        WHERE ${conds.join(' AND ')}
        ORDER BY confidence_band DESC NULLS LAST, created_at DESC
      `

      const result = await db.query(sql, params)
      const predictionRefs = (result.rows as Array<{ prediction_id?: string }>)
        .map(r => r.prediction_id).filter(Boolean) as string[]

      return {
        content: {
          chart_id,
          predictions:      result.rows,
          prediction_count: result.rows.length,
          prediction_id_refs: [...new Set(predictionRefs)],
          sparse_note:      'mimamsa_predictions: 50 rows — sparse early L5 population. Population grows with calibration cycles.',
          filters: { prediction_id, outcome_status, domain },
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
