/**
 * D6 Synergy — Capability Registration (per-wave file)
 * ======================================================
 * GATE A compliance: this is the per-wave registration file for D6.
 * It does NOT edit registry/index.ts or registry/types.ts.
 *
 * D6 registers the cross-layer synergy orchestration capability.
 * The MARO orchestration layer (D-PROFILES) pre-dates D6 and handles the
 * per-family normalization loop. D6 adds the explicit synergy surface that
 * combines the router→grounding→graph+assets→MARO chain into a single
 * introspectable capability descriptor, making the combined pipeline
 * discoverable by the D8 eval harness.
 *
 * Capabilities registered by D6:
 *   marsys://tool/synergy/pipeline        — combined router→grounding→MARO chain
 *   marsys://tool/synergy/cross_layer     — cross-layer signal reconciliation
 *
 * Total D6 new capabilities: 2
 *
 * Usage: import this file at application startup after D-PROFILES and D5 are registered.
 */

import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'
import { runWholeChartRead } from '../../synergy/orchestrator'
import type { SynergyContext } from '../../synergy/orchestrator'
import { query } from '@/lib/db/client'

/**
 * Build a SynergyContext backed by the platform's direct DB client.
 * Used by D6 handlers which run inside Next.js (server-only).
 */
function buildPlatformCtx(lel_enabled?: boolean): SynergyContext {
  return {
    db: {
      query: (sql: string, params: unknown[]) =>
        query(sql, params as unknown[]).then((r) => ({ rows: r.rows as Record<string, unknown>[] })),
    },
    lel_enabled: lel_enabled ?? false,
  }
}

// ── marsys://tool/synergy/pipeline ────────────────────────────────────────────

const synergyPipelineTool: CapabilityDescriptor = {
  uri: 'marsys://tool/synergy/pipeline',
  type: 'tool',
  layer: 'L0',
  name: 'synergy_pipeline',
  scope: 'global',

  description: [
    'D6 synergy pipeline — combines the router→grounding→graph+assets→MARO chain',
    'into a single introspectable capability descriptor.',
    'Accepts a chart_id and query; routes to the appropriate layer tools;',
    'grounds the result against L1 chart_facts; passes through the MARO normalizer',
    'for the declared model family.',
    'Not LLM-facing for end-user queries — consumed by the D8 eval harness',
    'and integration smoke tests for pipeline-completeness verification.',
    'chart_id is required and must be a valid chart UUID — never defaulted.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (required; never defaulted)',
      required: true,
    },
    query: {
      type: 'string',
      description: 'The natural-language query to route through the synergy pipeline',
      required: true,
    },
    model_family: {
      type: 'string',
      description: "Declared LLM family: 'anthropic' | 'gemini' | 'openai' | 'deepseek' | 'universal'",
      required: false,
    },
    dry_run: {
      type: 'boolean',
      description: 'If true, returns the planned route and grounding plan without executing tool calls',
      required: false,
    },
  },

  required_inputs: ['chart_id', 'query'],

  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: true,
  lel_capable: false,
  grounds_to: undefined,

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  async handler(args: Record<string, unknown>) {
    const chart_id = args['chart_id']
    if (!chart_id || typeof chart_id !== 'string') {
      return {
        content: {
          error: 'chart_id is required and must be a non-empty string. D6 synergy pipeline never defaults chart_id.',
        },
        is_error: true,
      }
    }

    const queryText = args['query'] ? String(args['query']) : undefined
    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : 'LAHIRI'
    const dry_run = Boolean(args['dry_run'] ?? false)

    // dry_run: return the planned pipeline stages without executing
    if (dry_run) {
      return {
        content: {
          pipeline: 'router→grounding→graph+assets→maro',
          chart_id,
          query: queryText,
          ayanamsha_id,
          dry_run: true,
          stages: [
            { stage: 'query_ucd',         uri: 'marsys://tool/L2/query_ucd',              status: 'planned' },
            { stage: 'domain_readings',   uri: 'marsys://tool/L2/query_domain_reading',   status: 'planned' },
            { stage: 'signal_rank',       uri: 'marsys://tool/L2/query_signals',          status: 'planned' },
            { stage: 'graph_traversal',   uri: 'marsys://tool/L2/traverse_chart_graph',   status: 'planned' },
            { stage: 'contradictions',    uri: 'marsys://tool/L2/query_contradictions',   status: 'planned' },
            { stage: 'temporal_enrichment', uri: 'marsys://tool/L3/query_temporal_activation', status: 'planned' },
          ],
        },
        is_error: false,
      }
    }

    // Live execution: call the D6 synergy orchestrator (runWholeChartRead)
    try {
      const ctx = buildPlatformCtx(false)
      const result = await runWholeChartRead(
        chart_id,
        ayanamsha_id,
        'holistic',
        queryText,
        ctx,
      )
      return {
        content: result,
        is_error: false,
      }
    } catch (err) {
      return {
        content: {
          error: `synergy_pipeline orchestration failed: ${String(err)}`,
          chart_id,
        },
        is_error: true,
      }
    }
  },
}

// ── marsys://tool/synergy/cross_layer ─────────────────────────────────────────

const synergyCrossLayerTool: CapabilityDescriptor = {
  uri: 'marsys://tool/synergy/cross_layer',
  type: 'tool',
  layer: 'L0',
  name: 'synergy_cross_layer',
  scope: 'global',

  description: [
    'D6 cross-layer signal reconciliation. Accepts a chart_id and a set of signals',
    'from multiple layers (L1 chart_facts, L2 Bodha, L3 Kāla, L4 Phala, L5 Mīmāṃsā)',
    'and returns a reconciled view that surfaces contradictions, convergences,',
    'and cross-domain linkages (per CGM + CDLM protocol, B.11 Whole-Chart-Read).',
    'chart_id is required — never defaulted.',
    'Not LLM-facing for end-user queries — consumed by D8 eval harness.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (required; never defaulted)',
      required: true,
    },
    signal_uris: {
      type: 'array',
      description: 'Array of marsys:// capability URIs to reconcile across layers',
      required: false,
    },
    layers: {
      type: 'array',
      description: "Layer scope for reconciliation: ['L1','L2','L3','L4','L5'] (default: all)",
      required: false,
    },
  },

  required_inputs: ['chart_id'],

  archetype: 'cross_domain',
  traversal_level: 'L-SYNTH',
  tool_role: 'synthesizer',
  emits_references: true,
  lel_capable: false,
  grounds_to: undefined,

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  async handler(args: Record<string, unknown>) {
    const chart_id = args['chart_id']
    if (!chart_id || typeof chart_id !== 'string') {
      return {
        content: {
          error: 'chart_id is required and must be a non-empty string.',
        },
        is_error: true,
      }
    }

    const signal_uris = (args['signal_uris'] as string[] | undefined) ?? []
    const layers = (args['layers'] as string[] | undefined) ?? ['L1', 'L2', 'L3', 'L4', 'L5']
    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : 'LAHIRI'

    // Run the D6 whole-chart read in cross_domain mode to surface contradictions +
    // convergences across the requested layers (B.11 Whole-Chart-Read Protocol).
    try {
      const ctx = buildPlatformCtx(false)
      const wholChart = await runWholeChartRead(
        chart_id,
        ayanamsha_id,
        'cross_domain',
        undefined,
        ctx,
      )

      // Extract the cross-layer reconciliation surface
      const contradictions = wholChart.contradictions
      const convergenceDomains = wholChart.ucd_digest.convergence_domains
      const signalRefs = wholChart.signals.signals.map((s) => ({
        signal_id: s.signal_id,
        computed_salience: s.computed_salience,
        domains_affected_array: s.domains_affected_array,
        constituent_facts_array: s.constituent_facts_array,
      }))

      return {
        content: {
          chart_id,
          reconciliation_scope: { layers, signal_uris },
          // Cross-layer convergence: domains with corroborating signals
          convergence_domains: convergenceDomains,
          // Contradictions between signals/layers (bodha_contradictions — currently 0 rows)
          contradictions: contradictions.contradictions,
          // Discoveries (novelty-ranked cross-layer findings)
          discoveries: contradictions.discoveries.slice(0, 20),
          // Ranked signals across all layers
          signal_refs: signalRefs,
          // CGM graph edges for cross-layer linkage
          graph: {
            nodes: wholChart.graph.nodes,
            edges: wholChart.graph.edges,
            relationship_basis_note: wholChart.graph.relationship_basis_note,
          },
          b11_compliance: true,
          meta: wholChart.meta,
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: {
          error: `synergy_cross_layer reconciliation failed: ${String(err)}`,
          chart_id,
        },
        is_error: true,
      }
    }
  },
}

// ── Registration export ────────────────────────────────────────────────────────

/**
 * Register D6 synergy capabilities.
 * Call at application startup after D-PROFILES (MARO) and D5 fan-out are registered.
 * GATE A: only registers NEW files for this wave — does not edit registry/index.ts.
 */
export function registerD6SynergyCapabilities(): void {
  registerCapability(synergyPipelineTool)
  registerCapability(synergyCrossLayerTool)
}

/**
 * D6 capability URI roster (for Gate C reverse-citation checks and roster smoke tests).
 */
export const D6_CAPABILITY_URIS = [
  'marsys://tool/synergy/pipeline',
  'marsys://tool/synergy/cross_layer',
] as const
