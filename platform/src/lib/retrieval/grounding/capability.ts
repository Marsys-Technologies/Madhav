/**
 * D3 Grounding Spine — Capability Registration (per-wave, Gate A)
 * ================================================================
 * Per the parallel-coordination brief §2 (GATE A):
 *   - This wave ONLY registers via its own per-wave file (this file).
 *   - The central registry/index.ts is OFF LIMITS to parallel agents.
 *   - Capabilities are registered here; the central index imports this module.
 *
 * Exposes two capabilities:
 *   1. marsys://tool/D3/resolve_signals  — grounding a batch of signals to L1 facts
 *   2. marsys://tool/D3/resolve_metric   — resolving a single governed metric
 */

import type { CapabilityDescriptor } from '../registry/types'
import { resolveSignals, resolveMetric } from './resolver'
import { makeLiveDbProxy } from './db_proxy'

// ── Capability 1: resolve_signals ─────────────────────────────────────────────

/**
 * Grounding tool: resolves a set of MSR signal_ids to their L1 facts.
 *
 * Used by:
 *   - Retrieval pipeline (after a signal query, before presenting to LLM)
 *   - Any tool that needs to present cited numeric facts alongside signals
 *
 * emits_references=true: returns signal_id + fact_id refs, not restated facts.
 * grounds_to.l1_fact_ids=true: the output resolves to chart_facts.fact_id.
 */
export const resolveSignalsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/D3/resolve_signals',
  type: 'tool',
  layer: 'L2',
  name: 'resolve_signals',

  description: [
    'Resolves a set of MSR signal_ids for a chart to their constituent L1 facts.',
    'Returns each signal paired with its resolved chart_facts rows (the authoritative L1 source).',
    'Identifies §N.5 violations: fact_ids in constituent_facts_array that are absent from chart_facts.',
    'Use this tool to obtain cited L1 facts before presenting any numeric or computed claims.',
    'chart_id is required — this tool is strictly chart-scoped.',
    'Missing signals are reported in not_found_signal_ids, not silently dropped.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required — grounding spine is chart-scoped.',
      required: true,
    },
    signal_ids: {
      type: 'array',
      description: 'List of bodha_msr_signals signal_id UUIDs to resolve (1–100 per call).',
      items: { type: 'string' },
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (e.g. 'LAHIRI'). Optional — omit to accept any ayanamsha.",
      required: false,
    },
  },

  required_inputs: ['chart_id', 'signal_ids'],
  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: {
    l1_fact_ids: true,
    l0_citation_ids: true,
  },
  lel_capable: false,

  llm_hints: {
    agentic: {
      cost_class: 'medium',
      cacheable: true,
      max_retries: 2,
    },
    bulk_context: {
      pre_fetch_priority: 80,
    },
  },

  async handler(args, _ctx) {
    const chart_id = args['chart_id'] as string
    const signal_ids = args['signal_ids'] as string[]
    const ayanamsha_id = args['ayanamsha_id'] as string | undefined

    const db = makeLiveDbProxy()
    const outcome = await resolveSignals(db, chart_id, signal_ids, ayanamsha_id)

    if (!outcome.ok) {
      return {
        content: {
          error_code: outcome.error.error_code,
          message: outcome.error.message,
        },
        is_error: true,
      }
    }

    return {
      content: outcome.result,
      is_error: false,
    }
  },
}

// ── Capability 2: resolve_metric ──────────────────────────────────────────────

/**
 * Governed metric resolver: returns a single numeric metric for a signal or fact.
 *
 * This tool enforces principle #3 (cite-don't-regenerate):
 *   - The LLM selects from a governed vocabulary (GOVERNED_METRICS).
 *   - The resolver fetches the deterministic DB value.
 *   - Out-of-vocabulary requests return an error, never a fabricated number.
 *
 * emits_references=true: the result carries the source_id + source_table + citation.
 */
export const resolveMetricCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/D3/resolve_metric',
  type: 'tool',
  layer: 'L2',
  name: 'resolve_metric',

  description: [
    'Resolves a single governed numeric metric for a signal (bodha_msr_signals) or fact (chart_facts).',
    'Valid metrics: computed_salience, dignity_score, shadbala_norm, deterministic_strength,',
    'orb_tightness, top_k_salience_rank, verification_certainty, house_weight_multiplier,',
    'ashtakavarga_support_multiplier, vargottama_amplification, argala_modifier,',
    'neechabhanga_modifier, cross_ayanamsha_consistency_score, fact_value_num.',
    'Out-of-vocabulary metric requests return an error — numeric values are never fabricated.',
    'chart_id is required — grounding spine is strictly chart-scoped.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    metric: {
      type: 'string',
      description:
        'Governed metric name. Must be one of the documented metric vocabulary. ' +
        'Out-of-vocabulary metrics are rejected with OUT_OF_VOCAB error.',
      required: true,
    },
    source_id: {
      type: 'string',
      description:
        'The signal_id (UUID) for signal metrics, or the fact_id (hex string) for fact_value_num.',
      required: true,
    },
  },

  required_inputs: ['chart_id', 'metric', 'source_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: {
    l1_fact_ids: true,
  },
  lel_capable: false,

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
  },

  async handler(args, _ctx) {
    const chart_id = args['chart_id'] as string
    const metric = args['metric'] as string
    const source_id = args['source_id'] as string

    const db = makeLiveDbProxy()
    const outcome = await resolveMetric(db, chart_id, metric, source_id)

    if (!outcome.ok) {
      return {
        content: {
          error_code: outcome.error.error_code,
          message: outcome.error.message,
          requested_metric: outcome.error.requested_metric,
        },
        is_error: true,
      }
    }

    return {
      content: outcome.metric,
      is_error: false,
    }
  },
}

// ── Wave registration exports ─────────────────────────────────────────────────

/**
 * All D3 grounding spine capabilities.
 * Import this array in the central registry to register the wave's capabilities.
 *
 * Gate A (parallel-coordination brief §2): callers import THIS array, not
 * the central index directly. The central registry/index.ts is not edited by
 * this wave.
 */
export const D3_GROUNDING_CAPABILITIES: CapabilityDescriptor[] = [
  resolveSignalsCapability,
  resolveMetricCapability,
]
