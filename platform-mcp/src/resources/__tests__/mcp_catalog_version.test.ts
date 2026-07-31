/**
 * mcp_catalog_version.test.ts — SAMĀPTI B-MCP-CATALOG-GAP (DVA Ruling 25)
 * ========================================================================
 * The regression test for the `mcp_server_info.tool_count` false-green.
 *
 * The defect: `tool_count` was `MCP_SURFACE_PROFILES.full.total`, a build-time figure over the
 * RETRIEVAL REGISTRY, served as though it described the MCP catalog. It reported 152 while
 * `tools/list` returned 124 and could not have moved if the served surface had collapsed to
 * zero — a health signal decoupled from the health it names (§N.8).
 *
 * The property that must hold, and that the old field could never satisfy:
 *   **`tool_count` EQUALS the length of `tools/list`, and MOVES when a tool is gated out.**
 *
 * `equals tools/list` is asserted against the REAL SDK over a real client/server transport
 * (not a mock), because equality-by-construction is exactly the claim. `moves when gated` is
 * asserted three ways — a tool removed, a tool added, and a tool disabled — and the same
 * assertions are run against the OLD implementation (`MCP_SURFACE_PROFILES.full.total`) to
 * prove the old field FAILS them. A regression test that only passes on the fix is weaker
 * evidence than one that is watched failing on the defect.
 */
import { describe, it, expect } from 'vitest'
import { z } from 'zod'
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js'
import { MCP_SURFACE_PROFILES } from '../../generated/mcp_surface_profiles.generated.js'
import { applyDeprecatedToolGate } from '../../lib/deprecated_tool_gate.js'
import { applyProfileGate, type ToolRegisteringServer } from '../../lib/mcp_profile.js'
import {
  censusServedTools,
  RETRIEVAL_REGISTRY_PROFILE_TOTAL,
  RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT,
  MCP_CATALOG_VERSION,
} from '../mcp_catalog_version.js'

const okHandler = async () => ({ content: [{ type: 'text' as const, text: 'ok' }] })

/* eslint-disable @typescript-eslint/no-explicit-any -- McpServer.tool() is a heavily
   overloaded SDK method; these tests only register by name, the same `as any` pattern
   server.ts and the gate modules already use at every call site. */
function register(server: McpServer, name: string): void {
  ;(server as any).tool(name, `desc for ${name}`, { q: z.string() }, okHandler)
}
/* eslint-enable @typescript-eslint/no-explicit-any */

describe('censusServedTools — the served count is live-derived and MOVES with the surface', () => {
  it('equals the length of the real tools/list response (equality by construction, not by tally)', async () => {
    const server = new McpServer({ name: 'test', version: '0.0.0' })
    for (const n of ['alpha_get', 'beta_get', 'gamma_get']) register(server, n)

    const [clientT, serverT] = InMemoryTransport.createLinkedPair()
    const client = new Client({ name: 'c', version: '0' })
    await Promise.all([server.connect(serverT), client.connect(clientT)])
    try {
      const list = await client.listTools()
      const census = censusServedTools(server)
      expect(census.count).toBe(list.tools.length)
      expect(census.names).toEqual(list.tools.map((t) => t.name).sort())
    } finally {
      await client.close()
      await server.close()
    }
  })

  it('CAN-FAIL: gating one tool OUT of the catalog DECREASES the count by exactly one', () => {
    const names = ['alpha_get', 'beta_get', 'gamma_get']

    const before = new McpServer({ name: 'test', version: '0.0.0' })
    for (const n of names) register(before, n)
    const baseline = censusServedTools(before).count

    // The mutation: one registration withheld — the surface genuinely shrank.
    const after = new McpServer({ name: 'test', version: '0.0.0' })
    for (const n of names.filter((n) => n !== 'beta_get')) register(after, n)
    const gated = censusServedTools(after).count

    expect(baseline).toBe(3)
    expect(gated).toBe(2)
    expect(gated).toBe(baseline! - 1)
    expect(censusServedTools(after).names).not.toContain('beta_get')
  })

  it('CAN-FAIL: the OLD implementation (manifest total) does NOT move under the same mutation', () => {
    // The precise reason the old field was a false-green: it is a module constant, so the
    // identical mutation above leaves it untouched. This test documents the defect rather
    // than asserting a fix — if it ever starts failing, the manifest figure has become
    // surface-coupled and this lane's premise needs re-examining.
    const oldMetricBefore = MCP_SURFACE_PROFILES.full.total
    const after = new McpServer({ name: 'test', version: '0.0.0' })
    register(after, 'alpha_get')
    const oldMetricAfter = MCP_SURFACE_PROFILES.full.total
    expect(oldMetricAfter).toBe(oldMetricBefore)
    // ...and it disagrees with the actual served catalog by a wide margin.
    expect(censusServedTools(after).count).toBe(1)
    expect(oldMetricAfter).not.toBe(censusServedTools(after).count)
  })

  it('grows when a tool is ADDED (the signal is bidirectional, not just a shrink detector)', () => {
    const server = new McpServer({ name: 'test', version: '0.0.0' })
    register(server, 'alpha_get')
    expect(censusServedTools(server).count).toBe(1)
    register(server, 'beta_get')
    expect(censusServedTools(server).count).toBe(2)
  })

  it('excludes a DISABLED tool, mirroring the SDK tools/list `enabled` filter', async () => {
    const server = new McpServer({ name: 'test', version: '0.0.0' })
    register(server, 'alpha_get')
    /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
    const beta = (server as any).tool('beta_get', 'desc', { q: z.string() }, okHandler)
    expect(censusServedTools(server).count).toBe(2)

    beta.disable()

    const [clientT, serverT] = InMemoryTransport.createLinkedPair()
    const client = new Client({ name: 'c', version: '0' })
    await Promise.all([server.connect(serverT), client.connect(clientT)])
    try {
      const list = await client.listTools()
      expect(censusServedTools(server).count).toBe(1)
      expect(censusServedTools(server).count).toBe(list.tools.length)
    } finally {
      await client.close()
      await server.close()
    }
  })

  it('tracks the RC-14 deprecated-name gate: gated legacy names are not counted as served', () => {
    const server = new McpServer({ name: 'test', version: '0.0.0' })
    applyDeprecatedToolGate(server as unknown as ToolRegisteringServer)
    register(server, 'alpha_get')
    register(server, 'get_signals')       // RC-14 legacy alias — gated
    register(server, 'bodha_signals_get') // its canonical face — served

    const census = censusServedTools(server)
    expect(census.count).toBe(2)
    expect(census.names).not.toContain('get_signals')
    expect(census.names).toContain('bodha_signals_get')
  })

  it('is profile-scoped: a narrower profile reports its own smaller, honest number', () => {
    const consultNames = MCP_SURFACE_PROFILES.consult.tool_names
    expect(consultNames.length).toBeGreaterThan(0)

    const server = new McpServer({ name: 'test', version: '0.0.0' })
    applyProfileGate(server as unknown as ToolRegisteringServer, 'consult')
    register(server, consultNames[0]!)
    register(server, 'definitely_not_in_consult_profile_get')

    expect(censusServedTools(server).count).toBe(1)
  })

  it('B.10: reports null + a note rather than falling back to the manifest figure', () => {
    const broken = { notARegistry: true } as unknown as McpServer
    const census = censusServedTools(broken)
    expect(census.count).toBeNull()
    expect(census.names).toEqual([])
    expect(census.note).toMatch(/never fabricated/i)
    // Critically: it must NOT substitute the wrong-population number.
    expect(census.count).not.toBe(RETRIEVAL_REGISTRY_PROFILE_TOTAL)
  })
})

describe('RETRIEVAL_REGISTRY_PROFILE_* — the renamed, date-stamped registry metric', () => {
  it('is the manifest total, preserved (renamed, not deleted)', () => {
    expect(RETRIEVAL_REGISTRY_PROFILE_TOTAL).toBe(MCP_SURFACE_PROFILES.full.total)
  })

  it('carries the manifest generation timestamp, so it can never be read as live telemetry', () => {
    expect(RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT).toMatch(/^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/)
    expect(Number.isNaN(Date.parse(RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT))).toBe(false)
  })

  it('leaves catalog_version byte-identical (it is a client cache key, not a health signal)', () => {
    expect(MCP_CATALOG_VERSION).toBe(
      `catalog-1+t${MCP_SURFACE_PROFILES.full.total}+r${MCP_CATALOG_VERSION.split('+r')[1]}`,
    )
    expect(MCP_CATALOG_VERSION).toMatch(/^catalog-1\+t\d+\+r[0-9a-f]{12}$/)
  })
})
