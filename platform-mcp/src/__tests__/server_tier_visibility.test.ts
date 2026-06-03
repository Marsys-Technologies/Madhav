/**
 * server_tier_visibility.test.ts — R1-T1
 * Assert all registered tools are present unconditionally.
 *
 * GISMCP Remediation R1 de-gating made tiers redundant; Stream A
 * 3.tier_excision (2026-05-28) removed `audience_tier` from Principal.
 *
 * Brahma clean-slate note (BRAHMA-BG-0-1, 2026-06-03):
 * The legacy-teardown removed all 40 tool source files. This test is updated
 * to assert the Layer-0 tool surface (1 tool: query_ephemeris). As additional
 * tools are added per the Layer-0→Layer-3 arc, update registerAll() and the
 * expected count. The "tool-count parity" invariant is preserved — just set
 * to the correct current count (1) instead of the legacy count (40).
 */

import { describe, it, expect } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Register function imports (mirrors server.ts) ─────────────────────────────
// Layer-0: brahmagyan.ephemeris
import { registerQueryEphemeris } from '../tools/query_ephemeris.js'

// ── Mock server ───────────────────────────────────────────────────────────────

function createMockServer() {
  const registeredNames: string[] = []
  return {
    _registeredNames: registeredNames,
    // Matches the McpServer.tool() call signature used by all register functions
    tool: (name: string, ..._rest: unknown[]) => { registeredNames.push(name) },
    resource: (..._args: unknown[]) => {},
  }
}

// ── Helper: register all current tools with a given principal ─────────────────

function registerAll(server: ReturnType<typeof createMockServer>, principal: Principal) {
  const getPrincipal = () => principal
  // Layer-0 tools — add entries here as each layer is built.
  registerQueryEphemeris(server as unknown as McpServer, getPrincipal)
}

// ── Principals ────────────────────────────────────────────────────────────────

// `tier` arg retained for label-only purposes (test description); Principal no
// longer carries audience_tier (Stream A 3.tier_excision 2026-05-28).
const makePrincipal = (tier: string): Principal => ({
  user_uid: `uid-${tier}`,
  key_id: `key-${tier}`,
})

// ── Current tool count (Brahma Layer-0) ──────────────────────────────────────
// IMPORTANT: update this constant when a new tool is wired in server.ts.
const EXPECTED_TOOL_COUNT = 1

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('server tool registration — tier visibility (R1 de-gating)', () => {

  it(`registers all ${EXPECTED_TOOL_COUNT} tools for client tier`, () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toHaveLength(EXPECTED_TOOL_COUNT)
  })

  it(`registers all ${EXPECTED_TOOL_COUNT} tools for acharya tier`, () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('acharya'))
    expect(server._registeredNames).toHaveLength(EXPECTED_TOOL_COUNT)
  })

  it(`registers all ${EXPECTED_TOOL_COUNT} tools for super_admin tier`, () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('super_admin'))
    expect(server._registeredNames).toHaveLength(EXPECTED_TOOL_COUNT)
  })

  it('query_ephemeris is present for client tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toContain('query_ephemeris')
  })

  it('query_ephemeris is present for acharya tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('acharya'))
    expect(server._registeredNames).toContain('query_ephemeris')
  })

  it('query_ephemeris is present for super_admin tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('super_admin'))
    expect(server._registeredNames).toContain('query_ephemeris')
  })

  it(`tool count is identical across all tiers (${EXPECTED_TOOL_COUNT} each)`, () => {
    const counts = ['client', 'acharya', 'super_admin'].map(tier => {
      const server = createMockServer()
      registerAll(server, makePrincipal(tier))
      return server._registeredNames.length
    })
    expect(counts[0]).toBe(EXPECTED_TOOL_COUNT)
    expect(counts[1]).toBe(EXPECTED_TOOL_COUNT)
    expect(counts[2]).toBe(EXPECTED_TOOL_COUNT)
  })

  it('no duplicate tool registrations', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('super_admin'))
    const unique = new Set(server._registeredNames)
    expect(unique.size).toBe(server._registeredNames.length)
  })
})
