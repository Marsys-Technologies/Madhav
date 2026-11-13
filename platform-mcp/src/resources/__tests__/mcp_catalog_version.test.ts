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
import { describe, it, expect, vi } from 'vitest'
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
  captureServedCatalog, createRequestServedCatalogReader,
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

  it('uses the served-descriptor token rather than the generated retrieval population', () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    register(server, 'fixture_alpha')
    const served = captureServedCatalog(server)
    expect(served.ok).toBe(true)
    if (!served.ok) throw new Error('snapshot unavailable')
    expect(served.count).toBe(1)
    expect(served.version).toMatch(/^catalog-2\+t1\+s[0-9a-f]{64}$/)
  })
})

import { registerServerInfoTool } from '../../tools/register_server_info.js'

async function connectedInfo(description = 'fixture description') {
  const server = new McpServer({ name: 'fixture', version: '0' })
  server.registerTool('fixture_alpha', { description, inputSchema: { q: z.string() } }, okHandler)
  registerServerInfoTool(server)
  const [ct, st] = InMemoryTransport.createLinkedPair()
  const client = new Client({ name: 'fixture-client', version: '0' })
  await Promise.all([server.connect(st), client.connect(ct)])
  const info = async (version?: string) => {
    const result = await client.callTool({ name: 'mcp_server_info', arguments: version === undefined ? {} : { client_catalog_version: version } })
    return (result.structuredContent as { object: Record<string, unknown> }).object
  }
  return { server, client, info, close: async () => { await client.close(); await server.close() } }
}

describe('served descriptor cache contract', () => {
  it('changes token when a served-only tool is added with generated manifest fixed', async () => {
    const f = await connectedInfo()
    try {
      const before = await f.info()
      f.server.registerTool('fixture_beta', { inputSchema: { q: z.string() } }, okHandler)
      const after = await f.info()
      expect(after.tool_count).toBe(Number(before.tool_count) + 1)
      expect(after.catalog_version).not.toBe(before.catalog_version)
    } finally { await f.close() }
  })
  it('changes token for same-count public descriptor changes', async () => {
    const left = await connectedInfo('first synthetic description')
    const right = await connectedInfo('second synthetic description')
    try {
      const a = await left.info(), b = await right.info()
      expect(a.tool_count).toBe(b.tool_count)
      expect(a.catalog_version).not.toBe(b.catalog_version)
    } finally { await left.close(); await right.close() }
  })
  it('does not report submission from the disconnected SDK void wrapper', async () => {
    const f = await connectedInfo()
    try {
      const connected = vi.spyOn(f.server, 'isConnected').mockReturnValue(false)
      const result = await f.info('synthetic-old-token')
      expect(result.stale).toBe(true)
      expect(result.list_changed_notified).toBe(false)
      connected.mockRestore()
    } finally { await f.close() }
  })
})

async function wireFixture(server: McpServer) {
  const [ct, st] = InMemoryTransport.createLinkedPair()
  const client = new Client({ name: 'fixture-client', version: '0' })
  await Promise.all([server.connect(st), client.connect(ct)])
  return { client, close: async () => { await client.close(); await server.close() } }
}
function snapshot(server: McpServer) {
  const value = captureServedCatalog(server)
  if (!value.ok) throw new Error('fixture snapshot unavailable')
  return value
}
function registry(server: McpServer) {
  return (server as unknown as { _registeredTools: Record<string, Record<string, unknown>> })._registeredTools
}

describe('exact served DTO and failure boundaries', () => {
  it('equals pristine SDK public wire including input/output schema and all descriptor fields', async () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    server.registerTool('fixture_rich', {
      title: 'Synthetic title', description: 'Synthetic description',
      inputSchema: z.object({ q: z.string().optional(), items: z.array(z.number()) }),
      outputSchema: z.object({ answer: z.string() }),
      annotations: { title: 'Synthetic annotation', readOnlyHint: true, destructiveHint: false },
      _meta: { fixture: { value: null, ordered: ['first', 'second'], numeric: 1 } },
    }, okHandler)
    server.registerTool('fixture_empty', {}, okHandler)
    server.experimental.tasks.registerToolTask('fixture_task', {
      inputSchema: { q: z.string() }, execution: { taskSupport: 'required' },
    }, {
      createTask: async () => { throw new Error('fixture task must not execute') },
      getTask: async () => { throw new Error('fixture task must not execute') },
      getTaskResult: async () => { throw new Error('fixture task must not execute') },
    })
    Object.defineProperty(registry(server).fixture_rich!, 'handler', { get: () => { throw new Error('private handler must not be read') } })
    const f = await wireFixture(server)
    try {
      const wire = JSON.parse(JSON.stringify((await f.client.listTools()).tools)) as unknown
      expect(snapshot(server).tools).toEqual(wire)
      expect(snapshot(server).count).toBe(3)
      expect(snapshot(server).tools.find(tool => tool.name === 'fixture_task')?.execution).toEqual({ taskSupport: 'required' })
      expect(JSON.stringify(snapshot(server))).not.toContain('private handler')
    } finally { await f.close() }
  })
  it('preserves registration order on wire while token ignores top-level tool order', () => {
    const a = new McpServer({ name: 'a', version: '0' }), b = new McpServer({ name: 'b', version: '0' })
    for (const name of ['fixture_a', 'fixture_b']) register(a, name)
    for (const name of ['fixture_b', 'fixture_a']) register(b, name)
    expect(snapshot(a).tools.map(t => t.name)).toEqual(['fixture_a', 'fixture_b'])
    expect(snapshot(b).tools.map(t => t.name)).toEqual(['fixture_b', 'fixture_a'])
    expect(snapshot(a).version).toBe(snapshot(b).version)
  })
  it('sorts object keys but preserves nested arrays, nulls and scalar types', () => {
    const version = (meta: Record<string, unknown>) => {
      const server = new McpServer({ name: 'fixture', version: '0' })
      server.registerTool('fixture_alpha', { _meta: meta }, okHandler)
      return snapshot(server).version
    }
    expect(version({ a: 1, b: { c: true, d: null } })).toBe(version({ b: { d: null, c: true }, a: 1 }))
    expect(version({ order: ['a', 'b'] })).not.toBe(version({ order: ['b', 'a'] }))
    expect(version({ a: null })).not.toBe(version({}))
    expect(version({ a: 1 })).not.toBe(version({ a: '1' }))
  })
  it('changes same-count cache for schema, annotations and output schema changes', () => {
    const make = () => {
      const server = new McpServer({ name: 'fixture', version: '0' })
      server.registerTool('fixture_alpha', { inputSchema: { q: z.string() } }, okHandler)
      return server
    }
    const a = make(), b = make(), c = make(), d = make()
    registry(b).fixture_alpha!.inputSchema = z.object({ q: z.number() })
    registry(c).fixture_alpha!.annotations = { readOnlyHint: true }
    registry(d).fixture_alpha!.outputSchema = z.object({ result: z.string() })
    const original = snapshot(a).version
    for (const server of [b, c, d]) {
      expect(snapshot(server).count).toBe(1)
      expect(snapshot(server).version).not.toBe(original)
    }
  })
  it('moves on disable/removal and ignores a disabled descriptor', () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    const entry = server.registerTool('fixture_alpha', {}, okHandler)
    const first = snapshot(server)
    entry.disable()
    expect(snapshot(server).count).toBe(0)
    expect(snapshot(server).version).not.toBe(first.version)
    const empty = snapshot(server).version
    registry(server).fixture_alpha!.description = 'changed but not served'
    expect(snapshot(server).version).toBe(empty)
    entry.remove()
    expect(snapshot(server).version).toBe(empty)
  })
  it('does not mistake malformed map-shaped registry for an empty fresh catalog', () => {
    const bad = { _registeredTools: new Map() } as unknown as McpServer
    expect(captureServedCatalog(bad).ok).toBe(false)
  })
  it.each([null, undefined, [], { broken: null }, { broken: { enabled: 'yes' } }])('refuses unreadable or partial registry %s', bad => {
    expect(captureServedCatalog({ _registeredTools: bad } as unknown as McpServer).ok).toBe(false)
  })
  it('refuses malformed public JSON rather than hashing a partial result', () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    server.registerTool('fixture_alpha', {}, okHandler)
    registry(server).fixture_alpha!._meta = { private: () => 'not public JSON' }
    expect(captureServedCatalog(server).ok).toBe(false)
    const cycle: Record<string, unknown> = {}; cycle.self = cycle
    registry(server).fixture_alpha!._meta = cycle
    expect(captureServedCatalog(server).ok).toBe(false)
  })
  it('handles a failed snapshot reader as bounded unavailable without leaking its exception', async () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    registerServerInfoTool(server, () => { throw new Error('INERT_PRIVATE_FAILURE') })
    const f = await wireFixture(server)
    try {
      const result = await f.client.callTool({ name: 'mcp_server_info', arguments: { client_catalog_version: 'old' } })
      expect(result.isError).toBe(true)
      expect(result.structuredContent).toBeDefined()
      const body = (result.structuredContent as { object: Record<string, unknown> }).object
      expect(body.error).toEqual({ code: 'SERVED_CATALOG_UNAVAILABLE', message: 'Served tool catalog is unavailable.' })
      expect(body.tool_count).toBeNull(); expect(body.catalog_version).toBeNull(); expect(body.stale).toBeNull()
      expect(JSON.stringify(result)).not.toContain('INERT_PRIVATE_FAILURE')
    } finally { await f.close() }
  })
  it('never exposes a partially registered bootstrap, then reads final and subsequent SDK state', async () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    const reader = createRequestServedCatalogReader(server)
    registerServerInfoTool(server, reader.read)
    register(server, 'fixture_alpha')
    const f = await wireFixture(server)
    try {
      const before = await f.client.callTool({ name: 'mcp_server_info', arguments: {} })
      expect(before.isError).toBe(true)
      reader.markRegistrationComplete()
      const after = await f.client.callTool({ name: 'mcp_server_info', arguments: {} })
      expect((after.structuredContent as { object: { tool_count: number } }).object.tool_count).toBe(2)
      register(server, 'fixture_beta')
      const changed = await f.client.callTool({ name: 'mcp_server_info', arguments: {} })
      expect((changed.structuredContent as { object: { tool_count: number } }).object.tool_count).toBe(3)
    } finally { await f.close() }
  })
  it('keeps generated-only retrieval changes out of served fingerprint', () => {
    const server = new McpServer({ name: 'fixture', version: '0' }); register(server, 'fixture_alpha')
    const before = snapshot(server).version
    const names = MCP_SURFACE_PROFILES.full.tool_names as unknown as string[]
    names.push('synthetic_retrieval_only')
    try { expect(snapshot(server).version).toBe(before) } finally { names.pop() }
  })
  it.each(['full', 'compact', 'consult'] as const)('retains bootstrap metadata and denies blocked tool call under %s', async profile => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    applyDeprecatedToolGate(server as unknown as ToolRegisteringServer)
    registerServerInfoTool(server)
    applyProfileGate(server as unknown as ToolRegisteringServer, profile)
    let calls = 0
    server.tool('synthetic_not_in_any_authority_get', 'fixture', {}, async () => { calls++; return okHandler() })
    const f = await wireFixture(server)
    try {
      const list = await f.client.listTools()
      expect(list.tools.map(t => t.name)).toContain('mcp_server_info')
      expect(list.tools.map(t => t.name)).not.toContain('synthetic_not_in_any_authority_get')
      const result = await f.client.callTool({ name: 'synthetic_not_in_any_authority_get', arguments: {} })
      expect(result.isError).toBe(true); expect(calls).toBe(0)
      expect(snapshot(server).count).toBe(list.tools.length)
    } finally { await f.close() }
  })
})

describe('opaque token and awaited notification submission', () => {
  it('invalidates old opaque token once and is fresh with the returned current token', async () => {
    const f = await connectedInfo()
    try {
      const notifications: string[] = []
      f.client.setNotificationHandler(z.object({ method: z.literal('notifications/tools/list_changed') }), n => { notifications.push(n.method) })
      const old = await f.info('catalog-1+t73+rd4897822b6f2')
      expect(old.stale).toBe(true); expect(old.list_changed_notified).toBe(true)
      expect(old.catalog_version).toMatch(/^catalog-2\+t2\+s[0-9a-f]{64}$/)
      const fresh = await f.info(String(old.catalog_version))
      expect(fresh.stale).toBe(false); expect(fresh.list_changed_notified).toBe(false)
      expect(notifications).toEqual(['notifications/tools/list_changed'])
      expect(fresh.tools_changed_at).toBeNull()
    } finally { await f.close() }
  })
  it('reports rejected public submission false while retaining metadata', async () => {
    const f = await connectedInfo()
    try {
      vi.spyOn(f.server.server, 'sendToolListChanged').mockRejectedValueOnce(new Error('synthetic rejection'))
      const result = await f.info('synthetic-old')
      expect(result.stale).toBe(true); expect(result.list_changed_notified).toBe(false)
      expect(result.tool_count).toBe(2)
    } finally { await f.close() }
  })
  it('awaits actual public submission before completing successful metadata', async () => {
    const f = await connectedInfo()
    let release: () => void = () => {}
    try {
      vi.spyOn(f.server.server, 'sendToolListChanged').mockImplementationOnce(() => new Promise<void>(resolve => { release = resolve }))
      let completed = false
      const pending = f.info('synthetic-old').then(value => { completed = true; return value })
      await new Promise(resolve => setTimeout(resolve, 10))
      expect(completed).toBe(false)
      release()
      expect((await pending).list_changed_notified).toBe(true)
    } finally { release(); await f.close() }
  })
})

import * as z3 from 'zod/v3'
import { applyStrictSchemaGate, type StrictSchemaGateServer } from '../../lib/strict_tool_schema_gate.js'

describe('request scope and canonical contract controls', () => {
  it('uses the full known SHA256 for an actually empty served list', () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    expect(snapshot(server).version).toBe('catalog-2+t0+s4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945')
  })
  it('projects SDK-supported Zod3 descriptors identically to pristine tools/list', async () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    server.registerTool('fixture_v3', { inputSchema: z3.object({ q: z3.string(), n: z3.number().optional() }), outputSchema: z3.object({ result: z3.string() }) }, okHandler)
    const f = await wireFixture(server)
    try { expect(snapshot(server).tools).toEqual(JSON.parse(JSON.stringify((await f.client.listTools()).tools))) }
    finally { await f.close() }
  })
  it('invalidates same-count rename', () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    const tool = server.registerTool('fixture_alpha', {}, okHandler)
    const before = snapshot(server)
    tool.update({ name: 'fixture_beta' })
    expect(snapshot(server).count).toBe(before.count)
    expect(snapshot(server).version).not.toBe(before.version)
  })
  it('keeps real strict-schema refusal on the metadata bootstrap call', async () => {
    const server = new McpServer({ name: 'fixture', version: '0' })
    applyStrictSchemaGate(server as unknown as StrictSchemaGateServer)
    registerServerInfoTool(server)
    const f = await wireFixture(server)
    try {
      const refused = await f.client.callTool({ name: 'mcp_server_info', arguments: { unexpected: 'synthetic' } })
      expect(refused.isError).toBe(true)
      const allowed = await f.client.callTool({ name: 'mcp_server_info', arguments: {} })
      expect(allowed.isError).not.toBe(true)
    } finally { await f.close() }
  })
  it('isolates concurrent full/compact/consult served populations and bootstrap metadata', async () => {
    const fixtures = await Promise.all((['full', 'compact', 'consult'] as const).map(async profile => {
      const server = new McpServer({ name: 'fixture', version: '0' })
      const reader = createRequestServedCatalogReader(server)
      applyStrictSchemaGate(server as unknown as StrictSchemaGateServer)
      applyDeprecatedToolGate(server as unknown as ToolRegisteringServer)
      registerServerInfoTool(server, reader.read)
      applyProfileGate(server as unknown as ToolRegisteringServer, profile)
      register(server, 'inquiry_start')
      register(server, 'bodha_signals_get')
      reader.markRegistrationComplete()
      return { profile, server, ...await wireFixture(server) }
    }))
    try {
      const results = await Promise.all(fixtures.map(async f => {
        const list = await f.client.listTools()
        const result = await f.client.callTool({ name: 'mcp_server_info', arguments: {} })
        const body = (result.structuredContent as { object: Record<string, unknown> }).object
        expect(body.tool_count).toBe(list.tools.length)
        expect(body.catalog_version).toBe(snapshot(f.server).version)
        expect(list.tools.map(t => t.name)).toContain('mcp_server_info')
        return { names: list.tools.map(t => t.name), version: body.catalog_version }
      }))
      expect(results[0]!.names).toContain('inquiry_start')
      for (const narrow of results.slice(1)) {
        expect(narrow.names).not.toContain('inquiry_start')
        expect(narrow.version).not.toBe(results[0]!.version)
      }
    } finally { await Promise.all(fixtures.map(f => f.close())) }
  })
})

describe('public response compatibility', () => {
  it('preserves every success field and identical text/structured payload', async () => {
    const f = await connectedInfo()
    try {
      const result = await f.client.callTool({ name: 'mcp_server_info', arguments: {} })
      const body = (result.structuredContent as { object: Record<string, unknown> }).object
      expect(result.isError).not.toBe(true)
      expect(Object.keys(body).sort()).toEqual([
        'name', 'version', 'catalog_version', 'tool_count', 'tool_count_note',
        'retrieval_registry_profile_total', 'retrieval_registry_profile_generated_at',
        'retrieval_registry_profile_note', 'tools_changed_at', 'tools_changed_at_note',
        'stale', 'list_changed_notified',
      ].sort())
      const text = (result.content as Array<{ type: string; text?: string }>)[0]!
      expect(text.type).toBe('text')
      expect(JSON.parse(text.text!)).toEqual(body)
      expect(body.retrieval_registry_profile_total).toBe(RETRIEVAL_REGISTRY_PROFILE_TOTAL)
      expect(body.retrieval_registry_profile_generated_at).toBe(RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT)
    } finally { await f.close() }
  })
  it('omitted and empty opaque tokens are initial discovery without notification', async () => {
    const f = await connectedInfo()
    try {
      const notifications: string[] = []
      f.client.setNotificationHandler(z.object({ method: z.literal('notifications/tools/list_changed') }), n => { notifications.push(n.method) })
      for (const token of [undefined, '']) {
        const result = await f.info(token)
        expect(result.stale).toBe(false); expect(result.list_changed_notified).toBe(false)
      }
      expect(notifications).toEqual([])
    } finally { await f.close() }
  })
  it('retains metadata on a synchronous public notification throw', async () => {
    const f = await connectedInfo()
    try {
      vi.spyOn(f.server.server, 'sendToolListChanged').mockImplementationOnce(() => { throw new Error('synthetic sender throw') })
      const result = await f.info('synthetic-old')
      expect(result.stale).toBe(true); expect(result.list_changed_notified).toBe(false)
      expect(result.catalog_version).toMatch(/^catalog-2\+t2\+s[0-9a-f]{64}$/)
    } finally { await f.close() }
  })
})
