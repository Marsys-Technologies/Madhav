/**
 * synthesis/capability.ts — the Large-N instrument as a served capability
 * ========================================================================
 * WP-1.4 (LCA-15 / R-48). Exposes composeLargeN as a registered retrieval capability so
 * the pre-aggregated L2 surfaces finally HAVE a consumer over the deployed channel (the
 * audit's core indictment: "the L2 pre-computation exists precisely for this and nothing
 * consumes it"). Conforms to the WP-1.5 envelope contract: declared coverage, honest
 * per-family totals + more_available (built in the instrument), YYYY-MM-DD as_of date.
 *
 * archetype 'cross_domain' / traversal 'L-SYNTH' / role 'synthesizer' — it is the cross-
 * layer synthesizer the D1 topology reserves this role for.
 */

import type { CapabilityDescriptor } from '../registry/types'
import { buildRetrievalEnvelope, buildCoverageStamp, resolveEnvelopeFormat } from '../envelope'
import { composeLargeN } from './instrument'

export const synthComposeLargeNCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/synthesis/compose_large_n',
  type:  'tool',
  layer: 'L2',
  name:  'compose_large_n',

  description: [
    'Large-N synthesis instrument (WP-1.4 / LCA-15). Composes a compound, Lane-7-heavy',
    'question ("map the whole marriage universe", "what does the chart say about moksha")',
    'by STAGED retrieval-with-aggregation, NOT a flat top-K wall: (1) decomposes the',
    'question into an evidence contract; (2) plans against PRE-AGGREGATED L2 surfaces first',
    '(gestalt verdict map, CDLM cross-domain cells, CGM dispositor paths); (3) map-reduces',
    'atomic signal families under a running budget (bounded — never dumps the 12k+ career',
    'signals); (4) returns a narrative with a DERIVATION LEDGER (every claim → resolvable',
    'signal_ids/fact_ids, §N.5). Thin stages are DISCLOSED, never fabricated (B.10).',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    question:     { type: 'string', description: 'The compound question to compose. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default 'lahiri_chitrapaksha')." },
    total_signal_rows: { type: 'number', description: 'Whole-answer atomic-signal budget (default 60).' },
    per_family_cap:    { type: 'number', description: 'Per-family exemplar cap (default 10).' },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-SYNTH',
  tool_role: 'synthesizer',
  emits_references: true,
  grounds_to: { l1_fact_ids: true, l0_citation_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'expensive', cacheable: true, requires_cot: true },
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }
    const question = args['question'] ? String(args['question']) : ''
    if (!question) return { content: { error: 'question is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : undefined
    const budget: Record<string, number> = {}
    if (args['total_signal_rows'] != null) budget['total_signal_rows'] = Number(args['total_signal_rows'])
    if (args['per_family_cap'] != null) budget['per_family_cap'] = Number(args['per_family_cap'])

    try {
      const answer = await composeLargeN({
        chart_id, question, ayanamsha_id,
        budget: Object.keys(budget).length > 0 ? budget : undefined,
      })

      // WP-1.5 coverage stamp: the composed answer is a bounded slice of the total evidence
      // universe. `served` = atomic rows actually composed; `total` = the sum of disclosed
      // family sizes (the real N-hundred+ the question spans). Honest, never fabricated.
      const totalUniverse = answer.families.reduce((n, f) => n + f.total_in_family, 0)
      const coverage = buildCoverageStamp(
        `large_n_synthesis[primary=${answer.contract.primary_domain}]`,
        answer.budget.total_signal_rows_served,
        totalUniverse,
      )

      const format = resolveEnvelopeFormat(args['response_format'])
      const envelope = buildRetrievalEnvelope({
        tool: 'compose_large_n',
        content: answer,
        query_class: 'per_chart_synthesis',
        insight_type: 'large_n_composition',
        coverage,
        grounding: {
          fact_ids: Array.from(new Set(answer.derivation_ledger.flatMap(e => e.fact_ids))),
          citations: [],
          grounding_score: null,
        },
        pagination: {
          offset: 0,
          limit: answer.budget.total_signal_rows_cap,
          total: totalUniverse,
          next_cursor: null,
          more_available: answer.budget.total_signal_rows_served < totalUniverse,
        },
      }, format)

      return { content: envelope, is_error: false }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
