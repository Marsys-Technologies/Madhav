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
import { query } from '@/lib/db/client'

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
    domain: {
      type: 'string',
      description:
        'Optional life-domain filter (e.g. "career", "relationship", "transition"). Narrows ' +
        'verdict_distribution to matches whose PREDICTION carries this domain, resolved via ' +
        'mimamsa_calibration.prediction_id -> mimamsa_predictions.domain. Sections with no ' +
        'domain dimension in the data are returned unfiltered and are named explicitly in ' +
        'filters.domain_unfiltered_sections.',
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

    // F-27 (PARIŚEṢA V4): `domain` is a REAL, derived filter, not a decorative param.
    // `mimamsa_calibration` carries no domain column of its own (its `score_domain` is a
    // numeric match-quality score, NOT a domain label — an easy and previously-made
    // misreading), but every calibration row carries `prediction_id`, and
    // `mimamsa_predictions.domain` is `text NOT NULL` (migration 347_mimamsa_bhavisya.sql:10).
    // The join is therefore fully derivable from L5's own schema and is served by the
    // already-shipped composite index `idx_mimamsa_calibration_prediction (chart_id,
    // prediction_id)` (348_mimamsa_pramana.sql:31). Same domain-scoping precedent as
    // `compute_spine_bundle.ts`.
    const domainRaw = args.domain
    const domain = typeof domainRaw === 'string' && domainRaw.trim() !== ''
      ? domainRaw.trim()
      : null

    const leakageFilter = include_heldout ? '' : `AND c.leakage_status != 'held_out'`
    const multFilter    = promoted_only ? 'AND gate_passed = true' : ''

    // Only INNER-JOIN when a domain was actually requested. An unconditional join would
    // silently drop any calibration row whose prediction row is missing — a data-integrity
    // condition the caller should see as a row, not lose to a join (§N.8: never let a
    // convenience path quietly change what "all rows" means).
    const domainJoin = domain
      ? `JOIN mimamsa_predictions p
           ON  p.chart_id      = c.chart_id
           AND p.prediction_id = c.prediction_id
          AND p.domain         = $2`
      : ''

    const verdictSql = `
      SELECT
        c.composite_verdict,
        COUNT(*)::int                        AS n,
        AVG(c.composite_score)::numeric(4,3) AS mean_score,
        AVG(c.score_timing)::numeric(4,3)    AS mean_timing,
        AVG(c.score_domain)::numeric(4,3)    AS mean_domain,
        AVG(c.score_magnitude)::numeric(4,3) AS mean_magnitude
      FROM mimamsa_calibration c
      ${domainJoin}
      WHERE c.chart_id = $1 ${leakageFilter}
      GROUP BY c.composite_verdict
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
      const [verdictResult, relResult, multResult, qaResult] = await Promise.all([
        query(verdictSql,      domain ? [chart_id, domain] : [chart_id]),
        query(reliabilitySql,  [chart_id]),
        query(multiplierSql,   [chart_id]),
        query(qaSql,           [chart_id]),
      ])

      const qa_fail_count = (qaResult.rows as Array<{ status: string }>)
        .filter(r => r.status === 'FAIL').length

      // Machine-readable narrowing signal (§N.6 item 4 — density signaling is data, not
      // narration). A caller must be able to tell "0 matches in this domain" apart from
      // "the filter did nothing" WITHOUT re-deriving it from the grouped rows.
      const verdict_row_count = (verdictResult.rows as Array<{ n: number }>)
        .reduce((sum, r) => sum + Number(r.n ?? 0), 0)

      // The remaining three sections are NOT domain-scoped, and this is reported as
      // measured data rather than asserted in prose (§N.8 Earned-Signal Principle):
      //   - reliability_curve : mimamsa_reliability has no domain column; its strata are
      //     keyed by `stratum_key`, and `multipliers_with_domain` below is the analogous
      //     honest coverage counter for the one section that DOES have the column.
      //   - multipliers       : mimamsa_multipliers.domain is a real column, but filtering
      //     on it would EMPTY a populated section rather than narrow it wherever the writer
      //     left it NULL (global scope). `multipliers_with_domain` measures that directly.
      //   - qa_results        : mimamsa_qa_eval has no domain dimension at all.
      const multipliers_with_domain = (multResult.rows as Array<{ domain: string | null }>)
        .filter(r => r.domain != null).length

      return {
        content: {
          chart_id,
          verdict_distribution: verdictResult.rows,
          verdict_row_count,
          reliability_curve:    relResult.rows,
          multipliers:          multResult.rows,
          qa_results:           qaResult.rows,
          qa_summary:           { total: qaResult.rows.length, fail_count: qa_fail_count },
          filters: {
            include_heldout,
            promoted_only,
            domain,
            domain_filtered_sections:   domain ? ['verdict_distribution'] : [],
            domain_unfiltered_sections: domain
              ? ['reliability_curve', 'multipliers', 'qa_results']
              : [],
            multipliers_total:       multResult.rows.length,
            multipliers_with_domain,
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
