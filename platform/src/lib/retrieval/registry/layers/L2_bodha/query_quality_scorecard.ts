/**
 * query_quality_scorecard — Synthesis Quality Scorecard (L2 Bodha)
 * =================================================================
 * Reads synthesis_quality_scorecard (bo_pramana_mapa, 2 rows).
 *
 * CRITICAL NOTE on DEFECT-001:
 * The scorecard field unresolved_constituent_facts_count=0 is a FALSE PASS.
 * This field was computed by the Bodha writer BEFORE the L1 rebuild that
 * changed all SHA-keyed fact_ids. The actual orphan count is 61,161/66,832
 * (91.5% of constituent_facts_array references are unresolvable).
 * This tool annotates this false pass in its output — never suppress it.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryQualityScorecardCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_quality_scorecard',
  type:  'tool',
  layer: 'L2',
  name:  'query_quality_scorecard',

  description: [
    'Returns the Bodha synthesis quality scorecard for a chart.',
    'Source: synthesis_quality_scorecard (keyed by chart_id + build_id; no ayanamsha split).',
    'CRITICAL: unresolved_constituent_facts_count in the scorecard reads 0 (FALSE PASS).',
    'Actual orphan count is ~61,161/66,832 (91.5%) per DEFECT-001 (OPEN).',
    'This tool annotates the false pass in its output — use defect_001_alert in the response.',
    'Use this tool to assess Bodha build quality before trusting constituent_facts provenance.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'quality',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha label echoed back for caller context (default: 'LAHIRI'). The scorecard is not split by ayanamsha — it is keyed by chart_id + build_id — so this value does not filter rows.",
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 15,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'

    try {
      const scorecardSql = `
        SELECT scorecard_id, chart_id, build_id,
               msr_signal_count, cdlm_cell_count, cgm_node_count, cgm_edge_count,
               two_pass_verified_pct, documented_approximation_pct,
               msr_citation_ref_coverage_pct,
               trap1_authority_inversion_count, trap2_narration_leak_count,
               unresolved_constituent_facts_count, scored_at
        FROM synthesis_quality_scorecard
        WHERE chart_id = $1
        ORDER BY scored_at DESC
        LIMIT 1
      `

      const result = await query<Record<string, unknown>>(scorecardSql, [chart_id])
      const scorecard = result.rows[0] as Record<string, unknown> | undefined

      return {
        content: {
          chart_id,
          ayanamsha_id,
          scorecard: scorecard ?? null,
          no_data: !scorecard,
          defect_001_alert: {
            severity: 'HIGH',
            message: [
              'DEFECT-001 (OPEN): unresolved_constituent_facts_count in the scorecard is a FALSE PASS.',
              'The Bodha writer computed this field before the L1 SHA hash rebuild.',
              'Actual orphan count: ~61,161/66,832 constituent_facts_array references (91.5%).',
              'Do NOT use this count as evidence of L1 provenance completeness.',
            ].join(' '),
            actual_orphan_count_estimate: 61161,
            total_constituent_refs_estimate: 66832,
            orphan_rate_pct: 91.5,
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
