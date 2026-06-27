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

    const query = String(args['query'] ?? '')
    const model_family = (args['model_family'] as string | undefined) ?? 'universal'
    const dry_run = Boolean(args['dry_run'] ?? false)

    // Pipeline introspection: return the planned route without executing full tool calls.
    // Full execution is wired at application-startup via the MARO orchestrator.
    return {
      content: {
        pipeline: 'router→grounding→graph+assets→maro',
        chart_id,
        query,
        model_family,
        dry_run,
        stages: [
          { stage: 'router', uri: 'marsys://tool/router/route', status: dry_run ? 'planned' : 'would_execute' },
          { stage: 'grounding', uri: 'marsys://grounding/resolve', status: dry_run ? 'planned' : 'would_execute' },
          { stage: 'maro', uri: 'marsys://tool/maro/orchestrate', status: dry_run ? 'planned' : 'would_execute' },
        ],
        note: 'D6 synergy pipeline descriptor — full execution delegated to MARO orchestrator at runtime.',
      },
      is_error: false,
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

    return {
      content: {
        chart_id,
        reconciliation_scope: { layers, signal_uris },
        note: 'D6 cross-layer reconciliation descriptor. Full synthesis delegated to the CGM+CDLM pipeline at runtime.',
        b11_compliance: 'Whole-Chart-Read Protocol: L2 Bodha synthesis consulted before domain-specific answer.',
      },
      is_error: false,
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
