#!/usr/bin/env tsx
/**
 * gochara/smoke_probe.ts — MR-35: Gochara serving outage detection smoke probe.
 *
 * CONTEXT: All three gochara tools were hard-down for 3+ hours (~15:47 IST) and
 * nothing alerted. Discovery was manual. UTKARṢA's "E2E probe" was a psycopg DB
 * query — it never called the deployed product. This probe closes the monitoring
 * gap permanently.
 *
 * WHAT THIS PROBE CHECKS:
 *   - gochara_forecast_get       × 2 charts (primary + cross-check)
 *   - gochara_activation_get     × 2 charts
 *   - gochara_election_avoidance_get × 2 charts
 *   - kala_now_get               × 1 chart (baseline: L3 serving health)
 *   - judgment_query             × 1 chart (baseline: verdict pipeline health)
 *
 * PASS CRITERIA (per call):
 *   - HTTP status < 500 (no server error)
 *   - No transport timeout (30s per call)
 *   - No `error: true` in the JSON-RPC response envelope
 *   - For gochara tools: backing_data_reachable must NOT be false
 *     (the exact symptom of the outage: tools returned backing_data_reachable=false
 *     rather than crashing, so a naive HTTP-200 pass would have masked the outage)
 *
 * CALLING CONVENTION: follows the exact `_mcp_client.ts` / `ElevMcpClient` pattern
 * established by `platform/scripts/census/elev_gates/` (the authoritative MCP calling
 * convention for this repo). Self-contained for scheduling reliability — no imports
 * from the elev_gates directory (same cross-manifest-isolation reason documented in
 * `elev_gates/_mcp_client.ts`'s header).
 *
 * TWO MODES:
 *   PLAN mode (MCP_SERVER_URL not set):
 *     Prints the probe plan and exits 0. Never a false pass — exit 0 is explicit
 *     about being plan-only. Safe to run anywhere, no credentials needed.
 *   LIVE mode (MCP_SERVER_URL set):
 *     Calls the deployed product. Exit 0 = all checks pass. Exit 1 = at least one
 *     check failed (with which tool and chart in the output).
 *
 * ENVIRONMENT:
 *   MCP_SERVER_URL  — base URL of the deployed MCP endpoint (e.g. https://host/mcp)
 *   MCP_BEARER      — Bearer token (optional if URL carries ?api_key=)
 *   GOCHARA_PROBE_TIMEOUT_MS — per-call timeout in ms (default: 30000)
 *
 * MANUAL RUN (from platform/):
 *   npx tsx scripts/gochara/smoke_probe.ts
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> npx tsx scripts/gochara/smoke_probe.ts
 *
 * TDD NOTE: this file starts with ALWAYS_FAIL_MODE = true (skeleton / commit 1).
 * Commit 2 sets ALWAYS_FAIL_MODE = false and wires the real probe logic.
 */

// ── TDD skeleton: hardcoded always-fail path ──────────────────────────────────
// This exists to prove the failure-detection machinery works before the real
// probe is wired. Remove / set false in commit 2.
const ALWAYS_FAIL_MODE = true

// ── Constants ─────────────────────────────────────────────────────────────────

/** The canonical Abhisek Mohanty chart — primary test fixture. */
const PRIMARY_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** Abhinandan Mohanty — cross-check chart used by W1 and the gochara build. */
const CROSS_CHECK_CHART_ID = 'cb73cd3d-9eba-4220-9902-0de91566e980'

const TOOL_TIMEOUT_MS = Number(process.env['GOCHARA_PROBE_TIMEOUT_MS'] ?? '30000')

// Date windows: probe a 90-day window centred ~today so there are plausibly
// some rows for a real chart regardless of when the probe runs.
function probeWindow(): { start: string; end: string } {
  const now = new Date()
  const start = new Date(now)
  start.setDate(start.getDate() - 30)
  const end = new Date(now)
  end.setDate(end.getDate() + 60)
  const fmt = (d: Date) => d.toISOString().split('T')[0]!
  return { start: fmt(start), end: fmt(end) }
}

// ── MCP client (self-contained, mirrors elev_gates/_mcp_client.ts) ────────────

type McpCallOutcome = {
  ok: boolean
  status: number
  body: string
  json?: unknown
  timed_out: boolean
  elapsed_ms: number
  error?: string
}

function resolveMcpTarget(): { baseUrl: string; bearer?: string } | null {
  const baseUrl = process.env['MCP_SERVER_URL']
  if (!baseUrl) return null
  const bearer = process.env['MCP_BEARER'] || process.env['MCP_SMOKE_BEARER_TOKEN'] || undefined
  return { baseUrl, bearer }
}

async function mcpCall(
  baseUrl: string,
  bearer: string | undefined,
  toolName: string,
  args: Record<string, unknown>,
  timeoutMs: number,
): Promise<McpCallOutcome> {
  const started = Date.now()
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    accept: 'application/json, text/event-stream',
  }
  if (bearer) headers['authorization'] = `Bearer ${bearer}`

  try {
    const res = await fetch(baseUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/call',
        params: { name: toolName, arguments: args },
      }),
      signal: AbortSignal.timeout(timeoutMs),
    })
    const text = await res.text()
    let json: unknown
    try {
      const dataLine = text.split('\n').find((l) => l.startsWith('data:'))
      const raw = dataLine ? dataLine.slice('data:'.length).trim() : text
      json = raw ? JSON.parse(raw) : undefined
    } catch {
      json = undefined
    }
    return { ok: res.ok, status: res.status, body: text, json, timed_out: false, elapsed_ms: Date.now() - started }
  } catch (err) {
    const isAbort = err instanceof Error && (err.name === 'AbortError' || err.name === 'TimeoutError')
    return {
      ok: false,
      status: 0,
      body: '',
      timed_out: isAbort,
      elapsed_ms: Date.now() - started,
      error: err instanceof Error ? err.message : String(err),
    }
  }
}

/** Unwraps the MCP envelope and returns the tool payload + isToolError flag.
 *  Mirrors `elev_gates/_mcp_client.ts`'s `unwrapToolPayload`. */
function unwrapPayload(outcome: McpCallOutcome): { payload: unknown; isToolError: boolean } {
  const envelope = (outcome.json as { result?: unknown; error?: unknown } | undefined) ?? {}
  const result = (
    envelope as {
      result?: {
        isError?: boolean
        content?: Array<{ text?: string }>
        structuredContent?: { object?: unknown }
      }
    }
  ).result
  const isToolError = Boolean(result?.isError) || Boolean((envelope as { error?: unknown }).error)
  let payload: unknown = envelope
  if (result?.structuredContent && typeof result.structuredContent === 'object' && 'object' in result.structuredContent) {
    payload = (result.structuredContent as { object: unknown }).object
  } else if (Array.isArray(result?.content) && result.content[0]?.text) {
    try {
      payload = JSON.parse(result.content[0].text as string)
    } catch {
      payload = result.content[0].text
    }
  }
  return { payload, isToolError }
}

// ── Probe result types ────────────────────────────────────────────────────────

type ProbeStatus = 'PASS' | 'FAIL' | 'SKIPPED'

type ProbeResult = {
  id: string
  tool: string
  chart_id: string
  status: ProbeStatus
  detail: string
  elapsed_ms?: number
}

// ── Individual probe checks ───────────────────────────────────────────────────

/**
 * Checks whether a gochara tool response indicates a real outage.
 *
 * The 2026-08 outage pattern: HTTP 200, no JSON-RPC error, but
 * `backing_data_reachable: false` in the payload. A naive HTTP-200 check
 * would pass while the tool is completely non-functional. This is the
 * discriminating check MR-35 exists to add.
 */
function gocharaOutageCheck(payload: Record<string, unknown>): string | null {
  // Explicit backing_data_reachable: false = the outage symptom
  if (payload['backing_data_reachable'] === false) {
    return `backing_data_reachable=false — tool is up but has no DB access (this was the outage symptom)`
  }
  // A not_covered refusal is legitimate (domain not swept for this chart) — not an outage
  if (payload['status'] === 'not_covered') {
    return null // PASS — honest coverage disclosure, not an error
  }
  return null // PASS
}

async function probeGocharaTool(
  baseUrl: string,
  bearer: string | undefined,
  toolName: string,
  chartId: string,
  chartLabel: string,
  extraArgs: Record<string, unknown>,
): Promise<ProbeResult> {
  const id = `gochara:${toolName}:${chartLabel}`
  const args = { chart_id: chartId, ...extraArgs }

  const outcome = await mcpCall(baseUrl, bearer, toolName, args, TOOL_TIMEOUT_MS)

  if (outcome.timed_out) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `TIMEOUT after ${TOOL_TIMEOUT_MS}ms — tool hung (outage class: server unresponsive)`,
    }
  }
  if (outcome.status >= 500) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `HTTP ${outcome.status} — server error. body(300)=${outcome.body.slice(0, 300)}`,
    }
  }
  if (outcome.status === 0) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `Transport error before response: ${outcome.error ?? 'unknown'}`,
    }
  }

  const { payload, isToolError } = unwrapPayload(outcome)
  if (isToolError) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `Tool-level error (isError=true in MCP envelope): ${JSON.stringify(payload).slice(0, 400)}`,
    }
  }

  if (typeof payload === 'object' && payload !== null) {
    const p = payload as Record<string, unknown>
    const outageReason = gocharaOutageCheck(p)
    if (outageReason) {
      return {
        id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
        detail: `OUTAGE DETECTED: ${outageReason}`,
      }
    }
  }

  return {
    id, tool: toolName, chart_id: chartId, status: 'PASS', elapsed_ms: outcome.elapsed_ms,
    detail: `HTTP ${outcome.status}, non-error payload, backing_data_reachable check passed. elapsed_ms=${outcome.elapsed_ms}`,
  }
}

async function probeBaselineTool(
  baseUrl: string,
  bearer: string | undefined,
  toolName: string,
  chartId: string,
  args: Record<string, unknown>,
  label: string,
): Promise<ProbeResult> {
  const id = `baseline:${toolName}`
  const outcome = await mcpCall(baseUrl, bearer, toolName, args, TOOL_TIMEOUT_MS)

  if (outcome.timed_out) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `TIMEOUT after ${TOOL_TIMEOUT_MS}ms — ${label}`,
    }
  }
  if (outcome.status >= 500) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `HTTP ${outcome.status} — ${label}. body(300)=${outcome.body.slice(0, 300)}`,
    }
  }
  if (outcome.status === 0) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `Transport error: ${outcome.error ?? 'unknown'} — ${label}`,
    }
  }
  const { isToolError, payload } = unwrapPayload(outcome)
  if (isToolError) {
    return {
      id, tool: toolName, chart_id: chartId, status: 'FAIL', elapsed_ms: outcome.elapsed_ms,
      detail: `Tool-level error — ${label}: ${JSON.stringify(payload).slice(0, 300)}`,
    }
  }
  return {
    id, tool: toolName, chart_id: chartId, status: 'PASS', elapsed_ms: outcome.elapsed_ms,
    detail: `HTTP ${outcome.status} — ${label} baseline healthy`,
  }
}

// ── Probe plan (PLAN mode) ────────────────────────────────────────────────────

function printPlanAndExit(): never {
  const window = probeWindow()
  const plan = [
    // ── gochara tools × 2 charts ──
    { tool: 'gochara_forecast_get',           chart: PRIMARY_CHART_ID,      label: 'primary',      args: { date_range: window } },
    { tool: 'gochara_forecast_get',           chart: CROSS_CHECK_CHART_ID,  label: 'cross-check',  args: { date_range: window } },
    { tool: 'gochara_activation_get',         chart: PRIMARY_CHART_ID,      label: 'primary',      args: {} },
    { tool: 'gochara_activation_get',         chart: CROSS_CHECK_CHART_ID,  label: 'cross-check',  args: {} },
    { tool: 'gochara_election_avoidance_get', chart: PRIMARY_CHART_ID,      label: 'primary',      args: { date_range: window } },
    { tool: 'gochara_election_avoidance_get', chart: CROSS_CHECK_CHART_ID,  label: 'cross-check',  args: { date_range: window } },
    // ── baseline tools ──
    { tool: 'kala_now_get',    chart: PRIMARY_CHART_ID, label: 'primary', args: { ayanamsha_id: 'lahiri_chitrapaksha' } },
    { tool: 'judgment_query',  chart: PRIMARY_CHART_ID, label: 'primary', args: { domain: 'career', ayanamsha_id: 'lahiri_chitrapaksha' } },
  ]

  console.log('[gochara/smoke_probe] PLAN MODE — MCP_SERVER_URL not set. No live calls. Exit 0.')
  console.log('[gochara/smoke_probe] Probe plan:')
  for (const p of plan) {
    console.log(`  ${p.tool}(chart_id=${p.chart}, ...${JSON.stringify(p.args)})`)
  }
  console.log('[gochara/smoke_probe] Set MCP_SERVER_URL (and optionally MCP_BEARER) to run LIVE.')
  process.exit(0)
}

// ── Report ────────────────────────────────────────────────────────────────────

function printReport(results: ProbeResult[]): void {
  const pass = results.filter((r) => r.status === 'PASS').length
  const fail = results.filter((r) => r.status === 'FAIL').length
  const skipped = results.filter((r) => r.status === 'SKIPPED').length

  console.log(JSON.stringify({
    battery: 'gochara_smoke_probe (MR-35)',
    generated_at: new Date().toISOString(),
    summary: { pass, fail, skipped, total: results.length },
    results,
  }, null, 2))

  console.error(`\n[gochara/smoke_probe] PASS=${pass} FAIL=${fail} SKIPPED=${skipped}`)

  if (fail > 0) {
    console.error(`[gochara/smoke_probe] FAILING CHECKS:`)
    for (const r of results.filter((x) => x.status === 'FAIL')) {
      console.error(`  FAIL  ${r.id}: ${r.detail}`)
    }
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  // TDD skeleton: always-fail path to prove detection works.
  // COMMIT 2 removes this block and wires the real probe.
  if (ALWAYS_FAIL_MODE) {
    const syntheticResult: ProbeResult = {
      id: 'tdd-skeleton:always-fail',
      tool: 'SKELETON',
      chart_id: PRIMARY_CHART_ID,
      status: 'FAIL',
      detail: 'TDD skeleton: ALWAYS_FAIL_MODE=true. This proves the probe exit-1 path works. Commit 2 wires real logic.',
    }
    printReport([syntheticResult])
    process.exit(1)
  }

  const target = resolveMcpTarget()
  if (!target) {
    printPlanAndExit()
  }

  const { baseUrl, bearer } = target
  const window = probeWindow()
  const results: ProbeResult[] = []

  // ── Gochara forecast × 2 charts ──
  results.push(await probeGocharaTool(baseUrl, bearer, 'gochara_forecast_get', PRIMARY_CHART_ID, 'primary',
    { date_range: window }))
  results.push(await probeGocharaTool(baseUrl, bearer, 'gochara_forecast_get', CROSS_CHECK_CHART_ID, 'cross-check',
    { date_range: window }))

  // ── Gochara activation × 2 charts ──
  results.push(await probeGocharaTool(baseUrl, bearer, 'gochara_activation_get', PRIMARY_CHART_ID, 'primary', {}))
  results.push(await probeGocharaTool(baseUrl, bearer, 'gochara_activation_get', CROSS_CHECK_CHART_ID, 'cross-check', {}))

  // ── Gochara election avoidance × 2 charts ──
  results.push(await probeGocharaTool(baseUrl, bearer, 'gochara_election_avoidance_get', PRIMARY_CHART_ID, 'primary',
    { date_range: window }))
  results.push(await probeGocharaTool(baseUrl, bearer, 'gochara_election_avoidance_get', CROSS_CHECK_CHART_ID, 'cross-check',
    { date_range: window }))

  // ── Baseline: kala_now_get (L3 serving health) ──
  results.push(await probeBaselineTool(baseUrl, bearer, 'kala_now_get', PRIMARY_CHART_ID,
    { chart_id: PRIMARY_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha' },
    'L3 Kāla baseline'))

  // ── Baseline: judgment_query (verdict pipeline health) ──
  results.push(await probeBaselineTool(baseUrl, bearer, 'judgment_query', PRIMARY_CHART_ID,
    { chart_id: PRIMARY_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', domain: 'career' },
    'verdict pipeline baseline'))

  printReport(results)
  const hasFail = results.some((r) => r.status === 'FAIL')
  process.exit(hasFail ? 1 : 0)
}

main().catch((err) => {
  console.error('[gochara/smoke_probe] FATAL:', err)
  process.exit(1)
})
