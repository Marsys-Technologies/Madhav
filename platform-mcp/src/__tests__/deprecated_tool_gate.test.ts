// @vitest-environment node
//
// RC-14 breaking flip — deprecated_tool_gate regression suite.
// Proves the three DONE-bar claims of RC-14 Piece 1:
//   (a) the 43 legacy P1 short names are unresolvable via the MCP surface (gated to no-op),
//   (b) the gate set is EXACTLY canonical_faces.json's deprecated_aliases keys minus the
//       6 renamed-at-source names, and none of the 43 is itself a canonical face,
//   (c) the 6 DEFERRED renames: new names ARE canonical faces, old names ARE deprecated
//       aliases (so old persisted web conversations still replay-resolve).

import { readFileSync } from 'node:fs'
import { describe, it, expect } from 'vitest'
import {
  DEPRECATED_MCP_TOOL_NAMES,
  applyDeprecatedToolGate,
} from '../lib/deprecated_tool_gate.js'

// Authoritative dedup source (platform package, read cross-package via fs in node env).
const canonicalFaces = JSON.parse(
  readFileSync(
    new URL('../../../platform/src/lib/retrieval/registry/canonical_faces.json', import.meta.url),
    'utf8',
  ),
) as { canonical_faces: string[]; deprecated_aliases: Record<string, string> }

// The 6 tools renamed at their source registration (NOT gated) — old -> new.
const SIX_RENAMES: Record<string, string> = {
  recall_session: 'session_recall',
  list_my_sessions: 'session_list',
  list_my_charts: 'catalog_charts_list',
  select_chart: 'catalog_chart_select',
  holistic_bundle_chart_facts: 'bodha_bundle_get',
  kala_temporal_bundle: 'kala_bundle_get',
}

describe('RC-14 deprecated_tool_gate — census + governance parity', () => {
  it('gates exactly 43 legacy names', () => {
    expect(DEPRECATED_MCP_TOOL_NAMES.size).toBe(43)
  })

  it('the gate set is EXACTLY canonical_faces.deprecated_aliases keys minus the 6 renames', () => {
    const depKeys = new Set(Object.keys(canonicalFaces.deprecated_aliases))
    // Remove the 6 renamed old names (they are deprecated_aliases for web replay, but are
    // renamed at source, not gated).
    for (const old of Object.keys(SIX_RENAMES)) depKeys.delete(old)
    expect([...DEPRECATED_MCP_TOOL_NAMES].sort()).toEqual([...depKeys].sort())
  })

  it('no gated legacy name is itself a canonical face (we never gate a go-forward name)', () => {
    const faces = new Set(canonicalFaces.canonical_faces)
    for (const legacy of DEPRECATED_MCP_TOOL_NAMES) {
      expect(faces.has(legacy), `${legacy} is both gated AND a canonical face`).toBe(false)
    }
  })

  it('every gated legacy name maps to a real canonical face (no capability dropped)', () => {
    const faces = new Set(canonicalFaces.canonical_faces)
    for (const legacy of DEPRECATED_MCP_TOOL_NAMES) {
      const canon = canonicalFaces.deprecated_aliases[legacy]
      expect(canon, `${legacy} has no deprecated_aliases target`).toBeDefined()
      expect(faces.has(canon!), `${legacy} -> ${canon} is not a canonical face`).toBe(true)
    }
  })
})

describe('RC-14 deprecated_tool_gate — runtime behavior', () => {
  function makeGatedServer() {
    const registered: string[] = []
    const server = { tool: (name: string, ..._rest: unknown[]) => { registered.push(name) } }
    const gate = applyDeprecatedToolGate(server)
    return { server, registered, gate }
  }

  it('no-ops every one of the 43 legacy names (never handed to the real registrar)', () => {
    const { server, registered, gate } = makeGatedServer()
    for (const legacy of DEPRECATED_MCP_TOOL_NAMES) {
      server.tool(legacy, 'desc', {}, async () => ({}))
    }
    expect(registered).toEqual([]) // none registered
    expect(new Set(gate.blockedDeprecated)).toEqual(new Set(DEPRECATED_MCP_TOOL_NAMES))
  })

  it('passes canonical faces through untouched', () => {
    const { server, registered } = makeGatedServer()
    const canon = ['ganita_positions_get', 'bodha_signals_get', 'ref_vector_search', 'catalog_assets_list']
    for (const n of canon) server.tool(n, 'desc', {}, async () => ({}))
    expect(registered).toEqual(canon)
  })

  it('passes the 6 NEW renamed names through (they are NOT gated)', () => {
    const { server, registered } = makeGatedServer()
    for (const nu of Object.values(SIX_RENAMES)) server.tool(nu, 'desc', {}, async () => ({}))
    expect(registered).toEqual(Object.values(SIX_RENAMES))
  })
})

describe('RC-14 — the 6 deferred renames (canonical_faces governance)', () => {
  it('all 6 NEW names are canonical faces; all 6 OLD names are deprecated aliases (web replay preserved)', () => {
    const faces = new Set(canonicalFaces.canonical_faces)
    for (const [oldName, newName] of Object.entries(SIX_RENAMES)) {
      expect(faces.has(newName), `${newName} should be a canonical face`).toBe(true)
      expect(faces.has(oldName), `${oldName} should NOT be a canonical face anymore`).toBe(false)
      expect(canonicalFaces.deprecated_aliases[oldName], `${oldName} should map to ${newName}`).toBe(newName)
    }
  })
})
