/**
 * canary_probes.ts — daily canary-battery probe logic, ported from
 * evals/r5-w0a-canary/canary_runner.ts (the R5 W0a §14 eight-probe audit).
 *
 * R5.1 C5.2 (CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md): "Canary battery -> scheduled
 * job (daily, feeds system_health; alert on regression)."
 *
 * WHY PORTED RATHER THAN SHELLED OUT: the standalone canary_runner.ts script lives
 * under evals/ at the repo root, which is OUTSIDE the `platform/` Docker build context
 * (.github/workflows/deploy.yml builds amjis-web with `context: ./platform`) and the
 * prod image is a Next.js `standalone` output with no `tsx`/devDependencies (see
 * platform/Dockerfile `runner` stage). A subprocess shell-out to the original script
 * would work in local dev but silently 404/ENOENT in prod. Porting the probe logic
 * into platform/src/lib keeps it inside the bundle the standalone build actually traces.
 *
 * SEMANTIC RE-LABELING (deliberate, not a copy-paste error): the original W0a script's
 * ProbeResult.observed_status values ('FAIL_AS_EXPECTED' / 'HEALED_UNEXPECTEDLY' / ...)
 * encoded a PRE-DEPLOY narrative ("these probes are expected to still be broken because
 * the fix hasn't shipped yet"). C1-C4 have since shipped and deployed (this brief's
 * phase order is C0->C1->C2->C3->C4->C5, and C5 does not start until C1-C4 are prod).
 * That pre-deploy narrative is now stale — for ongoing daily monitoring the correct
 * semantics are the plain post-deploy ones: 'pass' when the underlying defect signature
 * is ABSENT, 'fail' when it is PRESENT, 'error' on transport/HTTP failure. The specific
 * defect-detection heuristics per probe (P1-P8) are unchanged from the original script —
 * only the pass/fail polarity label changed to match "the fix should be live now."
 *
 * Usage: platform/src/app/api/admin/cron/run-canary-battery/route.ts calls
 * runCanaryBattery() and persists the results to the system_health table (migration 366).
 */

import 'server-only'

// Native's birth data (CLAUDE.md §B) — for completeness/parity with the source script;
// not currently used by the 8 chart-scoped probes below, kept for future probe additions
// that need the raw-ephemeris (non-chart-scoped) tools.
export const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
export const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

export interface ChartTag {
  tag: 'N' | 'A'
  id: string
}

export const CANARY_CHARTS: ChartTag[] = [
  { tag: 'N', id: NATIVE_CHART_ID },
  { tag: 'A', id: ABHINANDAN_CHART_ID },
]

// ── MCP JSON-RPC transport ──────────────────────────────────────────────────────

interface McpCallResult {
  ok: boolean
  status: number
  latencyMs: number
  body: unknown
  error?: string
}

async function mcpCall(mcpUrl: string, mcpKey: string, method: string, params: Record<string, unknown>): Promise<McpCallResult> {
  const id = Math.floor(Math.random() * 1_000_000)
  const t0 = performance.now()
  try {
    const res = await fetch(mcpUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        Authorization: `Bearer ${mcpKey}`,
      },
      body: JSON.stringify({ jsonrpc: '2.0', id, method, params }),
      signal: AbortSignal.timeout(30_000),
    })
    const latencyMs = performance.now() - t0
    const text = await res.text()
    // Server responds SSE-framed: "event: message\ndata: {...}\n\n" — strip the framing.
    const dataLine = text.split('\n').find((l) => l.startsWith('data:'))
    const jsonText = dataLine ? dataLine.slice('data:'.length).trim() : text
    let body: unknown
    try {
      body = JSON.parse(jsonText)
    } catch {
      body = { raw: text.slice(0, 500) }
    }
    return { ok: res.ok, status: res.status, latencyMs, body }
  } catch (e) {
    const latencyMs = performance.now() - t0
    return { ok: false, status: 0, latencyMs, body: null, error: e instanceof Error ? e.message : String(e) }
  }
}

interface ToolCallResult {
  tool: string
  httpOk: boolean
  httpStatus: number
  latencyMs: number
  toolIsError: boolean | null
  rawText: string | null
  parsedContent: unknown
  transportError: string | null
}

async function callTool(mcpUrl: string, mcpKey: string, name: string, args: Record<string, unknown>): Promise<ToolCallResult> {
  const r = await mcpCall(mcpUrl, mcpKey, 'tools/call', { name, arguments: args })
  const rpcResult = (r.body as { result?: unknown; error?: unknown } | null) ?? {}
  const result = (rpcResult as { result?: { content?: Array<{ type: string; text?: string }>; isError?: boolean } }).result
  let parsedContent: unknown = null
  let rawText: string | null = null
  if (result?.content?.[0]?.text) {
    rawText = result.content[0].text
    try {
      parsedContent = JSON.parse(rawText)
    } catch {
      parsedContent = null
    }
  }
  return {
    tool: name,
    httpOk: r.ok,
    httpStatus: r.status,
    latencyMs: Math.round(r.latencyMs * 10) / 10,
    toolIsError: result?.isError ?? null,
    rawText,
    parsedContent,
    transportError: r.error ?? null,
  }
}

// ── Probe result shape (persisted to system_health) ─────────────────────────────

export type ProbeStatus = 'pass' | 'fail' | 'error'

export interface ProbeResult {
  probe_id: string
  name: string
  chart_tag: 'N' | 'A'
  chart_id: string
  tool: string
  status: ProbeStatus
  detail: string
  latency_ms: number
}

function statusFromDefect(transportError: string | null, defectPresent: boolean): ProbeStatus {
  if (transportError) return 'error'
  return defectPresent ? 'fail' : 'pass'
}

/**
 * Runs the P1-P8 probe set (from the R5 W0a §14 audit) against both canonical charts.
 * Returns 16 ProbeResult rows (8 probes x 2 charts).
 */
export async function runCanaryBattery(mcpUrl: string, mcpKey: string): Promise<ProbeResult[]> {
  const results: ProbeResult[] = []

  for (const chart of CANARY_CHARTS) {
    // P1 — A1 fact: dasha as-of honored (no pre-birth 1950-era rows for a post-birth as_of_date)
    {
      const r = await callTool(mcpUrl, mcpKey, 'ganita_dashas_get', { chart_id: chart.id, as_of_date: todayIso() })
      const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const looksPreBirth = text.includes('1950')
      results.push({
        probe_id: 'P1', name: 'A1 fact — dasha as-of honored', chart_tag: chart.tag, chart_id: chart.id, tool: 'ganita_dashas_get',
        status: statusFromDefect(r.transportError, looksPreBirth),
        detail: r.transportError ?? `contains_1950=${looksPreBirth}; status=${r.httpStatus}`,
        latency_ms: r.latencyMs,
      })
    }
    // P2 — A2 orient: chart digest responds without tool-level error
    {
      const r = await callTool(mcpUrl, mcpKey, 'bodha_chart_digest_get', { chart_id: chart.id, mode: 'summary' })
      results.push({
        probe_id: 'P2', name: 'A2 orient — chart digest', chart_tag: chart.tag, chart_id: chart.id, tool: 'bodha_chart_digest_get',
        status: statusFromDefect(r.transportError, r.toolIsError === true),
        detail: r.transportError ?? `status=${r.httpStatus}; isError=${r.toolIsError}`,
        latency_ms: r.latencyMs,
      })
    }
    // P3 — A7 substrate: yogas envelope not hollow (verdict/ranking_basis present)
    {
      const r = await callTool(mcpUrl, mcpKey, 'ganita_yogas_get', { chart_id: chart.id, limit: 100 })
      const contentObj = r.parsedContent as { verdict?: unknown; ranking_basis?: unknown } | null
      const hollow = contentObj ? (contentObj.verdict === null && contentObj.ranking_basis === null) : false
      const bytes = r.rawText ? Buffer.byteLength(r.rawText, 'utf8') : 0
      results.push({
        probe_id: 'P3', name: 'A7 substrate — yogas envelope', chart_tag: chart.tag, chart_id: chart.id, tool: 'ganita_yogas_get',
        status: statusFromDefect(r.transportError, hollow),
        detail: r.transportError ?? `bytes=${bytes}; hollow=${hollow}; status=${r.httpStatus}`,
        latency_ms: r.latencyMs,
      })
    }
    // P4 — A3 substrate: ranked signals, no stale provenance-note literal
    {
      const r = await callTool(mcpUrl, mcpKey, 'bodha_signals_get', { chart_id: chart.id, domain: 'career', top_k: 5 })
      const text = r.rawText ?? ''
      const staleNoteClaim = text.includes('100% background') || text.includes('signature_tier_note')
      results.push({
        probe_id: 'P4', name: 'A3 substrate — ranked signals provenance', chart_tag: chart.tag, chart_id: chart.id, tool: 'bodha_signals_get',
        status: statusFromDefect(r.transportError, staleNoteClaim),
        detail: r.transportError ?? `stale_note_present=${staleNoteClaim}; status=${r.httpStatus}`,
        latency_ms: r.latencyMs,
      })
    }
    // P5 — A4 prediction: 12-month outlook, no raw SQL error leakage
    {
      const r = await callTool(mcpUrl, mcpKey, 'phala_outlook_get', { chart_id: chart.id })
      const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const leaksSql = /column ".*" does not exist/i.test(text) || text.includes('leakage_firewall_note')
      results.push({
        probe_id: 'P5', name: 'A4 prediction — 12-month outlook', chart_tag: chart.tag, chart_id: chart.id, tool: 'phala_outlook_get',
        status: statusFromDefect(r.transportError, leaksSql),
        detail: r.transportError ?? `leak_detected=${leaksSql}; status=${r.httpStatus}`,
        latency_ms: r.latencyMs,
      })
    }
    // P6 — dissent organ: synth_tail_divergence_get should be live (not 404)
    {
      const r = await callTool(mcpUrl, mcpKey, 'synth_tail_divergence_get', { chart_id: chart.id })
      const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const is404 = text.includes('404') || r.toolIsError === true
      results.push({
        probe_id: 'P6', name: 'dissent organ — synth_tail_divergence_get', chart_tag: chart.tag, chart_id: chart.id, tool: 'synth_tail_divergence_get',
        status: statusFromDefect(r.transportError, is404),
        detail: r.transportError ?? `looks_404=${is404}; status=${r.httpStatus}`,
        latency_ms: r.latencyMs,
      })
    }
    // P7 — corpus semantic search: ref_vector_search should be live (not 401)
    {
      const r = await callTool(mcpUrl, mcpKey, 'ref_vector_search', { query: 'career strength', chart_id: chart.id })
      const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const is401 = text.includes('401') || r.toolIsError === true
      results.push({
        probe_id: 'P7', name: 'corpus semantic search — ref_vector_search', chart_tag: chart.tag, chart_id: chart.id, tool: 'ref_vector_search',
        status: statusFromDefect(r.transportError, is401),
        detail: r.transportError ?? `looks_401=${is401}; status=${r.httpStatus}`,
        latency_ms: r.latencyMs,
      })
    }
    // P8 — citation lookup: empty results carry empty_reason, never silent-empty
    {
      const r = await callTool(mcpUrl, mcpKey, 'ref_classical_citation_get', { keyword: 'neecha bhanga' })
      const outer = r.parsedContent as { content?: { rows?: unknown[]; empty_reason?: unknown }; rows?: unknown[]; empty_reason?: unknown } | null
      const inner = outer?.content ?? outer
      const silentEmpty = inner ? (Array.isArray(inner.rows) && inner.rows.length === 0 && !inner.empty_reason) : false
      results.push({
        probe_id: 'P8', name: 'citation lookup — honest-empty', chart_tag: chart.tag, chart_id: chart.id, tool: 'ref_classical_citation_get',
        status: statusFromDefect(r.transportError, silentEmpty),
        detail: r.transportError ?? `silent_empty=${silentEmpty}; status=${r.httpStatus}`,
        latency_ms: r.latencyMs,
      })
    }
  }

  return results
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}
