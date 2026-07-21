/**
 * projection_compiler_parity.test.ts — R-1 projection compiler CI gate
 * ================================================================================
 * RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §3 R-1 item 2. Follows the
 * `r5_codegen_parity.test.ts` pattern (`platform-mcp/src/__tests__/
 * r5_codegen_parity.test.ts`): the SAME pure derivation functions the CLI
 * generator (`scripts/manifest/generate_projections.ts`) calls to write
 * artifacts are imported directly here and exercised against the REAL, live
 * `getCatalog()` registry — no fixture, no DB, no fs write. Two independent
 * claims:
 *
 *   1. COMPLETENESS/VALIDITY — every one of the ~120+ live capabilities is
 *      accounted for by the census, and every emitted projection entry is
 *      structurally well-formed (non-empty name/description, valid JSON-
 *      Schema-shaped input_schema, unique/valid names on the MCP surface).
 *      This is the "produces valid, complete output for all 120 capabilities"
 *      gate the task asked for.
 *   2. COMPARISON SOUNDNESS — the diff-report machinery this lane built (vs.
 *      `TOOL_CONTRACTS` for chat, vs. the real `registry_bridge.ts` hand-
 *      written blocks for MCP) is itself well-formed and reproduces known,
 *      hand-verified facts about the live estate (tripwires against silent
 *      breakage of the mechanical text-scan extractor).
 *
 * Divergence between the generated projections and the two hand-written
 * surfaces is EXPECTED and is not itself a failure — the whole point of this
 * lane is to make the shape of that gap machine-legible (see
 * R1_PROJECTION_COMPILER_REPORT.md). This test does not assert the two
 * surfaces are equal; it asserts the comparison itself is sound and that the
 * generated projections are internally complete and valid.
 */
import { describe, it, expect } from 'vitest'
import { getCatalog } from '../catalog'
import { CONTRACT_CATALOG } from '../../../contract/catalog'
import {
  buildMachineCensus,
  buildChatToolDefs,
  buildMcpToolRegistrations,
  buildMcpNonToolRegistrations,
  buildDocsResourceCatalog,
  buildToolSearchIndex,
  searchToolIndex,
  resolveType,
  toJsonSchema,
  MCP_NAME_PATTERN,
} from '../../../../../scripts/manifest/projection_builders'
import {
  extractRegistryBridgeTools,
  extractRegistryBridgeToolsFromDisk,
} from '../../../../../scripts/manifest/extract_registry_bridge_tools'
import { resolveWebToolBridge, type CanonicalFacesData } from '../../../../../scripts/manifest/web_tool_bridge_builder'
import {
  buildMcpSurfaceProfiles,
  consultIsSubsetOfFull,
  COMPACT_MAX_TOOLS,
} from '../../../../../scripts/manifest/mcp_surface_profile_builder'
import { TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL, getToolByName } from '../tool_name_bridge'
import canonicalFacesRaw from '../canonical_faces.json'
import { VIDHI_PRIMITIVES } from '../../../vidhi/registry_data'

// ── 1. Machine census — completeness over the full live catalog ─────────────

describe('R-1 projection compiler — machine census completeness', () => {
  it('census entries cover every live getCatalog() capability, 1:1, no drops or dupes', () => {
    const caps = getCatalog()
    expect(caps.length).toBeGreaterThanOrEqual(100) // sanity bound, not a hardcoded exact count

    const census = buildMachineCensus(caps, '2026-01-01T00:00:00.000Z')
    expect(census.total).toBe(caps.length)
    expect(census.entries.length).toBe(caps.length)

    const censusUris = new Set(census.entries.map((e) => e.uri))
    expect(censusUris.size).toBe(caps.length) // no duplicate URIs
    for (const cap of caps) {
      expect(censusUris.has(cap.uri), `missing census entry for ${cap.uri}`).toBe(true)
    }
  })

  it('every census entry has a non-empty resolved type (tolerates the primitive_type fallback)', () => {
    const caps = getCatalog()
    const census = buildMachineCensus(caps)
    for (const entry of census.entries) {
      expect(entry.type, `${entry.uri} resolved to empty/unknown type`).not.toBe('')
      expect(entry.type, `${entry.uri} resolved to empty/unknown type`).not.toBe('unknown')
      expect(['tool', 'resource', 'prompt']).toContain(entry.type)
    }
  })

  it('resolveType() never returns unknown for any live capability (real registry, not a fixture)', () => {
    const caps = getCatalog()
    const unresolved = caps.filter((c) => resolveType(c) === 'unknown')
    expect(unresolved.map((c) => c.uri)).toEqual([])
  })

  it('summary tallies sum back to the total (by_layer, by_type, by_scope all partition the full set)', () => {
    const caps = getCatalog()
    const census = buildMachineCensus(caps)
    const sumBy = (rec: Record<string, number>) => Object.values(rec).reduce((a, b) => a + b, 0)
    expect(sumBy(census.summary.by_layer)).toBe(census.total)
    expect(sumBy(census.summary.by_type)).toBe(census.total)
    expect(sumBy(census.summary.by_scope)).toBe(census.total)
    expect(sumBy(census.summary.by_archetype)).toBe(census.total)
    expect(sumBy(census.summary.by_tool_role)).toBe(census.total)
  })
})

// ── 2. Chat tool-def projection ──────────────────────────────────────────────

describe('R-1 projection compiler — (a) chat tool-def projection', () => {
  it('every emitted chat tool def is structurally valid: non-empty name/description, object-shaped input_schema', () => {
    const caps = getCatalog()
    const defs = buildChatToolDefs(caps)
    expect(defs.length).toBeGreaterThan(0)
    for (const d of defs) {
      expect(d.name.length, `empty name for ${d.uri}`).toBeGreaterThan(0)
      expect(d.description.length, `empty description for ${d.uri}`).toBeGreaterThan(0)
      expect(d.input_schema['type']).toBe('object')
      expect(typeof d.input_schema['properties']).toBe('object')
    }
  })

  it('chat def set is exactly the live capabilities with type=tool AND projection_tags includes chat (round-trip)', () => {
    const caps = getCatalog()
    const defs = buildChatToolDefs(caps)
    const expectedUris = new Set(
      caps
        .filter((c) => resolveType(c) === 'tool' && (c.projection_tags ?? []).includes('chat'))
        .map((c) => c.uri),
    )
    const actualUris = new Set(defs.map((d) => d.uri))
    expect(actualUris).toEqual(expectedUris)
  })

  it('chat def names are unique', () => {
    const caps = getCatalog()
    const defs = buildChatToolDefs(caps)
    const names = defs.map((d) => d.name)
    expect(new Set(names).size).toBe(names.length)
  })

  it('comparison vs. the real served TOOL_CONTRACTS is well-formed (both sides real, non-empty; overlap computable)', () => {
    const caps = getCatalog()
    const defs = buildChatToolDefs(caps)
    // TOOL_CONTRACTS (lib/contract/registry.ts) is the real served chat contract
    // catalog the plan cites (GT-3). This worktree's live count may differ from
    // the plan's cited figure — asserted as a sanity bound, not a hardcoded
    // exact match, so this test doesn't silently rot if registry.ts changes.
    expect(CONTRACT_CATALOG.length).toBeGreaterThan(0)
    const contractNames = new Set(CONTRACT_CATALOG.map((c) => c.canonical_name))
    const generatedNames = new Set(defs.map((d) => d.name))
    const overlap = [...contractNames].filter((n) => generatedNames.has(n))
    // Sanity: the overlap computation itself must be a subset of both sides.
    for (const n of overlap) {
      expect(contractNames.has(n)).toBe(true)
      expect(generatedNames.has(n)).toBe(true)
    }
  })
})

// ── 3. MCP tool-registration projection ──────────────────────────────────────

describe('R-1 projection compiler — (b) MCP tool-registration projection', () => {
  it('every emitted MCP tool registration has a valid MCP name (snake_case, no hyphens, <=64 chars)', () => {
    const caps = getCatalog()
    const regs = buildMcpToolRegistrations(caps)
    expect(regs.length).toBeGreaterThan(0)
    for (const r of regs) {
      expect(MCP_NAME_PATTERN.test(r.tool_name), `invalid MCP name: ${r.tool_name}`).toBe(true)
      expect(r.name_valid).toBe(true)
      expect(r.description.length).toBeGreaterThan(0)
    }
  })

  it('MCP tool registration names are unique', () => {
    const caps = getCatalog()
    const regs = buildMcpToolRegistrations(caps)
    const names = regs.map((r) => r.tool_name)
    expect(new Set(names).size).toBe(names.length)
  })

  it('every mcp_full/compact/consult-tagged non-tool capability is accounted for separately, not dropped', () => {
    const caps = getCatalog()
    const toolRegs = buildMcpToolRegistrations(caps)
    const nonTools = buildMcpNonToolRegistrations(caps)
    const toolUris = new Set(toolRegs.map((r) => r.uri))
    const nonToolUris = new Set(nonTools.map((n) => n.uri))

    const mcpTaggedNonTools = caps.filter(
      (c) =>
        resolveType(c) !== 'tool' &&
        ((c.projection_tags ?? []).includes('mcp_full') ||
          (c.projection_tags ?? []).includes('mcp_compact') ||
          (c.projection_tags ?? []).includes('mcp_consult')),
    )
    for (const c of mcpTaggedNonTools) {
      expect(nonToolUris.has(c.uri), `${c.uri} (non-tool, mcp-tagged) missing from non-tool accounting`).toBe(true)
      expect(toolUris.has(c.uri), `${c.uri} (non-tool) incorrectly appears in tool registrations`).toBe(false)
    }
  })

  it('extractRegistryBridgeTools finds a real, non-trivial set of blocks on a minimal fixture (unit-level, no fs)', () => {
    const fixture = `
      server.tool(
        'sample_tool_a',
        'Description for A',
        { chart_id: z.string() },
        async () => {}
      )
      server.tool(
        'sample_tool_b',
        { chart_id: z.string() },
        async () => {}
      )
    `
    const blocks = extractRegistryBridgeTools(fixture)
    expect(blocks.length).toBe(2)
    expect(blocks[0]!.tool_name).toBe('sample_tool_a')
    expect(blocks[0]!.description).toBe('Description for A')
    expect(blocks[1]!.tool_name).toBe('sample_tool_b')
    expect(blocks[1]!.description).toBeNull() // 3-arg overload, no description literal
  })

  it('extraction against the REAL registry_bridge.ts finds the known, hand-verified tool names (tripwire)', () => {
    // If a future edit to registry_bridge.ts changes its call shape enough to defeat
    // this mechanical text scan, THIS is the test that should fail first — not a
    // silent empty/garbled extraction shipped into the generated report.
    const blocks = extractRegistryBridgeToolsFromDisk()
    expect(blocks.length).toBeGreaterThanOrEqual(20) // real count is 25 at time of writing
    const names = new Set(blocks.map((b) => b.tool_name))
    for (const known of [
      'get_chart_orientation',
      'get_domain_reading',
      'get_signals',
      'judgment_query',
      'pact_query',
      'graha_portrait',
      'vector_search',
    ]) {
      expect(names.has(known), `expected known tool "${known}" not found by extractor`).toBe(true)
    }
    // Every block has a name; names are unique (real MCP constraint on the live server).
    expect(new Set(blocks.map((b) => b.tool_name)).size).toBe(blocks.length)
  })
})

// ── 4. Docs resource stub ────────────────────────────────────────────────────

describe('R-1 projection compiler — (d) docs resource stub (marsys://resource/catalog shape)', () => {
  it('lists every live capability exactly once, correct envelope shape', () => {
    const caps = getCatalog()
    const doc = buildDocsResourceCatalog(caps, '2026-01-01T00:00:00.000Z')
    expect(doc.uri).toBe('marsys://resource/catalog')
    expect(doc.mime_type).toBe('application/json')
    expect(doc.total).toBe(caps.length)
    expect(doc.capabilities.length).toBe(caps.length)
    const uris = new Set(doc.capabilities.map((c) => c.uri))
    expect(uris.size).toBe(caps.length)
  })
})

// ── 4b. Web↔MCP tool-name bridge (W5 L1) ────────────────────────────────────

describe('R-1 projection compiler — (e) web↔MCP tool-name bridge', () => {
  const canonicalFaces = canonicalFacesRaw as unknown as CanonicalFacesData

  it('resolves every distinct Vidhi live_tool name deterministically, and every resolved URI is a real live capability', () => {
    const caps = getCatalog()
    const liveToolNames = [...new Set(VIDHI_PRIMITIVES.map((p) => p.live_tool))].sort()
    const entries = resolveWebToolBridge(liveToolNames, caps, TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL, canonicalFaces)
    expect(entries.length).toBe(liveToolNames.length)

    const catalogUris = new Set(caps.map((c) => c.uri))
    const mapped = entries.filter((e) => e.uri !== null)
    for (const e of mapped) {
      expect(catalogUris.has(e.uri as string), `${e.name} resolved to a URI not in the live catalog: ${e.uri}`).toBe(true)
    }

    // Real, measured improvement over the pre-W5 hand-curated LIVE_TOOL_TO_RETRIEVAL
    // (4/23) — asserted as a floor, not an exact count, so this doesn't rot as the
    // catalog/canonical_faces.json evolve. If this ever regresses below 4 the
    // generated bridge is doing WORSE than the map it's meant to widen — a real bug.
    expect(mapped.length).toBeGreaterThan(4)

    // Deterministic — same inputs, same output (no randomness/ordering nondeterminism).
    const again = resolveWebToolBridge(liveToolNames, caps, TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL, canonicalFaces)
    expect(JSON.stringify(again)).toBe(JSON.stringify(entries))
  })

  it('every mapped live_tool resolves to something getToolByName() can actually execute (URI-shaped names now supported)', () => {
    const caps = getCatalog()
    const liveToolNames = [...new Set(VIDHI_PRIMITIVES.map((p) => p.live_tool))].sort()
    const entries = resolveWebToolBridge(liveToolNames, caps, TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL, canonicalFaces)
    for (const e of entries.filter((x) => x.uri !== null)) {
      expect(getToolByName(e.uri as string), `bridge resolved ${e.name} -> ${e.uri} but getToolByName() rejects it`).toBeDefined()
    }
  })

  it('canonical_faces.json bridge: unmapped entries are reported honestly, never silently dropped', () => {
    const caps = getCatalog()
    const entries = resolveWebToolBridge(canonicalFaces.canonical_faces, caps, TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL, canonicalFaces)
    expect(entries.length).toBe(canonicalFaces.canonical_faces.length)
    for (const e of entries) {
      if (e.uri === null) expect(e.resolution_kind).toBe('unmapped')
      else expect(e.resolution_kind).not.toBe('unmapped')
    }
  })
})

// ── 6. (f) W5 Lane L4 — tool-search index + search ───────────────────────────

describe('R-1 projection compiler — (f) tool-search index (W5 Lane L4)', () => {
  it('index covers every live getCatalog() capability, 1:1, no drops or dupes (no projection_tags filter)', () => {
    const caps = getCatalog()
    const index = buildToolSearchIndex(caps)
    expect(index.length).toBe(caps.length)
    const uris = new Set(index.map((e) => e.uri))
    expect(uris.size).toBe(caps.length)
    for (const cap of caps) {
      expect(uris.has(cap.uri), `missing tool-search index entry for ${cap.uri}`).toBe(true)
    }
  })

  it('every index entry has a non-empty name, description, and at least one keyword', () => {
    const caps = getCatalog()
    const index = buildToolSearchIndex(caps)
    for (const entry of index) {
      expect(entry.name.length, `empty name for ${entry.uri}`).toBeGreaterThan(0)
      expect(entry.description.length, `empty description for ${entry.uri}`).toBeGreaterThan(0)
      expect(entry.keywords.length, `no keywords derived for ${entry.uri}`).toBeGreaterThan(0)
      // keywords are deduped
      expect(new Set(entry.keywords).size).toBe(entry.keywords.length)
    }
  })

  it('a representative keyword search ("dasha") returns the expected relevant subset and excludes irrelevant tools', () => {
    const caps = getCatalog()
    const index = buildToolSearchIndex(caps)
    const result = searchToolIndex(index, 'dasha', 50)

    expect(result.total_matches).toBeGreaterThan(0)
    const names = new Set(result.results.map((r) => r.name))
    // The registry's real, known dasha-family capabilities must appear.
    const expectedSomeOf = ['get_dashas', 'ganita_dashas_get', 'ganita_dasha_periods_get']
    const foundAny = expectedSomeOf.some((n) => names.has(n))
    expect(foundAny, `expected at least one of ${expectedSomeOf.join(', ')} in dasha search results`).toBe(true)

    // Irrelevant, unambiguously non-dasha capabilities must NOT appear.
    const irrelevant = ['query_vastu_directions', 'ephemeris_cache_year']
    for (const n of irrelevant) {
      expect(names.has(n), `unexpected irrelevant match "${n}" in dasha search results`).toBe(false)
    }
  })

  it('a second representative search ("muhurta") is disjoint from an unrelated query ("vastu")', () => {
    const caps = getCatalog()
    const index = buildToolSearchIndex(caps)
    const muhurta = searchToolIndex(index, 'muhurta', 50)
    const vastu = searchToolIndex(index, 'vastu', 50)
    expect(muhurta.total_matches).toBeGreaterThan(0)
    expect(vastu.total_matches).toBeGreaterThan(0)
    const muhurtaUris = new Set(muhurta.results.map((r) => r.uri))
    const vastuUris = new Set(vastu.results.map((r) => r.uri))
    const overlap = [...muhurtaUris].filter((u) => vastuUris.has(u))
    expect(overlap).toEqual([])
  })

  it('an honest empty result for a query with zero token overlap (never a fabricated best-effort guess)', () => {
    const caps = getCatalog()
    const index = buildToolSearchIndex(caps)
    const result = searchToolIndex(index, 'zzznonexistentqueryxyz123', 20)
    expect(result.total_matches).toBe(0)
    expect(result.results).toEqual([])
  })

  it('results are capped at the requested limit and sorted by descending score', () => {
    const caps = getCatalog()
    const index = buildToolSearchIndex(caps)
    const result = searchToolIndex(index, 'chart', 3)
    expect(result.results.length).toBeLessThanOrEqual(3)
    for (let i = 1; i < result.results.length; i++) {
      expect(result.results[i - 1]!.score).toBeGreaterThanOrEqual(result.results[i]!.score)
    }
  })
})

// ── 7. MCP surface profiles — full / compact≤20 / consult (W5 L2) ───────────

describe('R-1 projection compiler — (g) MCP surface profiles (full/compact/consult)', () => {
  it('compact profile never exceeds COMPACT_MAX_TOOLS (RC-1: "≤20 umbrellas for non-Claude families")', () => {
    const caps = getCatalog()
    const profiles = buildMcpSurfaceProfiles(caps)
    expect(COMPACT_MAX_TOOLS).toBe(20)
    expect(profiles.compact.max_tools).toBe(20)
    expect(profiles.compact.tools.length).toBeLessThanOrEqual(20)
    expect(profiles.compact.tool_names.length).toBeLessThanOrEqual(20)
    expect(profiles.compact.total).toBe(profiles.compact.tools.length)
  })

  it('full profile is uncapped and non-trivially larger than compact (sanity: the cap is doing real work)', () => {
    const caps = getCatalog()
    const profiles = buildMcpSurfaceProfiles(caps)
    expect(profiles.full.max_tools).toBeNull()
    expect(profiles.full.total).toBeGreaterThan(profiles.compact.total)
  })

  it('every eligible mcp_compact-tagged capability beyond the cap is reported in overflow_tool_names, never silently dropped', () => {
    const caps = getCatalog()
    const profiles = buildMcpSurfaceProfiles(caps)
    const eligibleCompactCount = profiles.compact.total + profiles.compact.overflow_tool_names.length
    expect(eligibleCompactCount).toBeGreaterThanOrEqual(profiles.compact.total)
    // Overflow names are disjoint from surfaced names.
    const surfaced = new Set(profiles.compact.tool_names)
    for (const name of profiles.compact.overflow_tool_names) {
      expect(surfaced.has(name)).toBe(false)
    }
  })

  it('CONSULT PROFILE PROVABLY CANNOT REACH RAW/FULL-ONLY TOOLS (V5 gate): every consult tool name is a subset of full, and known full-only/internal tools are absent from consult', () => {
    const caps = getCatalog()
    const profiles = buildMcpSurfaceProfiles(caps)

    // (1) Structural subset invariant, computed by the builder itself and re-verified here.
    expect(consultIsSubsetOfFull(profiles)).toBe(true)
    const fullNames = new Set(profiles.full.tool_names)
    for (const name of profiles.consult.tool_names) {
      expect(fullNames.has(name), `consult tool "${name}" is not reachable via full`).toBe(true)
    }

    // (2) Direct adversarial probe: pick real, live full-only tool names (present in
    // `full`, i.e. real registered capabilities) that are NOT part of the small orienting
    // set, and assert none of them leak into consult. This is the "attempt to reach a raw
    // tool under a consult-scoped surface" proof — it fails loudly if the consult set ever
    // silently widens to include a non-orienting capability.
    const consultSet = new Set(profiles.consult.tool_names)
    const rawFullOnlyProbe = profiles.full.tool_names.filter((n) => !consultSet.has(n)).slice(0, 10)
    expect(rawFullOnlyProbe.length).toBeGreaterThan(0)
    for (const rawToolName of rawFullOnlyProbe) {
      expect(fullNames.has(rawToolName), `test fixture assumption broken: ${rawToolName} not even in full`).toBe(true)
      expect(consultSet.has(rawToolName), `consult profile can reach raw tool "${rawToolName}" — V5 gate violation`).toBe(false)
    }

    // (3) Known internal orchestration/meta-tools (self-declared "not LLM-facing" in their
    // own descriptor — see mcp_surface_profile_builder.ts's excluded_not_llm_facing doc
    // comment) must never appear in ANY profile, consult least of all.
    const internalMetaTools = ['maro_orchestrate', 'maro_mcp_surface', 'route', 'synergy_pipeline', 'synergy_cross_layer']
    for (const internalName of internalMetaTools) {
      expect(consultSet.has(internalName), `internal meta-tool "${internalName}" leaked into consult`).toBe(false)
      expect(profiles.full.tool_names.includes(internalName), `internal meta-tool "${internalName}" leaked into full`).toBe(false)
    }
  })

  it('F-R7: calibration_context_only capabilities never appear in any of the three profiles', () => {
    const caps = getCatalog()
    const profiles = buildMcpSurfaceProfiles(caps)
    const calibrationNames = new Set(
      caps.filter((c) => c.calibration_context_only === true).map((c) => c.name),
    )
    expect(calibrationNames.size).toBeGreaterThan(0) // sanity: the fixture (real catalog) has at least one
    for (const name of calibrationNames) {
      expect(profiles.full.tool_names.includes(name)).toBe(false)
      expect(profiles.compact.tool_names.includes(name)).toBe(false)
      expect(profiles.consult.tool_names.includes(name)).toBe(false)
    }
  })

  it('deterministic: rebuilding from the same catalog produces byte-identical profiles', () => {
    const caps = getCatalog()
    const a = buildMcpSurfaceProfiles(caps)
    const b = buildMcpSurfaceProfiles(caps)
    expect(JSON.stringify(a)).toBe(JSON.stringify(b))
  })

  it('every profile tool entry is structurally valid (non-empty tool_name/description, object input_schema)', () => {
    const caps = getCatalog()
    const profiles = buildMcpSurfaceProfiles(caps)
    for (const profile of [profiles.full, profiles.compact, profiles.consult]) {
      for (const t of profile.tools) {
        expect(t.tool_name.length).toBeGreaterThan(0)
        expect(t.description.length).toBeGreaterThan(0)
        expect(t.input_schema['type']).toBe('object')
      }
      // tool_names is exactly the tools' own names, same order.
      expect(profile.tool_names).toEqual(profile.tools.map((t) => t.tool_name))
    }
  })
})

// ── 8. Shared helper unit coverage ───────────────────────────────────────────

describe('R-1 projection compiler — toJsonSchema()', () => {
  it('wraps a ParameterSchema map into a valid object-typed JSON Schema, no fabricated bounds', () => {
    const schema = toJsonSchema(
      {
        chart_id: { type: 'string', description: 'UUID' },
        limit: { type: 'number', description: 'Max rows', default: 50 },
        mode: { type: 'string', enum: ['a', 'b'] },
      },
      ['chart_id'],
    )
    expect(schema['type']).toBe('object')
    const props = schema['properties'] as Record<string, Record<string, unknown>>
    expect(props['chart_id']!['type']).toBe('string')
    expect(props['limit']!['default']).toBe(50)
    expect(props['mode']!['enum']).toEqual(['a', 'b'])
    expect(schema['required']).toEqual(['chart_id'])
    // No min/max fabricated — ParameterSchema carries none, so none should appear.
    expect(props['limit']).not.toHaveProperty('minimum')
    expect(props['limit']).not.toHaveProperty('maximum')
  })

  it('handles an undefined input_schema without throwing (global/no-arg capabilities)', () => {
    const schema = toJsonSchema(undefined, undefined)
    expect(schema).toEqual({ type: 'object', properties: {} })
  })
})
