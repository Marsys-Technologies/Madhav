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
 * Fifteen lib/retrieve tools had no registry equivalent; they are ported here
 * per the D1 contract (chart_id required where per_chart, tier stripped,
 * emits_references set correctly). Covered by RETRIEVAL_D7_GAP_REPORT_v1_0.md.
 *
 * Capabilities registered by D7:
 *   marsys://tool/channel/mcp_wiring               — MCP server ↔ registry bridge descriptor
 *   marsys://tool/channel/chat_dispatch            — chat-route ↔ registry adapter descriptor
 *
 *   Wave A — sutravali (ported from lib/retrieve/sutravali_tools.ts):
 *   marsys://tool/L0/query_sutravali_rules          — sutravali flexible JSONB query
 *   marsys://tool/L0/query_sutravali_rules_for_planet — sutravali planet-scoped query
 *   marsys://tool/L0/read_sutravali_rule            — single rule fetch by UUID
 *   marsys://tool/L0/list_sutravali_rules_by_text   — list rules from a text
 *
 *   Wave B — classical attribution (ported from lib/retrieve/classical_attribution_lookup_tool.ts):
 *   marsys://tool/L2/classical_attribution_lookup   — MSR signal × classical text attribution
 *
 *   Wave C — chart facts umbrella (gap fill — B.11 floor injection target):
 *   marsys://tool/L1/chart_facts_query              — unified chart_facts parametric lookup
 *
 *   Wave D — remedy sub-tools (ported from lib/retrieve/remedy_tools.ts):
 *   marsys://tool/L0/query_remedies_for_chart       — per-chart remedy lookup by affliction
 *   marsys://tool/L0/list_remedies_by_category      — list remedies by category (global)
 *   marsys://tool/L0/read_remedy                    — single remedy by remedy_id (global)
 *   marsys://tool/L0/query_tantric_remedies         — tantric remedies by deity/planet (global)
 *   marsys://tool/L0/query_remedies_by_planet       — all remedies for a planet (global)
 *   marsys://tool/L0/query_mantras                  — mantra remedies by planet (global)
 *
 *   Wave E — classical text sub-tools (ported from lib/retrieve/index.ts CLASSICAL_TOOLS):
 *   marsys://tool/L0/read_chapter                   — fetch all verse chunks for a chapter
 *   marsys://tool/L0/list_classical_texts           — list all ingested classical texts
 *   marsys://tool/L0/find_verses_about              — embedding-similarity verse discovery
 *
 * Total D7 new capabilities: 17 (2 wiring + 15 gap-fill)
 *
 * Usage: import this file at application startup after D6 synergy is registered.
 */

import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'
import { query } from '@/lib/db/client'
import { resolveAddress, grahaCodeOf, AddressResolutionError, GRAHA_CODE_TO_NAME, type HouseNumber } from '@/lib/retrieval/address_resolver'
import { extractGroundingFromFactRows, judgmentFlag, type JudgmentFlagEntry } from '../../envelope'
import { PANCHANGA_CATEGORIES } from './L1_ganita/get_panchanga'
import { resolveConceptWithLiveFallback, liveFactCategories, noConceptMatchNote } from './L1_ganita/resolve_concept'

// Category-alias resolution (chart_facts_query category filter): bare umbrella terms that do
// not themselves exist as a fact_category but have an obvious real-category family behind them.
// 'panchanga' is not a stored fact_category — the real data lives under panchanga_tithi,
// panchanga_karana, panchanga_sun_moon_dynamics, etc. (all 40 panchanga_* categories, see
// get_panchanga.ts) — so a caller passing the natural umbrella term got an honest-empty 0/0
// instead of the populated family. Mirrors the facet-alias pattern in get_yoga_dosha.ts's
// FACET_TO_TYPE map: expand the alias to its real category set at the filter-compilation step,
// no new data or computation involved.
const CATEGORY_ALIASES: Record<string, readonly string[]> = {
  panchanga: PANCHANGA_CATEGORIES,
}

/** `about` facet resolution result for chart_facts_query — mirrors the shape the handler needs
 *  (fact_subject codes to feed into the whitelisted SQL below), backed by the canonical
 *  address resolver (`@/lib/retrieval/address_resolver.ts`, design §27.2) rather than a
 *  second, parallel resolver implementation. See R5_RUN_LEDGER/JL-007(c) for why an inline
 *  stopgap (`chart_query_about.ts`) existed for one wave, and JL-010 for the Ring-1
 *  reconciliation that folded it into this single call site + retired the stopgap file. */
interface AboutResolution {
  subjects: string[]
  category_hint?: string
  chain: unknown[]
  error?: string
}

function normalizeGrahaName(name: string): string | null {
  try {
    return grahaCodeOf(name)
  } catch {
    return null
  }
}

async function resolveAboutForChartQuery(
  chart_id: string,
  ayanamsha_id: string,
  about: unknown,
): Promise<AboutResolution> {
  if (about == null) return { subjects: [], chain: [] }

  if (typeof about === 'string') {
    const key = about.trim().toLowerCase()
    if (key === 'lagna' || key === 'ascendant') {
      // Trivial constant mapping (no computation, no classical derivation) — the LAGNA
      // fact_subject is not a "graha" the address resolver normalizes, it's the chart_facts
      // row itself. No DB read needed, keeping this the ONE-call/<=2KB gate case (JL-008-style
      // reasoning, W1 GATE).
      return {
        subjects: ['LAGNA'],
        category_hint: 'graha_position',
        chain: ['about:"lagna" resolves directly to the LAGNA fact_subject.'],
      }
    }
    const grahaCode = normalizeGrahaName(about)
    if (grahaCode) {
      return {
        subjects: [grahaCode],
        category_hint: 'graha_position',
        chain: [`about:"${about}" resolves to graha ${grahaCode} via the canonical address resolver.`],
      }
    }
    return { subjects: [], chain: [], error: `about: unrecognized address string "${about}"` }
  }

  if (typeof about === 'object') {
    const obj = about as Record<string, unknown>

    if (obj['graha'] != null) {
      const raw = String(obj['graha'])
      const grahaCode = normalizeGrahaName(raw)
      if (!grahaCode) return { subjects: [], chain: [], error: `about.graha: unrecognized graha "${raw}"` }
      return {
        subjects: [grahaCode],
        category_hint: 'graha_position',
        chain: [`about.graha "${raw}" resolves to ${grahaCode} via the canonical address resolver.`],
      }
    }

    if (obj['bhava'] != null || obj['house'] != null) {
      const n = Number(obj['bhava'] ?? obj['house'])
      if (!Number.isInteger(n) || n < 1 || n > 12) {
        return { subjects: [], chain: [], error: 'about.bhava/house must be an integer 1-12' }
      }
      const subject = `HOUSE_${n}`
      return {
        subjects: [subject],
        chain: [`about.bhava ${n} resolves directly to the ${subject} fact_subject (direct bhava addressing).`],
      }
    }

    if (obj['house_lord'] != null || obj['bhava_lord'] != null) {
      const n = Number(obj['house_lord'] ?? obj['bhava_lord'])
      if (!Number.isInteger(n) || n < 1 || n > 12) {
        return { subjects: [], chain: [], error: 'about.house_lord must be an integer 1-12' }
      }
      try {
        const resolved = await resolveAddress(chart_id, { type: 'lord_of', house: n as HouseNumber }, { ayanamsha_id })
        const entity = resolved.entities[0]
        if (!entity || entity.kind !== 'graha') {
          return { subjects: [], chain: [], error: `about.house_lord: unexpected resolution kind "${entity?.kind}"` }
        }
        return { subjects: [entity.graha_code], category_hint: 'graha_position', chain: resolved.chain }
      } catch (err) {
        return {
          subjects: [],
          chain: [],
          error: err instanceof AddressResolutionError ? err.message : `about.house_lord: ${String(err)}`,
        }
      }
    }

    return { subjects: [], chain: [], error: 'about: unrecognized address object shape' }
  }

  return { subjects: [], chain: [], error: 'about: must be a string or an address object' }
}

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
    'Supports optional filters: planet (graha name), house (1-12), sign (rashi name),',
    'antecedent_pattern (free-text substring match on antecedent JSONB), limit (default 20).',
    'SQL-only via the Python sidecar. Zero LLM.',
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
      description: 'Bhava number (1-12) to filter by. Optional.',
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
    'SQL-only via Python sidecar. Zero LLM.',
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
      description: 'Bhava number (1-12) to narrow the filter. Optional.',
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
    'SQL-only via Python sidecar. Zero LLM.',
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
    'SQL-only via Python sidecar. Zero LLM.',
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
    'emits_references: returns signal_id + attribution_id references.',
    'No audience-tier gating — tier gating is serve-time only.',
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
      const attributions = (output.attributions as unknown as Record<string, unknown>[]).map((a) => ({
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
            note: 'Audience-tier gating removed per DG1 (no-audience-tier). Serve-time gating at API boundary.',
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

// ── GAP FILL Wave C: marsys://tool/L1/chart_facts_query ──────────────────────
// Ports the B.11-floor-injected chart_facts_query tool (lib/retrieve type stub +
// contract alias for query_chart_facts). scope: per_chart — chart_id required.
// Tier stripped per DG1.
//
// R5 W1 (lane: chart_query) REWRITE — this handler used to call a Python sidecar route
// (`/api/ganita/chart_facts/query`) THAT DOES NOT EXIST, so it 404'd unconditionally
// (R5_RUN_LEDGER NF-1, confirmed still broken as of the W0a Ring-2 re-audit). Fixed by
// reading chart_facts DIRECTLY (same pattern as get_yoga_dosha.ts/get_positions.ts — this
// process already owns a pg pool, no sidecar hop was ever necessary for a plain SQL read).
//
// Also implements design §1/§18 EAV-pivot mandate ("~15 EAV rows = one astrological row;
// pivot INSIDE the tool") via `shape: 'pivoted'` (default) — GROUPs the flat (subject, key,
// value) rows into one wide row per fact_subject with a {key: value} object, instead of
// forcing the caller to page through raw rows. `shape: 'rows'` preserves the flat form for
// callers that want it.
//
// Also implements §27.1/§27.2 the universal `about` facet (see ./L1_ganita/chart_query_about.ts
// for the resolver + its scope note re: the sibling address-resolver lane).
//
// Fixed dead param: `ayanamsha_id` was declared on the MCP-side Zod shim
// (platform-mcp/src/tools/registry_bridge.ts) and always sent, but this handler never read
// it — every call silently queried whatever the sidecar defaulted to. Now honored, default
// 'lahiri_chitrapaksha' (matches the MCP shim's own default).
//
// Removed dead params: `as_of_date` / `from_date` / `to_date` — chart_facts has NO
// validity_start/validity_end columns (confirmed via information_schema); these params could
// never have done anything even when the sidecar route existed. Declaring them was dishonest
// (B.10) — a caller passing as_of_date got no error and no effect. See JL entry for this wave.

const chartFactsQueryCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/chart_facts_query',
  type: 'tool',
  layer: 'L1',
  name: 'chart_facts_query',
  scope: 'per_chart',

  description: [
    'Parametric EAV-crosstab lookup over the chart_facts table (a large, paginated result set per chart, single ayanamsha).',
    'Covers planet positions, dignities, strengths, house placements, divisional charts, yogas, doshas, and more.',
    'Default shape="pivoted": rows are grouped by fact_subject into ONE wide row per subject',
    '(e.g. LAGNA -> {sign, sign_lord, house_d1, longitude_sidereal, pada}) instead of ~5-15 raw EAV rows.',
    'shape="rows" returns the flat EAV rows unpivoted.',
    'The `about` facet lets you address the chart the way the shastra does instead of guessing categories:',
    '`about:"lagna"`, `about:{graha:"Saturn"}`, `about:{bhava:10}` (the house itself),',
    '`about:{house_lord:10}` (resolves the Nth house rashi from the lagna + classical BPHS rulership,',
    'and returns the resolved lord graha\'s own facts — the resolution chain is served in `about_resolution`).',
    'Required: chart_id. Optional filters: about, category (single or comma-list), planet, house, sign,',
    'nakshatra, divisional_chart (e.g. D9/D10), keyword, fact_subject (exact subject id, comma-list),',
    'ayanamsha_id (any of the 6 stored ayanamshas — lahiri_chitrapaksha [default], krishnamurti, raman,',
    'surya_siddhanta_classical, true_chitra, INVARIANT), shape, limit, offset.',
    'Pagination is disclosed: the response carries `total` (true count of matching subjects/rows across',
    'the whole chart, NOT just this page) and `more_available` (whether rows remain past offset+limit),',
    'so a caller can page the full subject set without silent truncation.',
    'emits_references: every pivoted field carries its source fact_id for Bodha back-reference.',
    'Pivoted graha_position rows additionally carry a `dignity` field (D1 dignity_state — ',
    'exalted/own/friend/neutral/enemy/debilitated — joined from graha_dignity_per_varga, cited ',
    'in fact_ids.dignity) so a caller does not need a second get_dignity call for basic exaltation status.',
    'Registry equivalent of the chart_facts_query B.11 floor tool (D7 gap fill).',
    'Portal-native alias for query_chart_facts per contract (is_alias=true in tool_metadata).',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    about: {
      type: 'object',
      description: [
        'Astrological address facet (design §27.1). A string ("lagna", a graha name) or an object:',
        '{graha:"Saturn"} | {bhava:10} | {house_lord:10}. When set, overrides subject-selecting filters',
        '(planet/house) and the resolution chain is served back in the response as `about_resolution`.',
      ].join(' '),
    },
    category: {
      type: 'string',
      description: [
        'Fact category to filter by (e.g. "graha_position", "graha_dignity_per_varga", "yoga_label",',
        '"house_bhava_bala_total"). Accepts a single value or comma-separated list for multiple categories.',
        'The umbrella term "panchanga" expands to the full panchanga_* family (panchanga_tithi,',
        'panchanga_karana, panchanga_sun_moon_dynamics, etc.).',
      ].join(' '),
    },
    planet: {
      type: 'string',
      description: 'Graha name to filter by (e.g. "Sun", "Moon", "Saturn", "Rahu", "Ketu"). Optional.',
    },
    house: {
      type: 'number',
      description: 'Bhava number (1-12) to filter by (matches fact_subject="HOUSE_<n>" rows). Optional.',
    },
    sign: {
      type: 'string',
      description: 'Rashi name to filter by (e.g. "Aries", "Scorpio") — matches subjects whose fact_key="sign" equals this. Optional.',
    },
    nakshatra: {
      type: 'string',
      description: 'Nakshatra name to filter by — matches subjects whose fact_key="nakshatra" equals this. Optional.',
    },
    divisional_chart: {
      type: 'string',
      description: [
        'Divisional chart code to filter by (e.g. "D9", "D10", "D2"); matches fact_subject="D9_<GRAHA>" convention',
        'for the DERIVED chart_facts rows. Additionally surfaces the divisional-native EAV facts for that varga',
        'from chart_divisionals in a separate `divisional_facts` section: per-varga sign/house (varga_position),',
        'hora class (varga_hora_class — surya_hora/chandra_hora + hora_d2_house), varga_dignity, house',
        'lords/occupants, etc. — data that lives ONLY in chart_divisionals, not chart_facts. Optional.',
      ].join(' '),
    },
    keyword: {
      type: 'string',
      description: 'Free-text keyword search over fact_key/fact_value_text. Optional.',
    },
    fact_subject: {
      type: 'string',
      description: [
        'Exact fact_subject filter (e.g. "LAGNA", "SUN", "D9_JUP", "HOUSE_10"). Accepts a',
        'single value or comma-separated list. Composes (intersects) with category and the',
        'other subject-selecting filters. WP-1.3(f)/LCA-3: this narrows the payload directly',
        'to the addressed subject(s) instead of returning every subject.',
      ].join(' '),
    },
    ayanamsha_id: {
      type: 'string',
      description: 'Ayanamsha to query (default: lahiri_chitrapaksha — matches the platform-mcp shim default). One ayanamsha per call by design (§1 E4).',
    },
    shape: {
      type: 'string',
      description: '"pivoted" (default — one wide row per fact_subject) or "rows" (flat EAV rows).',
      enum: ['pivoted', 'rows'],
    },
    limit: {
      type: 'number',
      description: 'Maximum rows/subjects to return (default: 100, max: 1000).',
    },
    offset: {
      type: 'number',
      description: [
        'Pagination offset — number of rows (shape="rows") or subjects (shape="pivoted") to',
        'skip before returning `limit` more (default: 0). R6 0b-deadtools V-8 fix: previously',
        'declared on the MCP-facing alias but silently dropped here (page 2 === page 1).',
      ].join(' '),
    },
  },

  required_inputs: ['chart_id'],

  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'umbrella',
  emits_references: true,
  lel_capable: false,
  grounds_to: { l1_fact_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 90, always_include: true },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const chart_id = args['chart_id'] as string | undefined
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    try {
      const ayanamsha_id = (args['ayanamsha_id'] as string) || 'lahiri_chitrapaksha'
      const shape = args['shape'] === 'rows' ? 'rows' : 'pivoted'
      const limit = Math.min(Number(args['limit'] ?? 100), 1000)
      // R6 0b-deadtools (V-8): offset was never read here — page 2 === page 1 for every
      // caller regardless of shape. shape="rows" pages raw EAV rows directly at the SQL
      // level; shape="pivoted" pages by SUBJECT (one wide row per fact_subject), so the
      // raw-row fetch below needs enough headroom to cover `offset + limit` distinct
      // subjects before grouping — see rowCapParamIdx below.
      const offsetRequested = Number(args['offset'] ?? 0)
      const offset = Math.max(0, Math.min(offsetRequested, 100_000))
      const offsetClamped = offset !== offsetRequested

      // ── `about` facet resolution — delegates to the canonical address resolver
      // (@/lib/retrieval/address_resolver.ts) for anything requiring classical derivation
      // (graha normalization, house-lord indirection); the lagna-sign pre-read that
      // `house_lord`/`bhava_lord` needs is handled internally by `resolveAddress`'s own
      // `lord_of` evaluator, not duplicated here. See JL-010 (Ring-1 reconciliation).
      let aboutResolution: Awaited<ReturnType<typeof resolveAboutForChartQuery>> | null = null
      let aboutError: string | null = null
      const subjectsFromAbout: string[] = []
      let categoryHintFromAbout: string | null = null

      if (args['about'] != null) {
        aboutResolution = await resolveAboutForChartQuery(chart_id, ayanamsha_id, args['about'])
        if (aboutResolution.error) {
          aboutError = aboutResolution.error
        } else {
          subjectsFromAbout.push(...aboutResolution.subjects)
          categoryHintFromAbout = aboutResolution.category_hint ?? null
        }
      }

      if (aboutError) {
        return { content: { error: aboutError, chart_id }, is_error: true }
      }

      // ── Whitelisted facet -> parameterized SQL compilation (design §3 SQL idiom / P2 rule) ──
      const params: unknown[] = [chart_id, ayanamsha_id]
      // D-1.5b Gate B (CR-18 / B_shadbala_ratio): ayanamsha-INVARIANT facts must surface
      // alongside the requested ayanamsha's facts. Some L1 quantities are genuinely
      // ayanamsha-independent and are stored by the ga_* writers under ayanamsha_id='INVARIANT'
      // rather than duplicated across all stored ayanamshas — e.g. graha_shadbala_total's
      // `required_rupa` (the classical minimum shadbala per graha: Sun/Mars/Saturn=5, Mercury=7,
      // Jupiter=6.5, Venus=5.5, Moon=6 rupas — a fixed BPHS constant, not a per-ayanamsha value),
      // graha_shadbala_naisargika, and the whole panchanga_* birth-anchor set. Filtering strictly
      // on `ayanamsha_id = $2` silently dropped ALL of these: a graha_shadbala_total pivot served
      // `ratio` + `rupa` (per-ayanamsha) but never `required_rupa` (INVARIANT), so Gate B — which
      // requires each shadbala row to carry BOTH ratio AND required_rupa — failed at 0/9. INVARIANT
      // facts belong to every ayanamsha view by definition; include them. Pivoting is by
      // fact_subject, so an INVARIANT `required_rupa` for SUN merges into the same wide row as
      // SUN's lahiri `ratio`/`rupa`. Collision safety (verified by DB enumeration, D-1.5b Gate B
      // integration review): the fix's target keys (`required_rupa` et al.) exist ONLY under
      // INVARIANT, so they are purely additive. Across the full INVARIANT set there are exactly two
      // shared key-NAMES with per-ayanamsha rows — `rupa` (INVARIANT graha_shadbala_naisargika vs
      // per-ayanamsha graha_shadbala_total) and `active_at_birth_flag` (bhadra_flag) — and BOTH are
      // provably safe: the pivot's `ORDER BY fact_category, fact_key` makes the per-ayanamsha
      // graha_shadbala_total row win the `rupa` slot (naisargika sorts earlier, never last-writes),
      // and `active_at_birth_flag` is itself ayanamsha-invariant (identical value in every ayanamsha).
      // So no served value changes. If you ADD a new INVARIANT key, re-check it does not destructively
      // collide with a per-ayanamsha key of the same (fact_subject, fact_key). `IN ($2,'INVARIANT')`
      // de-dupes automatically when $2 is 'INVARIANT'.
      let sql = `
        SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id IN ($2, 'INVARIANT')
      `

      const categoriesRaw = subjectsFromAbout.length > 0 && categoryHintFromAbout
        ? categoryHintFromAbout
        : (args['category'] as string | undefined)
      if (categoriesRaw) {
        const categories = categoriesRaw.split(',').map(c => c.trim()).filter(Boolean)
        // Expand any bare umbrella term (e.g. 'panchanga') to its real fact_category family —
        // see CATEGORY_ALIASES above. Case-insensitive match; non-aliased categories pass through
        // unchanged (including already-specific ones like 'panchanga_karana').
        const expandedCategories = categories.flatMap(c => CATEGORY_ALIASES[c.toLowerCase()] ?? [c])
        const dedupedCategories = Array.from(new Set(expandedCategories))
        params.push(dedupedCategories)
        sql += ` AND fact_category = ANY($${params.length}::text[])`
      }

      if (subjectsFromAbout.length > 0) {
        params.push(subjectsFromAbout)
        sql += ` AND fact_subject = ANY($${params.length}::text[])`
      } else {
        if (typeof args['house'] === 'number') {
          params.push(`HOUSE_${args['house']}`)
          sql += ` AND fact_subject = $${params.length}`
        }
        if (args['planet']) {
          const grahaCode = normalizeGrahaName(String(args['planet']))
          if (!grahaCode) {
            return { content: { error: `planet: unrecognized graha name "${args['planet']}"`, chart_id }, is_error: true }
          }
          params.push(grahaCode)
          // Match the bare D1 subject (e.g. "SAT") OR any divisional-prefixed subject (e.g. "D9_SAT")
          sql += ` AND (fact_subject = $${params.length} OR fact_subject LIKE '%\\_' || $${params.length} ESCAPE '\\')`
        }
      }

      if (args['divisional_chart']) {
        params.push(`${args['divisional_chart']}\\_%`)
        sql += ` AND fact_subject ILIKE $${params.length} ESCAPE '\\'`
      }

      if (args['sign']) {
        // R6 0b-deadtools (P-6): the `sign` filter used to ALWAYS resolve against
        // chart_facts's own fact_key='sign' rows — but those only exist for D1-scoped
        // categories (graha_position, arudha_pada, karaka_chara_position, ...); NO
        // divisional-chart subject (e.g. "D9_JUP") ever carries a fact_key='sign' row in
        // chart_facts (confirmed via information_schema + live data: D9_JUP has no `sign`
        // fact_key at all — its dignity/aspect/etc. facts live under D9_JUP, but the
        // per-varga SIGN itself is only stored in `chart_divisionals`, per S-12's
        // "21,635 chart_divisionals rows MCP-invisible" finding). So
        // divisional_chart=D9 + sign=Gemini silently bound to the D1 sign column and
        // always returned 0 rows for any divisional subject.
        // Fix: when `divisional_chart` is also supplied, resolve the sign match against
        // chart_divisionals (the real source of divisional sign data) and translate the
        // matched grahas into the fact_subject codes chart_facts uses for that varga
        // (e.g. "Jupiter" -> "D9_JUP") via the canonical grahaCodeOf() mapping — no new
        // astrology computed, just addressing the correct table for an existing fact.
        if (args['divisional_chart']) {
          const vargaLookup = await query<{ graha: string }>(
            `SELECT DISTINCT graha FROM chart_divisionals
             WHERE chart_id = $1 AND ayanamsha_id = $2 AND varga = $3 AND sign ILIKE $4`,
            [chart_id, ayanamsha_id, String(args['divisional_chart']), String(args['sign'])]
          )
          const matchedSubjects = (vargaLookup.rows ?? [])
            .map(r => {
              try {
                return `${args['divisional_chart']}_${grahaCodeOf(r.graha)}`
              } catch {
                return null // Lagna/karya/etc. — no chart_facts graha code; not a match failure
              }
            })
            .filter((s): s is string => Boolean(s))
          // Empty match list is a legitimate "no such placement" result (ANY over an
          // empty array is always false) — never fabricated, never silently widened.
          params.push(matchedSubjects)
          sql += ` AND fact_subject = ANY($${params.length}::text[])`
        } else {
          params.push('sign')
          const keyParamIdx = params.length
          params.push(args['sign'])
          sql += ` AND fact_subject IN (
            SELECT fact_subject FROM chart_facts
            WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_key = $${keyParamIdx} AND fact_value_text ILIKE $${params.length}
          )`
        }
      }

      if (args['nakshatra']) {
        params.push('nakshatra')
        const keyParamIdx = params.length
        params.push(args['nakshatra'])
        sql += ` AND fact_subject IN (
          SELECT fact_subject FROM chart_facts
          WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_key = $${keyParamIdx} AND fact_value_text ILIKE $${params.length}
        )`
      }

      if (args['keyword']) {
        params.push(`%${args['keyword']}%`)
        sql += ` AND (fact_key ILIKE $${params.length} OR fact_value_text ILIKE $${params.length})`
      }

      // WP-1.3(f) / LCA-3: direct fact_subject filter. Exact-match (comma-list) intersection
      // over the fact_subject column — lets a caller narrow to a named subject without going
      // through the category/planet/about facets. Empty match list (e.g. an unknown subject)
      // is a legitimate honest-empty result via ANY over the supplied array, never a widening.
      if (args['fact_subject']) {
        const subjects = String(args['fact_subject']).split(',').map(s => s.trim()).filter(Boolean)
        params.push(subjects)
        sql += ` AND fact_subject = ANY($${params.length}::text[])`
      }

      // WP-1.3(f) / LCA-3-EXT: disclosed pagination with a REAL total. The raw fetch below is
      // capped at (offset+limit)*20 rows and pivoted/sliced to one page, so `returned_count`
      // alone cannot tell a caller whether rows remain (the LCA-3-EXT "silent 1000-cap drop"
      // — 4,566 of 5,566 subjects vanished with no signal). Snapshot the WHERE clause + its
      // bound params HERE (before the row-cap param is appended) so the count query — run
      // right after the main fetch — reflects the whole matching set, not just this page.
      // shape="rows" counts raw rows; shape="pivoted" counts DISTINCT fact_subject.
      const whereOnly = sql.slice(sql.indexOf('FROM chart_facts'))
      const countSql = (shape === 'rows'
        ? 'SELECT COUNT(*)::int AS total '
        : 'SELECT COUNT(DISTINCT fact_subject)::int AS total ') + whereOnly
      const countParams = [...params]

      // Row cap: pivoting collapses ~15 EAV rows into one wide row, so the raw row fetch
      // needs headroom over `limit` (a limit on SUBJECTS, not raw rows) before the pivot step.
      // R6 0b-deadtools (V-8): the cap must also cover `offset` subjects/rows — previously
      // fixed at `limit * 20` regardless of offset, so any page beyond the first drew from
      // the SAME `limit*20`-row window as page 1 and (for shape="rows") the JS-side
      // `.slice(0, limit)` never advanced past row 0 — page 2 === page 1 for every caller.
      params.push((offset + limit) * 20)
      const rowCapParamIdx = params.length
      sql += ` ORDER BY fact_subject, fact_category, fact_key LIMIT $${rowCapParamIdx}::int`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []
      // Disclosed-pagination total (see the WP-1.3(f)/LCA-3-EXT snapshot comment above). Run
      // after the main fetch so the main query stays the first query() call for callers/tests
      // that key on call order.
      const countRes = await query<{ total: number }>(countSql, countParams)
      const total = Number(countRes.rows?.[0]?.total ?? 0)
      // R6 3b-budgets (R-24): grounding MUST be computed from the rows actually SERVED in
      // this response, not the full over-fetched `rows` window (limit*20 row cap, see the
      // R6 0b-deadtools comment above `params.push((offset + limit) * 20)`). The register
      // measured chart_facts(keyword=vargottama, limit=20) returning 20 served facts but
      // ~250 fact_ids/citations in grounding (~26KB of a 30KB payload) — the exact symptom
      // of grounding scoped to the whole fetch window instead of the served slice. Computed
      // per-shape below, after the served subset is known.
      let servedRowsForGrounding: Record<string, unknown>[] = []

      let content: Record<string, unknown>
      if (shape === 'rows') {
        const servedRows = rows.slice(offset, offset + limit)
        servedRowsForGrounding = servedRows
        content = {
          chart_id,
          ayanamsha_id,
          shape: 'rows',
          rows: servedRows,
          returned_count: servedRows.length,
          offset,
          offset_requested: offsetRequested,
          offset_clamped: offsetClamped,
          limit,
          // WP-1.3(f)/LCA-3-EXT disclosed pagination — see the count-query comment above.
          total,
          more_available: offset + servedRows.length < total,
        }
      } else {
        // Pivot: group by fact_subject into one wide row of {fact_key: value}
        const bySubject = new Map<string, { fact_category: string; facts: Record<string, unknown>; fact_ids: Record<string, string> }>()
        for (const row of rows) {
          const subject = String(row['fact_subject'])
          if (!bySubject.has(subject)) {
            bySubject.set(subject, { fact_category: String(row['fact_category']), facts: {}, fact_ids: {} })
          }
          const entry = bySubject.get(subject)!
          const key = String(row['fact_key'])
          const value = row['fact_value_num'] ?? row['fact_value_text'] ?? row['fact_value_jsonb'] ?? null
          entry.facts[key] = value
          entry.fact_ids[key] = String(row['fact_id'])
        }
        const servedSubjectEntries = Array.from(bySubject.entries()).slice(offset, offset + limit)
        const servedSubjects = new Set(servedSubjectEntries.map(([subject]) => subject))
        // R6 3b-budgets (R-24): grounding for shape="pivoted" scopes to fact_subjects that
        // actually made it into THIS page's pivoted rows — never the full over-fetched window.
        servedRowsForGrounding = rows.filter((row) => servedSubjects.has(String(row['fact_subject'])))
        const pivoted = servedSubjectEntries
          .map(([subject, entry]) => ({
            fact_subject: subject,
            fact_category: entry.fact_category,
            ...entry.facts,
            fact_ids: entry.fact_ids,
          }))

        // R5.2 A2 (punch #2): dignity field on positional rows. graha_position rows and
        // graha_dignity_per_varga rows never naturally pivot together — position uses the
        // bare graha code as fact_subject (e.g. "SAT"), dignity is keyed per-varga
        // ("D1_SAT", "D10_SAT", ...) — so a plain position query has never carried dignity
        // without a second call. This is a join/projection over data already in chart_facts
        // (verified: D1_SAT dignity_state="exalted" for the native chart, matching Saturn's
        // classical exaltation in Libra/Tula, which the same row's own `sign` field confirms)
        // — no new computation, per B.10.
        const positionRows = pivoted.filter(
          (p): p is typeof p & { sign: unknown } => GRAHA_CODE_TO_NAME[p.fact_subject] != null && 'sign' in p
        )
        if (positionRows.length > 0) {
          const dignitySubjects = positionRows.map((p) => `D1_${p.fact_subject}`)
          const dignityRes = await query<{ fact_subject: string; fact_value_text: string | null; fact_id: string }>(
            `SELECT fact_subject, fact_value_text, fact_id FROM chart_facts
             WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_dignity_per_varga'
               AND fact_subject = ANY($3::text[]) AND fact_key = 'dignity_state'`,
            [chart_id, ayanamsha_id, dignitySubjects]
          )
          const dignityBySubject = new Map(dignityRes.rows.map((r) => [r.fact_subject, r]))
          for (const p of positionRows) {
            const d = dignityBySubject.get(`D1_${p.fact_subject}`)
            if (d && d.fact_value_text) {
              ;(p as Record<string, unknown>)['dignity'] = d.fact_value_text
              ;(p.fact_ids as Record<string, string>)['dignity'] = d.fact_id
              // R6 3b-budgets (R-24): the dignity join fetches OUTSIDE the main `rows`
              // query — its fact_id must still ground, since it's served in this response.
              servedRowsForGrounding.push({
                fact_id: d.fact_id,
                fact_subject: d.fact_subject,
                fact_category: 'graha_dignity_per_varga',
                verification_pass_status: null,
              })
            }
          }
        }

        content = {
          chart_id,
          ayanamsha_id,
          shape: 'pivoted',
          facts: pivoted,
          returned_count: pivoted.length,
          offset,
          offset_requested: offsetRequested,
          offset_clamped: offsetClamped,
          limit,
          // WP-1.3(f)/LCA-3-EXT disclosed pagination — `total` is the true DISTINCT-subject
          // count over the whole matching set (e.g. 5,566 unfiltered), NOT this page's slice.
          total,
          more_available: offset + pivoted.length < total,
        }
      }

      if (aboutResolution) {
        content['about_resolution'] = {
          requested: args['about'],
          subjects: aboutResolution.subjects,
          chain: aboutResolution.chain,
        }
      }

      content['grounding'] = extractGroundingFromFactRows(servedRowsForGrounding)
      content['provenance'] = {
        table: 'chart_facts',
        note: 'fact_id references resolve to the canonical L1 chart_facts table.',
      }

      // R5.3 B3 bounded-fix #2: §31.4 time-sensitivity ladder (R5_AUTHORITY_DOSSIER §4).
      // D24-D60 lagna-dependent claims require sensitive_extreme birth-time confidence
      // (a Dn varga-lagna changes sign every ~120/n minutes — for D60 that's ~2 minutes).
      // Pratinidhi-R ruling: below that threshold, serve the judgment_flag + an honest
      // narrated note rather than assert D60 lagna-dependent claims at face value — never
      // floor/withhold the underlying facts (they may still be useful for D1-anchored
      // reads), just attach the caveat. Scoped to divisional_chart=D60 per this bounded
      // fix's brief; the same lookup generalizes to D24/D30 if a future item needs it.
      if (String(args['divisional_chart'] ?? '').toUpperCase() === 'D60') {
        const rectRes = await query<{ confidence_label: string | null; win_margin: string | null; lel_training_events: number | null; lel_training_matched: number | null }>(
          `SELECT confidence_label, win_margin, lel_training_events, lel_training_matched
           FROM phala_rectification_best WHERE chart_id = $1`,
          [chart_id]
        )
        const rect = rectRes.rows[0]
        const label = rect?.confidence_label ?? 'no_rectification_run'
        const belowThreshold = label !== 'high' && label !== 'resolved'
        if (belowThreshold) {
          const flags = Array.isArray(content['judgment_flags']) ? content['judgment_flags'] as JudgmentFlagEntry[] : []
          flags.push(judgmentFlag('time_sensitive_low_confidence', 'see time_sensitivity_note for the §31.4 ladder detail.'))
          content['judgment_flags'] = flags
          content['time_sensitivity_note'] = [
            `D60 (Shashtiamsha) lagna-dependent claims require sensitive_extreme birth-time`,
            `confidence per the §31.4 time-sensitivity ladder (a D60 varga-lagna changes sign`,
            `every ~2 minutes). This chart's rectification confidence is currently`,
            `"${label}"${rect ? ` (win_margin=${rect.win_margin ?? 'n/a'}, ${rect.lel_training_matched ?? 0}/${rect.lel_training_events ?? 0} LEL events matched)` : ' (no rectification row on record)'} —`,
            `below that bar. D60 rows below are served as-computed (not withheld), but any`,
            `lagna-dependent D60 claim (e.g. D60 lagna sign/house placements) should be read`,
            `as indicative, not confirmed, until rectification resolves further.`,
          ].join(' ')
        }
      }

      // ── S-12 / Gate B (CR-58): surface chart_divisionals EAV facts for the requested varga.
      // chart_facts carries the DERIVED per-varga facts (dignity, argala, aspects, ...) but NOT
      // the divisional-native EAV rows: per-varga sign/house (varga_position), hora class
      // (varga_hora_class: surya_hora/chandra_hora + hora_d2_house), varga_dignity, house
      // lords/occupants, etc. Those live ONLY in chart_divisionals — the S-12 "21,635
      // chart_divisionals rows MCP-invisible" finding — and are exactly the "operative-varga
      // placements" the confirm_in_varga recover-hints promise when they tell a caller to "pass
      // divisional_chart=<varga>". Gate B needs "both wealth lords in Chandra-hora, D2 house 12"
      // answerable in ONE call: ganita_chart_facts_get(divisional_chart='D2') must return the
      // hora_class assignment, which chart_facts alone cannot provide.
      //
      // Served as a SEPARATE, source-tagged, budget-capped `divisional_facts` section so the
      // chart_facts pivot/rows contract above is untouched — the chart_divisionals rows are
      // never flattened into the chart_facts `rows`/`facts` arrays, they carry their own
      // fact_id (chart_divisionals.id) and provenance, and the cap discloses `more_available`
      // with a paging pointer (§N.6 Serving Density Principle: layered, capped, disclosed —
      // catalog-native rows counted and pointed-at separately, never merged into confirmed
      // chart_facts findings). Only fires when `divisional_chart` is set, and honours the same
      // `category`/`planet` narrowing the caller already passed.
      if (args['divisional_chart']) {
        const DIVISIONAL_FACTS_CAP = 300
        const dvParams: unknown[] = [chart_id, ayanamsha_id, String(args['divisional_chart'])]
        let dvWhere = `FROM chart_divisionals WHERE chart_id = $1 AND ayanamsha_id = $2 AND varga = $3`
        if (categoriesRaw) {
          const categories = categoriesRaw.split(',').map((c) => c.trim()).filter(Boolean)
          dvParams.push(categories)
          dvWhere += ` AND fact_category = ANY($${dvParams.length}::text[])`
        }
        if (args['planet']) {
          // chart_divisionals stores the full graha name ("Sun", "Moon"); callers typically
          // pass the same. Tolerant ILIKE match — no code/name translation needed here.
          dvParams.push(String(args['planet']))
          dvWhere += ` AND graha ILIKE $${dvParams.length}`
        }
        const dvCountRes = await query<{ total: number }>(`SELECT COUNT(*)::int AS total ${dvWhere}`, dvParams)
        const dvTotal = Number(dvCountRes.rows?.[0]?.total ?? 0)
        dvParams.push(DIVISIONAL_FACTS_CAP)
        const dvRes = await query<Record<string, unknown>>(
          `SELECT id, graha, varga, fact_category, fact_key, fact_value_num, fact_value_text,
                  sign, house, degree_in_sign
           ${dvWhere}
           ORDER BY fact_category, graha, fact_key
           LIMIT $${dvParams.length}::int`,
          dvParams,
        )
        const dvRows = (dvRes.rows ?? []).map((r) => ({
          fact_id: r['id'],
          graha: r['graha'],
          varga: r['varga'],
          fact_category: r['fact_category'],
          fact_key: r['fact_key'],
          fact_value_num: r['fact_value_num'],
          fact_value_text: r['fact_value_text'],
          sign: r['sign'],
          house: r['house'],
          degree_in_sign: r['degree_in_sign'],
        }))
        content['divisional_facts'] = {
          source_table: 'chart_divisionals',
          varga: String(args['divisional_chart']),
          rows: dvRows,
          returned_count: dvRows.length,
          total: dvTotal,
          more_available: dvRows.length < dvTotal,
          note: [
            `Divisional-native EAV facts for ${String(args['divisional_chart'])} sourced from`,
            `chart_divisionals (per-varga sign/house, hora class [surya_hora/chandra_hora +`,
            `hora_d2_house], varga dignity, house lords/occupants, ...) — these are NOT stored in`,
            `chart_facts. fact_id references resolve to chart_divisionals.id.`,
            dvRows.length < dvTotal
              ? `Capped at ${DIVISIONAL_FACTS_CAP} of ${dvTotal} rows; narrow with category= to reach the rest.`
              : '',
          ].filter(Boolean).join(' '),
        }
      }

      // ── SATYA-ŚEṢA W1 (SATYA_SHESHA_BRIEF_v1_0.md §2 W1) — no bare empties ──────────────
      // UAT-DARPANA S4-03: `ganita_chart_facts_get(keyword="gulika")` returned a bare
      // `{facts: [], total: 0}` (the `keyword` filter only ILIKEs fact_key/fact_value_text —
      // it never searches fact_category, and GULIKA lives under category
      // `sensitive_point_gulika_mandi`). The answering LLM then asserted, in self-branded
      // "honest" language, that Gulika "isn't in your computed chart data." It IS there. The
      // bug was never the LLM's synthesis — it was that this serving layer returned a bare,
      // contextless empty with no signal that a resolvable alias exists.
      //
      // `total` (the disclosed-pagination true count over the WHOLE matching set, not just
      // this page — see the WP-1.3(f)/LCA-3-EXT comment above) is the honest empty signal:
      // total===0 means zero facts matched this filter set anywhere in the chart, not merely
      // that this page came up short. When that happens, every response now carries:
      //   - `empty_reason`: exactly what was searched, over what universe/filter.
      //   - `resolver_suggestion`: the top concept-resolver match for the query term (alias
      //     table first, then a live fact_category substring fallback — same two-pass logic
      //     `concept_locate` uses), so a caller can retry with the real category instead of
      //     concluding "there is nothing".
      // Never fabricated: if the resolver ALSO has no match, `resolver_suggestion` is `null`
      // and the note says so explicitly — that IS the honest empty (B.10).
      if (total === 0) {
        const appliedFilters: string[] = []
        if (categoriesRaw) appliedFilters.push(`category="${categoriesRaw}"`)
        if (args['keyword']) appliedFilters.push(`keyword="${String(args['keyword'])}"`)
        if (args['planet']) appliedFilters.push(`planet="${String(args['planet'])}"`)
        if (typeof args['house'] === 'number') appliedFilters.push(`house=${args['house']}`)
        if (args['sign']) appliedFilters.push(`sign="${String(args['sign'])}"`)
        if (args['nakshatra']) appliedFilters.push(`nakshatra="${String(args['nakshatra'])}"`)
        if (args['divisional_chart']) appliedFilters.push(`divisional_chart="${String(args['divisional_chart'])}"`)
        if (args['fact_subject']) appliedFilters.push(`fact_subject="${String(args['fact_subject'])}"`)
        if (args['about'] != null) appliedFilters.push(`about=${JSON.stringify(args['about'])}`)

        content['empty_reason'] = appliedFilters.length > 0
          ? `No chart_facts rows matched ${appliedFilters.join(' AND ')} for chart_id=${chart_id}, ` +
            `ayanamsha_id=${ayanamsha_id} (searched the whole chart_facts table — this is the true ` +
            `total over every matching subject, not just this page).`
          : `No chart_facts rows exist for chart_id=${chart_id}, ayanamsha_id=${ayanamsha_id} — no ` +
            `filters were applied, which would mean the chart itself has zero stored facts. Worth ` +
            `flagging independently of any single query.`

        // Resolve against the term a caller most plausibly typed with resolvable intent —
        // prefer the free-text `keyword` (the most naive/S4-03-shaped guess), then a supplied
        // category (may itself be a wrong/guessed name — exactly concept_locate's job to
        // correct), then the other subject-selecting filters.
        const resolverTerm =
          (args['keyword'] as string | undefined) ||
          categoriesRaw ||
          (args['planet'] as string | undefined) ||
          (args['sign'] as string | undefined) ||
          (args['nakshatra'] as string | undefined) ||
          (args['fact_subject'] as string | undefined) ||
          null

        if (resolverTerm) {
          const suggestion = await resolveConceptWithLiveFallback(resolverTerm, chart_id)
          if (suggestion) {
            content['resolver_suggestion'] = suggestion
          } else {
            // Genuine MISS on BOTH resolver passes — never fabricate a pointer. This IS the
            // honest empty (SATYA_SHESHA_BRIEF §2 W1: "if the resolver has no match, say 'no
            // concept match either'").
            const liveCategories = await liveFactCategories(chart_id)
            content['resolver_suggestion'] = null
            content['resolver_suggestion_note'] = noConceptMatchNote(resolverTerm, chart_id, liveCategories.length)
          }
        } else {
          content['resolver_suggestion'] = null
          content['resolver_suggestion_note'] = `No free-text term to resolve (only positional filters — ` +
            `house/divisional_chart/about — were supplied, all of which are structurally valid; a zero ` +
            `result here means no facts exist under that exact address, not that the address is unknown).`
        }
      }

      return { content, is_error: false }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── GAP FILL Wave D: Remedy sub-tools (from lib/retrieve/remedy_tools.ts) ─────
// The registry already has marsys://tool/L0/query_remedy_corpus (generic graha filter)
// and marsys://tool/L2/query_remedies (Bodha layer per-chart). The 6 specific sub-tools
// below map to the 7 RetrievalTool entries in REMEDY_TOOLS that the planner can dispatch
// via getTool(). query_remedies (global filter) is covered by query_remedy_corpus;
// the remaining 6 have no registry equivalent.
// Tier stripped per DG1. Per_chart only where chart_id is meaningful.

// D-1: query_remedies_for_chart — global (corpus lookup; no chart-scoped SQL)
const queryRemediesForChartCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_remedies_for_chart',
  type: 'tool',
  layer: 'L0',
  name: 'query_remedies_for_chart',
  scope: 'global',

  description: [
    'Return remedies relevant to a given affliction (planet name or life domain).',
    'Matches the affliction against both the planet and domain columns in brahma_remedy_corpus',
    'using ILIKE. Returns top remedies ordered by confidence and cost tier.',
    'Required: affliction. Optional: chart_id (provenance only, not used for data filtering), top_k (default 5).',
    'No chart-scoped SQL — this is a global corpus lookup.',
    'Registry equivalent of lib/retrieve/remedy_tools.ts::query_remedies_for_chart (D7 gap fill).',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Optional — used for provenance logging only, not for data filtering.',
      required: false,
    },
    affliction: {
      type: 'string',
      description: 'Planet name or life domain to match (ILIKE against both planet and domain columns). Required.',
      required: true,
    },
    top_k: {
      type: 'number',
      description: 'Maximum remedies to return (default: 5, max: 50).',
    },
  },

  required_inputs: ['affliction'],

  archetype: 'flat_fact',
  traversal_level: 'L-DOMAIN',
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
    const chart_id = args['chart_id'] as string | undefined  // optional — provenance only
    const affliction = args['affliction'] as string | undefined
    if (!affliction) {
      return { content: { error: 'affliction is required' }, is_error: true }
    }
    const topK = Math.min(Number(args['top_k'] ?? 5), 50)

    try {
      const sql = `
        SELECT remedy_id, planet, domain, category, deity,
               prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
               cost_tier, contraindications, source_canonical_id, source_citation,
               classical_attestation_text
        FROM brahma_remedy_corpus
        WHERE planet ILIKE $1 OR domain ILIKE $1
        ORDER BY confidence DESC NULLS LAST, cost_tier ASC
        LIMIT $2
      `
      // R6 0a-envauth (R-15/O-6): was a raw `pg.Pool` keyed on `process.env.DATABASE_URL`,
      // which is never set in production (amjis-web authenticates to Cloud SQL via the
      // connector + INSTANCE_CONNECTION_NAME/DB_USER/DB_PASSWORD/DB_NAME — see
      // lib/db/client.ts's initPool()). Every call 500'd with "DATABASE_URL not set".
      // Fixed to use the same shared `query()` helper the sibling
      // marsys://tool/L0/query_remedy_corpus capability already uses successfully.
      const result = await query(sql, [`%${affliction}%`, topK])
      const content: Record<string, unknown> = {
        affliction,
        remedies: result.rows,
        returned_count: result.rows.length,
        provenance: { table: 'brahma_remedy_corpus', note: 'No audience_tier gating — serve-time only.' },
      }
      if (chart_id) content['chart_id'] = chart_id
      return { content, is_error: false }
    } catch (err) {
      const errContent: Record<string, unknown> = { error: String(err) }
      if (chart_id) errContent['chart_id'] = chart_id
      return { content: errContent, is_error: true }
    }
  },
}

// D-2: list_remedies_by_category — global
const REMEDY_CATEGORY_PAGE_LIMIT = 10

const listRemediesByCategoryCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/list_remedies_by_category',
  type: 'tool',
  layer: 'L0',
  name: 'list_remedies_by_category',
  scope: 'global',

  description: [
    'List all remedies in a given category from brahma_remedy_corpus.',
    'category is required. Valid values: mantras | gemstones | charity | vrata |',
    'yantras | puja | tantric | ayurvedic | vastu | behavioral.',
    'Returns remedy_id, planet, domain, deity, prescription_text, mantra_text,',
    'mantra_sanskrit, cost_tier, source_canonical_id, classical_attestation_text.',
    'Ordered by planet then remedy_id. No chart_id needed (global reference data).',
    'Registry equivalent of lib/retrieve/remedy_tools.ts::list_remedies_by_category (D7 gap fill).',
  ].join(' '),

  input_schema: {
    category: {
      type: 'string',
      description: 'Remedy category: mantras|gemstones|charity|vrata|yantras|puja|tantric|ayurvedic|vastu|behavioral. Required.',
      required: true,
      enum: ['mantras', 'gemstones', 'charity', 'vrata', 'yantras', 'puja', 'tantric', 'ayurvedic', 'vastu', 'behavioral'],
    },
    limit: {
      type: 'number',
      description: `Maximum remedies in one response (default and max ${REMEDY_CATEGORY_PAGE_LIMIT}). Use offset to continue.`,
      default: REMEDY_CATEGORY_PAGE_LIMIT,
    },
    offset: {
      type: 'number',
      description: 'Zero-based offset for the next remedy page (default 0).',
      default: 0,
    },
  },

  required_inputs: ['category'],

  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'drill',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const category = args['category'] as string | undefined
    if (!category) {
      return { content: { error: 'category is required' }, is_error: true }
    }
    const requestedLimit = Number(args['limit'] ?? REMEDY_CATEGORY_PAGE_LIMIT)
    const limit = Number.isFinite(requestedLimit)
      ? Math.min(Math.max(Math.floor(requestedLimit), 1), REMEDY_CATEGORY_PAGE_LIMIT)
      : REMEDY_CATEGORY_PAGE_LIMIT
    const requestedOffset = Number(args['offset'] ?? 0)
    const offset = Number.isFinite(requestedOffset)
      ? Math.max(Math.floor(requestedOffset), 0)
      : 0
    try {
      // W4-loop-1 (E-5 group2): the corpus stores the category as remedy_type (singular:
      // 'gemstone', 'mantra', 'yantra', ...) — the hard `category = $1` predicate against a
      // plural enum value ('gemstones') matched nothing and returned a dishonest blank.
      // Normalize plural→singular and match across BOTH remedy_type and category columns;
      // emit empty_reason on a genuine empty match.
      const catSingular = category.trim().toLowerCase().replace(/s$/, '')
      const catLower = category.trim().toLowerCase()
      const sql = `
        SELECT remedy_id, planet, domain, category, remedy_type, deity,
               prescription_text, mantra_text, mantra_sanskrit,
               cost_tier, source_canonical_id, classical_attestation_text
        FROM brahma_remedy_corpus
        WHERE LOWER(remedy_type) = $1 OR LOWER(category) = $2 OR LOWER(category) = $1
        ORDER BY planet, remedy_id
        LIMIT $3 OFFSET $4
      `
      // R6 0a-envauth (R-15/O-6): see query_remedies_for_chart's comment above —
      // swapped the DATABASE_URL-keyed raw pg.Pool for the shared query() helper.
      const result = await query(sql, [catSingular, catLower, limit, offset])
      const countResult = await query<{ total: number }>(
        `SELECT COUNT(*)::int AS total
         FROM brahma_remedy_corpus
         WHERE LOWER(remedy_type) = $1 OR LOWER(category) = $2 OR LOWER(category) = $1`,
        [catSingular, catLower],
      )
      const remedies = result.rows ?? []
      const total = Number(countResult.rows?.[0]?.total ?? remedies.length)
      const moreAvailable = offset + remedies.length < total
      return {
        content: {
          category, remedies, returned_count: remedies.length,
          pagination: {
            limit,
            offset,
            total,
            more_available: moreAvailable,
            next_offset: moreAvailable ? offset + remedies.length : null,
          },
          ...(remedies.length === 0
            ? { empty_reason: `No remedies found in category="${category}". Stored remedy_type vocabulary: mantra, gemstone, yantra, charity, puja, vrata, homa, japa, behavioral, ayurvedic.` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// D-3: read_remedy — global
const readRemedyCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/read_remedy',
  type: 'tool',
  layer: 'L0',
  name: 'read_remedy',
  scope: 'global',

  description: [
    'Fetch the full record for a single remedy by remedy_id from brahma_remedy_corpus.',
    'Returns all columns including ingredients_jsonb and timing_rules_jsonb.',
    'remedy_id is required (UUID).',
    'Registry equivalent of lib/retrieve/remedy_tools.ts::read_remedy (D7 gap fill).',
  ].join(' '),

  input_schema: {
    remedy_id: {
      type: 'string',
      description: 'UUID of the remedy to fetch. Required.',
      required: true,
    },
  },

  required_inputs: ['remedy_id'],

  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 45 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const remedy_id = args['remedy_id'] as string | undefined
    if (!remedy_id) {
      return { content: { error: 'remedy_id is required' }, is_error: true }
    }
    try {
      // R6 0a-envauth (R-15/O-6): see query_remedies_for_chart's comment above —
      // swapped the DATABASE_URL-keyed raw pg.Pool for the shared query() helper.
      const result = await query('SELECT * FROM brahma_remedy_corpus WHERE remedy_id = $1', [remedy_id])
      const row = result.rows[0] ?? null
      return {
        content: { remedy_id, remedy: row, found: row !== null },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// D-4: query_tantric_remedies — global
const queryTantricRemediesCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_tantric_remedies',
  type: 'tool',
  layer: 'L0',
  name: 'query_tantric_remedies',
  scope: 'global',

  description: [
    'Query tantric remedies from brahma_remedy_corpus (category=tantric).',
    'All returned rows have passed the tantric careful-inclusion gate (BPHS / Phaladeepika sources only).',
    'Optional filters: deity (ILIKE), planet. Returns prescription, mantra, ingredients,',
    'timing rules, cost tier, contraindications, and classical attestation.',
    'Registry equivalent of lib/retrieve/remedy_tools.ts::query_tantric_remedies (D7 gap fill).',
  ].join(' '),

  input_schema: {
    deity: {
      type: 'string',
      description: 'Deity name to filter by (ILIKE match). Optional.',
    },
    planet: {
      type: 'string',
      description: 'Graha name to filter by. Optional.',
    },
  },

  required_inputs: [],

  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
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
    const deity  = args['deity']  as string | undefined
    const planet = args['planet'] as string | undefined

    try {
      // W4-loop-1 (E-5 group2): match the tantric class across BOTH remedy_type and category
      // columns (case-insensitive) and match planet case-insensitively; emit empty_reason on
      // a genuine empty match rather than a dishonest blank.
      const conditions: string[] = ["(LOWER(remedy_type) = 'tantric' OR LOWER(category) = 'tantric')"]
      const values: unknown[] = []
      if (deity)  { values.push(`%${deity}%`);  conditions.push(`deity ILIKE $${values.length}`) }
      if (planet) { values.push(planet);         conditions.push(`LOWER(planet) = LOWER($${values.length})`) }

      const sql = `
        SELECT remedy_id, planet, domain, deity,
               prescription_text, mantra_sanskrit, mantra_transliteration,
               ingredients_jsonb, timing_rules_jsonb, cost_tier, contraindications,
               source_canonical_id, source_citation, classical_attestation_text
        FROM brahma_remedy_corpus
        WHERE ${conditions.join(' AND ')}
        ORDER BY planet, remedy_id
      `
      // R6 0a-envauth (R-15/O-6): see query_remedies_for_chart's comment above —
      // swapped the DATABASE_URL-keyed raw pg.Pool for the shared query() helper.
      const result = await query(sql, values)
      return {
        content: {
          remedies: result.rows, returned_count: result.rows.length, filters: { deity, planet },
          ...(result.rows.length === 0
            ? { empty_reason: `No tantric-category remedies matched (deity=${deity ?? 'any'}, planet=${planet ?? 'any'}).` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// D-5: query_remedies_by_planet — global
const queryRemediesByPlanetCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_remedies_by_planet',
  type: 'tool',
  layer: 'L0',
  name: 'query_remedies_by_planet',
  scope: 'global',

  description: [
    'Return all remedies for a given planet across all categories from brahma_remedy_corpus.',
    'Useful for building a complete upaya profile for a planet.',
    'planet is required. Returns all categories ordered by category then remedy_id.',
    'Registry equivalent of lib/retrieve/remedy_tools.ts::query_remedies_by_planet (D7 gap fill).',
  ].join(' '),

  input_schema: {
    planet: {
      type: 'string',
      description: 'Graha name to look up (e.g. "Saturn", "Mars", "Venus"). Required.',
      required: true,
    },
  },

  required_inputs: ['planet'],

  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
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
      // W4-loop-1 (E-5 group2): planet is stored lowercase — match case-insensitively so
      // "Venus"/"venus"/"VENUS" all resolve. Emit empty_reason on a genuine empty match.
      const sql = `
        SELECT remedy_id, planet, domain, category, deity,
               prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
               cost_tier, contraindications, source_canonical_id, classical_attestation_text
        FROM brahma_remedy_corpus
        WHERE LOWER(planet) = LOWER($1)
        ORDER BY category, remedy_id
      `
      // R6 0a-envauth (R-15/O-6): see query_remedies_for_chart's comment above —
      // swapped the DATABASE_URL-keyed raw pg.Pool for the shared query() helper.
      const result = await query(sql, [planet])
      return {
        content: {
          planet, remedies: result.rows, returned_count: result.rows.length,
          ...(result.rows.length === 0
            ? { empty_reason: `No remedies found for planet="${planet}". Valid grahas: sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu.` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// D-6: query_mantras — global
const queryMantrasCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_mantras',
  type: 'tool',
  layer: 'L0',
  name: 'query_mantras',
  scope: 'global',

  description: [
    'Return mantra remedies (category=mantras) from brahma_remedy_corpus.',
    'Includes Sanskrit mantra, transliteration, and classical source.',
    'Optional filter: planet (graha name). Returns all mantras if planet is omitted.',
    'Registry equivalent of lib/retrieve/remedy_tools.ts::query_mantras (D7 gap fill).',
  ].join(' '),

  input_schema: {
    planet: {
      type: 'string',
      description: 'Graha name to filter mantras by (e.g. "Sun", "Jupiter"). Optional — returns all if omitted.',
    },
  },

  required_inputs: [],

  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
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
    const planet = args['planet'] as string | undefined
    try {
      // W4-loop-1 (E-5 group2): the mantra category is stored as remedy_type='mantra'
      // (singular); the hard `category='mantras'` predicate + case-sensitive planet match
      // was the "Venus"→0 / "venus"→N split. Match category across BOTH columns and match
      // planet case-insensitively; emit empty_reason on a genuine empty.
      //
      // F-144: `remedy_type='mantra'` also admits `category='corpus_sweep'` rows — the
      // deterministic OCR-sweep scaffold (brahmagyan/l0_remedy_corpus.py::sweep_classical_text_chunks)
      // that scores extraction legibility into `scaffold_status` ('live' | 'review' | 'rejected').
      // This handler had no scaffold_status predicate at all, so a garbled-OCR sweep row graded
      // 'review' (or a hand-rejected 'rejected' row) was served identically to a hand-curated
      // mantra — the R-19 defect (MARSYS_DEFECT_GAP_REGISTER_v2_0.md), confirmed live with named
      // example sweep_jupiter_mantra_2ab17171. Only 'live'-graded rows are servable here.
      const conditions: string[] = [
        "(LOWER(remedy_type) = 'mantra' OR LOWER(category) = 'mantras')",
        "scaffold_status = 'live'",
      ]
      const values: unknown[] = []
      if (planet) { values.push(planet); conditions.push(`LOWER(planet) = LOWER($${values.length})`) }

      const sql = `
        SELECT remedy_id, planet, deity,
               mantra_sanskrit, mantra_transliteration, mantra_text,
               prescription_text, timing_rules_jsonb,
               source_canonical_id, classical_attestation_text, classical_ref
        FROM brahma_remedy_corpus
        WHERE ${conditions.join(' AND ')}
        ORDER BY planet, remedy_id
      `
      // R6 0a-envauth (R-15/O-6): see query_remedies_for_chart's comment above —
      // swapped the DATABASE_URL-keyed raw pg.Pool for the shared query() helper.
      const result = await query(sql, values)
      return {
        content: {
          planet: planet ?? 'all', mantras: result.rows, returned_count: result.rows.length,
          ...(result.rows.length === 0
            ? { empty_reason: `No mantra remedies found${planet ? ` for planet="${planet}"` : ''}. Grahas are stored lowercase (sun..ketu).` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// ── GAP FILL Wave E: Classical text sub-tools ─────────────────────────────────
// Ports three CLASSICAL_TOOLS from lib/retrieve/index.ts that have no registry
// equivalent. marsys://tool/L0/query_classical_texts covers the main semantic
// search path (read_classical_text / search_classical_texts). The three below
// are distinct: chapter fetch, text listing, and embedding-similarity discovery.

// E-1: read_chapter — global
const readChapterCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/read_chapter',
  type: 'tool',
  layer: 'L0',
  name: 'read_chapter',
  scope: 'global',

  description: [
    'Fetch all verse chunks for a specific chapter of a classical Jyotish text.',
    'Required: text_id (e.g. "bphs", "hora_sara", "saravali") and chapter (integer).',
    'Returns all chunk content for the chapter in English translation.',
    'Delegates to the Python sidecar classical text tools endpoint.',
    'Registry equivalent of lib/retrieve/index.ts::read_chapter (D7 gap fill).',
  ].join(' '),

  input_schema: {
    text_id: {
      type: 'string',
      description: 'Classical text identifier (e.g. "bphs", "hora_sara", "saravali"). Required.',
      required: true,
    },
    chapter: {
      type: 'number',
      description: 'Chapter number to fetch (integer). Required.',
      required: true,
    },
  },

  required_inputs: ['text_id', 'chapter'],

  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 45 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const text_id = args['text_id'] as string | undefined
    const chapter = args['chapter'] as number | undefined
    if (!text_id) return { content: { error: 'text_id is required' }, is_error: true }
    if (chapter === undefined || chapter === null) return { content: { error: 'chapter is required' }, is_error: true }
    try {
      const mod = await import('@/lib/tools/classical_text_tools')
      const result = await (mod as unknown as { read_chapter: (args: { text_id: string; chapter: number }) => Promise<{ chunks: Array<{ content_en: string }> }> }).read_chapter({ text_id, chapter })
      return {
        content: {
          text_id,
          chapter,
          chunks: result.chunks.map((c: { content_en: string }) => ({ content: c.content_en })),
          returned_count: result.chunks.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), text_id, chapter }, is_error: true }
    }
  },
}

// E-2: list_classical_texts — global
const listClassicalTextsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/list_classical_texts',
  type: 'tool',
  layer: 'L0',
  name: 'list_classical_texts',
  scope: 'global',

  description: [
    'List all classical Jyotish texts ingested in the corpus with metadata.',
    'Returns text_id, title, author, language, chapter_count, verse_count, and other metadata.',
    'No filters required — returns the full text roster.',
    'Delegates to the Python sidecar classical text tools endpoint.',
    'Registry equivalent of lib/retrieve/index.ts::list_classical_texts (D7 gap fill).',
  ].join(' '),

  input_schema: {},

  required_inputs: [],

  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 40 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(_args: Record<string, unknown>, _ctx?: unknown) {
    try {
      const mod = await import('@/lib/tools/classical_text_tools')
      const result = await (mod as unknown as { list_classical_texts: () => Promise<{ texts: unknown[] }> }).list_classical_texts()
      return {
        content: {
          texts: result.texts,
          returned_count: result.texts.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// E-3: find_verses_about — global (embedding-similarity discovery)
const findVersesAboutCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/find_verses_about',
  type: 'tool',
  layer: 'L0',
  name: 'find_verses_about',
  scope: 'global',

  description: [
    'Discover classical text verses about a specific astrological topic using embedding similarity.',
    'Required: topic (free-text astrological topic, e.g. "Saturn in 7th house effects").',
    'Optional: text_ids (array — restrict search to specific texts), top_k (default 10, max 50).',
    'Returns ranked verses with source text key and confidence score.',
    'Distinct from query_classical_texts (which does keyword/ILIKE search) — this tool uses',
    'semantic vector similarity over embedded verse chunks.',
    'Registry equivalent of lib/retrieve/index.ts::find_verses_about (D7 gap fill).',
  ].join(' '),

  input_schema: {
    topic: {
      type: 'string',
      description: 'Free-text astrological topic to search for (e.g. "Saturn in 7th house effects"). Required.',
      required: true,
    },
    text_ids: {
      type: 'array',
      description: 'Restrict search to specific text IDs (e.g. ["bphs", "saravali"]). Optional.',
      items: { type: 'string' },
    },
    top_k: {
      type: 'number',
      description: 'Maximum verses to return (default: 10, max: 50).',
    },
  },

  required_inputs: ['topic'],

  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'hybrid_retrieval',
  emits_references: false,
  lel_capable: false,
  grounds_to: { l0_citation_ids: true },

  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: false },
    bulk_context: { pre_fetch_priority: 55 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const topic = args['topic'] as string | undefined
    if (!topic) return { content: { error: 'topic is required' }, is_error: true }
    const text_ids = Array.isArray(args['text_ids']) ? (args['text_ids'] as string[]) : undefined
    const top_k = Math.min(Number(args['top_k'] ?? 10), 50)
    try {
      const mod = await import('@/lib/tools/classical_text_tools')
      const result = await (mod as unknown as { find_verses_about: (args: { topic: string; text_ids?: string[]; top_k: number }) => Promise<{ results: Array<{ text: string; text_key: string; confidence_baseline: number }> }> }).find_verses_about({ topic, text_ids, top_k })
      return {
        content: {
          topic,
          text_ids: text_ids ?? 'all',
          top_k,
          results: result.results.map((r: { text: string; text_key: string; confidence_baseline: number }) => ({
            content: r.text,
            source_canonical_id: r.text_key,
            confidence: r.confidence_baseline,
          })),
          returned_count: result.results.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), topic }, is_error: true }
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
  // Wave A — sutravali (ported from lib/retrieve/sutravali_tools.ts)
  registerCapability(querySutravaliRulesTool)
  registerCapability(querySutravaliRulesForPlanetTool)
  registerCapability(readSutravaliRuleTool)
  registerCapability(listSutravaliRulesByTextTool)
  // Wave B — classical attribution (ported from lib/retrieve/classical_attribution_lookup_tool.ts)
  registerCapability(classicalAttributionLookupCapability)
  // Wave C — chart facts umbrella (B.11 floor injection target)
  registerCapability(chartFactsQueryCapability)
  // Wave D — remedy sub-tools (ported from lib/retrieve/remedy_tools.ts)
  registerCapability(queryRemediesForChartCapability)
  registerCapability(listRemediesByCategoryCapability)
  registerCapability(readRemedyCapability)
  registerCapability(queryTantricRemediesCapability)
  registerCapability(queryRemediesByPlanetCapability)
  registerCapability(queryMantrasCapability)
  // Wave E — classical text sub-tools (ported from lib/retrieve/index.ts CLASSICAL_TOOLS)
  registerCapability(readChapterCapability)
  registerCapability(listClassicalTextsCapability)
  registerCapability(findVersesAboutCapability)
}

/**
 * D7 capability URI roster (for Gate C reverse-citation checks and roster smoke tests).
 */
export const D7_CAPABILITY_URIS = [
  // Wiring
  'marsys://tool/channel/mcp_wiring',
  'marsys://tool/channel/chat_dispatch',
  // Wave A — sutravali
  'marsys://tool/L0/query_sutravali_rules',
  'marsys://tool/L0/query_sutravali_rules_for_planet',
  'marsys://tool/L0/read_sutravali_rule',
  'marsys://tool/L0/list_sutravali_rules_by_text',
  // Wave B — classical attribution
  'marsys://tool/L2/classical_attribution_lookup',
  // Wave C — chart facts
  'marsys://tool/L1/chart_facts_query',
  // Wave D — remedy sub-tools
  'marsys://tool/L0/query_remedies_for_chart',
  'marsys://tool/L0/list_remedies_by_category',
  'marsys://tool/L0/read_remedy',
  'marsys://tool/L0/query_tantric_remedies',
  'marsys://tool/L0/query_remedies_by_planet',
  'marsys://tool/L0/query_mantras',
  // Wave E — classical text sub-tools
  'marsys://tool/L0/read_chapter',
  'marsys://tool/L0/list_classical_texts',
  'marsys://tool/L0/find_verses_about',
] as const

// Auto-register on import — consistent with L0-L5 layer pattern (catalog.ts
// imports this file; the import alone triggers registration via this call).
registerD7ChannelCapabilities()
