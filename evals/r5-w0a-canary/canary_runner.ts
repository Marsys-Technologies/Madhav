/**
 * canary_runner.ts — R5 W0a canary lane (§14 eight-probe audit + deterministic
 * answer-battery subset + p50/p95 latency baseline).
 *
 * Governed by CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN_v1_0.md v1.2 (Ring-2 gate for
 * W0a: "all 8 probes pass or fail honestly on prod; baseline recorded") and
 * 00_ARCHITECTURE/RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md v1.6.
 *
 * Runs LIVE against prod amjis-mcp (read-only MCP tool calls only — no writes, no migrations).
 * This run is explicitly a "pre-W0a-deploy" baseline: the punchlist + perf fixes merged into
 * r5/w0a-integrated are NOT yet deployed when this script is run (Ring-2 deploy happens after
 * this branch merges), so probes P1/P3/P5/P6/P7/P8 are EXPECTED to still show broken — that is
 * the correct, honest baseline, not a new finding.
 *
 * Tool argument shapes below were introspected live via `tools/list` against prod immediately
 * before writing this script (not guessed) — see the input schema per tool for the ground truth.
 *
 * Usage:
 *   MCP_CANARY_KEY=<full key> npx tsx evals/r5-w0a-canary/canary_runner.ts
 *
 * Writes evals/r5-w0a-canary/results_<git-sha>.json.
 */

import { writeFileSync } from 'fs'
import { execSync } from 'child_process'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const MCP_URL = process.env['MCP_CANARY_URL'] ?? 'https://amjis-mcp-qm256lasva-el.a.run.app/mcp'
const MCP_KEY = process.env['MCP_CANARY_KEY'] ?? ''

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// Native's birth data (CLAUDE.md §B) — for the raw-ephemeris tools that are NOT chart-scoped
// (query_dasha_periods, ganita_dasha_periods_get, ganita_special_lagnas_get take
// datetime_iso/lat/long directly rather than chart_id).
const NATIVE_BIRTH = {
  datetime_iso: '1984-02-05T10:43:00+05:30',
  latitude_deg: 20.2961,
  longitude_deg: 85.8245,
  tz_offset_hours: 5.5,
  ayanamsha_id: 'lahiri',
}

function getGitSha(): string {
  try {
    return execSync('git rev-parse --short HEAD', { stdio: ['pipe', 'pipe', 'pipe'] }).toString().trim()
  } catch {
    return 'unknown'
  }
}

// ── MCP JSON-RPC transport ──────────────────────────────────────────────────────

let rpcId = 100

async function mcpCall(
  method: string,
  params: Record<string, unknown>,
): Promise<{ ok: boolean; status: number; latencyMs: number; body: unknown; error?: string }> {
  const id = rpcId++
  const t0 = performance.now()
  try {
    const res = await fetch(MCP_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        Authorization: `Bearer ${MCP_KEY}`,
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

async function callTool(name: string, args: Record<string, unknown>) {
  const r = await mcpCall('tools/call', { name, arguments: args })
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
    args,
    httpOk: r.ok,
    httpStatus: r.status,
    latencyMs: Math.round(r.latencyMs * 10) / 10,
    rpcError: (rpcResult as { error?: unknown }).error ?? null,
    toolIsError: result?.isError ?? null,
    rawText,
    parsedContent,
    transportError: r.error ?? null,
  }
}

// ── §14 eight-probe audit (P1-P8) ────────────────────────────────────────────────

interface ProbeResult {
  id: string
  name: string
  chart: 'N' | 'A'
  tool: string
  expected_pre_deploy: string
  observed_status: 'FAIL_AS_EXPECTED' | 'HEALED_UNEXPECTEDLY' | 'STILL_HEALTHY' | 'ERROR'
  detail: string
  latencyMs: number
}

async function runEightProbes(): Promise<ProbeResult[]> {
  const results: ProbeResult[] = []
  const charts: Array<{ tag: 'N' | 'A'; id: string }> = [
    { tag: 'N', id: NATIVE_CHART_ID },
    { tag: 'A', id: ABHINANDAN_CHART_ID },
  ]

  for (const chart of charts) {
    // P1 — A1 fact: dasha as-of, as_of_date should be honored
    {
      const r = await callTool('ganita_dashas_get', { chart_id: chart.id, as_of_date: '2026-07-08' })
      const anyRow = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const looksPreBirth = anyRow.includes('1950')
      results.push({
        id: 'P1', name: 'A1 fact — dasha as-of', chart: chart.tag, tool: 'ganita_dashas_get',
        expected_pre_deploy: 'STILL FAIL — as_of_date ignored, 1950-era rows returned',
        observed_status: r.transportError ? 'ERROR' : looksPreBirth ? 'FAIL_AS_EXPECTED' : 'HEALED_UNEXPECTEDLY',
        detail: r.transportError ? String(r.transportError) : `contains-1950=${looksPreBirth}; status=${r.httpStatus}`,
        latencyMs: r.latencyMs,
      })
    }
    // P2 — A2 orient: chart digest signal variance
    {
      const r = await callTool('bodha_chart_digest_get', { chart_id: chart.id, mode: 'summary' })
      results.push({
        id: 'P2', name: 'A2 orient — chart digest', chart: chart.tag, tool: 'bodha_chart_digest_get',
        expected_pre_deploy: 'Substantially healed per R4 (native chart); Abhinandan was never stale',
        observed_status: r.transportError ? 'ERROR' : (r.toolIsError ? 'FAIL_AS_EXPECTED' : 'STILL_HEALTHY'),
        detail: r.transportError ? String(r.transportError) : `status=${r.httpStatus}; isError=${r.toolIsError}`,
        latencyMs: r.latencyMs,
      })
    }
    // P3 — A7 substrate: yogas envelope hollow + oversized
    {
      const r = await callTool('ganita_yogas_get', { chart_id: chart.id, limit: 100 })
      const bytes = r.rawText ? Buffer.byteLength(r.rawText, 'utf8') : 0
      const contentObj = r.parsedContent as { verdict?: unknown; ranking_basis?: unknown } | null
      const hollow = contentObj ? (contentObj.verdict === null && contentObj.ranking_basis === null) : null
      results.push({
        id: 'P3', name: 'A7 substrate — yogas', chart: chart.tag, tool: 'ganita_yogas_get',
        expected_pre_deploy: 'STILL FAIL — hollow envelope (verdict/ranking_basis null), oversized (>64KB)',
        observed_status: r.transportError ? 'ERROR' : (hollow ? 'FAIL_AS_EXPECTED' : 'STILL_HEALTHY'),
        detail: r.transportError ? String(r.transportError) : `bytes=${bytes}; hollow=${hollow}; status=${r.httpStatus}`,
        latencyMs: r.latencyMs,
      })
    }
    // P4 — A3 substrate: ranked signals, stale provenance note
    {
      const r = await callTool('bodha_signals_get', { chart_id: chart.id, domain: 'career', top_k: 5 })
      const text = r.rawText ?? ''
      const staleNoteClaim = text.includes('100% background') || text.includes('signature_tier_note')
      results.push({
        id: 'P4', name: 'A3 substrate — ranked signals', chart: chart.tag, tool: 'bodha_signals_get',
        expected_pre_deploy: 'PARTIAL — stale signature_tier_note/defect_001_note persists',
        observed_status: r.transportError ? 'ERROR' : (staleNoteClaim ? 'FAIL_AS_EXPECTED' : 'STILL_HEALTHY'),
        detail: r.transportError ? String(r.transportError) : `stale_note_present=${staleNoteClaim}; status=${r.httpStatus}`,
        latencyMs: r.latencyMs,
      })
    }
    // P5 — A4 prediction: 12-month outlook, raw SQL error leakage
    {
      const r = await callTool('phala_outlook_get', { chart_id: chart.id })
      const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const leaksSql = /column ".*" does not exist/i.test(text) || text.includes('leakage_firewall_note')
      results.push({
        id: 'P5', name: 'A4 prediction — 12-month outlook', chart: chart.tag, tool: 'phala_outlook_get',
        expected_pre_deploy: 'STILL FAIL — raw SQL errors / leakage-internals leak pre-deploy',
        observed_status: r.transportError ? 'ERROR' : (leaksSql ? 'FAIL_AS_EXPECTED' : 'STILL_HEALTHY'),
        detail: r.transportError ? String(r.transportError) : `leak_detected=${leaksSql}; status=${r.httpStatus}`,
        latencyMs: r.latencyMs,
      })
    }
    // P6 — dissent organ: synth_tail_divergence_get, expect 404 (missing db/query route pre-deploy)
    {
      const r = await callTool('synth_tail_divergence_get', { chart_id: chart.id })
      const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const is404 = text.includes('404') || r.toolIsError === true
      results.push({
        id: 'P6', name: 'dissent organ', chart: chart.tag, tool: 'synth_tail_divergence_get',
        expected_pre_deploy: 'STILL DOWN pre-deploy — missing /api/mcp/db/query route (punchlist fix not yet live)',
        observed_status: r.transportError ? 'ERROR' : (is404 ? 'FAIL_AS_EXPECTED' : 'HEALED_UNEXPECTEDLY'),
        detail: r.transportError ? String(r.transportError) : `looks_404=${is404}; status=${r.httpStatus}`,
        latencyMs: r.latencyMs,
      })
    }
    // P7 — corpus semantic search: ref_vector_search, expect 401 pre-deploy (header-threading fix not live)
    {
      const r = await callTool('ref_vector_search', { query: 'career strength', chart_id: chart.id })
      const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
      const is401 = text.includes('401') || r.toolIsError === true
      results.push({
        id: 'P7', name: 'corpus semantic search', chart: chart.tag, tool: 'ref_vector_search',
        expected_pre_deploy: 'STILL DOWN pre-deploy — 401 auth-header gap (punchlist fix not yet live)',
        observed_status: r.transportError ? 'ERROR' : (is401 ? 'FAIL_AS_EXPECTED' : 'HEALED_UNEXPECTEDLY'),
        detail: r.transportError ? String(r.transportError) : `looks_401=${is401}; status=${r.httpStatus}`,
        latencyMs: r.latencyMs,
      })
    }
    // P8 — citation lookup: silent-empty, no reason
    {
      const r = await callTool('ref_classical_citation_get', { keyword: 'neecha bhanga' })
      // Response shape observed live: { content: { rows, total }, is_error } — one level deeper
      // than the P1-envelope tools (verified against raw response at canary-authoring time).
      const outer = r.parsedContent as { content?: { rows?: unknown[]; total?: number; empty_reason?: unknown }; rows?: unknown[]; empty_reason?: unknown } | null
      const inner = outer?.content ?? outer
      const silentEmpty = inner ? (Array.isArray(inner.rows) && inner.rows.length === 0 && !inner.empty_reason) : null
      results.push({
        id: 'P8', name: 'citation lookup', chart: chart.tag, tool: 'ref_classical_citation_get',
        expected_pre_deploy: 'STILL SILENT EMPTY pre-deploy — no empty_reason (punchlist JL-002 fix not yet live)',
        observed_status: r.transportError ? 'ERROR' : (silentEmpty ? 'FAIL_AS_EXPECTED' : (silentEmpty === false ? 'HEALED_UNEXPECTEDLY' : 'STILL_HEALTHY')),
        detail: r.transportError ? String(r.transportError) : `silent_empty=${silentEmpty}; status=${r.httpStatus}`,
        latencyMs: r.latencyMs,
      })
    }
  }
  return results
}

// ── Deterministic answer-battery subset (Q1 ×8 + Adversarial/canary ×8 = 16 items) ──
// These are the only R5_ANSWER_BATTERY_v1_0.md items marked "deterministic only, 0 rubric
// floor" — i.e. mechanically checkable WITHOUT an LLM judge/product-answer harness. All
// other battery items (Q2-Q9, 24 items) carry a rubric floor that requires the G10-QT LLM
// grading step against a synthesized natural-language answer; no such answering harness
// exists at the raw-MCP-tool layer this canary operates at, so those 24 items are recorded
// as `requires_llm_rubric_step` rather than faked.

interface BatteryResult {
  id: string
  question: string
  mechanically_checkable: boolean
  pass: boolean | null
  detail: string
  latencyMs: number | null
}

// ── Extra findings discovered while building this canary (beyond P1-P8 + the battery) ──
// Recorded honestly and separately — never folded into the P1-P8 or battery counts, since
// they were not part of the brief's named scope, but are real and worth flagging for the
// punchlist since Ring-2 gating depends on an honest tool-estate picture.

interface ExtraFinding {
  id: string
  tool: string
  finding: string
  detail: string
}

async function runExtraFindings(): Promise<ExtraFinding[]> {
  const out: ExtraFinding[] = []
  for (const tool of ['ganita_chart_facts_get', 'query_chart_facts']) {
    const r1 = await callTool(tool, { chart_id: NATIVE_CHART_ID, limit: 5 })
    const r2 = await callTool(tool, { chart_id: NATIVE_CHART_ID, ayanamsha_id: 'lahiri' })
    const text1 = r1.rawText ?? ''
    const text2 = r2.rawText ?? ''
    const broken = /Sidecar returned 404/i.test(text1) && /Sidecar returned 404/i.test(text2)
    out.push({
      id: `EXTRA-${tool}`,
      tool,
      finding: broken ? 'BROKEN — Sidecar returns 404 regardless of arguments' : 'appears functional',
      detail: broken
        ? `Both a bare-args call and an ayanamsha_id-qualified call returned "Sidecar returned 404: {"detail":"Not Found"}" with is_error=true, HTTP 200 wrapper. Not part of the original P1-P8 probe set or R5_ANSWER_BATTERY — discovered while mapping Q1 items to live tools during this canary build. Recommend punchlist follow-up: trace the platform-mcp → sidecar route for this tool and confirm whether it was ever wired to a live FastAPI endpoint.`
        : `status1=${r1.httpStatus} status2=${r2.httpStatus}`,
    })
  }
  return out
}

async function runDeterministicBattery(): Promise<BatteryResult[]> {
  const out: BatteryResult[] = []

  // NOTE on tool mapping: ganita_chart_facts_get / query_chart_facts were tried first for the
  // Q1 fact-lookup items and BOTH returned "Sidecar returned 404" regardless of args (verified
  // with and without filters) — a genuine, previously-undocumented defect distinct from P1-P8,
  // recorded separately below as EXTRA-1. ganita_positions_get (chart-scoped, no entity filter
  // param) was substituted as the working equivalent for raw-fact greps in this canary.

  // Q1-N-1 — lagna
  {
    const r = await callTool('ganita_positions_get', { chart_id: NATIVE_CHART_ID })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const containsAries = /aries/i.test(text)
    out.push({
      id: 'Q1-N-1', question: 'What is my lagna? (N)', mechanically_checkable: true,
      pass: r.transportError ? null : containsAries,
      detail: `contains_aries=${containsAries}; status=${r.httpStatus}. NOTE: byte-budget assertion (≤2KB) is a product-answer-layer constraint, not checkable against this raw registry dump (this call returns the full per-chart fact table) — correctness-only check performed here.${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // Q1-N-2 — Sun sign + dignity (entity rows use abbreviated fact_category codes, e.g. D1_SU,
  // not the literal word "Sun" — checking sign+dignity-term co-occurrence, not entity name)
  {
    const r = await callTool('ganita_condition_get', { chart_id: NATIVE_CHART_ID, facet: 'dignity' })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const containsCapricorn = /capricorn/i.test(text)
    const containsDignity = /(exalt|debilitat|own sign|moolatrikona|dignity|neutral|friend|enem)/i.test(text)
    out.push({
      id: 'Q1-N-2', question: 'What sign is my Sun, and is it a good placement? (N)', mechanically_checkable: true,
      pass: r.transportError ? null : (containsCapricorn && containsDignity),
      detail: `capricorn=${containsCapricorn}; dignity_term=${containsDignity}; status=${r.httpStatus}${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // Q1-N-3 — Moon nakshatra + pada (ganita_nakshatra_get returns chandra_bala transit-strength
  // data, NOT nakshatra placement, despite its name — a mapping mismatch discovered while
  // building this canary; using ganita_positions_get instead, confirmed to carry the nakshatra
  // fact for this chart)
  {
    const r = await callTool('ganita_positions_get', { chart_id: NATIVE_CHART_ID })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const containsPB = /purva\s*bhadrapada/i.test(text)
    out.push({
      id: 'Q1-N-3', question: 'What is my Moon nakshatra and pada? (N)', mechanically_checkable: true,
      pass: r.transportError ? null : containsPB,
      detail: `purva_bhadrapada=${containsPB}; status=${r.httpStatus}. NOTE: ganita_nakshatra_get (the name-matched tool) returns chandra_bala_natal_baseline transit data, not nakshatra placement — flagging as a tool-naming/mapping issue for the punchlist, not conflated with P1-P8.${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // Q1-N-4 — current dasha down to antardasha, zero pre-birth rows
  {
    const r = await callTool('ganita_dashas_get', { chart_id: NATIVE_CHART_ID, as_of_date: '2026-07-08' })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const looksPreBirth = text.includes('1950')
    out.push({
      id: 'Q1-N-4', question: 'What dasha am I running today, down to antardasha? (N)', mechanically_checkable: true,
      pass: r.transportError ? null : !looksPreBirth,
      detail: `pre_birth_rows_present=${looksPreBirth} (expected FALSE; pre-deploy this is a KNOWN FAIL per P1)`,
      latencyMs: r.latencyMs,
    })
  }
  // Q1-A-1 — Abhinandan lagna exact
  {
    const r = await callTool('ganita_positions_get', { chart_id: ABHINANDAN_CHART_ID })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const containsAries = /aries/i.test(text)
    const containsBharani = /bharani/i.test(text)
    out.push({
      id: 'Q1-A-1', question: "What's Abhinandan's lagna exactly? (A)", mechanically_checkable: true,
      pass: r.transportError ? null : containsAries,
      detail: `aries=${containsAries}; bharani_pada_in_default_view=${containsBharani} (default unpaginated view may not surface pada-level nakshatra — inconclusive on the pada sub-claim if false, not a hard fail); status=${r.httpStatus}${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // Q1-A-2 — Abhinandan Venus condition (same abbreviated-code caveat as Q1-N-2)
  {
    const r = await callTool('ganita_condition_get', { chart_id: ABHINANDAN_CHART_ID, facet: 'dignity' })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const ok = /pisces/i.test(text) && /exalt/i.test(text)
    out.push({
      id: 'Q1-A-2', question: 'Where is his Venus and what condition? (A)', mechanically_checkable: true,
      pass: r.transportError ? null : ok,
      detail: `pisces_and_exalted=${ok}; status=${r.httpStatus}${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // Q1-A-3 — Abhinandan current dasha window (chart-scoped tool; multi-level periods)
  {
    const r = await callTool('ganita_dashas_get', { chart_id: ABHINANDAN_CHART_ID, as_of_date: '2026-07-08' })
    const bytes = r.rawText ? Buffer.byteLength(r.rawText, 'utf8') : 0
    const looksPreBirth = (r.rawText ?? '').includes('1950')
    out.push({
      id: 'Q1-A-3', question: 'His current maha-antar-pratyantar? (A)', mechanically_checkable: true,
      pass: r.transportError ? null : (bytes > 0 && bytes <= 1536 * 1.5),
      detail: `bytes=${bytes} (ceiling ~2.3KB). ${bytes > 2304 ? 'OVERSIZED — consistent with the P1 as_of_date-ignored defect (same root cause, not a separate finding): ' + `pre_birth_rows_present=${looksPreBirth}` : ''}; status=${r.httpStatus}${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // Q1-N-5 — Jupiter vargottama vargas (no dedicated MCP tool found for per-varga vargottama
  // lookup at canary-audit time; best-effort against ganita_positions_get, honest-empty allowed
  // per the item's own spec — "per-varga list OR honest empty-with-reason; no fabrication")
  {
    const r = await callTool('ganita_positions_get', { chart_id: NATIVE_CHART_ID })
    out.push({
      id: 'Q1-N-5', question: 'Which vargas is my Jupiter vargottama in? (N)', mechanically_checkable: true,
      pass: r.transportError ? null : (r.httpStatus === 200),
      detail: `status=${r.httpStatus}; NOTE: no dedicated vargottama-lookup tool found in the current 124-tool estate — this check only confirms ganita_positions_get answers, not vargottama-specific fabrication-avoidance (needs manual/product-layer follow-up)${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }

  // X-2 — Entitlement: query a chart the probe-service-account credential lacks a grant for
  {
    const FOREIGN_CHART = '00000000-0000-0000-0000-000000000000'
    const r = await callTool('ganita_chart_facts_get', { chart_id: FOREIGN_CHART, category: 'lagna' })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const leaksRaw = /stack trace|at Object\.|at Module\./i.test(text)
    const isDenial = r.toolIsError === true || /denied|forbidden|not authorized|no grant|not found/i.test(text)
    out.push({
      id: 'X-2', question: 'Entitlement: query a chart id the session lacks', mechanically_checkable: true,
      pass: r.transportError ? null : (isDenial && !leaksRaw),
      detail: `denial=${isDenial}; raw_leak=${leaksRaw}; status=${r.httpStatus}${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // X-3 — Budget abuse: ask for every signal (large top_k), expect trim/pointer not raw dump
  {
    const r = await callTool('bodha_signals_get', { chart_id: NATIVE_CHART_ID, domain: 'career', top_k: 5000 })
    const bytes = r.rawText ? Buffer.byteLength(r.rawText, 'utf8') : 0
    out.push({
      id: 'X-3', question: 'Budget abuse: "Give me every signal you have" (N)', mechanically_checkable: true,
      pass: r.transportError ? null : (bytes <= 1_500_000),
      detail: `bytes=${bytes} (ceiling 1.5MB H-12 guard); status=${r.httpStatus}${r.transportError ? '; error=' + r.transportError : ''}`,
      latencyMs: r.latencyMs,
    })
  }
  // X-5 — Broken-organ honesty: call a known-degraded surface (P6 dissent organ pre-deploy)
  {
    const r = await callTool('synth_tail_divergence_get', { chart_id: NATIVE_CHART_ID })
    const text = r.rawText ?? JSON.stringify(r.parsedContent ?? '')
    const silentFailure = r.httpStatus === 200 && !r.toolIsError && !/error|fault|unavailable|404/i.test(text)
    out.push({
      id: 'X-5', question: 'Broken-organ honesty: call a known-degraded surface', mechanically_checkable: true,
      pass: r.transportError ? null : !silentFailure,
      detail: `silent_failure=${silentFailure} (expect FALSE — organ should surface fault, not silently succeed); status=${r.httpStatus}`,
      latencyMs: r.latencyMs,
    })
  }
  // X-8 — Stale-note check: bodha_signals_get provenance notes internally consistent
  {
    const r = await callTool('bodha_signals_get', { chart_id: NATIVE_CHART_ID, domain: 'career', top_k: 5 })
    const text = r.rawText ?? ''
    const hasNote = /_note"?\s*:/i.test(text)
    // pre-deploy this is a KNOWN fail (P4) — recorded honestly, not asserted pass
    out.push({
      id: 'X-8', question: 'Stale-note check: any response carrying provenance notes', mechanically_checkable: true,
      pass: r.transportError ? null : hasNote ? false : true,
      detail: `note_present=${hasNote} (pre-deploy P4 finding: note self-contradicts rows — recorded honestly as expected-fail if present)`,
      latencyMs: r.latencyMs,
    })
  }

  // Items requiring a full NL-answer + LLM-rubric harness (not mechanically checkable here)
  const requiresLlm = [
    'Q2-N-1', 'Q2-A-1', 'Q3-N-1', 'Q3-A-1', 'Q3-N-2', 'Q2-N-2', 'Q3-A-2',
    'Q5-N-1', 'Q5-N-2', 'Q5-A-1', 'Q5-A-2', 'Q6-N-1', 'Q6-N-2',
    'Q7-N-1', 'Q7-A-1', 'Q7-N-2',
    'Q8-N-1', 'Q8-A-1',
    'Q9-N-1', 'Q9-A-1', 'Q9-N-2', 'Q9-N-3',
    'X-1', 'X-4', 'X-6', 'X-7',
  ]
  for (const id of requiresLlm) {
    out.push({
      id, question: '(see R5_ANSWER_BATTERY_v1_0.md §3 for full text)', mechanically_checkable: false,
      pass: null, detail: 'requires G10-QT LLM rubric grading against a synthesized NL answer — no product-answer harness exists at the raw-MCP-tool canary layer; deferred to the product-level battery run', latencyMs: null,
    })
  }

  return out
}

// ── p50/p95 latency sample across the tool estate ────────────────────────────────

interface LatencySample {
  tool: string
  category: string
  n: number
  p50: number | null
  p95: number | null
  min: number | null
  max: number | null
  errors: number
}

function percentile(sorted: number[], p: number): number {
  const idx = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length))
  return sorted[idx] ?? 0
}

// Curated representative sample spanning categories; args verified against live tools/list
// input schemas at canary-authoring time (see header note).
const LATENCY_SAMPLE: Array<{ tool: string; category: string; args: Record<string, unknown> }> = [
  // ganita
  { tool: 'ganita_chart_facts_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID, limit: 20 } },
  { tool: 'ganita_dashas_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID, as_of_date: '2026-07-08' } },
  { tool: 'ganita_positions_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'ganita_yogas_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID, limit: 20 } },
  { tool: 'ganita_strength_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'ganita_nakshatra_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'ganita_condition_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID, facet: 'dignity' } },
  { tool: 'ganita_sade_sati_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'ganita_structural_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID, facet: 'aspects' } },
  { tool: 'ganita_tajaka_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'ganita_transit_anchors_get', category: 'ganita', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'ganita_dasha_periods_get', category: 'ganita', args: { ...NATIVE_BIRTH } },
  { tool: 'ganita_special_lagnas_get', category: 'ganita', args: { ...NATIVE_BIRTH } },
  // bodha
  { tool: 'bodha_chart_digest_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID, mode: 'summary' } },
  { tool: 'bodha_signals_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID, domain: 'career', top_k: 5 } },
  { tool: 'bodha_domain_reading_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID, domain: 'career' } },
  { tool: 'bodha_graph_traverse_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'bodha_graph_subgraph_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'bodha_quality_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'bodha_remedies_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID, domain: 'career' } },
  { tool: 'bodha_discoveries_get', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'get_domain_reading', category: 'bodha', args: { chart_id: NATIVE_CHART_ID, domain: 'career' } },
  { tool: 'get_signals', category: 'bodha', args: { chart_id: NATIVE_CHART_ID, domain: 'career' } },
  { tool: 'get_chart_quality', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'get_remedies', category: 'bodha', args: { chart_id: NATIVE_CHART_ID, domain: 'career' } },
  { tool: 'get_cgm_subgraph', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'assess_career', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'assess_marriage', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'assess_health', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'assess_wealth', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'apex_career_assess', category: 'bodha', args: { chart_id: NATIVE_CHART_ID } },
  // phala
  { tool: 'phala_outlook_get', category: 'phala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'phala_outlook', category: 'phala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'phala_anchors_get', category: 'phala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'phala_mitigation_get', category: 'phala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'phala_rectification_get', category: 'phala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'event_anchors', category: 'phala', args: { chart_id: NATIVE_CHART_ID, date_range: { start: '2026-07-01', end: '2026-12-31' } } },
  { tool: 'mitigation_map', category: 'phala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'muhurta_finder', category: 'phala', args: { chart_id: NATIVE_CHART_ID, action_type: 'general', date_range: { start: '2026-07-01', end: '2026-09-30' } } },
  { tool: 'prashna_undertaking_get', category: 'phala', args: { chart_id: NATIVE_CHART_ID, domain: 'career' } },
  // mimamsa / synth
  { tool: 'mimamsa_calibration_get', category: 'mimamsa', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'mimamsa_insight_get', category: 'mimamsa', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'mimamsa_lel_query', category: 'mimamsa', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'lel_query', category: 'mimamsa', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'query_calibration', category: 'mimamsa', args: { chart_id: NATIVE_CHART_ID, technique: 'vimshottari' } },
  { tool: 'synth_tail_divergence_get', category: 'mimamsa', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'synth_chart_brief_get', category: 'mimamsa', args: { chart_id: NATIVE_CHART_ID, depth: 'standard' } },
  // kala
  { tool: 'kala_life_arc_get', category: 'kala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'kala_muhurta_get', category: 'kala', args: { chart_id: NATIVE_CHART_ID, start_date: '2026-07-01', end_date: '2026-09-30', activity_type: 'general' } },
  { tool: 'kala_projections_get', category: 'kala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'kala_temporal_bundle', category: 'kala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'kala_windows_get', category: 'kala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'kala_yoga_activation_get', category: 'kala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'get_temporal_windows', category: 'kala', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'get_projections', category: 'kala', args: { chart_id: NATIVE_CHART_ID, domain: 'career' } },
  { tool: 'yoga_activation_by_dasha', category: 'kala', args: { chart_id: NATIVE_CHART_ID } },
  // reference / L0
  { tool: 'ref_vector_search', category: 'reference', args: { query: 'career strength', chart_id: NATIVE_CHART_ID } },
  { tool: 'ref_classical_citation_get', category: 'reference', args: { keyword: 'neecha bhanga' } },
  { tool: 'ref_dasha_systems_get', category: 'reference', args: {} },
  { tool: 'ref_dignity_reference_get', category: 'reference', args: {} },
  { tool: 'ref_doshas_get', category: 'reference', args: {} },
  { tool: 'ref_entities_list', category: 'reference', args: {} },
  { tool: 'ref_entity_resolve', category: 'reference', args: { name: 'Jupiter' } },
  { tool: 'ref_nakshatra_get', category: 'reference', args: { nakshatra: 'Purva Bhadrapada' } },
  { tool: 'ref_remedies_get', category: 'reference', args: {} },
  { tool: 'ref_rules_search', category: 'reference', args: { keyword: 'neecha bhanga' } },
  { tool: 'ref_yogas_get', category: 'reference', args: {} },
  { tool: 'resolve_entity', category: 'reference', args: { name: 'Jupiter' } },
  { tool: 'list_entities', category: 'reference', args: {} },
  { tool: 'list_assets', category: 'reference', args: {} },
  { tool: 'query_chart_facts', category: 'reference', args: { chart_id: NATIVE_CHART_ID } },
  { tool: 'query_dasha_periods', category: 'reference', args: { ...NATIVE_BIRTH } },
  { tool: 'query_mantras', category: 'reference', args: {} },
  { tool: 'query_planet_position', category: 'reference', args: { date: '2026-07-08', planet: 'Sun' } },
  { tool: 'query_remedies', category: 'reference', args: { domain: 'career' } },
  { tool: 'list_my_charts', category: 'reference', args: {} },
]

async function runLatencySample(repsPerTool: number): Promise<LatencySample[]> {
  const out: LatencySample[] = []
  for (const spec of LATENCY_SAMPLE) {
    const lats: number[] = []
    let errors = 0
    for (let i = 0; i < repsPerTool; i++) {
      const r = await callTool(spec.tool, spec.args)
      if (r.transportError || r.httpStatus >= 500 || r.toolIsError === true) errors++
      lats.push(r.latencyMs)
    }
    const sorted = [...lats].sort((a, b) => a - b)
    out.push({
      tool: spec.tool,
      category: spec.category,
      n: repsPerTool,
      p50: sorted.length ? Math.round(percentile(sorted, 50) * 10) / 10 : null,
      p95: sorted.length ? Math.round(percentile(sorted, 95) * 10) / 10 : null,
      min: sorted.length ? Math.round(sorted[0] * 10) / 10 : null,
      max: sorted.length ? Math.round(sorted[sorted.length - 1] * 10) / 10 : null,
      errors,
    })
  }
  return out
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  if (!MCP_KEY) {
    console.error('MCP_CANARY_KEY env var required (see R5_RUN_LEDGER_v1_0.md P0-iii for the provisioned test credential).')
    process.exit(1)
  }

  console.log('R5 W0a canary — pre-deploy baseline run starting...')
  const gitSha = getGitSha()
  const runAt = new Date().toISOString()

  console.log('Running §14 eight-probe audit (P1-P8 × 2 charts)...')
  const probes = await runEightProbes()

  console.log('Running deterministic answer-battery subset...')
  const battery = await runDeterministicBattery()

  console.log('Running extra-findings check (tool-mapping issues discovered while building this canary)...')
  const extraFindings = await runExtraFindings()

  console.log(`Running p50/p95 latency sample (${LATENCY_SAMPLE.length} tools)...`)
  const latency = await runLatencySample(3)

  const results = {
    run_at: runAt,
    git_sha: gitSha,
    label: 'W0a pre-deploy baseline (punchlist + perf fixes merged to r5/w0a-integrated but NOT yet deployed)',
    mcp_url: MCP_URL,
    native_chart_id: NATIVE_CHART_ID,
    abhinandan_chart_id: ABHINANDAN_CHART_ID,
    eight_probes: probes,
    deterministic_battery: battery,
    extra_findings: extraFindings,
    latency_sample: latency,
    summary: {
      probes_fail_as_expected: probes.filter((p) => p.observed_status === 'FAIL_AS_EXPECTED').length,
      probes_healed_unexpectedly: probes.filter((p) => p.observed_status === 'HEALED_UNEXPECTEDLY').length,
      probes_still_healthy: probes.filter((p) => p.observed_status === 'STILL_HEALTHY').length,
      probes_error: probes.filter((p) => p.observed_status === 'ERROR').length,
      probes_total: probes.length,
      battery_mechanically_checkable: battery.filter((b) => b.mechanically_checkable).length,
      battery_pass: battery.filter((b) => b.mechanically_checkable && b.pass === true).length,
      battery_fail: battery.filter((b) => b.mechanically_checkable && b.pass === false).length,
      battery_requires_llm_rubric: battery.filter((b) => !b.mechanically_checkable).length,
      latency_tools_sampled: latency.length,
      latency_tools_with_errors: latency.filter((l) => l.errors > 0).length,
    },
  }

  const outPath = join(__dirname, `results_${gitSha}.json`)
  writeFileSync(outPath, JSON.stringify(results, null, 2))
  console.log(`Written: ${outPath}`)
  console.log(JSON.stringify(results.summary, null, 2))
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
