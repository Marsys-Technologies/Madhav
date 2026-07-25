#!/usr/bin/env tsx
/**
 * budget_census_gate.ts — Elevation Campaign, Stream α (SATYA), Lane K1, Task 2.
 *
 * Asserts worst-case response size per tool stays under its declared
 * `MCP_RESPONSE_BUDGET_KB` ceiling (registry_bridge.ts ~L303-348 — see
 * `_tool_enumeration.ts`'s `extractResponseBudgetLedger()`, which parses that literal
 * object directly from source rather than hand-copying the 26 numbers here). Run
 * against the canonical chart (482012f1-710e-4a25-994a-93821f5871aa).
 *
 * "Worst case" per tool: every call requests `verbosity: 'detailed'` (the ceiling's
 * own governing knob per registry_bridge.ts's W3 "One Envelope" comment — 'detailed'
 * is the untightened default every existing caller gets today) with no `budget_kb`
 * override, so the measured byte count is the tool's real, un-shrunk worst case
 * against its OWN static ceiling — the number this gate exists to keep honest.
 *
 * Ceiling definition (registry_bridge.ts's own comment, ~L300-302): "the wire budget
 * for a fully-assembled MCP tool response (envelope + orientation_context together —
 * the whole structuredContent object), not just the inner content block." This gate
 * measures `JSON.stringify(structuredContent.object)` byte length accordingly (via
 * `_mcp_client.ts`'s `unwrapToolPayload`), not just an inner field.
 *
 * Secondary, INFORMATIONAL-ONLY check (never fails the gate): re-calls each tool with
 * `budget_kb` set to DOUBLE its static ceiling, to spot-check the C1 contract's clamp
 * rule ("a caller-supplied budget_kb HIGHER than the tool's static default is clamped
 * to the static default — the server ceiling is a hard cap"). C1 is FROZEN but marks
 * itself opt-in per capability ("MAY accept"), so a tool not yet wired for budget_kb
 * is expected and reported as INFO, not FAIL.
 *
 * Two modes: PLAN (no MCP_SERVER_URL — lists the ceiling ledger only, exit 0) / LIVE.
 *
 * Run (plan mode, from `platform/`):
 *   npx tsx scripts/census/elev_gates/budget_census_gate.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/elev_gates/budget_census_gate.ts
 */
import { extractResponseBudgetLedger } from './_tool_enumeration'
import { ElevMcpClient, resolveMcpTarget, unwrapToolPayload, CANONICAL_CHART_ID, envOrDefault, DEFAULT_TOOL_TIMEOUT_MS } from './_mcp_client'
import { printGateReport, type GateResult } from './_report'

const AYANAMSHA_ID = 'lahiri_chitrapaksha'
const TOOL_TIMEOUT_MS = Number(envOrDefault('BUDGET_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))
const MIN_GAP_MS = Number(envOrDefault('BUDGET_MIN_GAP_MS', '300'))

// Worst-case-shaping param overrides — same rationale as smoke_gate.ts's table, tuned
// here toward "widest reasonable page" rather than "minimal valid" (a budget gate
// wants the biggest honest payload the tool can produce, not the smallest).
const WORST_CASE_OVERRIDES: Record<string, Record<string, unknown>> = {
  graha_portrait: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, graha_key: 'SU', include: ['position', 'dignity', 'aspects', 'yogas'] },
  judgment_query: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  pact_query: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  get_domain_reading: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  assess_career: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_health: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_marriage: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_wealth: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  list_assets: { limit: 200 },
  vector_search: { query_text: 'Saturn dignity strength career', chart_id: CANONICAL_CHART_ID, limit: 50 },
  tool_search: { query: 'chart' },
  query_chart_facts: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, limit: 200 },
}

function paramsFor(toolName: string): Record<string, unknown> {
  const base = WORST_CASE_OVERRIDES[toolName] ?? { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID }
  return { ...base, verbosity: 'detailed' }
}

async function sleep(ms: number): Promise<void> {
  await new Promise((r) => setTimeout(r, ms))
}

function byteLen(v: unknown): number {
  return Buffer.byteLength(JSON.stringify(v) ?? '', 'utf-8')
}

async function main(): Promise<void> {
  const ledger = extractResponseBudgetLedger()
  const toolNames = Object.keys(ledger).sort()
  const results: GateResult[] = []

  results.push({
    id: 'budget:ledger-extracted',
    title: 'MCP_RESPONSE_BUDGET_KB ledger parsed from registry_bridge.ts source',
    status: toolNames.length > 0 ? 'PASS' : 'FAIL',
    detail: `${toolNames.length} tools with a declared byte ceiling: ${toolNames.join(', ')}`,
  })

  const target = resolveMcpTarget()
  if (!target) {
    for (const name of toolNames) {
      results.push({
        id: `budget-plan:${name}`,
        title: `${name} — declared ceiling ${ledger[name]}KB`,
        status: 'SKIPPED',
        detail: `PLAN mode — no MCP_SERVER_URL set, no live call executed. Worst-case call plan: ${JSON.stringify(paramsFor(name))}`,
      })
    }
    const reason = 'MCP_SERVER_URL not set — running in PLAN mode only (ledger extraction verified, no live byte measurement).'
    process.exit(printGateReport('budget_census_gate (PLAN mode)', results, reason))
    return
  }

  const client = new ElevMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()

  for (const name of toolNames) {
    const ceilingKb = ledger[name]!
    const args = paramsFor(name)
    const outcome = await client.callTool(name, args)
    if (outcome.timed_out || outcome.status >= 500 || outcome.status === 0) {
      results.push({
        id: `budget:${name}`,
        title: `${name} — could not measure (call failed)`,
        status: 'QUARANTINED',
        detail: `status=${outcome.status}, timed_out=${outcome.timed_out}, error=${outcome.error ?? 'n/a'} — this is a smoke-gate-class failure, not a budget violation; see smoke_gate.ts.`,
      })
      await sleep(MIN_GAP_MS)
      continue
    }
    const { payload, isToolError } = unwrapToolPayload(outcome)
    if (isToolError) {
      results.push({
        id: `budget:${name}`,
        title: `${name} — tool-level error, size not meaningful`,
        status: 'QUARANTINED',
        detail: `Tool returned an in-band error for this worst-case arg guess: ${JSON.stringify(payload).slice(0, 200)}`,
      })
      await sleep(MIN_GAP_MS)
      continue
    }
    const bytes = byteLen(payload)
    const ceilingBytes = ceilingKb * 1024
    const withinBudget = bytes <= ceilingBytes
    results.push({
      id: `budget:${name}`,
      title: `${name} — ${bytes}B measured vs ${ceilingBytes}B (${ceilingKb}KB) ceiling`,
      status: withinBudget ? 'PASS' : 'FAIL',
      detail: withinBudget
        ? `Within budget (${((bytes / ceilingBytes) * 100).toFixed(1)}% of ceiling).`
        : `OVER BUDGET by ${bytes - ceilingBytes}B (${(((bytes - ceilingBytes) / ceilingBytes) * 100).toFixed(1)}% over) — args=${JSON.stringify(args)}`,
    })

    // Secondary, informational-only C1 clamp spot-check (never affects exit code).
    await sleep(MIN_GAP_MS)
    const doubled = await client.callTool(name, { ...args, budget_kb: ceilingKb * 2 })
    if (!doubled.timed_out && doubled.status < 500 && doubled.status !== 0) {
      const { payload: doubledPayload, isToolError: doubledErr } = unwrapToolPayload(doubled)
      if (!doubledErr) {
        const doubledBytes = byteLen(doubledPayload)
        results.push({
          id: `budget-c1-clamp:${name}`,
          title: `${name} — C1 clamp spot-check (budget_kb=${ceilingKb * 2} requested, static ceiling=${ceilingKb}KB)`,
          status: doubledBytes <= ceilingBytes ? 'PASS' : 'WARN',
          detail:
            doubledBytes <= ceilingBytes
              ? `Server held the hard cap (${doubledBytes}B <= ${ceilingBytes}B) — C1 clamp behavior confirmed OR tool does not yet accept budget_kb (same observable result).`
              : `INFORMATIONAL: doubled-budget_kb call returned ${doubledBytes}B, exceeding the static ceiling ${ceilingBytes}B — either this tool has not yet wired the C1 clamp, or a real regression. Not counted as a gate FAIL (C1 is opt-in per capability); flagged for Verifier follow-up.`,
        })
      }
    }
    await sleep(MIN_GAP_MS)
  }

  process.exit(printGateReport('budget_census_gate (LIVE)', results))
}

main().catch((err) => {
  console.error('budget_census_gate FATAL:', err)
  process.exit(2)
})
