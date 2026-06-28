/**
 * query_manifestation_grammar — Manifestation Grammar (L5 Mīmāṃsā)
 * ===================================================================
 * Queries mimamsa_manifestation_grammar (mi_sambandha) — count unknown, per_chart.
 * Returns per-native grammar of how each signal/house/karaka expresses:
 *   structural cells (classical prediction) + empirical cells (observed expression).
 *
 * emits_references: true (signal_id back to bo_laksana/bodha_msr_signals).
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryManifestationGrammarCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_manifestation_grammar',
  type:  'tool',
  layer: 'L5',
  name:  'query_manifestation_grammar',

  description: [
    'Returns the manifestation grammar for a chart from mimamsa_manifestation_grammar (mi_sambandha).',
    'Per-native grammar: how each origin (signal/house/karaka) actually expresses through channels in this chart.',
    'Each row carries channel propensity (fire_count/opportunity_count → channel_propensity) vs prior_propensity, with propensity_delta.',
    'Useful for calibrating interpretation models against lived reality.',
    'emits_references: origin_ref references back to bodha_msr_signals.',
    'Filter by origin_kind, origin_ref, or domain to narrow scope.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    origin_kind: {
      type: 'string',
      description: 'Filter by origin kind (signal, house, karaka, composite_state, etc.).',
    },
    origin_ref: {
      type: 'string',
      description: 'Filter by specific origin reference id (e.g. signal_id back to bodha_msr_signals).',
    },
    domain: {
      type: 'string',
      description: 'Filter by life domain (career, wealth, relationship, health, etc.).',
    },
    top_k: {
      type: 'number',
      description: 'Max rows to return (default: 50, max: 500).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 15 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const origin_kind = args['origin_kind'] as string | undefined
    const origin_ref  = args['origin_ref'] as string | undefined
    const domain      = args['domain'] as string | undefined
    const top_k       = Math.min(Number(args['top_k'] ?? 50), 500)

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (origin_kind) { conds.push(`origin_kind = $${p++}`); params.push(origin_kind) }
      if (origin_ref)  { conds.push(`origin_ref = $${p++}`);  params.push(origin_ref) }
      if (domain)      { conds.push(`domain = $${p++}`);      params.push(domain) }

      params.push(top_k)

      const sql = `
        SELECT origin_kind, origin_ref, channel_id, domain,
               fire_count, opportunity_count, channel_propensity,
               prior_propensity, propensity_delta, n_support,
               confidence_band, evidence_grade, citation_ref,
               grammar_formula_version, updated_at
        FROM mimamsa_manifestation_grammar
        WHERE ${conds.join(' AND ')}
        ORDER BY channel_propensity DESC NULLS LAST
        LIMIT $${p}
      `

      const result = await query(sql, params)
      const originRefs = [...new Set(
        (result.rows as Array<{ origin_ref?: string }>).map(r => r.origin_ref).filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id,
          grammar_rows:  result.rows,
          row_count:     result.rows.length,
          origin_refs:   originRefs,
          filters: { origin_kind, origin_ref, domain, top_k },
          provenance: { tables: ['mimamsa_manifestation_grammar'] },
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
