#!/usr/bin/env tsx
/**
 * specificity_gate_v0.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 1
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.1 / §3 W0.6: "specificity gate v0 (canonical +
 * existing 4 charts as proxy cohort; full-cohort gating from W2)").
 *
 * DESIGN AUTHORITY: KALA_SUPREME_ELEVATION_v1_0.md §5 E3 — "The specificity gate (hard
 * CI): compose every view's reading for the canonical charts AND k random cohort charts;
 * any sentence template whose output is invariant across charts is filler and FAILS the
 * build. Delight becomes lintable — provable non-genericness." §5 also names the HARD
 * gate as W2 work (once the real cohort (item 22) exists) — this file is explicitly the
 * v0 SKELETON named in brief §3 W0.6: it proves the mechanism works and catches the
 * grossest case (byte-identical reading text across two DIFFERENT charts), using
 * whatever charts already exist in the system as a proxy cohort, NOT the ratified ~10⁴
 * synthetic cohort (that lands at W2 with item 22).
 *
 * WHY "v0" AND NOT "HARD": a v0 skeleton can only prove non-invariance across the charts
 * it can actually reach live. It is a real, teeth-bearing check (byte-identical composed
 * text across two structurally different charts is unambiguously filler) but it is not
 * yet a statistical/cohort-scale gate — that is explicitly W2 scope per the brief.
 *
 * SIBLING-LANE COORDINATION (per this lane's task brief): the eight kala_* tool facades
 * this gate calls are built by concurrent sibling `.worktrees/shad-darshana-*` lanes and
 * may not be merged/deployed yet. Every tool this gate cannot reach is reported SKIPPED
 * (never a fabricated PASS, never a FAIL for something outside this lane's control) —
 * see `_kala_tool_registration.ts`'s header for the full rationale.
 *
 * Two modes, matching every sibling gate in `platform/scripts/census/elev_gates/`:
 *   PLAN mode (no MCP_SERVER_URL) — statically reports which of the eight tools are
 *     registered yet and prints the call plan; exits 0 always, no network calls.
 *   LIVE mode (MCP_SERVER_URL [+ MCP_BEARER]) — drives the real deployed connector:
 *     discovers a small proxy cohort (the two canonical charts + up to two more via
 *     `catalog_charts_list`, capped at 4 total per brief §0.6.1), calls every REGISTERED
 *     kala_* tool once per chart with minimal input, and FAILS the build if any two
 *     charts' composed reading text comes back byte-identical and non-empty.
 *
 * Run (plan mode, from `platform/`):
 *   npx tsx scripts/census/shad_darshana_gates/specificity_gate_v0.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/shad_darshana_gates/specificity_gate_v0.ts
 */
import {
  ShadDarshanaMcpClient,
  resolveMcpTarget,
  unwrapToolPayload,
  envOrDefault,
  DEFAULT_TOOL_TIMEOUT_MS,
  CANONICAL_CHART_ID,
  CROSS_CHECK_CHART_ID,
} from './_mcp_client'
import { printGateReport, type GateResult } from './_report'
import { SHAD_DARSHANA_EIGHT_TOOLS, collectShadDarshanaRegistration, isKalaToolRegistered } from './_kala_tool_registration'

const TOOL_TIMEOUT_MS = Number(envOrDefault('SPECIFICITY_GATE_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))
const MIN_GAP_MS = Number(envOrDefault('SPECIFICITY_GATE_MIN_GAP_MS', '300'))
const MAX_COHORT_SIZE = 4 // brief §0.6.1: "canonical + existing 4 charts as proxy cohort"

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Best-effort extraction of the composed reading text from a kala_* envelope payload.
 * The exact wire shape is owned by the sibling facade lanes and `kala_envelope.ts` /
 * `argument_composer.ts` (out of this lane's scope) — this walks the handful of plausible
 * locations (`reading.full_text`, `reading.thesis` + `reading.verdict.statement` composed
 * inline, or a top-level `full_text`) rather than assuming one fixed shape. Returns null,
 * never a fabricated string, when nothing textual is found.
 */
function extractReadingText(payload: unknown): string | null {
  if (typeof payload !== 'object' || payload === null) return null
  const obj = payload as Record<string, unknown>
  const reading = obj['reading']
  if (typeof reading === 'object' && reading !== null) {
    const r = reading as Record<string, unknown>
    if (typeof r['full_text'] === 'string' && r['full_text'].length > 0) return r['full_text']
    const parts: string[] = []
    if (typeof r['thesis'] === 'string') parts.push(r['thesis'])
    const verdict = r['verdict']
    if (typeof verdict === 'object' && verdict !== null && typeof (verdict as Record<string, unknown>)['statement'] === 'string') {
      parts.push((verdict as Record<string, unknown>)['statement'] as string)
    }
    if (parts.length > 0) return parts.join(' ')
  }
  if (typeof obj['full_text'] === 'string' && obj['full_text'].length > 0) return obj['full_text']
  return null
}

function planResults(): GateResult[] {
  const registration = collectShadDarshanaRegistration()
  const results: GateResult[] = []
  for (const tool of SHAD_DARSHANA_EIGHT_TOOLS) {
    const registered = isKalaToolRegistered(tool, registration)
    results.push({
      id: `specificity-plan:${tool}`,
      title: `Call plan: ${tool}(chart_id) across [${CANONICAL_CHART_ID.slice(0, 8)}, ${CROSS_CHECK_CHART_ID.slice(0, 8)}, +up to 2 discovered] — registered=${registered}`,
      status: 'SKIPPED',
      detail: registered
        ? `PLAN mode — no MCP_SERVER_URL set, no live call executed. Statically registered in: ${registration[tool].join(', ')}`
        : 'PLAN mode — tool not yet statically registered under platform-mcp/src/tools (sibling facade lane likely not merged yet).',
    })
  }
  return results
}

/** Discovers a small proxy cohort: the two canonical charts, plus up to two more via
 *  `catalog_charts_list` if that tool is reachable, capped at MAX_COHORT_SIZE total. Never
 *  fabricates chart ids — a cohort smaller than MAX_COHORT_SIZE is reported honestly. */
async function discoverCohort(client: ShadDarshanaMcpClient): Promise<{ chartIds: string[]; note: string }> {
  const chartIds = [CANONICAL_CHART_ID, CROSS_CHECK_CHART_ID]
  const outcome = await client.callTool('catalog_charts_list', {}, TOOL_TIMEOUT_MS)
  if (outcome.timed_out || !outcome.ok) {
    return { chartIds, note: `catalog_charts_list unreachable (status=${outcome.status}, timed_out=${outcome.timed_out}) — proxy cohort = the 2 canonical charts only.` }
  }
  const { payload, isToolError } = unwrapToolPayload(outcome)
  if (isToolError || typeof payload !== 'object' || payload === null) {
    return { chartIds, note: 'catalog_charts_list returned a tool error or non-object payload — proxy cohort = the 2 canonical charts only.' }
  }
  const obj = payload as Record<string, unknown>
  const charts = Array.isArray(obj['charts']) ? (obj['charts'] as unknown[]) : Array.isArray(obj['items']) ? (obj['items'] as unknown[]) : []
  for (const c of charts) {
    if (chartIds.length >= MAX_COHORT_SIZE) break
    if (typeof c !== 'object' || c === null) continue
    const id = (c as Record<string, unknown>)['chart_id']
    if (typeof id === 'string' && id.length > 0 && !chartIds.includes(id)) chartIds.push(id)
  }
  return {
    chartIds,
    note: chartIds.length >= MAX_COHORT_SIZE
      ? `proxy cohort filled to ${MAX_COHORT_SIZE} (v0 cap) via catalog_charts_list.`
      : `proxy cohort has only ${chartIds.length} chart(s) — fewer than the ${MAX_COHORT_SIZE} v0 cap; catalog_charts_list did not surface more. Honest, not padded.`,
  }
}

async function liveResults(client: ShadDarshanaMcpClient): Promise<GateResult[]> {
  const results: GateResult[] = []
  const registration = collectShadDarshanaRegistration()
  const { chartIds, note } = await discoverCohort(client)
  results.push({
    id: 'specificity-cohort',
    title: 'Proxy cohort discovery',
    status: chartIds.length >= 2 ? 'PASS' : 'WARN',
    detail: `${note} chart_ids=${JSON.stringify(chartIds)}`,
  })

  for (const tool of SHAD_DARSHANA_EIGHT_TOOLS) {
    if (!isKalaToolRegistered(tool, registration)) {
      results.push({
        id: `specificity:${tool}`,
        title: `Specificity — ${tool}`,
        status: 'SKIPPED',
        detail: 'Tool not yet statically registered — sibling facade lane not merged yet. Not a fabricated pass.',
      })
      continue
    }

    const textByChart = new Map<string, string>()
    let hadHardFailure = false
    let hadSoftIssue = false
    const perChartNotes: string[] = []

    for (const chartId of chartIds) {
      const outcome = await client.callTool(tool, { chart_id: chartId }, TOOL_TIMEOUT_MS)
      await sleep(MIN_GAP_MS)
      if (outcome.timed_out || outcome.status >= 500) {
        hadHardFailure = true
        perChartNotes.push(`${chartId.slice(0, 8)}: HARD FAIL (timed_out=${outcome.timed_out}, status=${outcome.status})`)
        continue
      }
      if (!outcome.ok) {
        // 4xx — likely a minimal-args schema mismatch this v0 gate can't predict pre-merge
        // (the facade's real required params are the sibling lane's to define). Reported
        // as a soft issue, not a hard specificity failure.
        hadSoftIssue = true
        perChartNotes.push(`${chartId.slice(0, 8)}: HTTP ${outcome.status} (possible arg-schema mismatch, not a specificity verdict)`)
        continue
      }
      const { payload, isToolError } = unwrapToolPayload(outcome)
      if (isToolError) {
        hadSoftIssue = true
        perChartNotes.push(`${chartId.slice(0, 8)}: tool-level error`)
        continue
      }
      const text = extractReadingText(payload)
      if (text == null || text.trim().length === 0) {
        hadSoftIssue = true
        perChartNotes.push(`${chartId.slice(0, 8)}: no reading text found in payload (envelope shape may differ from what this v0 extractor expects)`)
        continue
      }
      textByChart.set(chartId, text)
    }

    if (hadHardFailure) {
      results.push({ id: `specificity:${tool}`, title: `Specificity — ${tool}`, status: 'FAIL', detail: `Live infra failure: ${perChartNotes.join('; ')}` })
      continue
    }
    if (textByChart.size < 2) {
      results.push({
        id: `specificity:${tool}`,
        title: `Specificity — ${tool}`,
        status: hadSoftIssue ? 'WARN' : 'SKIPPED',
        detail: `Could not compare ≥2 charts' reading text (got ${textByChart.size}). ${perChartNotes.join('; ')}`,
      })
      continue
    }

    const distinctTexts = new Set(textByChart.values())
    const pass = distinctTexts.size > 1
    results.push({
      id: `specificity:${tool}`,
      title: `Specificity — ${tool}`,
      status: pass ? 'PASS' : 'FAIL',
      detail: pass
        ? `Non-invariant: ${distinctTexts.size} distinct reading text(s) across ${textByChart.size} charts.`
        : `FILLER DETECTED (E3): byte-identical reading text across ${textByChart.size} different charts. First 200 chars: ${[...distinctTexts][0]!.slice(0, 200)}`,
    })
  }
  return results
}

async function main(): Promise<void> {
  const target = resolveMcpTarget()
  if (!target) {
    process.exit(printGateReport(
      'specificity_gate_v0 (PLAN mode)',
      planResults(),
      'MCP_SERVER_URL not set — running in PLAN mode only (registration checked statically, no live tool calls executed, exit 0 always).',
    ))
    return
  }

  const client = new ShadDarshanaMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()
  process.exit(printGateReport('specificity_gate_v0 (LIVE)', await liveResults(client)))
}

main().catch((err) => {
  console.error('specificity_gate_v0 FATAL:', err)
  process.exit(2)
})
