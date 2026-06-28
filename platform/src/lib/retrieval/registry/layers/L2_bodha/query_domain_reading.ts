/**
 * query_domain_reading — Domain Reading (L2 Bodha)
 * =================================================
 * Drill into a life domain via two sources:
 *   - bodha_question_lenses (bo_drishti): question lenses keyed by question_type
 *     (NO domain column — returned chart-wide, not domain-filtered)
 *   - bodha_cdlm_cells (bo_sangati): CDLM cross-domain matrix cells (domain_row/col)
 *
 * Returns a reconciled multi-vantage domain view. Signal references are emitted
 * from CDLM cells (shared_signal_ids_array); bodha_question_lenses carries no
 * signal_id_refs column.
 *
 * DEFECT-001 note: constituent_facts_array on referenced signals has a 91.5%
 * orphan rate (L1 hash rebuild mismatch). Downstream joins to chart_facts by
 * constituent_fact_id will return empty for most signals. The drill link to
 * query_signals handles this with graceful-empty on constituent_facts lookups.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryDomainReadingCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_domain_reading',
  type:  'tool',
  layer: 'L2',
  name:  'query_domain_reading',

  description: [
    'Drill into a specific life domain for a chart using the Bodha synthesis layer.',
    'Returns the chart question lenses from bodha_question_lenses (no domain column —',
    'returned chart-wide) and the domain-scoped CDLM cross-domain matrix cells from bodha_cdlm_cells.',
    'CDLM cells carry signal references (shared_signal_ids_array) for downstream hydration.',
    'If no lens exists for the requested domain, returns the list of available domains.',
    'Multi-vantage: lens covers house + karaka + varga vantages; CDLM covers cross-domain spillover.',
    'Follows query_ucd in the reading hierarchy; drill further with query_signals.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: ['marsys://tool/L2/query_signals'],

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    domain: {
      type: 'string',
      description: [
        'Life domain to query.',
        'One of: career, wealth, relationship, health, character, spirituality, other.',
        'If omitted or unrecognized, returns the list of available domains for this chart.',
      ].join(' '),
      enum: ['career', 'wealth', 'relationship', 'health', 'character', 'spirituality', 'other'],
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to filter by (default: 'LAHIRI').",
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 5,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id     = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const domain       = args['domain'] as string | undefined
    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'

    const VALID_DOMAINS = ['career', 'wealth', 'relationship', 'health', 'character', 'spirituality', 'other']

    try {
      // Domain discovery is sourced from bodha_cdlm_cells (domain_row/domain_col).
      // bodha_question_lenses has NO domain column — see MODEL-MISMATCH note below.
      if (!domain || !VALID_DOMAINS.includes(domain)) {
        const availSql = `
          SELECT DISTINCT d AS domain
          FROM bodha_cdlm_cells,
               LATERAL (VALUES (domain_row), (domain_col)) AS v(d)
          WHERE chart_id = $1 AND ayanamsha_id = $2 AND d IS NOT NULL
          ORDER BY d
        `
        const availRes = await query<Record<string, unknown>>(availSql, [chart_id, ayanamsha_id])
        return {
          content: {
            chart_id,
            ayanamsha_id,
            available_domains: availRes.rows,
            requested_domain:  domain ?? null,
            note: domain ? `Domain '${domain}' not found. Available domains listed.` : 'No domain requested.',
          },
          is_error: false,
        }
      }

      // Question lenses from bodha_question_lenses.
      // MODEL-MISMATCH: this table carries no domain column; lenses are keyed by
      // question_type with template_element_ids_jsonb / all_relevant_ranked_jsonb.
      // We cannot filter lenses by life-domain, so we return the chart's lenses
      // (ranked payload included) alongside the domain-scoped CDLM cells. The
      // lens<->domain reconciliation is deferred to a later wave (see needs_decision).
      const lensSql = `
        SELECT
          lens_id,
          question_type,
          template_element_ids_jsonb,
          all_relevant_ranked_jsonb,
          lens_template_version,
          points_only_assertion,
          verification_pass_status,
          computed_at
        FROM bodha_question_lenses
        WHERE chart_id = $1 AND ayanamsha_id = $2
        ORDER BY question_type
        LIMIT 60
      `

      // CDLM cross-domain cell from bodha_cdlm_cells (real columns)
      const cdlmSql = `
        SELECT
          cell_id,
          domain_row,
          domain_col,
          domain_relationship_class,
          shared_signal_count,
          net_linkage_strength,
          computed_linkage_strength,
          shared_signal_ids_array,
          dominant_linkage_rank_in_chart,
          cell_remedy_priority_rank,
          computed_at
        FROM bodha_cdlm_cells
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND (domain_row = $3 OR domain_col = $3)
        ORDER BY net_linkage_strength DESC NULLS LAST
        LIMIT 10
      `

      const [lensRes, cdlmRes] = await Promise.all([
        query<Record<string, unknown>>(lensSql, [chart_id, ayanamsha_id]),
        query<Record<string, unknown>>(cdlmSql, [chart_id, ayanamsha_id, domain]),
      ])

      // Collect signal_id references emitted by this tool (CDLM cells only;
      // bodha_question_lenses carries no signal_id_refs column).
      const signalRefs = new Set<string>()
      for (const cell of cdlmRes.rows as Array<{ shared_signal_ids_array?: string[] }>) {
        if (cell.shared_signal_ids_array) {
          for (const id of cell.shared_signal_ids_array) signalRefs.add(id)
        }
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          domain,
          question_lenses: lensRes.rows,
          cdlm_cells:      cdlmRes.rows,
          signal_id_refs:  Array.from(signalRefs),
          lens_count:      lensRes.rows.length,
          cdlm_cell_count: cdlmRes.rows.length,
          drill_next:      'marsys://tool/L2/query_signals',
          provenance: {
            tables: ['bodha_question_lenses', 'bodha_cdlm_cells'],
            model_mismatch_note: [
              'bodha_question_lenses has no domain column; lenses are returned chart-wide,',
              'not domain-filtered. Signal references derive from CDLM cells only.',
            ].join(' '),
            defect_001_note: [
              'constituent_facts_array in referenced signals has 91.5% orphan rate (DEFECT-001 OPEN).',
              'L1 fact joins via signal references will be empty for most signals until L2 rebuild.',
            ].join(' '),
          },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id, domain },
        is_error: true,
      }
    }
  },
}
