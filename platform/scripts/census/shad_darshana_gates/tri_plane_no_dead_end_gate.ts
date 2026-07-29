#!/usr/bin/env tsx
/**
 * tri_plane_no_dead_end_gate.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 3
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.3 / §3 W0.6: "tri-plane no-dead-end battery (asserting
 * honest no_lever allowed)").
 *
 * DESIGN AUTHORITY: KALA_SUPREME_ELEVATION_v1_0.md §11 (item 43) — "every served temporal
 * object carries live pointers into the other two planes... or an honest
 * `no_lever (reason)`... CI battery: no view ships a row that dead-ends."
 *
 * This is the LIVE-serving half of the battery — it calls the real deployed kala_* tools
 * and inspects each envelope's `tri_plane` block. The unit-level half (which needs no live
 * server and is always runnable) lives at
 * `platform-mcp/src/__tests__/shad_darshana_w0_tri_plane_no_dead_end.test.ts`, exercising
 * `kala_envelope.ts`'s own `TriPlanePointers`/`noLeverPointer`/`isNoLever` shape directly —
 * that file is the one every session should treat as this item's primary always-green
 * regression guard; THIS script is the complementary end-to-end check once the eight
 * facades are live.
 *
 * A tri_plane field is graded:
 *   - PASS  — a well-formed pointer ({instrument, hint}, both non-empty strings), OR a
 *             well-formed honest no_lever ({no_lever:true, reason} with non-empty reason).
 *   - FAIL  — the field is present but malformed (missing hint/reason, wrong shape) — a
 *             pointer that LOOKS present but wouldn't actually resolve is worse than an
 *             honest absence.
 *   - WARN  — the field is `null`. Per the design, `null` is only legal when "this object
 *             IS that plane already" — a business rule this v0 skeleton cannot verify
 *             per-object without the real view semantics (that lands with the facades
 *             themselves), so a bare null is flagged for human/Verifier review rather than
 *             hard-failed. A completely MISSING `tri_plane` key is FAIL (item 43 requires
 *             the block on every served temporal object, full stop).
 *
 * Two modes, matching every sibling gate in this directory. See specificity_gate_v0.ts's
 * header for the shared PLAN/LIVE + sibling-lane-coordination rationale (identical here).
 *
 * Run (plan mode, from `platform/`):
 *   npx tsx scripts/census/shad_darshana_gates/tri_plane_no_dead_end_gate.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/shad_darshana_gates/tri_plane_no_dead_end_gate.ts
 */
import { ShadDarshanaMcpClient, resolveMcpTarget, unwrapToolPayload, envOrDefault, DEFAULT_TOOL_TIMEOUT_MS, CANONICAL_CHART_ID, CROSS_CHECK_CHART_ID } from './_mcp_client'
import { printGateReport, type GateResult } from './_report'
import { SHAD_DARSHANA_EIGHT_TOOLS, collectShadDarshanaRegistration, isKalaToolRegistered } from './_kala_tool_registration'

const TOOL_TIMEOUT_MS = Number(envOrDefault('TRI_PLANE_GATE_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))
const MIN_GAP_MS = Number(envOrDefault('TRI_PLANE_GATE_MIN_GAP_MS', '300'))
const PLANES = ['interpretation_ref', 'prediction_ref', 'intervention_ref'] as const

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

type PlaneGrade = 'PASS' | 'FAIL' | 'WARN'

function gradePlaneValue(value: unknown): { grade: PlaneGrade; note: string } {
  if (value === null || value === undefined) {
    return { grade: 'WARN', note: 'null — only legal when this object IS that plane already; not independently verifiable at v0.' }
  }
  if (typeof value !== 'object') {
    return { grade: 'FAIL', note: `malformed — expected an object, got ${typeof value}` }
  }
  const obj = value as Record<string, unknown>
  if (obj['no_lever'] === true) {
    const reason = obj['reason']
    if (typeof reason === 'string' && reason.trim().length > 0) {
      return { grade: 'PASS', note: `honest no_lever: ${reason.slice(0, 120)}` }
    }
    return { grade: 'FAIL', note: 'no_lever:true but reason missing/empty — a dead end wearing an honest label.' }
  }
  const instrument = obj['instrument']
  const hint = obj['hint']
  if (typeof instrument === 'string' && instrument.trim().length > 0 && typeof hint === 'string' && hint.trim().length > 0) {
    return { grade: 'PASS', note: `resolvable pointer: ${instrument}` }
  }
  return { grade: 'FAIL', note: `malformed pointer shape: ${JSON.stringify(obj).slice(0, 200)}` }
}

function planResults(): GateResult[] {
  const registration = collectShadDarshanaRegistration()
  return SHAD_DARSHANA_EIGHT_TOOLS.map((tool) => {
    const registered = isKalaToolRegistered(tool, registration)
    return {
      id: `tri-plane-plan:${tool}`,
      title: `Call plan: ${tool}(chart_id) → inspect envelope.tri_plane.{${PLANES.join(',')}} — registered=${registered}`,
      status: 'SKIPPED' as const,
      detail: registered
        ? 'PLAN mode — no MCP_SERVER_URL set, no live call executed.'
        : 'PLAN mode — tool not yet statically registered (sibling facade lane likely not merged yet).',
    }
  })
}

async function liveResults(client: ShadDarshanaMcpClient): Promise<GateResult[]> {
  const results: GateResult[] = []
  const registration = collectShadDarshanaRegistration()
  const charts = [CANONICAL_CHART_ID, CROSS_CHECK_CHART_ID]

  for (const tool of SHAD_DARSHANA_EIGHT_TOOLS) {
    if (!isKalaToolRegistered(tool, registration)) {
      results.push({ id: `tri-plane:${tool}`, title: `Tri-plane — ${tool}`, status: 'SKIPPED', detail: 'Tool not yet registered — sibling facade lane not merged yet.' })
      continue
    }
    for (const chartId of charts) {
      const outcome = await client.callTool(tool, { chart_id: chartId }, TOOL_TIMEOUT_MS)
      await sleep(MIN_GAP_MS)
      const idPrefix = `tri-plane:${tool}:${chartId.slice(0, 8)}`
      if (outcome.timed_out || outcome.status >= 500) {
        results.push({ id: idPrefix, title: `Tri-plane — ${tool} (${chartId.slice(0, 8)})`, status: 'FAIL', detail: `Live infra failure: timed_out=${outcome.timed_out}, status=${outcome.status}` })
        continue
      }
      if (!outcome.ok) {
        results.push({ id: idPrefix, title: `Tri-plane — ${tool} (${chartId.slice(0, 8)})`, status: 'WARN', detail: `HTTP ${outcome.status} — possible arg-schema mismatch pre-merge, not a tri-plane verdict.` })
        continue
      }
      const { payload, isToolError } = unwrapToolPayload(outcome)
      if (isToolError || typeof payload !== 'object' || payload === null) {
        results.push({ id: idPrefix, title: `Tri-plane — ${tool} (${chartId.slice(0, 8)})`, status: 'WARN', detail: 'tool error or non-object payload — cannot inspect tri_plane.' })
        continue
      }
      const triPlane = (payload as Record<string, unknown>)['tri_plane']
      if (typeof triPlane !== 'object' || triPlane === null) {
        results.push({ id: idPrefix, title: `Tri-plane — ${tool} (${chartId.slice(0, 8)})`, status: 'FAIL', detail: 'envelope has no tri_plane block at all — item 43 requires it on every served temporal object.' })
        continue
      }
      const tp = triPlane as Record<string, unknown>
      for (const plane of PLANES) {
        const { grade, note } = gradePlaneValue(tp[plane])
        results.push({
          id: `${idPrefix}:${plane}`,
          title: `Tri-plane — ${tool} (${chartId.slice(0, 8)}) . ${plane}`,
          status: grade,
          detail: note,
        })
      }
    }
  }
  return results
}

async function main(): Promise<void> {
  const target = resolveMcpTarget()
  if (!target) {
    process.exit(printGateReport(
      'tri_plane_no_dead_end_gate (PLAN mode)',
      planResults(),
      'MCP_SERVER_URL not set — running in PLAN mode only (registration checked statically, no live tool calls executed, exit 0 always).',
    ))
    return
  }
  const client = new ShadDarshanaMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()
  process.exit(printGateReport('tri_plane_no_dead_end_gate (LIVE)', await liveResults(client)))
}

main().catch((err) => {
  console.error('tri_plane_no_dead_end_gate FATAL:', err)
  process.exit(2)
})
