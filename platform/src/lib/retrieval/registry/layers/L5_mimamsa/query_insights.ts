/**
 * query_insights — Insight Surface Query (L5 Mīmāṃsā)
 * =====================================================
 * Reads mimamsa_insight_units + overlays for a chart.
 * Returns ranked, retrievable insight units with provenance chains:
 *   - Calibrated-outlook insights (prediction → event match scores)
 *   - Manifestation-grammar insights (channel propensity learnings)
 *   - Emergent-law discoveries (pattern candidates from mining)
 *   - Load-bearing conclusion map
 *   - Negative-knowledge statements
 *
 * Primary context-loader for L5 calibrated reading surface.
 */

import type { CapabilityDescriptor } from '../../index'
import { query } from '@/lib/db/client'

export const queryInsightsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_insights',
  type:  'tool',
  layer: 'L5',
  name:  'query_insights',

  description: [
    'Returns ranked L5 Mīmāṃsā insight units for a chart.',
    'Includes calibrated outlooks, manifestation-grammar learnings,',
    'emergent-law discoveries, load-bearing conclusions, and negative knowledge.',
    'All units carry provenance chains back to L1 chart_facts.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID',
      required: true,
    },
    insight_type: {
      type: 'string',
      description: "Filter by type: 'calibrated_outlook'|'manifestation_grammar'|'emergent_law'|'load_bearing'|'negative_knowledge'",
      required: false,
    },
    domain: {
      type: 'string',
      description: 'Filter by life domain (career, health, relationship, etc.)',
      required: false,
    },
    min_rank: {
      type: 'number',
      description: 'Minimum rank_consequence threshold (0..1, default: 0)',
      required: false,
    },
    top_k: {
      type: 'number',
      description: 'Max insight units to return (default: 30, max: 200)',
      required: false,
    },
    include_negative_knowledge: {
      type: 'boolean',
      description: 'Include is_negative_knowledge=true rows (default: true)',
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: true,

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 2,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id    = String(args.chart_id)
    const insight_type = args.insight_type ? String(args.insight_type) : null
    const domain      = args.domain ? String(args.domain) : null
    const min_rank    = Number(args.min_rank ?? 0)
    const top_k       = Math.min(Number(args.top_k ?? 30), 200)
    const include_neg = args.include_negative_knowledge !== false

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2

    if (insight_type) { filters.push(`insight_type = $${p++}`); params.push(insight_type) }
    if (domain)        { filters.push(`domain = $${p++}`);       params.push(domain) }
    if (min_rank > 0)  { filters.push(`rank_consequence >= $${p++}`); params.push(min_rank) }
    if (!include_neg)  { filters.push(`is_negative_knowledge = false`) }

    params.push(top_k)

    const sql = `
      SELECT insight_id, insight_type, domain, horizon, question_lens,
             statement, rank_consequence, confidence_band, n_support,
             leakage_status, evidence_grade, freshness_lel_version,
             last_calibrated_at, provenance_chain, is_negative_knowledge,
             surface_formula_version, updated_at
      FROM mimamsa_insight_units
      WHERE ${filters.join(' AND ')}
      ORDER BY rank_consequence DESC NULLS LAST
      LIMIT $${p}
    `

    // Calibration summary
    const calSql = `
      SELECT
        COUNT(*)::int                                              AS total_matches,
        COUNT(*) FILTER (WHERE composite_verdict = 'CONFIRMED')   AS confirmed,
        COUNT(*) FILTER (WHERE composite_verdict = 'PARTIAL')     AS partial,
        COUNT(*) FILTER (WHERE composite_verdict = 'REFUTED')     AS refuted,
        COUNT(*) FILTER (WHERE composite_verdict = 'UNRESOLVED')  AS unresolved,
        AVG(composite_score)::numeric(4,3)                        AS mean_composite_score
      FROM mimamsa_calibration
      WHERE chart_id = $1
    `

    try {
      const [insightResult, calResult] = await Promise.all([
        query(sql, params),
        query(calSql, [chart_id]),
      ])

      const calibration_summary = (calResult.rows[0] ?? {}) as Record<string, unknown>

      const evidence_grade_counts: Record<string, number> = {}
      for (const row of insightResult.rows as Array<Record<string, unknown>>) {
        const g = String(row.evidence_grade ?? 'unknown')
        evidence_grade_counts[g] = (evidence_grade_counts[g] ?? 0) + 1
      }

      return {
        content: {
          chart_id,
          insight_units:       insightResult.rows,
          calibration_summary,
          evidence_grade_counts,
          filters:             { insight_type, domain, min_rank, top_k, include_neg },
          total_returned:      insightResult.rows.length,
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
