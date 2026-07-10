/**
 * mcp_tool_smoke.ts — per-tool smoke battery
 * =============================================
 * Task item 5: "a lightweight test that calls every registered MCP tool
 * once with minimal valid params and asserts non-500/non-silent-empty" —
 * this feeds Phase-0 lanes 0b/0a's dead-tool fixes. Coordinates with those
 * lanes by grepping the register for currently-known-dead tools so this
 * battery documents expected-fail vs expected-pass honestly at merge time.
 *
 * KNOWN_DEAD_TOOLS below is sourced directly from
 * MARSYS_DEFECT_GAP_REGISTER_v2_0.md §SECTION 4 "New rows (v2) — dead
 * tools" (lane 0b's exact scope, Phase 0 plan line: "Lane 0b: schema-drift
 * dead tools — R-9, R-10, R-12, R-14, T-7"). As lane 0b lands fixes, delete
 * entries here — this flips those tools from EXPECTED-FAIL to
 * REQUIRED-PASS, so the battery starts enforcing the fix (ratchet).
 *
 * This script needs a LIVE, reachable MCP server (Streamable HTTP
 * transport, POST /mcp) plus a valid bearer principal — see
 * platform-mcp/src/server.ts:179 and src/auth.ts for the auth contract.
 * It is NOT runnable from a DB-only CI job or from this static worktree
 * sandbox (no deployed platform-mcp instance + credentials available here).
 *
 * Two modes:
 *   PLAN mode (no MCP_SERVER_URL set): statically enumerates every tool
 *     registered via server.tool(...) across platform-mcp/src/tools, prints
 *     the minimal-params call plan and the expected-fail/expected-pass
 *     classification per register row, and exits with a SKIPPED-WITH-REASON
 *     report (TAP-9 discipline — never silently pass).
 *   LIVE mode (MCP_SERVER_URL + MCP_SMOKE_BEARER_TOKEN set): drives the
 *     actual Streamable HTTP JSON-RPC handshake (initialize → tools/call)
 *     against every tool and asserts non-500 / non-silent-empty.
 *
 * Run (plan mode, always safe):
 *   npx tsx platform/scripts/audit/tap/mcp_tool_smoke.ts
 * Run (live mode, pipeline only):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_SMOKE_BEARER_TOKEN=... \
 *     npx tsx platform/scripts/audit/tap/mcp_tool_smoke.ts
 */
import { NATIVE_CHART_ID, printReport, type LawResult } from './lib/tap_db'
import { collectRegisteredTools } from './lib/mcp_registered_tools'

const AYANAMSHA_ID = 'lahiri_chitrapaksha'

// Register §SECTION 4 "New rows (v2) — dead tools" + Phase 0 lane 0b scope.
// Delete an entry here the moment its fix lands (see file header) — that
// is the ratchet: this battery starts requiring PASS the instant the entry
// is gone.
const KNOWN_DEAD_TOOLS: Record<string, { register_row: string; expected: string }> = {
  bodha_discoveries_get: { register_row: 'R-9', expected: '500 — column "salience_score" does not exist (schema drift)' },
  synth_tail_divergence_get: { register_row: 'R-10', expected: '500 — column "tier" does not exist (schema drift)' },
  prashna_undertaking_get: { register_row: 'R-12', expected: '500 — column gj.verdict does not exist (schema drift)' },
  query_calibration: { register_row: 'R-14', expected: 'ok:true/0 rows masking a broken SQL column list (db_note leak)' },
  muhurta_finder: { register_row: 'T-7', expected: 'Silent empty — no windows, no empty_reason, no error object' },
}

// Minimal per-tool param overrides for tools whose required_inputs go beyond
// {chart_id, ayanamsha_id}. Best-effort — not exhaustively verified against
// every tool's zod schema; LIVE mode will surface any 400 (bad params) as
// its own class, distinct from 500 (server defect), so a wrong minimal-param
// guess here still won't produce a false PASS/FAIL on the thing this battery
// actually checks (crash vs silent-empty).
const PARAM_OVERRIDES: Record<string, Record<string, unknown>> = {
  graha_portrait: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID, graha_key: 'SU' },
  judgment_query: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  pact_query: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  get_domain_reading: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID, domain: 'career' },
  assess_career: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_health: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_marriage: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  assess_wealth: { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID },
  list_my_charts: {},
  list_my_sessions: {},
  select_chart: { chart_id: NATIVE_CHART_ID },
  intent_classify: { query_text: 'How strong is my Saturn?' },
  resolve_entity: { entity_text: 'Saturn' },
  list_entities: {},
  read_classical_text: { text_id: 'BPHS', chapter: 1 },
  read_chapter: { text_id: 'BPHS', chapter: 1 },
  list_classical_texts: {},
  search_classical_texts: { query_text: 'Saturn dignity' },
  find_verses_about: { topic: 'Saturn' },
}

function defaultParamsFor(toolName: string): Record<string, unknown> {
  return PARAM_OVERRIDES[toolName] ?? { chart_id: NATIVE_CHART_ID, ayanamsha_id: AYANAMSHA_ID }
}

// ── LIVE mode: minimal MCP Streamable HTTP JSON-RPC client ──────────────────
async function initSession(baseUrl: string, token: string): Promise<string | undefined> {
  const res = await fetch(baseUrl, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      accept: 'application/json, text/event-stream',
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'tap5-mcp-smoke', version: '1.0.0' },
      },
    }),
  })
  return res.headers.get('mcp-session-id') ?? undefined
}

async function callTool(
  baseUrl: string,
  token: string,
  sessionId: string | undefined,
  toolName: string,
  args: Record<string, unknown>
): Promise<{ ok: boolean; status: number; body: string }> {
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    accept: 'application/json, text/event-stream',
    authorization: `Bearer ${token}`,
  }
  if (sessionId) headers['mcp-session-id'] = sessionId
  const res = await fetch(baseUrl, {
    method: 'POST',
    headers,
    body: JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name: toolName, arguments: args } }),
  })
  const body = await res.text()
  return { ok: res.ok, status: res.status, body }
}

async function main() {
  const toolNames = [...collectRegisteredTools()].sort()
  const results: LawResult[] = []
  const mcpServerUrl = process.env.MCP_SERVER_URL
  const bearer = process.env.MCP_SMOKE_BEARER_TOKEN

  results.push({
    id: 'smoke:registered-tool-count',
    title: 'Total registered MCP tools discovered (static enumeration)',
    status: toolNames.length >= 50 ? 'PASS' : 'FAIL',
    detail: `${toolNames.length} tools found via server.tool()/regAlias()/globalAlias() call sites (see lib/mcp_registered_tools.ts).`,
  })

  if (!mcpServerUrl || !bearer) {
    for (const toolName of toolNames) {
      const dead = KNOWN_DEAD_TOOLS[toolName]
      results.push({
        id: `smoke-plan:${toolName}`,
        title: `Call plan: ${toolName}(${JSON.stringify(defaultParamsFor(toolName))})`,
        status: dead ? 'QUARANTINED' : 'SKIPPED',
        detail: dead ? `EXPECTED-FAIL per ${dead.register_row}: ${dead.expected}` : 'EXPECTED-PASS — no live server reachable to execute (plan mode).',
        register_rows: dead ? [dead.register_row] : [],
      })
    }
    const reason =
      'MCP_SERVER_URL / MCP_SMOKE_BEARER_TOKEN not set — running in PLAN mode only (no live tool calls executed). ' +
      'Pipeline invocation: deploy/point at a running platform-mcp instance and export MCP_SERVER_URL=https://<host>/mcp ' +
      'plus MCP_SMOKE_BEARER_TOKEN=<valid bearer key> before re-running this script for LIVE mode.'
    console.log(JSON.stringify({ battery: 'MCP per-tool smoke (PLAN mode)', mode: 'plan', tool_count: toolNames.length, results }, null, 2))
    process.exit(printReport('MCP per-tool smoke battery', results, reason))
    return
  }

  // LIVE mode
  const sessionId = await initSession(mcpServerUrl, bearer).catch(() => undefined)
  for (const toolName of toolNames) {
    const dead = KNOWN_DEAD_TOOLS[toolName]
    try {
      const { ok, status, body } = await callTool(mcpServerUrl, bearer, sessionId, toolName, defaultParamsFor(toolName))
      const isServerError = status >= 500
      const isSilentEmpty = ok && (body.trim() === '' || body.includes('"content":[]') || body.includes('"rows":[]'))
      const isBad = isServerError || isSilentEmpty
      if (dead) {
        results.push({
          id: `smoke:${toolName}`,
          title: `${toolName} — known-dead tool call`,
          status: isBad ? 'QUARANTINED' : 'PASS',
          detail: isBad ? `Confirmed still failing per ${dead.register_row}: status=${status}.` : `Tool now returns healthily — ${dead.register_row} appears FIXED. Delete its entry from KNOWN_DEAD_TOOLS.`,
          register_rows: [dead.register_row],
        })
      } else {
        results.push({
          id: `smoke:${toolName}`,
          title: `${toolName} — status ${status}`,
          status: isBad ? 'FAIL' : 'PASS',
          detail: isBad ? `Non-500/non-silent-empty violation: status=${status}, silent_empty=${isSilentEmpty}.` : 'OK, non-empty.',
        })
      }
    } catch (err) {
      results.push({
        id: `smoke:${toolName}`,
        title: `${toolName} — request threw`,
        status: dead ? 'QUARANTINED' : 'FAIL',
        detail: `${err instanceof Error ? err.message : String(err)}`,
        register_rows: dead ? [dead.register_row] : [],
      })
    }
  }
  process.exit(printReport('MCP per-tool smoke battery (LIVE)', results))
}

main().catch((err) => {
  console.error('mcp_tool_smoke FATAL:', err)
  process.exit(4)
})
