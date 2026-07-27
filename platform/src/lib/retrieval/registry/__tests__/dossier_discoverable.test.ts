/**
 * dossier_discoverable.test.ts — PARIŚODHANA B2 (Reachability Triangle, T1-1).
 * ================================================================================
 * Locks the discoverability fix: `dossier` (a platform-mcp-native `server.tool` with
 * NO registry `CapabilityDescriptor`) is findable via `tool_search`. Before this fix,
 * a tool-searching agent asking "how is my wealth?" / "assess my career fully" got only
 * the atom tools and never the ONE tool that serves the WHOLE domain concept slice at
 * 100% completeness accounting — γ's tool-searching consumer scored ~15% precisely
 * because it could not reach `dossier`.
 *
 * These assertions run against the REAL live registry (getCatalog(), no DB, no network)
 * and the SAME `buildToolSearchIndex` the live `tool_search` capability and the projection
 * compiler both call — so a green here means the served surface is fixed, not a fixture.
 */
import { describe, it, expect } from 'vitest'
import { getCatalog } from '../catalog'
import { buildToolSearchIndex, searchToolIndex, MCP_NATIVE_DISCOVERY_ENTRIES } from '../tool_search'

describe('dossier discoverability via tool_search (PARIŚODHANA B2)', () => {
  const index = buildToolSearchIndex(getCatalog())

  const namesFor = (query: string): Set<string> =>
    new Set(searchToolIndex(index, query, 50).results.map((r) => r.name))

  it.each([
    ['wealth'],
    ['career'],
    ['complete domain reading'],
    ['completeness'],
    ['dossier'],
    ['whole picture of my finances'],
  ])('a tool_search for %j surfaces the dossier discovery entry', (query) => {
    expect(namesFor(query).has('dossier')).toBe(true)
  })

  it('the dossier entry carries its MCP-native discovery URI (not a registry marsys://tool/L*/... URI)', () => {
    const hit = searchToolIndex(index, 'dossier', 50).results.find((r) => r.name === 'dossier')
    expect(hit).toBeDefined()
    expect(hit!.uri).toBe('marsys://tool/MCP/dossier')
  })

  it('the supplement is a single, well-formed entry (honest — not a fabricated registry capability)', () => {
    expect(MCP_NATIVE_DISCOVERY_ENTRIES).toHaveLength(1)
    const [entry] = MCP_NATIVE_DISCOVERY_ENTRIES
    expect(entry!.uri).toBe('marsys://tool/MCP/dossier')
    expect(entry!.layer).toBe('MCP')
    expect(entry!.name.length).toBeGreaterThan(0)
    expect(entry!.description.length).toBeGreaterThan(0)
    expect(entry!.keywords.length).toBeGreaterThan(0)
    // keywords are deduped + sorted (same discipline as the registry-derived entries)
    expect(new Set(entry!.keywords).size).toBe(entry!.keywords.length)
    expect([...entry!.keywords]).toEqual([...entry!.keywords].sort())
  })

  it('the dossier entry does NOT collide with any registry capability URI (getCatalog() is unchanged)', () => {
    const catalogUris = new Set(getCatalog().map((c) => c.uri))
    for (const entry of MCP_NATIVE_DISCOVERY_ENTRIES) {
      expect(catalogUris.has(entry.uri)).toBe(false)
    }
  })

  it('a nonsense query still returns an honest empty result (the supplement never becomes a catch-all)', () => {
    const r = searchToolIndex(index, 'zzznonexistentqueryxyz123', 20)
    expect(r.total_matches).toBe(0)
    expect(r.results).toEqual([])
  })
})
