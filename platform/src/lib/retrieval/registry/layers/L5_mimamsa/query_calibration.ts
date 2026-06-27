/**
 * query_calibration — Calibration & Reliability Query (L5 Mīmāṃsā)
 * ==================================================================
 * Reads mimamsa_calibration + mimamsa_reliability + mimamsa_multipliers.
 * Returns calibration scorecard, reliability curve, and learned weights:
 *   - Per-match verdict distribution (confirmed/partial/denied)
 *   - Reliability curve by probability bin (ECE, Brier)
 *   - Promoted signal-family multipliers
 *   - QA harness results (negative-control battery)
 */

import type { CapabilityDescriptor } from '../../index'

export const queryCalibrationCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_calibration',
  type:  'tool',
  layer: 'L5',
  name:  'query_calibration',

  description: [
    'Returns the L5 calibration scorecard for a chart.',
    'Includes prediction-event match verdicts, reliability curve (ECE/Brier),',
    'learned signal-family multipliers, and negative-control QA results.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID',
      required: true,
    },
    include_held_out: {
      type: 'boolean',
      description: 'Include held-out partition matches (default: false)',
      required: false,
    },
    promoted_only: {
      type: 'boolean',
      description: 'Return only promoted (gate_passed=true) multipliers (default: false)',
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  llm_hints: {
    agentic: {
      cost_class: 'medium',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 3,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id       = String(args.chart_id)
    const include_heldout = Boolean(args.include_held_out ?? false)
    const promoted_only  = Boolean(args.promoted_only ?? false)

    const leakageFilter = include_heldout ? '' : `AND leakage_status != 'held_out'`
    const multFilter    = promoted_only ? 'AND gate_passed = true' : ''

    const verdictSql = `
      SELECT
        composite_verdict,
        COUNT(*)::int                      AS n,
        AVG(composite_score)::numeric(4,3) AS mean_score,
        AVG(score_timing)::numeric(4,3)    AS mean_timing,
        AVG(score_domain)::numeric(4,3)    AS mean_domain,
        AVG(score_magnitude)::numeric(4,3) AS mean_magnitude
      FROM mimamsa_calibration
      WHERE chart_id = $1 ${leakageFilter}
      GROUP BY composite_verdict
      ORDER BY n DESC
    `

    const reliabilitySql = `
      SELECT stratum_key, predicted_prob_bin, observed_rate, n,
             brier_score, ece, held_out_validity, evidence_grade
      FROM mimamsa_reliability
      WHERE chart_id = $1
      ORDER BY stratum_key
    `

    const multiplierSql = `
      SELECT weight_id, mechanism, target_kind, target_ref, domain,
             applied_multiplier, raw_multiplier, n_observations,
             promotion_status, gate_passed, kill_switch_state, divergence_from_classical
      FROM mimamsa_multipliers
      WHERE chart_id = $1 ${multFilter}
      ORDER BY applied_multiplier DESC
    `

    const qaSql = `
      SELECT check_id, check_type, target, result_score, status, checked_at
      FROM mimamsa_qa_eval
      WHERE chart_id = $1
      ORDER BY status DESC, checked_at DESC
    `

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const [verdictResult, relResult, multResult, qaResult] = await Promise.all([
        db.query(verdictSql,      [chart_id]),
        db.query(reliabilitySql,  [chart_id]),
        db.query(multiplierSql,   [chart_id]),
        db.query(qaSql,           [chart_id]),
      ])

      const qa_fail_count = (qaResult.rows as Array<{ status: string }>)
        .filter(r => r.status === 'FAIL').length

      return {
        content: {
          chart_id,
          verdict_distribution: verdictResult.rows,
          reliability_curve:    relResult.rows,
          multipliers:          multResult.rows,
          qa_results:           qaResult.rows,
          qa_summary:           { total: qaResult.rows.length, fail_count: qa_fail_count },
          filters:              { include_heldout, promoted_only },
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
