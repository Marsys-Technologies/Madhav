import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js'
import { registerAllKalaViews } from './register_all.js'

const chart = '00000000-0000-4000-8000-000000000281'
const principal = { user_uid: 'CODEX-k3', key_id: 'CODEX-key', role: 'guest' as const }
type Registered = { shape: z.ZodRawShape; call: (args: Record<string, unknown>) => Promise<CallToolResult> }
const tools = new Map<string, Registered>()
const fetchMock = vi.fn()
const finder = vi.hoisted(() => vi.fn())
vi.mock('../muhurta_finder.js', async importOriginal => ({
  ...await importOriginal<typeof import('../muhurta_finder.js')>(), handleMuhurtaFinder: finder,
}))
vi.mock('../../lib/kala_lattice_query.js', async importOriginal => ({
  ...await importOriginal<typeof import('../../lib/kala_lattice_query.js')>(),
  fetchLatticeSubstrate: async () => ({ lattice_rows: [], parihara_rules: [], census_rows: [],
    lattice_available: true, parihara_available: true, census_available: true, unavailable_reason: null }),
}))

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2026-10-09T01:00:00Z'))
  fetchMock.mockReset()
  finder.mockReset()
  fetchMock.mockImplementation(async () => ({ ok: true, json: async () => ({ authorized: false }) }))
  vi.stubGlobal('fetch', fetchMock)
  tools.clear()
  registerAllKalaViews({ tool(name: string, _description: string, shape: z.ZodRawShape, call: Registered['call']) {
    if (tools.has(name)) throw new Error(`duplicate registration: ${name}`)
    tools.set(name, { shape, call })
  } } as unknown as McpServer, principal)
})
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals() })

async function call(name: string, args: Record<string, unknown>) {
  const tool = tools.get(name)!
  return tool.call(z.object(tool.shape).parse(args))
}
function payload(result: CallToolResult): Record<string, unknown> {
  return (result.structuredContent as { object: Record<string, unknown> }).object
}

describe('K7-1b legacy public names, recorded before aliasing', () => {
  it('retains all seven public names alongside UPAYA and the dasha calendar', () => {
    expect([...tools.keys()].sort()).toEqual([
      'kala_ahead_get', 'kala_dasha_sandhi_get', 'kala_elect_get', 'kala_explain_get',
      'kala_now_get', 'kala_priority_get', 'kala_ritual_get', 'kala_story_get', 'kala_upaya_get',
    ])
  })
  it('NOW authorization denial keeps the complete old MCP envelope', async () => {
    expect(await call('kala_now_get', { chart_id: chart })).toMatchInlineSnapshot(`
      {
        "content": [
          {
            "text": "{"ok":false,"error":"AUTHZ_DENIED: not authorized to access this chart","tool":"kala_now_get","chart_id":"00000000-0000-4000-8000-000000000281"}",
            "type": "text",
          },
        ],
        "isError": true,
        "structuredContent": {
          "object": {
            "chart_id": "00000000-0000-4000-8000-000000000281",
            "error": "AUTHZ_DENIED: not authorized to access this chart",
            "ok": false,
            "tool": "kala_now_get",
          },
          "type": "object",
        },
      }
    `)
  })
  it('NOW denial fetches authorization only, with the original principal', async () => {
    await call('kala_now_get', { chart_id: chart })
    expect(fetchMock.mock.calls.map(([url, init]) => [new URL(url).pathname, JSON.parse(init.body)])).toEqual([
      ['/api/mcp/authz', { user_uid: principal.user_uid, chart_id: chart, required: 'view' }],
    ])
  })
  it('an exact-instant request cannot bypass NOW chart authorization to reach published stages', async () => {
    const result = await call('kala_now_get', { chart_id: chart, at: '2026-10-09T12:00:00Z' })
    expect([result.isError, fetchMock.mock.calls.map(([url]) => new URL(url).pathname)])
      .toEqual([true, ['/api/mcp/authz']])
  })
  it('EXPLAIN never invents assertion identity from a missing domain/bhava', async () => {
    expect(await call('kala_explain_get', { chart_id: chart })).toMatchInlineSnapshot(`
      {
        "content": [
          {
            "text": "{"ok":false,"error":"either \`domain\` or \`bhava\` is required","tool":"kala_explain_get"}",
            "type": "text",
          },
        ],
        "isError": true,
        "structuredContent": {
          "object": {
            "error": "either \`domain\` or \`bhava\` is required",
            "ok": false,
            "tool": "kala_explain_get",
          },
          "type": "object",
        },
      }
    `)
  })
  it('ELECT mortality withholding stays a successful permanent refusal', async () => {
    expect(await call('kala_elect_get', { chart_id: chart, question_frame: { entity: 'death' } })).toMatchInlineSnapshot(`
      {
        "content": [
          {
            "text": "{"withheld":true,"withheld_reason":"individualized_mortality_window_hard_exclusion","clause":"§3.5.C (MACRO_PLAN_v2_0.md Ethical Framework) via KALA_W4_UPAYA_DESIGN_v1_0.md §5.4 / ADJUDICATION-13","statement":"This request is withheld under the individualized-mortality-window HARD EXCLUSION. MACRO_PLAN_v2_0.md §3.5.C's no-date-of-death clause is ABSOLUTE across every audience tier — it is not a disclosure tier and it is not conditioned on filing, so no audience setting and no consent state unlocks it. No candidate window, no ranked slate, no diagnosis and no partial computation is served with this response, because none was attempted: the check runs before any computation. If the underlying question is about timing a rite, a remedy or an undertaking, re-ask it in those terms and it will be served in full.","detector":{"test":"request_shape","matched_on":"death"},"audience_tier_independent":true,"filing_state_independent":true}",
            "type": "text",
          },
        ],
        "structuredContent": {
          "object": {
            "audience_tier_independent": true,
            "clause": "§3.5.C (MACRO_PLAN_v2_0.md Ethical Framework) via KALA_W4_UPAYA_DESIGN_v1_0.md §5.4 / ADJUDICATION-13",
            "detector": {
              "matched_on": "death",
              "test": "request_shape",
            },
            "filing_state_independent": true,
            "statement": "This request is withheld under the individualized-mortality-window HARD EXCLUSION. MACRO_PLAN_v2_0.md §3.5.C's no-date-of-death clause is ABSOLUTE across every audience tier — it is not a disclosure tier and it is not conditioned on filing, so no audience setting and no consent state unlocks it. No candidate window, no ranked slate, no diagnosis and no partial computation is served with this response, because none was attempted: the check runs before any computation. If the underlying question is about timing a rite, a remedy or an undertaking, re-ask it in those terms and it will be served in full.",
            "withheld": true,
            "withheld_reason": "individualized_mortality_window_hard_exclusion",
          },
          "type": "object",
        },
      }
    `)
  })
  it('ritual Mode-3 keeps its exact redirect to ELECT', async () => {
    expect(await call('kala_ritual_get', { chart_id: chart, undertaking: 'sign the contract' })).toMatchInlineSnapshot(`
      {
        "content": [
          {
            "text": "{"tool":"kala_ritual_get","wrong_view":true,"mode_detected":"activity_election","reason":"kala_ritual_get serves YAJÑA-SETU Modes 1–2 only (opportunity scan / pattern search). The supplied 'undertaking' field (\\"sign the contract\\") names Mode 3 (activity election: undertaking → act-time slate + paired preparatory rite), which is served EXCLUSIVELY by kala_elect_get per the Mode-3 routing rule (KALA_SUPREME_ELEVATION_v1_0.md §8, clauses 1–2). No Mode-3 passthrough, proxy, or delegation is implemented in kala_ritual_get, by design, at W0 or ever — call kala_elect_get directly with this undertaking instead.","correct_surface":"kala_elect_get","tri_plane":{"interpretation_ref":{"no_lever":true,"reason":"wrong_view redirect — no interpretive content is served by this response."},"prediction_ref":{"no_lever":true,"reason":"wrong_view redirect — no predictive content is served by this response."},"intervention_ref":{"instrument":"kala_elect_get","hint":"Mode 3 (activity election): serves the act-time slate AND the paired preparatory rite with its own best time, as one answer."}}}",
            "type": "text",
          },
        ],
      }
    `)
  })
  it('ritual Mode-3 reaches no registry, stage, or sky request', async () => {
    await call('kala_ritual_get', { chart_id: chart, undertaking: 'sign the contract' })
    expect(fetchMock).not.toHaveBeenCalled()
  })
  it('authorized NOW keeps its legacy today clock and exact question frame with unavailable stages', async () => {
    fetchMock.mockImplementation(async (url: string) => url.includes('/api/mcp/authz')
      ? { ok: true, json: async () => ({ authorized: true }) }
      : { ok: false, status: 503, text: async () => 'CODEX unavailable' })
    const frame = { domain: 'career', horizon: 'today', entity: 'CODEX business' }
    const body = payload(await call('kala_now_get', { chart_id: chart, question_frame: frame }))
    expect([body.as_of_date, body.question_frame, body.windows, body.darshana]).toEqual([
      '2026-10-09', frame, [], null,
    ])
  })
  it('ELECT retains its default 90-day horizon and the old empty slate, never a synthesized event class', async () => {
    finder.mockImplementation(async (args: Record<string, unknown>) => ({ structuredContent: { object: {
      ok: true, chart_id: chart, action_type: args.action_type, query_window: args.date_range,
      windows: [], window_count: 0, provenance_envelope: {},
    } }, content: [] }))
    const frame = { domain: 'career', horizon: '90 days', entity: 'CODEX business' }
    const body = payload(await call('kala_elect_get', { chart_id: chart, undertaking: 'business', question_frame: frame }))
    expect([body.undertaking, body.query_window, body.question_frame, body.candidates]).toEqual([
      'business', { start: '2026-10-09', end: '2027-01-07' }, frame, [],
    ])
  })
  it('EXPLAIN retains the PACT chain and domain, without inferring a stored assertion identity', async () => {
    const chain = [{ stage: 'promise', status: 'denied', reason: 'CODEX no sourced promise' }]
    fetchMock.mockImplementation(async (_url: string, init: RequestInit) => {
      const request = JSON.parse(String(init.body))
      return request.uri === 'marsys://tool/L-PACT/pact_query'
        ? { ok: true, json: async () => ({ ok: true, content: { content: {
          pact_status: 'denied_at_promise', stages: chain, about: { domain: 'career' },
          as_of_date: '2026-10-09', fact_id_refs: [],
        }, is_error: false } }) }
        : { ok: false, status: 503, text: async () => 'CODEX unavailable' }
    })
    const frame = { domain: 'career', entity: 'CODEX business' }
    const body = payload(await call('kala_explain_get', { chart_id: chart, domain: 'career', question_frame: frame }))
    expect([body.pact_status, body.chain, body.question_frame, body.fact_id_refs]).toEqual([
      'denied_at_promise', chain, frame, [],
    ])
  })
})
