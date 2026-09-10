/**
 * query_predictions — Prediction Log (L5 Mīmāṃsā)
 * ==================================================
 * Queries mimamsa_predictions (mi_bhavisya). Returns logged predictions with confidence,
 * falsifiers, and outcome status.
 *
 * NIRMĀṆA L5 W3-3: the header and description used to pin "50 rows per chart". That number
 * was a wrapper-local constant shadowing a live value (§N.7 item 3) and had already drifted —
 * live 2026-09-05 is 139 rows for the canonical chart and 56 for Abhinandan. The population
 * GROWS with every calibration cycle, so any pinned count is wrong by construction. The prose
 * now describes the SHAPE (sparse, growing, per-chart) and the response reports the real
 * `total_matching` it measured.
 *
 * emits_references: true (prediction_id → ph_pramana L4 falsifier refs).
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

/** Bounded serving cap (mirrors query_journal / query_load_bearing). Chosen ABOVE the
 *  current live maximum (139 rows, canonical chart, 2026-09-05) so this bound discloses
 *  the ceiling without truncating any chart's population today. */
const MAX_LIMIT = 200

export const queryPredictionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_predictions',
  type:  'tool',
  layer: 'L5',
  name:  'query_predictions',

  description: [
    'Returns logged predictions for a chart from mimamsa_predictions (mi_bhavisya).',
    'Source: mimamsa_predictions — a sparse, early-stage L5 population that GROWS with each',
    'calibration cycle; the served response reports the real total_matching it measured for',
    'this chart rather than a pinned count.',
    'Each prediction carries: outcome_claim, confidence band, falsifier_jsonb, lifecycle_status',
    '(pending|confirmed|denied|expired), and domain.',
    'emits_references: prediction_id references link to ph_pramana (L4 via source_pramana_id).',
    'Filter by lifecycle_status to review confirmed/denied predictions.',
    `Bounded to ${MAX_LIMIT} rows with a disclosed total_matching + more_available.`,
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
    limit: {
      type: 'number',
      description: `Max predictions to return (default ${MAX_LIMIT}, max ${MAX_LIMIT}).`,
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 12 },
  },

  // NIRMĀṆA L5 W3-3 (§N.6 / plan §2 D-SERVICE P8). paginated: bounded LIMIT with a
  // disclosed total_matching + more_available (no offset cursor — the population is
  // small enough that a raised limit, not a page walk, is the honest control).
  density_contract: {
    paginated: true,
    facets: ['lifecycle_status', 'domain', 'prediction_id'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const prediction_id    = args['prediction_id'] as string | undefined
    const lifecycle_status = args['lifecycle_status'] as string | undefined
    const domain           = args['domain'] as string | undefined
    const limit            = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (prediction_id)    { conds.push(`prediction_id = $${p++}`);    params.push(prediction_id) }
      if (lifecycle_status) { conds.push(`lifecycle_status = $${p++}`); params.push(lifecycle_status) }
      if (domain)           { conds.push(`domain = $${p++}`);          params.push(domain) }

      const where = conds.join(' AND ')
      const sql = `
        SELECT prediction_id, source_pramana_id, domain, outcome_claim,
               confidence_band, magnitude_expected, lifecycle_status,
               observation_window, eval_date, falsifier_jsonb, base_rate,
               driving_signals, emitted_at, created_at
        FROM mimamsa_predictions
        WHERE ${where}
        ORDER BY confidence_band DESC NULLS LAST, created_at DESC
        LIMIT $${p}
      `

      // Family size BEFORE the LIMIT, same filters as the page — so `more_available`
      // is measured, not inferred from whether the page happened to fill.
      const [result, countResult] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM mimamsa_predictions WHERE ${where}`,
          params,
        ),
      ])
      const total_matching = Number(countResult.rows[0]?.total ?? 0)
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
          total_matching,
          more_available:   total_matching > result.rows.length,
          prediction_id_refs: [...new Set(predictionRefs)],
          // Shape, not a pinned count (§N.7 item 3) — the count lives in total_matching,
          // measured on this call.
          sparse_note:
            'mimamsa_predictions is a sparse early-stage L5 population that grows with each ' +
            'calibration cycle; total_matching above is this chart\'s real measured count under ' +
            'the applied filters, not a fixed per-chart figure.',
          ...(result.rows.length === 0
            ? {
                empty_reason:
                  `No predictions matched for chart ${chart_id} ` +
                  `(prediction_id=${prediction_id ?? 'any'}, lifecycle_status=${lifecycle_status ?? 'any'}, ` +
                  `domain=${domain ?? 'any'}). ` +
                  (total_matching === 0
                    ? 'mimamsa_predictions holds no row matching these filters for this chart.'
                    : 'Filters excluded every row.'),
              }
            : {}),
          filters: { prediction_id, lifecycle_status, domain, limit },
          provenance: {
            tables: ['mimamsa_predictions'],
            source: 'L5 Mīmāṃsā prediction log (mi_bhavisya); served chart-scoped.',
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
