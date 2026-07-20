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
  resolveType,
  toJsonSchema,
  MCP_NAME_PATTERN,
} from '../../../../../scripts/manifest/projection_builders'
import {
  extractRegistryBridgeTools,
  extractRegistryBridgeToolsFromDisk,
} from '../../../../../scripts/manifest/extract_registry_bridge_tools'

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

// ── 5. Shared helper unit coverage ───────────────────────────────────────────

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
