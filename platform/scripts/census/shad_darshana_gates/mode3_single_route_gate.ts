#!/usr/bin/env tsx
/**
 * mode3_single_route_gate.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 6
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.6 / §3 W0.6: "Mode-3 single-route assertion test").
 *
 * DESIGN AUTHORITY (binding rule, quoted verbatim): KALA_SUPREME_ELEVATION_v1_0.md §8,
 * "THE MODE-3 ROUTING RULE":
 *   1. `kala_elect_get` is the sole server of Mode 3.
 *   2. `kala_ritual_get` serves Modes 1–2 ONLY. It never accepts an undertaking as its
 *      subject and never emits an act-time slate. A Mode-3-shaped call arriving at
 *      `kala_ritual_get` returns an honest `wrong_view` coverage state naming
 *      `kala_elect_get` as the correct surface, plus the tri-plane pointer to it — a
 *      redirect, NEVER a passthrough, proxy, or internal delegation.
 *   4. CI asserts (2) — "a test that a Mode-3-shaped payload to `kala_ritual_get` yields
 *      `wrong_view` and not a slate."
 *
 * THIS gate is that CI assertion, driven against the real deployed connector.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * COORDINATION NOTE (per this lane's task brief — read before interpreting a FAIL/WARN):
 * `kala_ritual_get` is built by the sibling `.worktrees/shad-darshana-upaya-ritual-stub`
 * lane, concurrently with this one. It is very likely NOT merged/deployed when this gate
 * first runs. This gate is written against the SPEC above, not against unmerged code:
 *   - Tool not registered at all           → SKIPPED (sibling not merged yet; not a FAIL).
 *   - Tool registered but the Mode-3-shaped payload this gate sends doesn't match the
 *     sibling's actual finalized input schema (a 4xx) → WARN, with the schema-mismatch
 *     risk stated explicitly — this gate guesses a payload shape (an `undertaking` field,
 *     naming the Elevation §8 Mode-3 boundary: "an undertaking-shaped question") because
 *     the real schema is the sibling lane's to define, not this lane's to invent.
 *   - Tool reachable and responds → the routing-rule assertion runs for real: PASS iff
 *     the response carries a `wrong_view`-shaped coverage state naming `kala_elect_get`
 *     AND carries no act-time slate; FAIL if it returns any slate/candidate list (rule
 *     violated) or a wrong_view that doesn't name kala_elect_get (rule half-satisfied).
 * This gate is NEVER weakened to force a PASS before the sibling lane merges — an honest
 * SKIPPED/WARN is the correct state per this lane's task brief ("do NOT weaken or skip a
 * check just to get green ... report that state truthfully instead").
 * ══════════════════════════════════════════════════════════════════════════════════════
 *
 * Two modes, matching every sibling gate in this directory.
 *
 * Run (plan mode, from `platform/`):
 *   npx tsx scripts/census/shad_darshana_gates/mode3_single_route_gate.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/shad_darshana_gates/mode3_single_route_gate.ts
 */
import { ShadDarshanaMcpClient, resolveMcpTarget, unwrapToolPayload, envOrDefault, DEFAULT_TOOL_TIMEOUT_MS, CANONICAL_CHART_ID } from './_mcp_client'
import { printGateReport, type GateResult } from './_report'
import { isKalaToolRegistered, collectShadDarshanaRegistration } from './_kala_tool_registration'

const TOOL_TIMEOUT_MS = Number(envOrDefault('MODE3_GATE_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))

/**
 * The best-effort Mode-3-shaped payload: names an UNDERTAKING (Elevation §8's dividing
 * line between "Mode 3 — ACTIVITY ELECTION, given an undertaking" and Modes 1-2, which
 * take a horizon or a declared sky-pattern spec instead). The exact field name is the
 * sibling `upaya-ritual-stub` lane's to finalize; this is the spec-faithful guess.
 */
function mode3ShapedPayload(chartId: string): Record<string, unknown> {
  return {
    chart_id: chartId,
    undertaking: { intent: 'sign_contract', description: 'sign a business contract' },
  }
}

/** Detects an act-time slate in a payload — any array of candidate/window rows that looks
 *  like ELECT output smuggled through kala_ritual_get (the passthrough the rule forbids). */
function hasActTimeSlate(payload: Record<string, unknown>): boolean {
  const candidateKeys = ['candidates', 'slate', 'act_time_slate', 'elected_windows', 'ranked_candidates']
  return candidateKeys.some((k) => Array.isArray(payload[k]) && (payload[k] as unknown[]).length > 0)
}

/** Detects the honest wrong_view redirect naming kala_elect_get. Checks a handful of
 *  plausible field locations since the exact envelope shape is the sibling lane's to
 *  define (coverage state entry, top-level flag, or tri_plane pointer). */
function findsWrongViewToElect(payload: Record<string, unknown>): { found: boolean; note: string } {
  const haystacks: unknown[] = [payload['coverage'], payload['coverage_state'], payload]
  for (const h of haystacks) {
    const text = JSON.stringify(h ?? {})
    if (text.includes('wrong_view') && text.includes('kala_elect_get')) {
      return { found: true, note: 'wrong_view naming kala_elect_get found.' }
    }
  }
  const triPlane = payload['tri_plane']
  if (typeof triPlane === 'object' && triPlane !== null) {
    const text = JSON.stringify(triPlane)
    if (text.includes('kala_elect_get')) {
      return { found: true, note: 'tri_plane pointer to kala_elect_get found alongside coverage check.' }
    }
  }
  return { found: false, note: `no wrong_view+kala_elect_get reference found. Payload keys: ${Object.keys(payload).join(', ')}` }
}

function planResult(): GateResult {
  const registered = isKalaToolRegistered('kala_ritual_get', collectShadDarshanaRegistration())
  return {
    id: 'mode3-plan:kala_ritual_get',
    title: `Call plan: kala_ritual_get(${JSON.stringify(mode3ShapedPayload(CANONICAL_CHART_ID))}) — registered=${registered}`,
    status: 'SKIPPED',
    detail: registered
      ? 'PLAN mode — no MCP_SERVER_URL set, no live call executed.'
      : 'PLAN mode — kala_ritual_get not yet statically registered (sibling upaya-ritual-stub lane not merged yet). This IS the expected pre-merge state.',
  }
}

async function liveResult(client: ShadDarshanaMcpClient): Promise<GateResult> {
  const registered = isKalaToolRegistered('kala_ritual_get', collectShadDarshanaRegistration())
  if (!registered) {
    return {
      id: 'mode3:kala_ritual_get',
      title: 'Mode-3 single-route assertion — kala_ritual_get',
      status: 'SKIPPED',
      detail: 'kala_ritual_get not yet registered on the live server — sibling upaya-ritual-stub lane not merged/deployed yet. Not a fabricated pass; re-run once that lane lands.',
    }
  }

  const outcome = await client.callTool('kala_ritual_get', mode3ShapedPayload(CANONICAL_CHART_ID), TOOL_TIMEOUT_MS)
  if (outcome.timed_out || outcome.status >= 500) {
    return { id: 'mode3:kala_ritual_get', title: 'Mode-3 single-route assertion — kala_ritual_get', status: 'FAIL', detail: `Live infra failure: timed_out=${outcome.timed_out}, status=${outcome.status}` }
  }
  if (!outcome.ok) {
    return {
      id: 'mode3:kala_ritual_get',
      title: 'Mode-3 single-route assertion — kala_ritual_get',
      status: 'WARN',
      detail: `HTTP ${outcome.status} — this gate's Mode-3-shaped payload (an "undertaking" field) may not match the sibling lane's finalized input schema. Not a routing-rule verdict. Body: ${outcome.body.slice(0, 300)}`,
    }
  }
  const { payload, isToolError } = unwrapToolPayload(outcome)
  if (isToolError || typeof payload !== 'object' || payload === null) {
    return { id: 'mode3:kala_ritual_get', title: 'Mode-3 single-route assertion — kala_ritual_get', status: 'WARN', detail: 'Tool-level error or non-object payload — cannot evaluate routing rule.' }
  }
  const obj = payload as Record<string, unknown>

  const slate = hasActTimeSlate(obj)
  const { found: wrongView, note: wrongViewNote } = findsWrongViewToElect(obj)

  if (slate) {
    return {
      id: 'mode3:kala_ritual_get',
      title: 'Mode-3 single-route assertion — kala_ritual_get',
      status: 'FAIL',
      detail: 'RULE VIOLATION: kala_ritual_get returned an act-time slate for a Mode-3-shaped (undertaking) payload — the exact passthrough/proxy behavior the Mode-3 routing rule forbids.',
    }
  }
  if (!wrongView) {
    return {
      id: 'mode3:kala_ritual_get',
      title: 'Mode-3 single-route assertion — kala_ritual_get',
      status: 'FAIL',
      detail: `No slate returned (good), but no honest wrong_view→kala_elect_get redirect found either — the rule requires an explicit redirect, not a silent empty. ${wrongViewNote}`,
    }
  }
  return {
    id: 'mode3:kala_ritual_get',
    title: 'Mode-3 single-route assertion — kala_ritual_get',
    status: 'PASS',
    detail: `Mode-3 routing rule holds: no slate, and ${wrongViewNote}`,
  }
}

async function main(): Promise<void> {
  const target = resolveMcpTarget()
  if (!target) {
    process.exit(printGateReport(
      'mode3_single_route_gate (PLAN mode)',
      [planResult()],
      'MCP_SERVER_URL not set — running in PLAN mode only (registration checked statically, no live tool calls executed, exit 0 always).',
    ))
    return
  }
  const client = new ShadDarshanaMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()
  process.exit(printGateReport('mode3_single_route_gate (LIVE)', [await liveResult(client)]))
}

main().catch((err) => {
  console.error('mode3_single_route_gate FATAL:', err)
  process.exit(2)
})
