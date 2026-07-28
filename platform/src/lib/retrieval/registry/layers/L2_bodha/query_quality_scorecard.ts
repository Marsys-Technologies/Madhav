/**
 * query_quality_scorecard — Synthesis Quality Scorecard (L2 Bodha)
 * =================================================================
 * Reads synthesis_quality_scorecard (bo_pramana_mapa, 2 rows).
 *
 * E-2 freshness contract on DEFECT-001 (R5.1 C2 item 1):
 * The scorecard field unresolved_constituent_facts_count was computed by the Bodha
 * writer BEFORE a since-completed L1 rebuild, and its stored value should not be taken
 * at face value. Rather than restate the historical "91.5% orphan (OPEN)" literal —
 * which post-R4 is FALSE and would mislead worse than no note at all — this tool
 * re-derives the CURRENT orphan rate live against chart_facts on every call and returns
 * it as structured data (`defect_001` — `{ status, note, as_of, expires_on, metrics }`).
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'
import { deriveDefect001Note } from '../../../provenance/freshness_notes'

export const queryQualityScorecardCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_quality_scorecard',
  type:  'tool',
  layer: 'L2',
  name:  'query_quality_scorecard',

  description: [
    'Returns the Bodha synthesis quality scorecard for a chart.',
    'Source: synthesis_quality_scorecard (keyed by chart_id + build_id; no ayanamsha split).',
    'CRITICAL: unresolved_constituent_facts_count in the stored scorecard row may be stale —',
    'it was computed before a since-completed L1 rebuild. This tool re-derives DEFECT-001',
    'live on every call (E-2 freshness contract) — read `defect_001` in the response for the',
    'CURRENT orphan rate, not the stored scorecard field.',
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
      description: "Ayanamsha label echoed back for caller context (default: 'lahiri_chitrapaksha'). The scorecard is not split by ayanamsha — it is keyed by chart_id + build_id — so this value does not filter rows.",
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

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA

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

      // E-2 freshness contract: re-derive DEFECT-001 live rather than trusting the stored
      // unresolved_constituent_facts_count (computed by the writer before the L1 rebuild).
      const defect001 = await deriveDefect001Note(chart_id)

      // GA.1-class fix (SAMĀPANA Track C item 2): the DB row's own
      // unresolved_constituent_facts_count is a writer-time snapshot that goes stale the
      // moment any L1 rebuild runs after the Bodha writer scored it — this tool used to serve
      // that stale number verbatim inside `scorecard` while ALSO serving a correct live-derived
      // count separately as `defect_001`, so two disagreeing numbers reached the same caller
      // under the same field name's plain-English meaning. Overwrite the served scorecard
      // field with the SAME live-derived count so there is only ever one number, never two.
      if (scorecard) {
        scorecard.unresolved_constituent_facts_count = defect001.metrics['orphan_refs'] ?? null
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          scorecard: scorecard ?? null,
          no_data: !scorecard,
          // Structured, live-derived — read this, not the stored scorecard field.
          defect_001: defect001,
          // Legacy field retained (additive) for callers of the prior wave's shape; text
          // now sourced from the same live derivation rather than a hardcoded literal.
          //
          // PARISHODHANA B3 fix (stale prose, flagged as a cosmetic residual in
          // SAMAPANA_REPORT_v1_0.md §3 item 2): this message used to say the served
          // scorecard field "may not reflect this" / "is not refreshed here" — true before
          // the GA.1-class fix above (line ~107), but self-contradicting the moment that fix
          // landed, since `scorecard.unresolved_constituent_facts_count` IS now overwritten
          // with this same live-derived count on every call. The residual gap is narrower and
          // still worth disclosing: the underlying DB ROW in synthesis_quality_scorecard
          // remains an unrefreshed writer-time snapshot — only the SERVED field is corrected,
          // in memory, at response time.
          defect_001_alert: {
            severity: defect001.status === 'RESOLVED' ? 'INFO' : defect001.status === 'UNKNOWN' ? 'UNKNOWN' : 'HIGH',
            message: [
              `DEFECT-001 status (derived live, as_of=${defect001.as_of}): ${defect001.status}.`,
              defect001.note,
              'The served scorecard.unresolved_constituent_facts_count field above is overwritten',
              'with this same live-derived count (SAMĀPANA Track C, GA.1-class fix) — it no longer',
              'disagrees with defect_001. The underlying synthesis_quality_scorecard DB row itself',
              'remains a writer-time snapshot from before the L1 SHA hash rebuild and is not',
              'updated in place; only the value served here is corrected.',
            ].join(' '),
            ...defect001.metrics,
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
