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
 * D7 GAP FILL (2026-06-28 — chat-channel migration, §2):
 * Five lib/retrieve tools had no registry equivalent; they are ported here
 * per the D1 contract (chart_id required where per_chart, tier stripped,
 * emits_references set correctly). Covered by RETRIEVAL_D7_GAP_REPORT_v1_0.md.
 *
 * Capabilities registered by D7:
 *   marsys://tool/channel/mcp_wiring        — MCP server ↔ registry bridge descriptor
 *   marsys://tool/channel/chat_dispatch     — chat-route ↔ registry adapter descriptor
 *   marsys://tool/L0/query_sutravali_rules          — sutravali flexible JSONB query (gap fill)
 *   marsys://tool/L0/query_sutravali_rules_for_planet — sutravali planet-scoped query (gap fill)
 *   marsys://tool/L0/read_sutravali_rule            — single rule fetch by UUID (gap fill)
 *   marsys://tool/L0/list_sutravali_rules_by_text   — list rules from a text (gap fill)
 *   marsys://tool/L2/classical_attribution_lookup   — MSR signal × classical text attribution (gap fill)
 *
 * Total D7 new capabilities: 7 (2 wiring + 5 gap-fill)
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

// ── GAP FILL: marsys://tool/L0/query_sutravali_rules ─────────────────────────
// Ports lib/retrieve/sutravali_tools.ts::queryRulesTool (query_rules).
// Scope: global — sutravali_rules is a reference corpus, not per-chart.
// Tier stripped per DG1; audience_tier removed from handler.

const querySutravaliRulesTool: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_sutravali_rules',
  type: 'tool',
  layer: 'L0',
  name: 'query_sutravali_rules',
  scope: 'global',

  description: [
    'Query sutravali_rules by antecedent JSONB pattern.',
    'Supports optional filters: planet (graha name), house (1–12), sign (rashi name),',
    'antecedent_pattern (free-text substring match on antecedent JSONB), limit (default 20).',
    'SQL-only via the Python sidecar (/api/brahma/sutravali/query_rules). Zero LLM.',
    'Returns classical rule rows with antecedent, predicate, prediction, confidence,',
    'text_id, and provenance. Use to look up classical rules for a planet/house combination.',
    'Registry equivalent of lib/retrieve/sutravali_tools.ts::query_rules (D7 gap fill).',
  ].join(' '),

  input_schema: {
    planet: {
      type: 'string',
      description: 'Graha name to filter by (e.g. "Sun", "Moon", "Saturn"). Optional.',
    },
    house: {
      type: 'number',
      description: 'Bhava number (1–12) to filter by. Optional.',
    },
    sign: {
      type: 'string',
      description: 'Rashi name to filter by (e.g. "Aries", "Scorpio"). Optional.',
    },
    antecedent_pattern: {
      type: 'string',
      description: 'Free-text substring match applied to the antecedent JSONB field. Optional.',
    },
    limit: {
      type: 'number',
      description: 'Maximum rows to return (default: 20, max: 200).',
    },
  },

  required_inputs: [],

  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'hybrid_retrieval',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    try {
      const sidecarUrl = (process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000').replace(/\/$/, '')
      const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''
      const limit = Math.min(Number(args['limit'] ?? 20), 200)

      const body: Record<string, unknown> = { limit }
      if (typeof args['planet'] === 'string') body['planet'] = args['planet']
      if (typeof args['house'] === 'number') body['house'] = args['house']
      if (typeof args['sign'] === 'string') body['sign'] = args['sign']
      if (typeof args['antecedent_pattern'] === 'string') body['antecedent_pattern'] = args['antecedent_pattern']

      const res = await fetch(`${sidecarUrl}/api/brahma/sutravali/query_rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': sidecarKey },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(10_000),
      })
      if (!res.ok) {
        return { content: { error: `Sidecar returned ${res.status}: ${await res.text()}` }, is_error: true }
      }
      const rows = await res.json() as unknown[]
      return { content: { rules: rows, returned_count: rows.length, filters: body }, is_error: false }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// ── GAP FILL: marsys://tool/L0/query_sutravali_rules_for_planet ──────────────
// Ports lib/retrieve/sutravali_tools.ts::queryRulesForPlanetTool (query_rules_for_planet).

const querySutravaliRulesForPlanetTool: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_sutravali_rules_for_planet',
  type: 'tool',
  layer: 'L0',
  name: 'query_sutravali_rules_for_planet',
  scope: 'global',

  description: [
    'Query sutravali_rules for a specific planet (graha), optionally filtered by bhava (house).',
    'Returns all classical rules referencing the planet in the antecedent.',
    'SQL-only via Python sidecar (/api/brahma/sutravali/query_rules_for_planet). Zero LLM.',
    'planet is required; house and limit are optional.',
    'Registry equivalent of lib/retrieve/sutravali_tools.ts::query_rules_for_planet (D7 gap fill).',
  ].join(' '),

  input_schema: {
    planet: {
      type: 'string',
      description: 'Graha name (e.g. "Sun", "Moon", "Saturn"). Required.',
      required: true,
    },
    house: {
      type: 'number',
      description: 'Bhava number (1–12) to narrow the filter. Optional.',
    },
    limit: {
      type: 'number',
      description: 'Maximum rows to return (default: 50, max: 500).',
    },
  },

  required_inputs: ['planet'],

  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'drill',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const planet = args['planet'] as string | undefined
    if (!planet) {
      return { content: { error: 'planet is required' }, is_error: true }
    }
    try {
      const sidecarUrl = (process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000').replace(/\/$/, '')
      const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''
      const limit = Math.min(Number(args['limit'] ?? 50), 500)

      const qs = new URLSearchParams({ planet, limit: String(limit) })
      if (typeof args['house'] === 'number') qs.set('house', String(args['house']))

      const res = await fetch(`${sidecarUrl}/api/brahma/sutravali/query_rules_for_planet?${qs.toString()}`, {
        headers: { 'x-api-key': sidecarKey },
        signal: AbortSignal.timeout(10_000),
      })
      if (!res.ok) {
        return { content: { error: `Sidecar returned ${res.status}: ${await res.text()}` }, is_error: true }
      }
      const rows = await res.json() as unknown[]
      return { content: { rules: rows, returned_count: rows.length, planet, limit }, is_error: false }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// ── GAP FILL: marsys://tool/L0/read_sutravali_rule ───────────────────────────
// Ports lib/retrieve/sutravali_tools.ts::readRuleTool (read_rule).

const readSutravaliRuleTool: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/read_sutravali_rule',
  type: 'tool',
  layer: 'L0',
  name: 'read_sutravali_rule',
  scope: 'global',

  description: [
    'Fetch a single sutravali rule by its UUID rule_id.',
    'Returns antecedent, predicate, prediction, confidence, text_id, and provenance.',
    'SQL-only via Python sidecar (/api/brahma/sutravali/read_rule/{rule_id}). Zero LLM.',
    'rule_id is required.',
    'Registry equivalent of lib/retrieve/sutravali_tools.ts::read_rule (D7 gap fill).',
  ].join(' '),

  input_schema: {
    rule_id: {
      type: 'string',
      description: 'UUID of the sutravali rule to fetch. Required.',
      required: true,
    },
  },

  required_inputs: ['rule_id'],

  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 40 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const rule_id = args['rule_id'] as string | undefined
    if (!rule_id) {
      return { content: { error: 'rule_id is required' }, is_error: true }
    }
    try {
      const sidecarUrl = (process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000').replace(/\/$/, '')
      const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''

      const res = await fetch(`${sidecarUrl}/api/brahma/sutravali/read_rule/${encodeURIComponent(rule_id)}`, {
        headers: { 'x-api-key': sidecarKey },
        signal: AbortSignal.timeout(10_000),
      })
      if (!res.ok) {
        return { content: { error: `Sidecar returned ${res.status}: ${await res.text()}` }, is_error: true }
      }
      const row = await res.json()
      return { content: { rule: row }, is_error: false }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// ── GAP FILL: marsys://tool/L0/list_sutravali_rules_by_text ──────────────────
// Ports lib/retrieve/sutravali_tools.ts::listRulesByTextTool (list_rules_by_text).

const listSutravaliRulesByTextTool: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/list_sutravali_rules_by_text',
  type: 'tool',
  layer: 'L0',
  name: 'list_sutravali_rules_by_text',
  scope: 'global',

  description: [
    'List all sutravali rules sourced from a given text_id',
    '(e.g. "bphs", "hora_sara", "phaladeepika", "saravali").',
    'Paginated via limit (default 50, max 500) and offset (default 0).',
    'SQL-only via Python sidecar (/api/brahma/sutravali/list_rules_by_text/{text_id}). Zero LLM.',
    'text_id is required.',
    'Registry equivalent of lib/retrieve/sutravali_tools.ts::list_rules_by_text (D7 gap fill).',
  ].join(' '),

  input_schema: {
    text_id: {
      type: 'string',
      description: 'Classical text identifier (e.g. "bphs", "hora_sara", "phaladeepika"). Required.',
      required: true,
    },
    limit: {
      type: 'number',
      description: 'Maximum rows to return (default: 50, max: 500).',
    },
    offset: {
      type: 'number',
      description: 'Pagination offset (default: 0).',
    },
  },

  required_inputs: ['text_id'],

  archetype: 'prose_citation',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'drill',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 50 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const text_id = args['text_id'] as string | undefined
    if (!text_id) {
      return { content: { error: 'text_id is required' }, is_error: true }
    }
    try {
      const sidecarUrl = (process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000').replace(/\/$/, '')
      const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''
      const limit = Math.min(Number(args['limit'] ?? 50), 500)
      const offset = Number(args['offset'] ?? 0)

      const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) })
      const res = await fetch(
        `${sidecarUrl}/api/brahma/sutravali/list_rules_by_text/${encodeURIComponent(text_id)}?${qs.toString()}`,
        {
          headers: { 'x-api-key': sidecarKey },
          signal: AbortSignal.timeout(10_000),
        }
      )
      if (!res.ok) {
        return { content: { error: `Sidecar returned ${res.status}: ${await res.text()}` }, is_error: true }
      }
      const rows = await res.json() as unknown[]
      return { content: { rules: rows, returned_count: rows.length, text_id, limit, offset }, is_error: false }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// ── GAP FILL: marsys://tool/L2/classical_attribution_lookup ──────────────────
// Ports lib/retrieve/classical_attribution_lookup_tool.ts.
// scope: per_chart — attributions are scoped to MSR signals which are per-chart.
// Tier stripped per DG1 (classical_disclosure_filter.ts RETIRED; no audience_tier).
// emits_references: true — returns signal_ids and attribution_ids (references not text).

const classicalAttributionLookupCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L2/classical_attribution_lookup',
  type: 'tool',
  layer: 'L2',
  name: 'classical_attribution_lookup',
  scope: 'per_chart',

  description: [
    'Fetch classical text attributions for MSR signals in a chart.',
    'Each attribution links an MSR signal (signal_id) to a classical text passage',
    '(text_key, title, author, chapter, verse_range, content) with an attribution_type',
    '(confirms | contradicts | partial | extends | silent) and confidence score.',
    'Provides the classical grounding for Bodha layer signals.',
    'Required: chart_id + signal_ids (array of signal_id strings).',
    'Optional: attribution_type filter, confidence_tier filter (HIGH|MEDIUM|LOW).',
    'emits_references: returns signal_id + attribution_id references; content is the',
    'full classical passage without audience-tier gating (tier gating is serve-time only).',
    'Registry equivalent of lib/retrieve/classical_attribution_lookup_tool.ts (D7 gap fill).',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    signal_ids: {
      type: 'array',
      description: 'Array of MSR signal_id strings to look up attributions for. Required.',
      required: true,
      items: { type: 'string' },
    },
    attribution_type: {
      type: 'string',
      description: "Filter by attribution type: 'confirms'|'contradicts'|'partial'|'extends'|'silent'. Optional.",
      enum: ['confirms', 'contradicts', 'partial', 'extends', 'silent'],
    },
    confidence_tier: {
      type: 'string',
      description: "Filter by confidence tier: 'HIGH'|'MEDIUM'|'LOW'. Optional.",
      enum: ['HIGH', 'MEDIUM', 'LOW'],
    },
  },

  required_inputs: ['chart_id', 'signal_ids'],

  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: true,
  lel_capable: false,
  grounds_to: { l1_fact_ids: true, l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 70 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const chart_id = args['chart_id'] as string | undefined
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }
    const signal_ids = Array.isArray(args['signal_ids']) ? (args['signal_ids'] as string[]) : []
    if (signal_ids.length === 0) {
      return { content: { error: 'signal_ids array is required and must be non-empty' }, is_error: true }
    }
    const attribution_type = typeof args['attribution_type'] === 'string'
      ? args['attribution_type'] as 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent'
      : undefined
    const confidence_tier = typeof args['confidence_tier'] === 'string'
      ? args['confidence_tier'] as 'HIGH' | 'MEDIUM' | 'LOW'
      : undefined

    try {
      // Delegate to the underlying Tool 26 implementation
      const { classical_attribution_lookup } = await import('@/lib/tools/classical_attribution_lookup')
      const output = await classical_attribution_lookup({ signal_ids, attribution_type, confidence_tier })

      // Strip audience_tier — no tier gating in the registry layer (serve-time gating only)
      const attributions = output.attributions.map((a: Record<string, unknown>) => ({
        attribution_id: a['attribution_id'],
        msr_signal_id: a['msr_signal_id'],
        text_key: a['text_key'],
        title: a['title'],
        author: a['author'],
        chapter: a['chapter'],
        verse_range: a['verse_range'],
        content: a['content'],
        attribution_type: a['attribution_type'],
        confidence: a['confidence'],
        confidence_tier: a['confidence_tier'],
        derivation_notes: a['derivation_notes'],
        translation_cross_checked: a['translation_cross_checked'],
      }))

      return {
        content: {
          chart_id,
          signal_ids,
          attributions,
          returned_count: attributions.length,
          filters: { attribution_type, confidence_tier },
          provenance: {
            note: 'Audience-tier gating removed per DG1 (no-audience-tier). Serve-time gating handled at API boundary.',
            source_table: 'classical_attributions (via lib/tools/classical_attribution_lookup)',
            legacy_replacement: 'lib/retrieve/classical_attribution_lookup_tool.ts (classical_disclosure_filter.ts RETIRED)',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── Registration export ────────────────────────────────────────────────────────

/**
 * Register D7 channel wiring + gap-fill capabilities.
 * Call at application startup after D6 synergy is registered.
 * GATE A: only registers NEW files for this wave — does not edit registry/index.ts.
 */
export function registerD7ChannelCapabilities(): void {
  registerCapability(mcpWiringTool)
  registerCapability(chatDispatchTool)
  // D7 gap-fill: sutravali + classical attribution (ported from lib/retrieve)
  registerCapability(querySutravaliRulesTool)
  registerCapability(querySutravaliRulesForPlanetTool)
  registerCapability(readSutravaliRuleTool)
  registerCapability(listSutravaliRulesByTextTool)
  registerCapability(classicalAttributionLookupCapability)
}

/**
 * D7 capability URI roster (for Gate C reverse-citation checks and roster smoke tests).
 */
export const D7_CAPABILITY_URIS = [
  'marsys://tool/channel/mcp_wiring',
  'marsys://tool/channel/chat_dispatch',
  'marsys://tool/L0/query_sutravali_rules',
  'marsys://tool/L0/query_sutravali_rules_for_planet',
  'marsys://tool/L0/read_sutravali_rule',
  'marsys://tool/L0/list_sutravali_rules_by_text',
  'marsys://tool/L2/classical_attribution_lookup',
] as const
