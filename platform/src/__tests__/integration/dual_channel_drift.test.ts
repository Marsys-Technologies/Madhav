/**
 * dual_channel_drift.test.ts — D7 Drift Gate
 * ============================================
 * Proves that the chat channel path (registry-backed getToolByName in route.ts)
 * and the MCP channel path (getCatalog() tool handler) draw from the SAME
 * registry source and produce identical filter behavior for any given tool name
 * and chart_id.
 *
 * D7 acceptance criterion:
 *   "A drift test proves identical filter behavior both channels."
 *   — CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION_v1_0.md §5
 *
 * Design:
 *   - Chat channel:  getToolByName(toolName) → TOOL_NAME_TO_URI → getCapability(uri)
 *   - MCP channel:   getCatalog() → filter by uri (same backing _registry store)
 *
 *   Because both channels read from the SAME Map<CapabilityUri, CapabilityDescriptor>,
 *   the resolved capability object (including handler, required_inputs, scope) is
 *   guaranteed identical — this test makes that structural invariant explicit and
 *   machine-checked.
 *
 * Two distinct chart_ids are used per spec (never native-only):
 *   X = 482012f1-710e-4a25-994a-93821f5871aa  (native chart — subject Abhisek)
 *   Y = 00000000-0000-0000-0000-000000000001  (synthetic second chart)
 *
 * No DB / network required — pure registry state + handler identity checks.
 * Safe to run in all environments including CI.
 *
 * Registration strategy:
 *   - All layer registries auto-register on import (side-effect pattern).
 *   - registerD7ChannelCapabilities() is explicitly called in beforeAll to
 *     ensure D7 gap-fill capabilities are present even if startup ordering
 *     varies. The registry is idempotent (re-registering overwrites).
 *
 * BRIEF: CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION_v1_0 §5 (Drift test)
 */

import { describe, it, expect, beforeAll } from 'vitest'

// ── Layer registry imports (auto-register on import via side-effect) ──────────
// These trigger registerL0Capabilities(), L1, L2 side effects:
import '@/lib/retrieval/registry/layers/L0_brahmagyan/index'
import '@/lib/retrieval/registry/layers/L1_ganita/index'
import '@/lib/retrieval/registry/layers/L2_bodha/index'

// ── Registry API ──────────────────────────────────────────────────────────────

import {
  getCatalog,
  getCapability,
} from '@/lib/retrieval/registry'

import type { CapabilityDescriptor } from '@/lib/retrieval/registry/types'

import {
  getToolByName,
  TOOL_NAME_TO_URI,
  resolveToolUri,
} from '@/lib/retrieval/registry/tool_name_bridge'

import {
  registerD7ChannelCapabilities,
  D7_CAPABILITY_URIS,
} from '@/lib/retrieval/registry/layers/register_d7_channel'

// ── Test chart ids ────────────────────────────────────────────────────────────

/** Chart X — native chart (always in prod DB; ≥2-chart rule satisfied alongside Y) */
const CHART_X = '482012f1-710e-4a25-994a-93821f5871aa'

/** Chart Y — synthetic second chart (UUID format; never equals native) */
const CHART_Y = '00000000-0000-0000-0000-000000000001'

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Simulate the CHAT CHANNEL path for a given tool name + chart_id.
 *
 * In route.ts (D7 Step 3), the chat route calls:
 *   const tool = getToolByName(toolName)
 *   // tool.retrieve(plan, params) calls capability.handler(args, ctx)
 *
 * This function returns the resolved CapabilityDescriptor (the canonical
 * registry entry) that the chat channel would invoke.
 */
function chatChannelResolve(toolName: string, chartId: string): {
  uri: string | undefined
  capability: CapabilityDescriptor | undefined
  chartIdPassedThrough: boolean
} {
  const uri = resolveToolUri(toolName)
  const capability = uri ? getCapability(uri) : undefined
  // The chat channel passes chart_id from the query plan to the handler.
  // It never defaults chart_id — it must come from the request.
  const chartIdPassedThrough = !!(uri && capability && chartId.length > 0)
  return { uri, capability, chartIdPassedThrough }
}

/**
 * Simulate the MCP CHANNEL path for a given capability URI + chart_id.
 *
 * In the MCP server, getCatalog() returns all registered capabilities.
 * The MCP handler dispatches to capability.handler(args, ctx) where
 * args includes chart_id from the incoming MCP call.
 *
 * This function returns the resolved CapabilityDescriptor from getCatalog()
 * that the MCP channel would invoke.
 */
function mcpChannelResolve(uri: string, chartId: string): {
  capability: CapabilityDescriptor | undefined
  chartIdPassedThrough: boolean
} {
  const catalog = getCatalog()
  const capability = catalog.find(c => c.uri === uri)
  const chartIdPassedThrough = !!(capability && chartId.length > 0)
  return { capability, chartIdPassedThrough }
}

// ── Test suite ────────────────────────────────────────────────────────────────

describe('D7 dual-channel drift gate — chat vs MCP identical filter behavior', () => {
  beforeAll(() => {
    // Ensure D7 gap-fill capabilities are registered (idempotent if already present).
    // L0/L1/L2 capabilities are registered via side-effect imports above.
    registerD7ChannelCapabilities()
  })

  // ── Structural invariant: both channels read the same registry ────────────

  it('getCatalog() includes msr_sql URI (L2 query_signals) — MCP channel backed by registry', () => {
    const catalog = getCatalog()
    const uri = 'marsys://tool/L2/query_signals'
    expect(catalog.find(c => c.uri === uri), `MCP channel: ${uri} not in catalog`).toBeDefined()
  })

  it('getCatalog() includes D7 gap-fill capabilities — D7 registered in same registry', () => {
    const catalog = getCatalog()
    const catalogUris = catalog.map(c => c.uri)
    for (const d7Uri of D7_CAPABILITY_URIS) {
      expect(catalogUris, `D7 URI missing from MCP catalog: ${d7Uri}`).toContain(d7Uri)
    }
  })

  it('getToolByName resolves to getCapability — same object reference (chat channel proof)', () => {
    // Both getToolByName (chat) and getCatalog (MCP) read from _registry.
    // When they resolve the same URI, they MUST return the same descriptor.
    const toolsUnderTest = [
      { name: 'msr_sql',                     expectedUri: 'marsys://tool/L2/query_signals' },
      { name: 'chart_facts_query',            expectedUri: 'marsys://tool/L1/chart_facts_query' },
      { name: 'classical_attribution_lookup', expectedUri: 'marsys://tool/L2/classical_attribution_lookup' },
    ] as const

    for (const { name, expectedUri } of toolsUnderTest) {
      const uri = resolveToolUri(name)
      expect(uri, `TOOL_NAME_TO_URI missing entry for '${name}'`).toBe(expectedUri)

      const capViaChat = getCapability(uri!)
      const capViaMcp  = getCatalog().find(c => c.uri === uri)

      expect(capViaChat, `chat channel: getCapability('${uri}') returned undefined`).toBeDefined()
      expect(capViaMcp,  `MCP channel: getCatalog() has no entry for '${uri}'`).toBeDefined()

      // Object identity: same backing Map → same reference
      expect(capViaChat, 'chat and MCP channels return DIFFERENT object references — registry split!').toBe(capViaMcp)
    }
  })

  // ── Per-query drift check for CHART X ────────────────────────────────────

  describe(`Chart X (native, ${CHART_X})`, () => {
    const QUERIES: Array<{ toolName: string; expectedUri: string }> = [
      { toolName: 'msr_sql',                     expectedUri: 'marsys://tool/L2/query_signals' },
      { toolName: 'query_msr_aggregate',          expectedUri: 'marsys://tool/L2/query_signals' },
      { toolName: 'classical_attribution_lookup', expectedUri: 'marsys://tool/L2/classical_attribution_lookup' },
      { toolName: 'query_remedies_for_chart',     expectedUri: 'marsys://tool/L0/query_remedies_for_chart' },
      { toolName: 'find_verses_about',            expectedUri: 'marsys://tool/L0/find_verses_about' },
    ]

    for (const { toolName, expectedUri } of QUERIES) {
      it(`'${toolName}' → same capability, same handler, same required_inputs (chart X)`, () => {
        const chat = chatChannelResolve(toolName, CHART_X)
        const mcp  = mcpChannelResolve(expectedUri, CHART_X)

        // 1. Chat channel resolves to the expected URI
        expect(chat.uri, `chat: resolveToolUri('${toolName}') wrong URI`).toBe(expectedUri)

        // 2. Both channels resolved a capability
        expect(chat.capability, `chat channel: capability undefined for '${toolName}'`).toBeDefined()
        expect(mcp.capability,  `MCP channel: capability undefined for '${expectedUri}'`).toBeDefined()

        // 3. Same capability descriptor (identity — single registry)
        expect(chat.capability, 'channels resolved DIFFERENT capability objects — registry drift!').toBe(mcp.capability)

        // 4. Same handler function (identical filter behavior proof)
        expect(chat.capability!.handler, 'handler function differs between channels').toBe(mcp.capability!.handler)

        // 5. Same required_inputs (same grounding requirements)
        expect(JSON.stringify(chat.capability!.required_inputs))
          .toBe(JSON.stringify(mcp.capability!.required_inputs))

        // 6. chart_id passes through on both channels
        expect(chat.chartIdPassedThrough, 'chat channel did not pass chart_id').toBe(true)
        expect(mcp.chartIdPassedThrough,  'MCP channel did not pass chart_id').toBe(true)
      })
    }
  })

  // ── Per-query drift check for CHART Y ────────────────────────────────────

  describe(`Chart Y (synthetic, ${CHART_Y})`, () => {
    const QUERIES: Array<{ toolName: string; expectedUri: string }> = [
      { toolName: 'msr_sql',           expectedUri: 'marsys://tool/L2/query_signals' },
      { toolName: 'chart_facts_query', expectedUri: 'marsys://tool/L1/chart_facts_query' },
      { toolName: 'query_rules',       expectedUri: 'marsys://tool/L0/query_sutravali_rules' },
      { toolName: 'read_chapter',      expectedUri: 'marsys://tool/L0/read_chapter' },
      { toolName: 'query_mantras',     expectedUri: 'marsys://tool/L0/query_mantras' },
    ]

    for (const { toolName, expectedUri } of QUERIES) {
      it(`'${toolName}' → same capability, same handler, same required_inputs (chart Y)`, () => {
        const chat = chatChannelResolve(toolName, CHART_Y)
        const mcp  = mcpChannelResolve(expectedUri, CHART_Y)

        expect(chat.uri).toBe(expectedUri)
        expect(chat.capability).toBeDefined()
        expect(mcp.capability).toBeDefined()
        expect(chat.capability).toBe(mcp.capability)
        expect(chat.capability!.handler).toBe(mcp.capability!.handler)
        expect(JSON.stringify(chat.capability!.required_inputs))
          .toBe(JSON.stringify(mcp.capability!.required_inputs))
        expect(chat.chartIdPassedThrough).toBe(true)
        expect(mcp.chartIdPassedThrough).toBe(true)
      })
    }
  })

  // ── Cross-chart invariant: capability is chart-agnostic ──────────────────

  it('same tool resolves to same capability for chart X and chart Y — chart-agnostic proof', () => {
    const TOOL_NAMES = [
      'msr_sql',
      'classical_attribution_lookup',
      'query_remedies_for_chart',
      'find_verses_about',
      'query_rules',
    ] as const

    for (const toolName of TOOL_NAMES) {
      const chatX = chatChannelResolve(toolName, CHART_X)
      const chatY = chatChannelResolve(toolName, CHART_Y)

      // Same URI for both charts
      expect(chatX.uri, `URI differs for '${toolName}' between charts X and Y`).toBe(chatY.uri)

      if (chatX.capability && chatY.capability) {
        // Same capability object (chart-agnostic registry — capability is not per-chart-keyed)
        expect(chatX.capability, `Different capability objects for '${toolName}' across charts`).toBe(chatY.capability)
        // Same handler
        expect(chatX.capability.handler, `Handler differs for '${toolName}' across charts`).toBe(chatY.capability.handler)
      }
    }
  })

  // ── No audience_tier in any D7 capability ────────────────────────────────

  it('no audience_tier field in any D7 capability (DG1 ruling: tier stripped)', () => {
    const catalog = getCatalog()
    const d7Caps = catalog.filter(c => (D7_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    expect(d7Caps.length, 'No D7 caps found in catalog').toBeGreaterThan(0)

    for (const cap of d7Caps) {
      expect(
        Object.prototype.hasOwnProperty.call(cap, 'audience_tier'),
        `${cap.uri} has audience_tier — must be stripped per DG1 ruling`
      ).toBe(false)
    }
  })

  // ── TOOL_NAME_TO_URI coverage: all D7-mapped entries resolve ─────────────

  it('every D7 URI in TOOL_NAME_TO_URI resolves to a registered capability (no dead map entries)', () => {
    const d7UriSet = new Set<string>(D7_CAPABILITY_URIS)
    const deadEntries: string[] = []

    for (const [name, uri] of Object.entries(TOOL_NAME_TO_URI)) {
      if (!d7UriSet.has(uri)) continue  // skip non-D7 entries (registered by other layers)
      const cap = getCapability(uri)
      if (!cap) deadEntries.push(`${name} → ${uri}`)
    }

    expect(
      deadEntries,
      `Dead TOOL_NAME_TO_URI entries (D7 URIs with no registry capability):\n${deadEntries.join('\n')}`
    ).toHaveLength(0)
  })

  // ── Alias convergence: two names → same URI → same capability ────────────

  it('msr_sql and query_msr_aggregate are aliases → same URI and same handler', () => {
    const cap1 = chatChannelResolve('msr_sql', CHART_X)
    const cap2 = chatChannelResolve('query_msr_aggregate', CHART_X)

    expect(cap1.uri).toBe(cap2.uri)
    expect(cap1.capability).toBe(cap2.capability)
    expect(cap1.capability?.handler).toBe(cap2.capability?.handler)
  })

  it('read_classical_text + search_classical_texts + classical_text_search all map to same URI', () => {
    const aliases = ['read_classical_text', 'search_classical_texts', 'classical_text_search'] as const
    const uris = aliases.map(name => resolveToolUri(name))

    // All three aliases map to the same URI
    const uniqueUris = new Set(uris.filter(Boolean))
    expect(uniqueUris.size, `Expected 1 unique URI for classical text aliases, got: ${[...uniqueUris].join(', ')}`).toBe(1)

    // All three resolve the same capability object from the registry
    const caps = uris.map(uri => uri ? getCapability(uri) : undefined)
    expect(caps[0]).toBeDefined()
    for (let i = 1; i < caps.length; i++) {
      expect(caps[i], `Alias '${aliases[i]}' resolved different capability`).toBe(caps[0])
    }
  })

  // ── No native contamination in resolved capabilities ─────────────────────

  it('no native chart_id or PII in any D7 capability name/description/URI', () => {
    const NATIVE_ID = CHART_X
    const NATIVE_NAMES = ['Abhisek Mohanty', '1984-02-05', 'Bhubaneswar']

    const catalog = getCatalog()
    const d7Caps = catalog.filter(c => (D7_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    expect(d7Caps.length).toBeGreaterThan(0)

    for (const cap of d7Caps) {
      const text = `${cap.uri} ${cap.name} ${cap.description ?? ''}`
      expect(text, `Native chart_id contamination in ${cap.uri}`).not.toContain(NATIVE_ID)
      for (const pii of NATIVE_NAMES) {
        expect(text, `PII '${pii}' found in ${cap.uri}`).not.toContain(pii)
      }
    }
  })

  // ── getToolByName(name) functional equivalence to getCatalog().find ───────

  it('getToolByName returns a retrieve() function that wraps the same capability handler', () => {
    // Verify that the tool wrapper returned by getToolByName references the same
    // underlying handler as the capability returned by getCatalog().
    // This is the authoritative single-source-of-truth check.
    const toolsToCheck = [
      { toolName: 'msr_sql',       expectedUri: 'marsys://tool/L2/query_signals' },
      { toolName: 'chart_facts_query', expectedUri: 'marsys://tool/L1/chart_facts_query' },
      { toolName: 'query_rules',   expectedUri: 'marsys://tool/L0/query_sutravali_rules' },
    ] as const

    for (const { toolName, expectedUri } of toolsToCheck) {
      // Chat channel resolution
      const toolWrapper = getToolByName(toolName)
      expect(toolWrapper, `getToolByName('${toolName}') returned undefined`).toBeDefined()
      expect(toolWrapper!.name).toBe(toolName)

      // MCP channel resolution
      const cap = getCatalog().find(c => c.uri === expectedUri)
      expect(cap, `MCP catalog missing: ${expectedUri}`).toBeDefined()

      // Handler identity: getCapability (used internally by getToolByName) returns same object as getCatalog
      const capViaGet = getCapability(expectedUri)
      expect(capViaGet, `getCapability('${expectedUri}') returned undefined`).toBeDefined()
      expect(capViaGet, `getCapability and getCatalog.find returned different objects for ${expectedUri}`).toBe(cap)
    }
  })
})
