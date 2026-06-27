/**
 * query_domain_reading — Domain Reading (L2 Bodha)
 * =================================================
 * Drill into a life domain via two sources:
 *   - bodha_question_lenses (bo_drishti): domain question lenses (60 rows)
 *   - bodha_cdlm_cells (bo_sangati): CDLM cross-domain matrix cells (70 rows)
 *
 * Returns a reconciled multi-vantage domain view. Each lens carries references
 * back to bodha_msr_signals via signal_id_refs (emits_references=true).
 *
 * DEFECT-001 note: constituent_facts_array on referenced signals has a 91.5%
 * orphan rate (L1 hash rebuild mismatch). Downstream joins to chart_facts by
 * constituent_fact_id will return empty for most signals. The drill link to
 * query_signals handles this with graceful-empty on constituent_facts lookups.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryDomainReadingCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_domain_reading',
  type:  'tool',
  layer: 'L2',
  name:  'query_domain_reading',

  description: [
    'Drill into a specific life domain for a chart using the Bodha synthesis layer.',
    'Returns the domain question lens from bodha_question_lenses and the corresponding',
    'CDLM cross-domain matrix cell from bodha_cdlm_cells.',
    'Both sources carry signal_id references into bodha_msr_signals for downstream hydration.',
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
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      // If no domain requested, return available domains for this chart
      if (!domain || !VALID_DOMAINS.includes(domain)) {
        const availSql = `
          SELECT DISTINCT domain_primary
          FROM bodha_question_lenses
          WHERE chart_id = $1 AND ayanamsha_id = $2
          ORDER BY domain_primary
        `
        const availRes = await db.query(availSql, [chart_id, ayanamsha_id])
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

      // Domain question lens from bodha_question_lenses
      const lensSql = `
        SELECT
          lens_id,
          domain_primary,
          domain_secondary,
          question_text,
          house_axis_primary,
          karaka_primary,
          varga_primary,
          signal_id_refs,
          lens_weight,
          tradition_filter,
          updated_at
        FROM bodha_question_lenses
        WHERE chart_id = $1 AND ayanamsha_id = $2 AND domain_primary = $3
        ORDER BY lens_weight DESC NULLS LAST
        LIMIT 10
      `

      // CDLM cross-domain cell from bodha_cdlm_cells
      const cdlmSql = `
        SELECT
          cell_id,
          domain_row,
          domain_col,
          relationship_type,
          signal_count,
          net_valence,
          top_signal_ids,
          spillover_weight,
          classical_warrant,
          updated_at
        FROM bodha_cdlm_cells
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND (domain_row = $3 OR domain_col = $3)
        ORDER BY spillover_weight DESC NULLS LAST
        LIMIT 10
      `

      const [lensRes, cdlmRes] = await Promise.all([
        db.query(lensSql, [chart_id, ayanamsha_id, domain]),
        db.query(cdlmSql, [chart_id, ayanamsha_id, domain]),
      ])

      // Collect signal_id references emitted by this tool
      const signalRefs = new Set<string>()
      for (const lens of lensRes.rows as Array<{ signal_id_refs?: string[] }>) {
        if (lens.signal_id_refs) {
          for (const id of lens.signal_id_refs) signalRefs.add(id)
        }
      }
      for (const cell of cdlmRes.rows as Array<{ top_signal_ids?: string[] }>) {
        if (cell.top_signal_ids) {
          for (const id of cell.top_signal_ids) signalRefs.add(id)
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
            defect_001_note: [
              'constituent_facts_array in referenced signals has 91.5% orphan rate (DEFECT-001 OPEN).',
              'L1 fact joins via signal_id_refs will be empty for most signals until L2 rebuild.',
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
