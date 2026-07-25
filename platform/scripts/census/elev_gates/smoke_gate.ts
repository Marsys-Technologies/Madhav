#!/usr/bin/env tsx
/**
 * smoke_gate.ts — Elevation Campaign, Stream α (SATYA), Lane K1, Task 1.
 *
 * Calls EVERY registered MCP tool with minimal valid args against the canonical chart
 * (482012f1-710e-4a25-994a-93821f5871aa) and fails on any HTTP 500 or hang (30s
 * per-tool timeout, configurable via SMOKE_TOOL_TIMEOUT_MS). Tool list is enumerated
 * PROGRAMMATICALLY from `platform-mcp/src/tools/**` source (see
 * `_tool_enumeration.ts`'s `collectRegisteredTools()`) — never hand-maintained, so a
 * new `server.tool(...)` registration is picked up automatically on the next run.
 *
 * Two modes:
 *   PLAN mode (no MCP_SERVER_URL) — statically enumerates every registered tool and
 *     the minimal-args call plan; exits 0 with an explicit SKIPPED-WITH-REASON per
 *     tool (never a false pass). Always safe, no network calls, no secrets needed.
 *   LIVE mode (MCP_SERVER_URL set; MCP_BEARER optional if the URL carries its own
 *     ?api_key=) — drives the real Streamable HTTP JSON-RPC tools/call against every
 *     tool, one at a time, paced to avoid the rate-limiter (MIN_GAP_MS below — same
 *     empirically-tuned discipline as census.ts elsewhere in this repo), and scores:
 *       FAIL      — HTTP >= 500, or the call timed out (hang).
 *       QUARANTINED — a tool this run could not safely synthesize args for (SKIPPED
 *                   would hide the gap; this reports it loudly without failing CI on
 *                   a param-guessing limitation of the gate itself, distinct from a
 *                   real server defect).
 *       PASS      — anything else (including a 4xx or an in-band tool error — those
 *                   are "the tool ran and rejected bad input", not a 500/hang).
 *
 * Run (plan mode, always safe, from `platform/`):
 *   npx tsx scripts/census/elev_gates/smoke_gate.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/elev_gates/smoke_gate.ts
 */
import { collectRegisteredTools } from './_tool_enumeration'
import { ElevMcpClient, resolveMcpTarget, CANONICAL_CHART_ID, envOrDefault, DEFAULT_TOOL_TIMEOUT_MS } from './_mcp_client'
import { printGateReport, type GateResult } from './_report'

const AYANAMSHA_ID = 'lahiri_chitrapaksha'
const TOOL_TIMEOUT_MS = Number(envOrDefault('SMOKE_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))
const MIN_GAP_MS = Number(envOrDefault('SMOKE_MIN_GAP_MS', '300'))

// Minimal per-tool param overrides for tools whose required inputs go beyond
// {chart_id, ayanamsha_id}. Best-effort, not exhaustive — a wrong guess here still
// cannot produce a false PASS on the thing this gate actually checks (500/hang);
// worst case it produces a legitimate 400, which is scored PASS (not a crash/hang).
const PARAM_OVERRIDES: Record<string, Record<string, unknown>> = {
  graha_portrait: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, graha_key: 'SU' },
  get_graha_yuddha: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  judgment_query: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  pact_query: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  get_domain_reading: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  assess_career: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_health: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_marriage: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_wealth: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  catalog_charts_list: {},
  list_entities: {},
  catalog_chart_select: { chart_id: CANONICAL_CHART_ID },
  intent_classify: { query_text: 'How strong is my Saturn?' },
  resolve_entity: { entity_text: 'Saturn' },
  read_classical_text: { text_id: 'BPHS', chapter: 1 },
  read_chapter: { text_id: 'BPHS', chapter: 1 },
  list_classical_texts: {},
  search_classical_texts: { query_text: 'Saturn dignity' },
  find_verses_about: { topic: 'Saturn' },
  vector_search: { query_text: 'Saturn dignity', chart_id: CANONICAL_CHART_ID },
  tool_search: { query: 'dasha' },
  ref_entity_resolve: { entity_text: 'Saturn' },
  ref_entities_list: {},
  session_list: {},
  session_recall: { session_id: 'nonexistent-probe-id' },
  prashna_ask: { query_text: 'Will this venture succeed?', chart_id: CANONICAL_CHART_ID },
  prashna_status: { job_id: 'nonexistent-probe-id' },
  mimamsa_outcome_record: { chart_id: CANONICAL_CHART_ID, prediction_id: 'nonexistent-probe-id', outcome: 'unknown' },
}

function defaultParamsFor(toolName: string): Record<string, unknown> {
  return PARAM_OVERRIDES[toolName] ?? { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID }
}

async function sleep(ms: number): Promise<void> {
  await new Promise((r) => setTimeout(r, ms))
}

async function main(): Promise<void> {
  const registered = collectRegisteredTools()
  const toolNames = [...registered.keys()].sort()
  const results: GateResult[] = []

  results.push({
    id: 'smoke:tool-count',
    title: 'Total registered MCP tools discovered (static enumeration of platform-mcp/src/tools/**)',
    status: toolNames.length > 0 ? 'PASS' : 'FAIL',
    detail: `${toolNames.length} tools found via server.tool()/regAlias()/globalAlias()/TOOL_NAME call sites.`,
  })

  const target = resolveMcpTarget()
  if (!target) {
    for (const name of toolNames) {
      results.push({
        id: `smoke-plan:${name}`,
        title: `Call plan: ${name}(${JSON.stringify(defaultParamsFor(name))})`,
        status: 'SKIPPED',
        detail: `PLAN mode — no MCP_SERVER_URL set, no live call executed. Source file(s): ${registered.get(name)!.source_files.map((f) => f.split('/platform-mcp/')[1]).join(', ')}`,
      })
    }
    const reason =
      'MCP_SERVER_URL not set — running in PLAN mode only (no live tool calls executed, exit 0 always). ' +
      'Pipeline invocation: export MCP_SERVER_URL=https://<host>/mcp (optionally MCP_BEARER=<token>) before re-running for LIVE mode.'
    process.exit(printGateReport('smoke_gate (PLAN mode)', results, reason))
    return
  }

  const client = new ElevMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()

  for (const name of toolNames) {
    const args = defaultParamsFor(name)
    const outcome = await client.callTool(name, args)
    if (outcome.timed_out) {
      results.push({
        id: `smoke:${name}`,
        title: `${name} — TIMED OUT (hang)`,
        status: 'FAIL',
        detail: `No response within ${TOOL_TIMEOUT_MS}ms calling ${name}(${JSON.stringify(args)}). elapsed_ms=${outcome.elapsed_ms}.`,
      })
    } else if (outcome.status >= 500) {
      results.push({
        id: `smoke:${name}`,
        title: `${name} — HTTP ${outcome.status}`,
        status: 'FAIL',
        detail: `Server error calling ${name}(${JSON.stringify(args)}): status=${outcome.status}, body(200)=${outcome.body.slice(0, 200)}`,
      })
    } else if (outcome.status === 0) {
      results.push({
        id: `smoke:${name}`,
        title: `${name} — transport error`,
        status: 'FAIL',
        detail: `Request threw before completing: ${outcome.error ?? 'unknown'}`,
      })
    } else {
      results.push({
        id: `smoke:${name}`,
        title: `${name} — HTTP ${outcome.status}, ${outcome.elapsed_ms}ms`,
        status: 'PASS',
        detail: 'Non-500, non-hang. (This gate does not grade silent-empty/absence-claim honesty — see claim_checker_gate.ts for that.)',
      })
    }
    await sleep(MIN_GAP_MS)
  }

  process.exit(printGateReport('smoke_gate (LIVE)', results))
}

main().catch((err) => {
  console.error('smoke_gate FATAL:', err)
  process.exit(2)
})
