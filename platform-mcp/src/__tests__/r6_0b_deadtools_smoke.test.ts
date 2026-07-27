/**
 * r6_0b_deadtools_smoke.test.ts — Ring-1 smoke tests for R6 lane 0b-deadtools.
 *
 * Per-row regression pins for the schema-drift/dead-tool fixes in this lane:
 *   R-9  bodha_discoveries_get   — no more `salience_score`/`domain` columns in the SQL
 *   R-10 synth_tail_divergence_get — no more `tier` column; uses stored salience_pctl_in_class
 *   R-12 prashna_undertaking_get — no more `gj.verdict`/`gj.verdict_strength` columns
 *   R-14 mimamsa_calibration_get — no longer 400s (query_calibration now in the surgical whitelist)
 *   T-7  muhurta_finder          — handler return value is a valid MCP tool-result shape
 *                                  (has `content`), not a bare McpEnvelope, on both the
 *                                  success and the !env.ok path.
 *
 * Follows the established idiom in registry_bridge_r5w3_judgment_and_portrait.test.ts:
 * mock `fetch` (the tool's only I/O), capture the real `server.tool(...)` callback via a
 * fake McpServer, and assert on the real handler's behavior — not a reimplementation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, _desc: string, _schema: unknown, handler: ToolHandler) => {
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
  process.env['SERVICE_TOKEN'] = 'test-service-token' // skip real GCP identity-token auth
})

// ── R-9 / R-10 / R-12: SQL no longer references dropped columns ──────────────

describe('register_p1_synthesis — R6 0b-deadtools schema-drift fixes', () => {
  // NOTE (MC-015, ŚODHANA-ŚEṢA W1): this test originally pinned the R-9 fix by inspecting
  // the raw SQL this handler used to issue directly against `bodha_discoveries`. MC-015
  // found that raw-SQL path itself was the bug — it meant bodha_discoveries_get never went
  // through the registry capability (marsys://tool/L2/query_discoveries) and so could never
  // see that capability's `discovery_families` ayanāṃśa-collapse (see PR #803). The handler
  // now proxies to the registry capability instead of running SQL directly (mirroring
  // kala_projections_get's existing, always-correct proxy pattern) — so there is no more SQL
  // for this tool to inspect. Re-pinned as: (a) no `/api/mcp/db/query` call happens for this
  // tool at all, (b) the registry-capability call it DOES make carries `domain` correctly.
  // Full discovery_families pass-through regression: mc015_bodha_discoveries_family_wiring.test.ts.
  it('bodha_discoveries_get (R-9 / MC-015): proxies to the registry capability, never issues raw SQL against bodha_discoveries', async () => {
    const capabilityCalls: Array<{ uri: string; args: Record<string, unknown> }> = []
    const capturedSql: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (url: string, opts: { body: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      if (url.includes('/api/retrieval/capability')) {
        const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
        capabilityCalls.push(body)
        return {
          ok: true,
          json: async () => ({ ok: true, content: { chart_id: TEST_CHART_ID, rows: [], count: 0, total_matching: 0, discovery_families: [], discovery_family_count: 0, total_family_count: 0 } }),
          text: async () => '',
        }
      }
      if (url.includes('/api/mcp/db/query')) {
        const body = JSON.parse(opts.body) as { sql?: string }
        if (body.sql) capturedSql.push(body.sql)
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      throw new Error(`unmocked fetch: ${url}`)
    }))

    const { registerP1SynthesisTools } = await import('../tools/register_p1_synthesis.js')
    const { server, handlers } = makeCapturingServer()
    registerP1SynthesisTools(server, PRINCIPAL)
    const handler = handlers.get('bodha_discoveries_get')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'career', min_salience: 0.5 })
    expect(result.isError).toBeFalsy()
    expect(capabilityCalls.length).toBeGreaterThan(0)
    expect(capabilityCalls[0]!.uri).toBe('marsys://tool/L2/query_discoveries')
    expect(capabilityCalls[0]!.args['domain']).toBe('career')
    // The schema-drift columns R-9 originally fixed can no longer leak back in, because
    // this tool no longer builds any SQL string at all.
    expect(capturedSql.some(s => s.includes('bodha_discoveries'))).toBe(false)
  })

  it('synth_tail_divergence_get (R-10): SQL never references `tier`; uses signature_tier + stored salience_pctl_in_class', async () => {
    const capturedSql: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (url: string, opts: { body: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      const body = JSON.parse(opts.body) as { sql?: string }
      if (body.sql) capturedSql.push(body.sql)
      return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
    }))

    const { registerP1SynthesisTools } = await import('../tools/register_p1_synthesis.js')
    const { server, handlers } = makeCapturingServer()
    registerP1SynthesisTools(server, PRINCIPAL)
    const handler = handlers.get('synth_tail_divergence_get')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'career' })
    expect(result.isError).toBeFalsy()
    const sql = capturedSql.find(s => s.includes('bodha_msr_signals'))
    expect(sql).toBeDefined()
    expect(sql).not.toMatch(/,\s*tier\b/)
    expect(sql).not.toMatch(/PERCENT_RANK/)
    expect(sql).toMatch(/signature_tier/)
    expect(sql).toMatch(/salience_pctl_in_class/)
  })

  it('prashna_undertaking_get (R-12): SQL never references gj.verdict/gj.verdict_strength; uses gj.judgment_text', async () => {
    const capturedSql: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (url: string, opts: { body: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      const body = JSON.parse(opts.body) as { sql?: string }
      if (body.sql) capturedSql.push(body.sql)
      return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
    }))

    const { registerP1SynthesisTools } = await import('../tools/register_p1_synthesis.js')
    const { server, handlers } = makeCapturingServer()
    registerP1SynthesisTools(server, PRINCIPAL)
    const handler = handlers.get('prashna_undertaking_get')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'career', top_windows: 3 })
    expect(result.isError).toBeFalsy()
    const gjSql = capturedSql.find(s => s.includes('ga_prashna_judgment'))
    expect(gjSql).toBeDefined()
    expect(gjSql).not.toMatch(/gj\.verdict\b/)
    expect(gjSql).not.toMatch(/gj\.verdict_strength/)
    expect(gjSql).not.toMatch(/gj\.significator_positions/)
    expect(gjSql).not.toMatch(/gj\.timing_indication/)
    expect(gjSql).not.toMatch(/gj\.classical_citations/)
    expect(gjSql).toMatch(/gj\.judgment_text/)

    // Composite score never fabricates a verdict_strength placeholder (canonical-or-floor).
    const content = (result.structuredContent?.object as { content: { composite_undertaking_score_note?: string | null } }).content
    expect(content.composite_undertaking_score_note).toMatch(/verdict_strength omitted/)
  })
})

// R-14's tool_name_bridge whitelist fix lives in the `platform` package
// (platform/src/lib/retrieval/registry/tool_name_bridge.ts), a separate deployable from
// this platform-mcp package — see
// platform/src/lib/retrieval/registry/tool_name_bridge_r6_0b_deadtools.test.ts
// for that half of the R-14 regression pin (mimamsa_calibration_get's 400).

// ── T-7: muhurta_finder no longer returns a bare envelope with no `content` ──

describe('muhurta_finder — R6 0b-deadtools (T-7) response-shape fix', () => {
  it('success path: handler return value has a `content` array (valid MCP tool-result shape)', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      if (url.includes('/api/mcp/primitives/muhurta_finder')) {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            trace_id: 't1',
            epistemics: {},
            result: {
              ok: true,
              chart_id: TEST_CHART_ID,
              action_type: 'education',
              query_window: { start: '2026-06-04', end: '2026-09-01' },
              windows: [{
                start: '2026-06-04T00:00:00Z', end: '2026-06-06T00:00:00Z', score: 0.7,
                factors: {}, source_citation: 'BPHS ch.46',
              }],
              window_count: 1,
              provenance_envelope: { source: 'phala.muhurta', asset: 'PH-4-4' },
            },
            citations: [], plan: null, predictions_logged: [], synthesis_audit: null,
            suggested_followups: [], warnings: [],
          }),
          text: async () => '',
        }
      }
      throw new Error(`unmocked fetch: ${url}`)
    }))

    const { registerMuhurtaFinder } = await import('../tools/muhurta_finder.js')
    const { server, handlers } = makeCapturingServer()
    registerMuhurtaFinder(server as unknown as Parameters<typeof registerMuhurtaFinder>[0], () => PRINCIPAL)
    const handler = handlers.get('muhurta_finder')!

    const result = await handler({
      chart_id: TEST_CHART_ID, action_type: 'education',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
    })

    // The T-7 bug: this used to be a bare {ok, trace_id, epistemics, result, ...} object
    // with NO `content` key at all — not a valid MCP tool-call response.
    expect(Array.isArray(result.content)).toBe(true)
    expect(result.content.length).toBeGreaterThan(0)
    expect(result.isError).toBeFalsy()
    const parsed = JSON.parse((result.content as Array<{ text: string }>)[0]!.text) as {
      windows: Array<{ score: number }>
    }
    expect(parsed.windows.length).toBe(1)
    expect(parsed.windows[0]!.score).toBe(0.7)
  })

  it('platform-error path (!env.ok): handler still returns a valid `content`-bearing, isError shape (not a bare envelope)', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.includes('/api/mcp/authz')) {
        return { ok: true, json: async () => ({ authorized: true }), text: async () => '' }
      }
      if (url.includes('/api/mcp/primitives/muhurta_finder')) {
        return {
          ok: true,
          json: async () => ({
            ok: false,
            trace_id: 't2',
            error: { class: 'internal', message: 'boom' },
          }),
          text: async () => '',
        }
      }
      throw new Error(`unmocked fetch: ${url}`)
    }))

    const { registerMuhurtaFinder } = await import('../tools/muhurta_finder.js')
    const { server, handlers } = makeCapturingServer()
    registerMuhurtaFinder(server as unknown as Parameters<typeof registerMuhurtaFinder>[0], () => PRINCIPAL)
    const handler = handlers.get('muhurta_finder')!

    const result = await handler({
      chart_id: TEST_CHART_ID, action_type: 'education',
      date_range: { start: '2026-06-04', end: '2026-09-01' },
    })

    expect(Array.isArray(result.content)).toBe(true)
    expect(result.content.length).toBeGreaterThan(0)
    expect(result.isError).toBe(true)
  })
})
