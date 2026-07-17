/**
 * alias_check.test.ts — D-2 Lane V-0 (BIND_D-2.md §F1.7 ledger row 4).
 *
 * V-3 (cycle-2) has now shipped its authored canonical-face list at
 * platform/src/lib/retrieval/registry/canonical_faces.json, so the mechanical-fallback stub
 * branch these tests originally exercised is DEACTIVATED (loadCanonicalFacesFile() finds the
 * file). This suite now asserts the `v3_canonical_face_list` branch: the check reconciles live
 * tools against V-3's authored canonical set + declared deprecations. The fixture `tools` arrays
 * supply only the live tool names; the canonical/deprecated sets come from the shipped file.
 */
import { describe, it, expect } from 'vitest'
import { checkAliasCount, loadCanonicalFacesFile } from '../alias_check.js'
import type { McpToolDescriptor } from '../mcp_client.js'

describe('alias_check — v3_canonical_face_list branch (authored list shipped)', () => {
  it('loads V-3\'s authored canonical-face file (confirms the stub branch is now deactivated)', () => {
    const file = loadCanonicalFacesFile()
    expect(file).not.toBeNull()
    expect(file!.canonical_faces.length).toBeGreaterThan(0)
    // Sanity: the file is internally self-consistent — every deprecated alias maps to a name
    // that is itself in the canonical set (no dangling targets).
    const canonicalSet = new Set(file!.canonical_faces)
    for (const target of Object.values(file!.deprecated_aliases)) {
      expect(canonicalSet.has(target)).toBe(true)
    }
  })

  it('reconciles live tools that are all accounted-for (canonical or declared deprecated alias)', () => {
    const tools: McpToolDescriptor[] = [
      { name: 'bodha_signals_get', description: 'Primary signal reader.' },
      { name: 'get_signals', description: '[Phase-1 alias] Legacy name (same as bodha_signals_get).' },
      { name: 'ganita_natal_positions_compute', description: 'Primary positions reader.' },
      { name: 'compute_natal_positions', description: '[Phase-1 alias] Legacy name (same as ganita_natal_positions_compute).' },
    ]
    const result = checkAliasCount(tools)
    expect(result.source).toBe('v3_canonical_face_list')
    expect(result.live_tool_count).toBe(4)
    // canonical/deprecated counts come from the authored file, not the fixture.
    const file = loadCanonicalFacesFile()!
    expect(result.canonical_face_count).toBe(file.canonical_faces.length)
    expect(result.deprecated_alias_count).toBe(Object.keys(file.deprecated_aliases).length)
    // All four fixture tools are accounted for by the authored list → clean reconcile.
    expect(result.unaccounted_tools).toEqual([])
    expect(result.orphan_twins).toEqual([])
    expect(result.reconciles).toBe(true)
  })

  it('flags a live tool that is neither canonical nor a declared deprecated alias as unaccounted', () => {
    const tools: McpToolDescriptor[] = [
      { name: 'bodha_signals_get', description: 'Primary signal reader.' },
      { name: 'a_tool_not_in_the_authored_list', description: 'Unknown live tool with no canonical-face entry.' },
    ]
    const result = checkAliasCount(tools)
    expect(result.source).toBe('v3_canonical_face_list')
    expect(result.unaccounted_tools).toContain('a_tool_not_in_the_authored_list')
    expect(result.reconciles).toBe(false)
  })

  it('catches the previously-unmarked twin (get_signals) that the mechanical fallback could not — the authored list names it explicitly', () => {
    // get_signals/bodha_signals_get is the real BIND_D-2.md §B.5-cited pair. The old mechanical
    // fallback could NOT catch it (no [Phase-1 alias] marker in its description); V-3's authored
    // list declares it a deprecated alias explicitly, so it is now accounted for, not miscounted
    // as an independent canonical face.
    const file = loadCanonicalFacesFile()!
    expect(Object.keys(file.deprecated_aliases)).toContain('get_signals')
    expect(file.deprecated_aliases['get_signals']).toBe('bodha_signals_get')
    expect(file.canonical_faces).not.toContain('get_signals')

    const tools: McpToolDescriptor[] = [
      { name: 'bodha_signals_get', description: 'Primary signal reader.' },
      { name: 'get_signals', description: 'Legacy signal reader (no Phase-1 alias marker).' },
    ]
    const result = checkAliasCount(tools)
    expect(result.source).toBe('v3_canonical_face_list')
    expect(result.detail).toMatch(/authored canonical-face list/)
    // get_signals is accounted for as a deprecated alias (not unaccounted), unlike the old under-count.
    expect(result.unaccounted_tools).not.toContain('get_signals')
  })
})
