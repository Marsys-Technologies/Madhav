/**
 * D2 Router — Capability Registration (per-wave file)
 * =====================================================
 * GATE A compliance: this is the per-wave registration file for D2.
 * It does NOT edit registry/index.ts or registry/types.ts.
 * It registers the router's own meta-capability into the registry
 * via the append-only pattern described in the parallel coordination brief.
 *
 * This file exports a single `registerRouterCapabilities()` function
 * that callers invoke at startup. It has no side effects at import time.
 *
 * What is registered here:
 * - `marsys://tool/router/route` — the routing meta-tool (for D3/D8 introspection)
 *
 * The router itself is NOT a tool that LLMs call; it is an internal component.
 * This registration makes the router discoverable by the D8 eval harness
 * and the integration smoke test.
 */

import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'
import { route } from '../../router/router'
import type { RouteInput, RouteClass } from '../../router'

/**
 * The router meta-capability — not LLM-facing, but introspectable by D3/D8.
 * scope=global because the router is chart-agnostic at the meta level
 * (chart_id is injected per-call by D3, not stored in the descriptor).
 */
const routerMetaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/router/route',
  type: 'tool',
  layer: 'L0',
  name: 'route',
  scope: 'global',

  description: [
    'Internal D2 query router. Classifies a query into one of five route classes',
    '(numeric_exact, relational, narrative, simple, multi_hop) and selects the',
    'appropriate tool chain from the registry. chart_id must be supplied per call.',
    'Not LLM-facing — consumed by the grounding spine (D3) and eval harness (D8).',
  ].join(' '),

  input_schema: {
    query: {
      type: 'string',
      description: 'The natural-language query to classify and route',
      required: true,
    },
    chart_id: {
      type: 'string',
      description: 'Chart UUID (required; never defaulted)',
      required: true,
    },
    lel_enabled: {
      type: 'boolean',
      description: 'Whether LEL signals are enabled (default: false)',
      required: false,
    },
    budget_usd: {
      type: 'number',
      description: 'Budget ceiling in USD for this query (default: per route class)',
      required: false,
    },
    force_route_class: {
      type: 'string',
      description: "Override: force a specific route class ('numeric_exact'|'relational'|'narrative'|'simple'|'multi_hop')",
      required: false,
    },
  },

  required_inputs: ['query', 'chart_id'],

  // D1 topology fields (FROZEN contract)
  archetype: 'orientation_digest',   // Router is an orchestration/orientation surface
  traversal_level: 'L-ORIENT',       // Entry point — analogous to the orientation layer
  tool_role: 'umbrella',             // Router is the umbrella that fans out to all others
  emits_references: true,            // Returns tool URIs (references) not raw facts
  lel_capable: false,                // Router itself doesn't touch LEL data
  grounds_to: undefined,

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  async handler(args: Record<string, unknown>) {
    const chart_id = args['chart_id']
    if (!chart_id || typeof chart_id !== 'string') {
      return {
        content: { error: 'chart_id is required' },
        is_error: true,
      }
    }

    const input: RouteInput = {
      query: String(args['query'] ?? ''),
      chart_id,
      hints: {
        lel_enabled: Boolean(args['lel_enabled'] ?? false),
        budget_usd: args['budget_usd'] !== undefined
          ? Number(args['budget_usd'])
          : undefined,
        force_route_class: args['force_route_class'] as RouteClass | undefined,
      },
    }

    try {
      const result = await route(input)
      return {
        content: {
          route_class: result.route_class,
          traversal_level: result.traversal_level,
          primary_tool: result.primary_tool,
          planned_tool_uris: result.trajectory.planned_tool_uris,
          umbrella_then_drill: result.umbrella_then_drill,
          budget: result.budget,
          routing_method: result.trajectory.routing_method,
          rule_fired: result.trajectory.rule_fired,
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err) },
        is_error: true,
      }
    }
  },
}

/**
 * Register D2 router capabilities.
 * Call at application startup (after registry is initialized).
 */
export function registerRouterCapabilities(): void {
  registerCapability(routerMetaCapability)
}
