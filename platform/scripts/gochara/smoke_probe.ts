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
 *   - HTTP 2xx, no transport timeout (30s per call)
 *   - Matching JSON-RPC success with a non-empty tool payload
 *   - For gochara tools: provenance_envelope.backing_data_reachable is true
 *   - Coverage refusals and withheld generations are reported separately
 *
 * CALLING CONVENTION: a self-contained stateless JSON-RPC request to the MCP endpoint.
 * Accepts JSON and complete SSE responses.
 *
 * TWO MODES:
 *   PLAN mode (MCP_SERVER_URL not set):
 *     Prints the probe plan and exits 0. Never a false pass — exit 0 is explicit
 *     about being plan-only. Safe to run anywhere, no credentials needed.
 *   LIVE mode (MCP_SERVER_URL set):
 *     Calls the deployed product. Exit 0 = no failed checks, with skipped outcomes
 *     counted separately. Exit 1 = at least one check failed.
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
 * TDD NOTE: commit 1 started with ALWAYS_FAIL_MODE = true to prove exit-1 detection
 * works before real logic was wired. ALWAYS_FAIL_MODE is now false (commit 2) —
 * the real probe calls the deployed product.
 */

// ── TDD skeleton: hardcoded always-fail path ──────────────────────────────────
// Was true in commit 1 to prove the failure-detection path works before real
// logic was wired. Now false — real probe is live (commit 2).
const ALWAYS_FAIL_MODE = false

// ── Constants ─────────────────────────────────────────────────────────────────

/** The canonical native chart — primary test fixture. */
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

// ── MCP client ──────────────────────────────────────────────────────────────

type CallFailure = 'http_failure' | 'timeout' | 'transport_error' | 'invalid_rpc'
  | 'rpc_error' | 'tool_error' | 'missing_payload' | 'judgment_error'

type McpCallOutcome = { status: number; elapsed_ms: number } & (
  | { ok: true; payload: Record<string, unknown> }
  | { ok: false; reason: CallFailure }
)

function resolveMcpTarget(): { baseUrl: string; bearer?: string } | null {
  const baseUrl = process.env['MCP_SERVER_URL']
  if (!baseUrl) return null
  const bearer = process.env['MCP_BEARER'] || process.env['MCP_SMOKE_BEARER_TOKEN'] || undefined
  return { baseUrl, bearer }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function parseRecord(text: string): Record<string, unknown> | null {
  try {
    const value: unknown = JSON.parse(text)
    return isRecord(value) ? value : null
  } catch {
    return null
  }
}

function readRpcReply(text: string, mediaType: string | undefined, requestId: number): Record<string, unknown> | null {
  if (mediaType === 'application/json') {
    const reply = parseRecord(text)
    return reply?.jsonrpc === '2.0' && reply.id === requestId ? reply : null
  }
  if (mediaType !== 'text/event-stream') return null

  // SSE joins every data line in one event. Progress and unrelated replies can
  // precede the final response. A duplicate matching reply is ambiguous.
  const completeEvents = text.replace(/\r\n?/g, '\n').split('\n\n')
  completeEvents.pop() // A stream ending without a blank line cannot dispatch its trailing event.
  let reply: Record<string, unknown> | null = null
  for (const event of completeEvents) {
    const data = event.split('\n').filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).replace(/^ /, ''))
    if (data.length === 0) continue
    const message = parseRecord(data.join('\n'))
    if (message?.jsonrpc !== '2.0') return null
    if (message.id !== requestId) continue
    if (reply !== null) return null
    reply = message
  }
  return reply
}

function readToolPayload(result: Record<string, unknown>): Record<string, unknown> | null {
  if ('structuredContent' in result) {
    const structured = result.structuredContent
    if (!isRecord(structured)) return null
    const payload = 'object' in structured ? structured.object : structured
    return isRecord(payload) && Object.keys(payload).length > 0 ? payload : null
  }
  const content = result.content
  if (!Array.isArray(content) || content.length !== 1) return null
  const [item] = content
  if (!isRecord(item) || item.type !== 'text' || typeof item.text !== 'string') return null
  const payload = parseRecord(item.text)
  return payload && Object.keys(payload).length > 0 ? payload : null
}

async function mcpCall(
  baseUrl: string,
  bearer: string | undefined,
  toolName: string,
  args: Record<string, unknown>,
  timeoutMs: number,
): Promise<McpCallOutcome> {
  const started = Date.now()
  const requestId = 1
  let status = 0
  const fail = (reason: CallFailure): McpCallOutcome => ({
    ok: false, reason, status, elapsed_ms: Date.now() - started,
  })
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
        id: requestId,
        method: 'tools/call',
        params: { name: toolName, arguments: args },
      }),
      signal: AbortSignal.timeout(timeoutMs),
    })
    status = res.status
    if (!res.ok) return fail('http_failure')

    const mediaType = res.headers.get('content-type')?.split(';', 1)[0]?.trim().toLowerCase()
    const reply = readRpcReply(await res.text(), mediaType, requestId)
    if (!reply) return fail('invalid_rpc')
    if ('error' in reply) {
      const error = reply.error
      const validError = !('result' in reply) && isRecord(error)
        && Number.isInteger(error.code) && typeof error.message === 'string'
      return fail(validError ? 'rpc_error' : 'invalid_rpc')
    }
    if (!isRecord(reply.result)) return fail('invalid_rpc')
    if (reply.result.isError === true) return fail('tool_error')
    if ('isError' in reply.result && reply.result.isError !== false) return fail('invalid_rpc')

    const payload = readToolPayload(reply.result)
    if (!payload) return fail('missing_payload')
    if (payload.ok === false || payload.error === true) return fail('tool_error')
    // The judgment bridge retains registrar errors in its retrieval content while
    // discarding the capability's is_error flag. Inspect only that own content.
    if (toolName === 'judgment_query' && isRecord(payload.content) && typeof payload.content.error === 'string') {
      return fail('judgment_error')
    }
    return { ok: true, status, payload, elapsed_ms: Date.now() - started }
  } catch (err) {
    const timedOut = err instanceof Error && (err.name === 'AbortError' || err.name === 'TimeoutError')
    return fail(timedOut ? 'timeout' : 'transport_error')
  }
}

// ── Individual probe checks ──────────────────────────────────────────────────

type ProbeStatus = 'PASS' | 'FAIL' | 'SKIPPED'

type ProbeResult = {
  id: string
  tool: string
  status: ProbeStatus
  detail: string
  http_status?: number
  elapsed_ms?: number
}

function gocharaVerdict(
  payload: Record<string, unknown>, tool: string, chartId: string,
): Pick<ProbeResult, 'status' | 'detail'> {
  const provenance = payload.provenance_envelope
  if (!isRecord(provenance) || provenance.source !== tool || provenance.chart_id !== chartId) {
    return { status: 'FAIL', detail: 'missing_gochara_evidence' }
  }
  if (provenance.backing_data_reachable === false) {
    return { status: 'FAIL', detail: 'backing_data_unreachable' }
  }
  if (provenance.backing_data_reachable !== true || !Array.isArray(payload.windows) || !isRecord(payload.coverage)) {
    return { status: 'FAIL', detail: 'missing_gochara_evidence' }
  }
  if (payload.invalid_domain != null) return { status: 'FAIL', detail: 'invalid_domain' }
  if (payload.not_covered != null) {
    const refusal = payload.not_covered
    if (!isRecord(refusal) || typeof refusal.domain !== 'string' || !isRecord(refusal.cross_pointer)
      || typeof refusal.cross_pointer.instrument !== 'string' || payload.windows.length !== 0) {
      return { status: 'FAIL', detail: 'invalid_coverage_refusal' }
    }
    return { status: 'SKIPPED', detail: 'not_covered' }
  }
  if (payload.coverage.withheld_reason) {
    return { status: 'SKIPPED', detail: 'generation_withheld' }
  }
  if (payload.coverage.status === 'unpublished') {
    return { status: 'SKIPPED', detail: 'generation_unpublished' }
  }
  return { status: 'PASS', detail: 'backing_data_reachable' }
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
  const outcome = await mcpCall(baseUrl, bearer, toolName, { chart_id: chartId, ...extraArgs }, TOOL_TIMEOUT_MS)
  const verdict = outcome.ok ? gocharaVerdict(outcome.payload, toolName, chartId)
    : { status: 'FAIL' as const, detail: outcome.reason }
  return { id, tool: toolName, http_status: outcome.status, elapsed_ms: outcome.elapsed_ms, ...verdict }
}

async function probeBaselineTool(
  baseUrl: string,
  bearer: string | undefined,
  toolName: string,
  args: Record<string, unknown>,
): Promise<ProbeResult> {
  const outcome = await mcpCall(baseUrl, bearer, toolName, args, TOOL_TIMEOUT_MS)
  return {
    id: `baseline:${toolName}`, tool: toolName, status: outcome.ok ? 'PASS' : 'FAIL',
    detail: outcome.ok ? 'baseline_response' : outcome.reason,
    http_status: outcome.status, elapsed_ms: outcome.elapsed_ms,
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
    console.log(`  ${p.tool}(chart=${p.label}, ...${JSON.stringify(p.args)})`)
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
  // TDD skeleton (commit 1): always-fail path to prove detection works.
  // ALWAYS_FAIL_MODE is now false; this block is inert dead code kept as
  // a documented test anchor. Safe to delete after audit.
  if (ALWAYS_FAIL_MODE) {
    const syntheticResult: ProbeResult = {
      id: 'tdd-skeleton:always-fail',
      tool: 'SKELETON',
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
  results.push(await probeBaselineTool(baseUrl, bearer, 'kala_now_get',
    { chart_id: PRIMARY_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha' }))

  // ── Baseline: judgment_query (verdict pipeline health) ──
  results.push(await probeBaselineTool(baseUrl, bearer, 'judgment_query',
    { chart_id: PRIMARY_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', domain: 'career' }))

  printReport(results)
  const hasFail = results.some((r) => r.status === 'FAIL')
  process.exit(hasFail ? 1 : 0)
}

main().catch(() => {
  console.error('[gochara/smoke_probe] FATAL: unexpected_probe_failure')
  process.exit(1)
})
