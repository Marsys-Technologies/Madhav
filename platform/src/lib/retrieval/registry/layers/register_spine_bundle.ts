/**
 * register_spine_bundle.ts — query_spine_bundle capability (W5 Lane L5, plan §8
 * item 11 "Spine bundles as first-class capabilities on all profiles").
 *
 * Cross-layer capability (spans L2 signal → L3 activation → L4 anchors →
 * L5 calibration) — tagged `layer: 'L2'` (the chain's root layer) with a
 * `L-SPINE` URI segment, following the same precedent as other cross-layer
 * single-file capabilities in this directory (register_d8_assess_domain.ts's
 * `marsys://tool/L-DOMAIN/...`, register_d9_judgment.ts's `marsys://tool/L-JUDGMENT/...`).
 *
 * Serving mechanism: reads the persisted `bodha_spine_bundles` materialized row
 * when fresh (see platform/src/lib/retrieval/spine/materialize.ts for the full
 * post-build-hook + lazy-fallback design), falling back to a live recompute+persist
 * when the row is missing or stale relative to the chart's current build state.
 * The `source` field on every response discloses which path served the caller —
 * never silently presented as always-live or always-cached.
 */

import type { CapabilityDescriptor } from '../types'
import { registerCapability } from '../index'
import { getOrMaterializeSpineBundle } from '../../spine/materialize'
import { DEFAULT_AYANAMSHA } from '../constants'
import { DEFAULT_SPINE_TOP_K, MAX_SPINE_TOP_K, SPINE_DOMAINS } from '../../spine/constants'

export const querySpineBundleCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-SPINE/query_spine_bundle',
  type: 'tool',
  layer: 'L2',
  name: 'query_spine_bundle',

  description: [
    'Returns the pre-joined "spine bundle" for one domain of a chart: the chain',
    'signal (bodha_msr_signals) → its activation windows (kala_activation) →',
    'its phala anchors (phala_anchors) → the chart\'s calibration scorecard',
    '(mimamsa_calibration/mimamsa_multipliers, filtered to this domain).',
    'This is the single-call replacement for the 3-5 separate calls (query_signals,',
    'query_temporal_activation, query_predictive_anchors, query_calibration) that',
    'answering a cross-layer question previously required.',
    'Served from a post-build materialized view when fresh; the `source` field',
    'discloses whether this response came from the persisted view or a live',
    'recompute (missing/stale row) — never silently presented as always-cached.',
    'Drill further into any one layer with the four capabilities named above.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-SYNTH',
  tool_role: 'synthesizer',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L2/query_signals',
    'marsys://tool/L3/query_temporal_activation',
    'marsys://tool/L4/query_predictive_anchors',
    'marsys://tool/L5/query_calibration',
  ],

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    domain: {
      type: 'string',
      description: `Domain to bundle. One of: ${SPINE_DOMAINS.join(', ')}. Default: 'career'.`,
      enum: [...SPINE_DOMAINS],
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'lahiri_chitrapaksha').",
    },
    top_k: {
      type: 'number',
      description: `Max signals in the bundle (default: ${DEFAULT_SPINE_TOP_K}, max: ${MAX_SPINE_TOP_K}).`,
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 9,
    },
  },

  density_contract: {
    paginated: false,
    facets: ['domain', 'ayanamsha_id', 'top_k'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, ctx?: import('../types').CapabilityContext) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }
    const domain = (args['domain'] as string | undefined) ?? 'career'
    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const top_k = args['top_k'] !== undefined ? Number(args['top_k']) : undefined

    try {
      const result = await getOrMaterializeSpineBundle({ chart_id, domain, ayanamsha_id, top_k }, ctx)
      return {
        content: {
          ...result.bundle,
          source: result.source,
          computed_at: result.computed_at,
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: err instanceof Error ? err.message : String(err), chart_id },
        is_error: true,
      }
    }
  },
}

registerCapability(querySpineBundleCapability)
