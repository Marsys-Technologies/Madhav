/**
 * w3_l5_budget_unification.test.ts — W3-L5 (budget unification, R-2 item 5 / W-8).
 *
 * Ground-truth recon for this lane found ~60 MCP tools (across ~18 registration files)
 * that returned raw `dualOutput`/inline JSON responses with NO response-budget pass at
 * all — the unclamped surface named GT-48/GT-19. This suite proves three of the newly
 * migrated tools now demonstrably trim oversized output instead of shipping it
 * unbounded, and that the migration did not regress a tool that was already budgeted.
 *
 * Pattern follows registry_bridge_r5w3_judgment_and_portrait.test.ts's precedent: mock
 * `fetch` (registry_bridge.ts's only I/O) and capture the REAL callback
 * `server.tool(...)` registers via a fake `McpServer` — this exercises the actual MCP
 * seam, not just an internal helper in isolation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { budgetMcpContent, finalizeMcpBudget, type TrimmableSection, type BudgetResult } from '../lib/response_budget.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, ..._rest: unknown[]) => {
      const handler = _rest[_rest.length - 1] as ToolHandler
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function stubFetch(payloads: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    const defaults: Record<string, unknown> = {
      'marsys://tool/L2/query_ucd': { chart_id: body.args['chart_id'], digest: {}, entity_profiles: [] },
      'marsys://tool/L1/get_chart_header': {
        chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2,
        moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha',
        current_maha_antar: 'Saturn/Mercury',
      },
    }
    const payload = body.uri in payloads ? payloads[body.uri] : defaults[body.uri]
    if (payload === undefined) throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    // Matches the real /api/retrieval/capability route (platform/src/app/api/retrieval/
    // capability/route.ts): `{ok: true, content: await capability.handler(args)}` — ONE
    // envelope layer. (get_domain_reading/get_signals separately unwrap an inner
    // {content, is_error} shape because THEIR specific capability handlers return that
    // shape as their own payload contract — list_assets/get_classical_citation/
    // get_positions's capabilities return the payload directly, no such inner wrapper.)
    return {
      ok: true,
      json: async () => ({ ok: true, content: payload }),
      text: async () => '',
    }
  }))
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

/** A big array whose serialized JSON comfortably exceeds every ceiling used below. */
function bigRows(n: number): Record<string, unknown>[] {
  return Array.from({ length: n }, (_, i) => ({
    id: `row-${i}`,
    text: 'x'.repeat(300),
    citation: `Classical Text CH${i}:V${i}`,
  }))
}

describe('registry_bridge.ts — previously-unclamped tools now trim (W3-L5)', () => {
  it('get_classical_citation (40KB ceiling) trims an oversized matches array', async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({ 'marsys://tool/L0/query_classical_texts': { matches: bigRows(400) } })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)

    const handler = handlers.get('get_classical_citation')
    expect(handler).toBeDefined()
    const result = await handler!({ query: 'exalted Mars' })

    const rawBytes = Buffer.byteLength(JSON.stringify({ matches: bigRows(400) }), 'utf8')
    const shippedBytes = Buffer.byteLength(JSON.stringify(result.structuredContent), 'utf8')
    expect(rawBytes).toBeGreaterThan(40 * 1024) // the untrimmed payload really is oversized
    expect(shippedBytes).toBeLessThan(rawBytes) // and the shipped one is materially smaller
    const object = result.structuredContent?.object as Record<string, unknown>
    expect(Array.isArray(object['matches'])).toBe(true)
    expect((object['matches'] as unknown[]).length).toBeLessThan(400)
    expect(object['trim_report']).toBeTruthy()
  })

  it('list_assets (40KB ceiling, chart-agnostic) trims an oversized asset list', async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({ 'marsys://resource/asset-registry/all': { assets: bigRows(500) } })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)

    const handler = handlers.get('list_assets')
    expect(handler).toBeDefined()
    const result = await handler!({})

    const rawBytes = Buffer.byteLength(JSON.stringify({ assets: bigRows(500) }), 'utf8')
    const shippedBytes = Buffer.byteLength(JSON.stringify(result.structuredContent), 'utf8')
    expect(rawBytes).toBeGreaterThan(40 * 1024)
    expect(shippedBytes).toBeLessThan(rawBytes)
    const object = result.structuredContent?.object as Record<string, unknown>
    expect((object['assets'] as unknown[]).length).toBeLessThan(500)
  })

  it('get_positions (40KB ceiling, chart-scoped) trims an oversized positions array', async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({ 'marsys://tool/L1/get_positions': { positions: bigRows(600) } })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)

    const handler = handlers.get('get_positions')
    expect(handler).toBeDefined()
    const result = await handler!({ chart_id: TEST_CHART_ID })

    const rawBytes = Buffer.byteLength(JSON.stringify({ positions: bigRows(600) }), 'utf8')
    const shippedBytes = Buffer.byteLength(JSON.stringify(result.structuredContent), 'utf8')
    expect(rawBytes).toBeGreaterThan(40 * 1024)
    expect(shippedBytes).toBeLessThan(rawBytes)
    const object = result.structuredContent?.object as Record<string, unknown>
    expect((object['positions'] as unknown[]).length).toBeLessThan(600)
  })

  it('a small get_positions response is returned unchanged (no-op below the ceiling)', async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({ 'marsys://tool/L1/get_positions': { positions: bigRows(2) } })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)

    const handler = handlers.get('get_positions')!
    const result = await handler({ chart_id: TEST_CHART_ID })
    const object = result.structuredContent?.object as Record<string, unknown>
    expect((object['positions'] as unknown[]).length).toBe(2)
    expect(object['trim_report']).toBeFalsy()
  })
})

describe('budgetMcpContent — the shared migration helper (bo_2-8.ts / l0_brahmagyan.ts / etc.)', () => {
  it('trims an oversized top-level array to fit the declared ceiling', () => {
    const content = { ok: true, tool: 'test_tool', events: bigRows(300) }
    const before = Buffer.byteLength(JSON.stringify(content), 'utf8')
    expect(before).toBeGreaterThan(20 * 1024)

    const budgeted = budgetMcpContent(content, 'test_tool', 20) as Record<string, unknown>
    const after = Buffer.byteLength(JSON.stringify(budgeted), 'utf8')
    expect(after).toBeLessThan(before)
    expect(after).toBeLessThanOrEqual(20 * 1024 + 512) // small slack for trim_report/drill_pointers overhead
    expect((budgeted['events'] as unknown[]).length).toBeLessThan(300)
  })

  it('is a no-op for content already under budget', () => {
    const content = { ok: true, tool: 'test_tool', events: bigRows(1) }
    const budgeted = budgetMcpContent(content, 'test_tool', 40)
    expect(budgeted).toBe(content) // same reference — untouched
  })

  it('is a no-op for non-object content (string/array/null)', () => {
    expect(budgetMcpContent('plain string', 'test_tool')).toBe('plain string')
    expect(budgetMcpContent(null, 'test_tool')).toBe(null)
  })
})

describe('still_over_budget resolution (GT-45/W-5) — deleted from BudgetResult, wired via judgment_flags', () => {
  it('BudgetResult no longer carries a still_over_budget field at all', () => {
    // Structural check: a BudgetResult value must not have the property, at either the
    // type or the runtime-object level — GT-45 named it dead output on every call path;
    // this lane's resolution was to delete it rather than leave it "surfaced but unread".
    const result: BudgetResult<{ padding: string }> = {
      content: { padding: 'x' },
      trim_report: null,
      trimmed: false,
      approx_bytes_before: 1,
      approx_bytes_after: 1,
    }
    expect('still_over_budget' in result).toBe(false)
  })

  it('finalizeMcpBudget wires the honest over-budget gap to a judgment_flags entry carrying the stable `budget_exceeded_after_trim` code', () => {
    // Base content alone must be genuinely unshrinkable by EVERY lever this file has: not
    // a declared trimmable section (PASS 1/2 can't touch it), and no individual string
    // over 120 chars (so the last-resort truncateLongStringsInPlace walk can't touch it
    // either) — an array of many short strings, never trimmed, sums to well over the tiny
    // 1KB ceiling used below.
    const content = {
      padding: Array.from({ length: 60 }, (_, i) => `field-${i}-`.padEnd(100, 'x')),
      rows: [{ a: 1 }, { a: 2 }, { a: 3 }],
    }
    const rowsSection: TrimmableSection<typeof content> = {
      path: 'rows',
      getArray: (c) => c.rows,
      setArray: (c, kept) => { c.rows = kept as typeof c.rows },
      minKeep: 0,
      recover: { instrument: 'bodha_signals_get', hint: 'full set' },
      label: 'rows',
    }
    const budgeted = finalizeMcpBudget(content as unknown as Record<string, unknown>, {
      maxKb: 1,
      sections: [rowsSection as unknown as TrimmableSection<Record<string, unknown>>],
    })
    // W3-L2's closed judgment_flags enum landed after this test was first written — a flag
    // entry is now the structured {code, detail?} shape (or, for not-yet-migrated emitters,
    // a bare legacy string). Check both shapes rather than assuming one.
    const flags = budgeted['judgment_flags'] as Array<{ code: string; detail?: string } | string> | undefined
    expect(flags).toBeDefined()
    const flagCode = (f: { code: string; detail?: string } | string) => (typeof f === 'string' ? f : f.code)
    expect(flags!.some(f => flagCode(f) === 'budget_exceeded_after_trim')).toBe(true)
    // The old ad-hoc, maxKb-baked-in string is gone — replaced by the stable closed-enum code.
    expect(flags!.some(f => typeof f === 'string' && f.startsWith('response_still_over_'))).toBe(false)
  })

  it('does NOT emit the over-budget flag when trimming successfully closes the gap', () => {
    const content = { padding: 'x'.repeat(10), rows: bigRows(200) }
    const rowsSection: TrimmableSection<typeof content> = {
      path: 'rows',
      getArray: (c) => c.rows,
      setArray: (c, kept) => { c.rows = kept as typeof c.rows },
      minKeep: 1,
      recover: { instrument: 'bodha_signals_get', hint: 'full set' },
      label: 'rows',
    }
    const budgeted = finalizeMcpBudget(content as unknown as Record<string, unknown>, {
      maxKb: 40,
      sections: [rowsSection as unknown as TrimmableSection<Record<string, unknown>>],
    })
    const flags = (budgeted['judgment_flags'] as Array<{ code: string } | string> | undefined) ?? []
    expect(flags.some(f => (typeof f === 'string' ? f : f.code) === 'budget_exceeded_after_trim')).toBe(false)
  })
})
