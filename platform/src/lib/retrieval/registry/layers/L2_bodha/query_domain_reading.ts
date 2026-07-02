/**
 * query_domain_reading — Domain Reading (L2 Bodha)
 * =================================================
 * Drill into a life domain via two sources:
 *   - bodha_question_lenses (bo_drishti): question lenses keyed by question_type
 *     filtered at query-time via DOMAIN_TO_QUESTION_TYPES (inverted from
 *     bo_drishti.py::QUESTION_TYPE_CONFIG). No domain column in the table — mapping is pure query logic.
 *   - bodha_cdlm_cells (bo_sangati): CDLM cross-domain matrix cells (domain_row/col)
 *
 * Returns a reconciled multi-vantage domain view. Signal references are emitted
 * from CDLM cells; bodha_question_lenses carries no signal_id_refs column.
 *
 * Payload bounding (F-021R-b / F-023):
 *   - shared_signal_ids_array stripped from served cells by default (shared_signal_count
 *     is the useful scalar; raw IDs available via query_signals drill).
 *   - signal_id_refs capped to max_signal_refs (default 200) — sufficient for
 *     downstream temporal-activation filtering (query_temporal_activation top_k=20).
 *   - response_format=full restores the arrays (capped at higher limits).
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
import { DEFAULT_AYANAMSHA } from '../../constants'

/**
 * Maps each valid life-domain to the question_types that cover it.
 * Inverted from bo_drishti.py::QUESTION_TYPE_CONFIG (source of truth).
 * Domain 'other' returns an empty array — no filter applied (all lenses returned).
 */
const DOMAIN_TO_QUESTION_TYPES: Record<string, string[]> = {
  career:       ['career', 'progeny'],
  wealth:       ['wealth', 'property'],
  relationship: ['marriage', 'progeny'],
  health:       ['health', 'longevity'],
  character:    ['character', 'education', 'siblings'],
  spirituality: ['spirituality', 'education', 'foreign_travel'],
  other:        [],
}

export const queryDomainReadingCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_domain_reading',
  type:  'tool',
  layer: 'L2',
  name:  'query_domain_reading',

  description: [
    'Drill into a specific life domain for a chart using the Bodha synthesis layer.',
    'Returns question lenses from bodha_question_lenses filtered by question_type via the',
    'DOMAIN_TO_QUESTION_TYPES mapping (inverted from bo_drishti.py::QUESTION_TYPE_CONFIG),',
    'and the domain-scoped CDLM cross-domain matrix cells from bodha_cdlm_cells.',
    'CDLM cells include shared_signal_count; shared_signal_ids_array is omitted by default (token-safe).',
    'signal_id_refs emits a capped set of signal IDs (default 200) for downstream hydration.',
    'Use response_format=full to include shared_signal_ids_array per cell and up to 2000 signal refs.',
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
      description: "Ayanamsha to filter by (default: 'lahiri_chitrapaksha').",
    },
    max_signal_refs: {
      type: 'number',
      description: [
        'Max signal IDs to include in signal_id_refs (default 200).',
        'Capped at 2000. Sufficient for downstream temporal-activation filtering.',
        'Use response_format=full to get up to 2000 automatically.',
      ].join(' '),
    },
    response_format: {
      type: 'string',
      description: [
        "Controls payload verbosity. 'default' (or omitted): token-safe —",
        'shared_signal_ids_array omitted from cells, signal_id_refs capped to 200.',
        "'full': shared_signal_ids_array included (capped per cell), signal_id_refs capped to 2000.",
      ].join(' '),
      enum: ['default', 'full'],
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

    const domain          = args['domain'] as string | undefined
    const ayanamsha_id    = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const response_format = (args['response_format'] as string | undefined) ?? 'default'
    const is_full         = response_format === 'full'
    // Default cap: 200 (enough for temporal-activation filter top_k=20 with headroom).
    // Full mode cap: 2000. Hard ceiling either way.
    const max_signal_refs = is_full
      ? 2000
      : Math.min(
          typeof args['max_signal_refs'] === 'number' ? (args['max_signal_refs'] as number) : 200,
          2000,
        )

    const VALID_DOMAINS = ['career', 'wealth', 'relationship', 'health', 'character', 'spirituality', 'other']

    try {
      // Domain discovery is sourced from bodha_cdlm_cells (domain_row/domain_col).
      // bodha_question_lenses has no domain column; lenses are filtered via DOMAIN_TO_QUESTION_TYPES.
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
      // bodha_question_lenses has no domain column; lenses are keyed by question_type.
      // We resolve domain -> question_types via DOMAIN_TO_QUESTION_TYPES and apply
      // a WHERE question_type = ANY($3) filter when the domain has a non-empty mapping.
      // Domain 'other' (or empty mapping) skips the filter and returns all lenses.
      const relevantQuestionTypes = DOMAIN_TO_QUESTION_TYPES[domain] ?? []
      const filterByQuestionType = relevantQuestionTypes.length > 0

      const lensSql = filterByQuestionType
        ? `
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
          AND question_type = ANY($3)
        ORDER BY question_type
        LIMIT 60
      `
        : `
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
        filterByQuestionType
          ? query<Record<string, unknown>>(lensSql, [chart_id, ayanamsha_id, relevantQuestionTypes])
          : query<Record<string, unknown>>(lensSql, [chart_id, ayanamsha_id]),
        query<Record<string, unknown>>(cdlmSql, [chart_id, ayanamsha_id, domain]),
      ])

      // Collect signal refs from CDLM cells and apply bounding.
      // shared_signal_ids_array is stripped from served cells in default mode
      // (shared_signal_count already present; raw IDs available via query_signals).
      const MAX_IDS_PER_CELL_FULL = 50
      const allSignalRefs = new Set<string>()

      const cdlmCells = (cdlmRes.rows as Array<Record<string, unknown>>).map(cell => {
        const ids = Array.isArray(cell['shared_signal_ids_array'])
          ? (cell['shared_signal_ids_array'] as string[])
          : []

        // Accumulate into the global ref set (capped later)
        for (const id of ids) allSignalRefs.add(id)

        if (is_full) {
          // Full mode: include the array but cap per cell to avoid runaway payloads
          return ids.length > MAX_IDS_PER_CELL_FULL
            ? { ...cell, shared_signal_ids_array: ids.slice(0, MAX_IDS_PER_CELL_FULL), shared_signal_ids_truncated: true }
            : cell
        }
        // Default: strip shared_signal_ids_array — shared_signal_count is the useful signal
        const { shared_signal_ids_array: _dropped, ...rest } = cell
        return rest
      })

      const signalRefsTotal = allSignalRefs.size
      const signalRefsArray = Array.from(allSignalRefs).slice(0, max_signal_refs)

      return {
        content: {
          chart_id,
          ayanamsha_id,
          domain,
          question_lenses:        lensRes.rows,
          cdlm_cells:             cdlmCells,
          signal_id_refs:         signalRefsArray,
          signal_id_refs_total:   signalRefsTotal,
          signal_id_refs_capped:  signalRefsArray.length < signalRefsTotal,
          lens_count:             lensRes.rows.length,
          cdlm_cell_count:        cdlmRes.rows.length,
          drill_next:             'marsys://tool/L2/query_signals',
          response_format,
          provenance: {
            tables: ['bodha_question_lenses', 'bodha_cdlm_cells'],
            model_mismatch_note: [
              'bodha_question_lenses has no domain column; lenses are filtered at query-time',
              'via DOMAIN_TO_QUESTION_TYPES (source: bo_drishti.py::QUESTION_TYPE_CONFIG).',
              'Domain \'other\' or unmapped domains return all lenses (no filter).',
              'Signal references derive from CDLM cells only.',
            ].join(' '),
            defect_001_note: [
              'constituent_facts_array in referenced signals has 91.5% orphan rate (DEFECT-001 OPEN).',
              'L1 fact joins via signal references will be empty for most signals until L2 rebuild.',
            ].join(' '),
            bounding_note: is_full
              ? `response_format=full: shared_signal_ids_array included (capped ${MAX_IDS_PER_CELL_FULL}/cell), signal_id_refs capped at ${max_signal_refs}.`
              : `response_format=default: shared_signal_ids_array omitted from cells (use shared_signal_count); signal_id_refs capped at ${max_signal_refs} of ${signalRefsTotal} total.`,
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
