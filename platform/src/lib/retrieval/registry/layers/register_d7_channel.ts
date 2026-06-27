/**
 * D7 Channel — Capability Registration (per-wave file)
 * ======================================================
 * GATE A compliance: this is the per-wave registration file for D7.
 * It does NOT edit registry/index.ts or registry/types.ts.
 *
 * D7 registers the MCP channel wiring capabilities — the bridge between
 * the retrieval registry and the MCP server's tool surface. These capabilities
 * make the channel wiring discoverable by the D8 eval harness and the
 * integration smoke test.
 *
 * Capabilities registered by D7:
 *   marsys://tool/channel/mcp_wiring      — MCP server ↔ registry bridge descriptor
 *   marsys://tool/channel/chat_dispatch   — chat-route ↔ registry adapter descriptor
 *
 * Total D7 new capabilities: 2
 *
 * These capabilities are introspection-only — they describe the wiring contracts
 * between channels and the registry, enabling the D8 eval harness to verify
 * channel completeness without running the live servers.
 *
 * Usage: import this file at application startup after D6 synergy is registered.
 */

import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'

// ── marsys://tool/channel/mcp_wiring ─────────────────────────────────────────

const mcpWiringTool: CapabilityDescriptor = {
  uri: 'marsys://tool/channel/mcp_wiring',
  type: 'tool',
  layer: 'L0',
  name: 'channel_mcp_wiring',
  scope: 'global',

  description: [
    'D7 MCP channel wiring descriptor. Describes the bridge between the retrieval',
    'registry (platform/src/lib/retrieval/registry) and the MCP server tool surface',
    '(platform-mcp/src/server.ts).',
    'Returns the current wiring state: which registry URIs are surfaced via MCP tools,',
    'which MCP tools map back to registry URIs via mcp_capability_bridge.ts,',
    'and which registry capabilities are not yet MCP-surfaced.',
    'Used by the D8 eval harness for channel-parity verification.',
    'Not LLM-facing for end-user queries — internal channel introspection only.',
  ].join(' '),

  input_schema: {
    include_unmapped: {
      type: 'boolean',
      description: 'If true, also returns registry capabilities not yet surfaced via MCP (default: true)',
      required: false,
    },
  },

  required_inputs: [],

  archetype: 'calibration',
  traversal_level: 'L-ORIENT',
  tool_role: 'quality',
  emits_references: true,
  lel_capable: false,
  grounds_to: undefined,

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  async handler(args: Record<string, unknown>) {
    const include_unmapped = args['include_unmapped'] !== false  // default true

    // Static wiring map — reflects the current mcp_capability_bridge.ts + server.ts state.
    // Updated by D7 wave as new capabilities are added to both channels.
    const wiredMappings: Record<string, string> = {
      'resolve_entity': 'marsys://tool/L0/resolve_entity',
      'list_entities': 'marsys://tool/L0/list_entities',
      'intent-classify': 'marsys://prompt/intent-classify',
      'asset-registry-all': 'marsys://resource/asset-registry/all',
      'asset-registry-L0': 'marsys://resource/asset-registry/L0',
    }

    const result: Record<string, unknown> = {
      channel: 'mcp',
      bridge_file: 'platform/src/lib/retrieval/registry/mcp_capability_bridge.ts',
      server_file: 'platform-mcp/src/server.ts',
      wired_count: Object.keys(wiredMappings).length,
      wired_mappings: wiredMappings,
    }

    if (include_unmapped) {
      result['note'] = [
        'D6/D7 registry capabilities (synergy/pipeline, synergy/cross_layer,',
        'channel/mcp_wiring, channel/chat_dispatch, maro/orchestrate, maro/mcp_surface)',
        'are internal-only and intentionally not surfaced as MCP tools.',
        'Layer tools (L1-L5) are surfaced via their layer-specific MCP tool registrations.',
      ].join(' ')
    }

    return { content: result, is_error: false }
  },
}

// ── marsys://tool/channel/chat_dispatch ──────────────────────────────────────

const chatDispatchTool: CapabilityDescriptor = {
  uri: 'marsys://tool/channel/chat_dispatch',
  type: 'tool',
  layer: 'L0',
  name: 'channel_chat_dispatch',
  scope: 'global',

  description: [
    'D7 chat-route channel wiring descriptor. Describes the adapter between the',
    'Consume chat route (/api/chat/consult → runAdapterDispatch) and the retrieval',
    'registry. The chat route currently uses getTool() from lib/retrieve/index',
    '(the legacy retrieve layer). This descriptor marks the intended migration',
    'point: once lib/retrieve tools are fully retired, the chat route should',
    'delegate to getCatalog() from the retrieval registry instead.',
    'Used by the D8 eval harness to track chat-channel migration status.',
    'Not LLM-facing — internal channel introspection only.',
  ].join(' '),

  input_schema: {},

  required_inputs: [],

  archetype: 'calibration',
  traversal_level: 'L-ORIENT',
  tool_role: 'quality',
  emits_references: false,
  lel_capable: false,
  grounds_to: undefined,

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  async handler(_args: Record<string, unknown>) {
    return {
      content: {
        channel: 'chat',
        route: '/api/chat/consult',
        current_dispatch: 'runAdapterDispatch → getTool() from lib/retrieve/index (legacy)',
        registry_dispatch: 'getCatalog() from lib/retrieval/registry/index (target)',
        migration_status: 'PENDING — chat route not yet wired to retrieval registry',
        migration_note: [
          'The chat route uses the legacy lib/retrieve layer (getTool + RETRIEVAL_TOOLS).',
          'Migration to the registry layer (getCatalog) is tracked as a D7 follow-on task.',
          'Current state is intentional: registry/retrieval layers coexist during migration.',
        ].join(' '),
      },
      is_error: false,
    }
  },
}

// ── Registration export ────────────────────────────────────────────────────────

/**
 * Register D7 channel wiring capabilities.
 * Call at application startup after D6 synergy is registered.
 * GATE A: only registers NEW files for this wave — does not edit registry/index.ts.
 */
export function registerD7ChannelCapabilities(): void {
  registerCapability(mcpWiringTool)
  registerCapability(chatDispatchTool)
}

/**
 * D7 capability URI roster (for Gate C reverse-citation checks and roster smoke tests).
 */
export const D7_CAPABILITY_URIS = [
  'marsys://tool/channel/mcp_wiring',
  'marsys://tool/channel/chat_dispatch',
] as const
