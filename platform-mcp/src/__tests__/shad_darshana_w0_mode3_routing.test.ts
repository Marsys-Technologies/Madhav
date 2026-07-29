/**
 * shad_darshana_w0_mode3_routing.test.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 6
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.6 / §3 W0.6: "Mode-3 single-route assertion test — the
 * CI-facing enforcement of the Mode-3 routing rule: a Mode-3-shaped payload to
 * `kala_ritual_get` must return `wrong_view` naming `kala_elect_get`, never pass through").
 *
 * DESIGN AUTHORITY (binding rule, quoted verbatim): KALA_SUPREME_ELEVATION_v1_0.md §8,
 * "THE MODE-3 ROUTING RULE": "`kala_ritual_get` serves Modes 1–2 ONLY. It never accepts an
 * undertaking as its subject and never emits an act-time slate. A Mode-3-shaped call
 * arriving at `kala_ritual_get` returns an honest `wrong_view` coverage state naming
 * `kala_elect_get` as the correct surface, plus the tri-plane pointer to it — a redirect,
 * never a passthrough, proxy, or internal delegation... CI asserts (2) — a test that a
 * Mode-3-shaped payload to `kala_ritual_get` yields `wrong_view` and not a slate."
 *
 * REAL-SDK REGISTRATION-GATE STYLE (brief §7 rail: "real-SDK tests for registration
 * gates"), following the established `registry_bridge_r5w4_pact.test.ts` precedent: this
 * test captures the ACTUAL `server.tool(...)` handler closure `registerRegistryBridgeTools`
 * registers (per brief §2 file map: "tools/kala_views/... + ONE registration block in
 * registry_bridge.ts") and invokes it directly — it exercises the real MCP seam, not a
 * reimplementation of it.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * COORDINATION NOTE (per this lane's task brief): `kala_ritual_get` is built by the
 * sibling `.worktrees/shad-darshana-upaya-ritual-stub` lane, concurrently with this one,
 * and is very likely NOT merged yet when this test file first runs. This test is written
 * against the SPEC above, not against unmerged code:
 *   - `kala_ritual_get` not registered at all → the test calls vitest's `skip()` (SKIPPED,
 *     not PASSED, not FAILED) with a clear reason. This is the expected pre-merge state.
 *   - Registered, but this test's Mode-3-shaped payload (an `undertaking` field — the
 *     spec's own vocabulary for the Mode-3 boundary) doesn't match the sibling's finalized
 *     input schema, OR its internal DB-proxy calls don't match this test's permissive
 *     fetch stub → reported via `expect.fail` with an explicit "test-harness gap, not a
 *     routing-rule verdict" message, never silently attributed to the routing rule itself.
 *   - Reachable end-to-end → the real routing-rule assertion runs: PASS iff the response
 *     carries `wrong_view` + names `kala_elect_get` and carries NO act-time slate.
 * This test is NEVER weakened to force a PASS before the sibling lane merges.
 * ══════════════════════════════════════════════════════════════════════════════════════
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

/** Captures every `server.tool(name, ...args, handler)` call — the handler is always the
 *  LAST argument regardless of how many schema/description args precede it, matching every
 *  registration shape already used across `registry_bridge.ts` (mirrors
 *  registry_bridge_r5w4_pact.test.ts's `makeCapturingServer`, generalized to not assume a
 *  fixed arg count since kala_ritual_get's exact registration signature is the sibling
 *  lane's to define). */
function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, ...rest: unknown[]) => {
      const handler = rest[rest.length - 1] as ToolHandler
      if (typeof handler === 'function') handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** Mode-3-shaped payload — names an UNDERTAKING (Elevation §8's own dividing line for Mode 3).
 *  `undertaking` is a plain string per the now-merged `kala_ritual_get`'s ratified MCP schema
 *  (`ritual.ts`: `undertaking: z.string().optional()` — a deliberate design choice, documented
 *  in that file's header, that the field has "no shape an undertaking could hide behind").
 *  Originally authored as `{ intent, description }` before the sibling lane's schema was
 *  visible; corrected post-merge to match the real, ratified contract — the routing rule
 *  itself was never in question, only this test's payload shape. */
const MODE3_SHAPED_PAYLOAD = {
  chart_id: TEST_CHART_ID,
  undertaking: 'sign a business contract',
}

function extractPayload(response: Awaited<ReturnType<ToolHandler>>): unknown {
  if (response.structuredContent?.object !== undefined) return response.structuredContent.object
  try {
    return JSON.parse(response.content?.[0]?.text ?? '{}')
  } catch {
    return {}
  }
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('ṢAḌ-DARŚANA Mode-3 single-route rule — kala_ritual_get (Elevation §8)', () => {
  it('is registered as a real server.tool callback alongside the rest of registry_bridge.ts, or is honestly SKIPPED pre-merge', async (ctx) => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)

    if (!handlers.has('kala_ritual_get')) {
      ctx.skip()
      return
    }
    expect(handlers.get('kala_ritual_get')).toBeTypeOf('function')
  })

  it('a Mode-3-shaped (undertaking) payload returns wrong_view naming kala_elect_get, and NEVER an act-time slate — the binding routing rule', async (ctx) => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)

    const handler = handlers.get('kala_ritual_get')
    if (!handler) {
      ctx.skip()
      return
    }

    // Permissive best-effort fetch stub: kala_ritual_get's real internal DB-proxy call
    // shape (if any) is the sibling lane's to define and unknown at authoring time. This
    // stub only exists so an internal call doesn't hard-crash before reaching the routing
    // branch; a real mismatch here is a test-harness gap (see try/catch below), not a
    // routing-rule failure.
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({ ok: true, content: {} }),
      text: async () => '{}',
    })))

    let response: Awaited<ReturnType<ToolHandler>>
    try {
      response = await handler(MODE3_SHAPED_PAYLOAD)
    } catch (err) {
      expect.fail(
        'kala_ritual_get handler threw before this test could evaluate the routing rule. ' +
        'This is most likely a TEST-HARNESS gap (this permissive fetch stub or the ' +
        '`undertaking` payload shape not matching the real, now-merged implementation), ' +
        'not necessarily a Mode-3-routing-rule violation — update this stub/payload once ' +
        `the sibling lane's real implementation is visible. Underlying error: ${err instanceof Error ? err.message : String(err)}`,
      )
      return
    }

    expect(response.isError, 'kala_ritual_get should redirect on a Mode-3-shaped payload, never tool-error').toBeFalsy()

    const payload = extractPayload(response)
    const serialized = JSON.stringify(payload)

    // RULE CLAUSE: never an act-time slate (the passthrough/proxy the rule forbids).
    const slateKeys = ['candidates', 'slate', 'act_time_slate', 'elected_windows', 'ranked_candidates']
    const hasSlate = typeof payload === 'object' && payload !== null && slateKeys.some((k) => Array.isArray((payload as Record<string, unknown>)[k]) && ((payload as Record<string, unknown>)[k] as unknown[]).length > 0)
    expect(hasSlate, `RULE VIOLATION: kala_ritual_get returned an act-time slate for a Mode-3-shaped payload. Payload: ${serialized.slice(0, 500)}`).toBe(false)

    // RULE CLAUSE: an honest wrong_view naming kala_elect_get.
    expect(serialized, 'must carry the wrong_view coverage state').toContain('wrong_view')
    expect(serialized, 'must name kala_elect_get as the correct surface').toContain('kala_elect_get')
  })
})
