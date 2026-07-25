#!/usr/bin/env tsx
/**
 * w1_bare_empty_census_gate.ts — SATYA-ŚEṢA Campaign, Builder B1, W1 CI gate.
 *
 * SATYA_SHESHA_BRIEF_v1_0.md §2 W1: "a probe script iterating the Phase-0.7 census's 46
 * concepts by their OBVIOUS English/Sanskrit names against the live serving path. Every probe
 * must return rows OR a resolver_suggestion — a bare empty fails the build."
 *
 * The 46-concept census is UAT-DARPANA Phase 0.7's Full Concept-Coverage Matrix
 * (00_ARCHITECTURE/llm_consumption_audit/uat_darpana/RETRIEVAL_AUDIT_REPORT_v1_0.md Appendix
 * A + A.7 — "Combined R-2 totals: 46 concepts audited"). This gate re-probes every one of
 * those 46 concepts, but — unlike the original census, which used each concept's EXPERT
 * capability call — via the SAME naive front door that broke for S4-03 ("What's my exact
 * Gulika placement?"): a free-text keyword guess against `ganita_chart_facts_get`
 * (chart_facts_query). That is the exact failure class W1 fixes: `keyword` only ILIKEs
 * fact_key/fact_value_text (never fact_category), so a caller who does not already know the
 * real category name got a bare `{facts: [], total: 0}` and the answering LLM concluded "there
 * is nothing" — even though GULIKA lives under `sensitive_point_gulika_mandi`.
 *
 * 43 of the 46 concepts are probed this way (`keyword=<naive term>` on chart_facts_query),
 * graded PASS if the response carries real rows (total > 0) OR a `resolver_suggestion` (the
 * concept-resolver's honest pointer — see `resolve_concept.ts`). 3 concepts (Deity
 * attributions, Medical astrology, NBRY/neecha-bhanga grounds) are NOT chart_facts-native —
 * their real data lives in `chart_divisionals`, `ga_medical`, and `ga_yoga_firings`
 * respectively, so forcing them through chart_facts_query's `keyword` param would require
 * fabricating a fact_category that does not exist (B.10). These 3 are instead probed via
 * their OWN documented serving tool (Appendix A's own "Capability" column) and graded on real
 * rows served — a regression guard, not a resolver test, since Appendix A already confirmed
 * them SERVED.
 *
 * Two modes, matching every sibling gate in this directory:
 *   PLAN mode (no MCP_SERVER_URL) — statically validates the census (46 entries, no
 *     duplicates, every entry has a probe) and prints the call plan; exits 0 always, no
 *     network calls, no secret required.
 *   LIVE mode (MCP_SERVER_URL + MCP_BEARER) — drives the real deployed connector against
 *     BOTH canonical charts (482012f1 primary + 1c826d5a chart-agnostic cross-check per
 *     SATYA_SHESHA_BRIEF_v1_0.md §4), paced, and FAILS the build on any bare empty.
 *
 * Run (plan mode, from `platform/`):
 *   npx tsx scripts/census/elev_gates/w1_bare_empty_census_gate.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/elev_gates/w1_bare_empty_census_gate.ts
 */
import { ElevMcpClient, resolveMcpTarget, unwrapToolPayload, envOrDefault, DEFAULT_TOOL_TIMEOUT_MS } from './_mcp_client'
import { printGateReport, type GateResult } from './_report'

const PRIMARY_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const CROSS_CHECK_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const TOOL_TIMEOUT_MS = Number(envOrDefault('W1_CENSUS_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))
const MIN_GAP_MS = Number(envOrDefault('W1_CENSUS_MIN_GAP_MS', '300'))

type CensusEntry = {
  /** Concept display name, verbatim from RETRIEVAL_AUDIT_REPORT_v1_0.md Appendix A/A.7. */
  concept: string
  /** Appendix cluster this concept was audited under (A.1-A.5, A.7). */
  cluster: string
  tool: string
  args: (chartId: string) => Record<string, unknown>
  /**
   * 'resolver' — probed via chart_facts_query's `keyword` filter (the S4-03-shaped naive
   *   guess). PASS = real rows (total > 0) OR a non-null `resolver_suggestion`.
   * 'direct'   — probed via the concept's own dedicated tool (not chart_facts-native data).
   *   PASS = real rows served (regression guard; Appendix A already confirmed these SERVED).
   */
  grading: 'resolver' | 'direct'
}

/** The 46-concept census (RETRIEVAL_AUDIT_REPORT_v1_0.md Appendix A + A.7, "46 concepts
 *  audited"). Each `args()` naive term is the OBVIOUS English/Sanskrit name a caller who does
 *  not know the real fact_category would type — deliberately NOT the expert category name. */
const CENSUS: CensusEntry[] = [
  // ── A.1 — arudhas A1-A12+UL, karakas, avasthas, tara-bala ──────────────────────────────
  { concept: 'Arudha Lagna (A1)', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha lagna' }) },
  { concept: 'Arudha A2', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A3', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A4', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A5', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A6', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A7', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A8', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A9', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A10', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A11', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Arudha A12', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'arudha' }) },
  { concept: 'Upapada Lagna (UL)', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'upapada' }) },
  { concept: 'Karakas (Chara AK-DK + Sthira)', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'karaka' }) },
  { concept: 'Avasthas', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'avastha' }) },
  { concept: 'Tara Bala (9-fold nakshatra strength)', cluster: 'A.1', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'tara bala' }) },

  // ── A.2 — deity/hora/vimsopaka/sensitive-degrees/kala-sarpa/graha-yuddha ───────────────
  // Deity attributions live ONLY in chart_divisionals (varga_deity_attribution) — not a
  // chart_facts category. Probed via the real serving route (divisional_chart facet), same
  // as RETRIEVAL_AUDIT_REPORT_v1_0.md Appendix A confirmed ("8 real per-graha rows").
  { concept: 'Deity attributions', cluster: 'A.2', tool: 'ganita_chart_facts_get', grading: 'direct', args: (c) => ({ chart_id: c, divisional_chart: 'D2' }) },
  { concept: 'Hora classes', cluster: 'A.2', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'hora' }) },
  { concept: 'Vimsopaka bala', cluster: 'A.2', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'vimsopaka' }) },
  { concept: 'Sensitive degrees (pushkara/gandanta/mrityu-bhaga)', cluster: 'A.2', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'sensitive degrees' }) },
  { concept: 'Kala-sarpa per varga', cluster: 'A.2', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'kala sarpa' }) },
  { concept: 'Graha-yuddha', cluster: 'A.2', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'graha yuddha' }) },

  // ── A.3 — argala, parivartana, sambandha, aspects, KP cusps, tajaka ────────────────────
  { concept: 'Argala', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'argala' }) },
  { concept: 'Parivartana', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'parivartana' }) },
  { concept: 'Sambandha', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'sambandha' }) },
  { concept: 'Aspects (Parashari graha drishti)', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'drishti' }) },
  { concept: 'Aspects (Jaimini rashi drishti)', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'rashi drishti' }) },
  { concept: 'Aspects (Tajik)', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'tajik' }) },
  { concept: 'KP cusps / sub-lords', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'kp' }) },
  { concept: 'Tajaka (Varshaphal)', cluster: 'A.3', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'varshaphal' }) },

  // ── A.4 — ayurdaya, medical, yoga catalog+firings+NBRY, doshas ─────────────────────────
  { concept: 'Ayurdaya (Pindayu/Amsayu/Nisargayu)', cluster: 'A.4', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'ayurdaya' }) },
  // Medical astrology is served from `ga_medical` — no chart_facts fact_category exists for
  // it (grounds_to.l1_fact_ids: false on get_medical_indications.ts). Probed directly.
  { concept: 'Medical astrology (Vaidya-phala)', cluster: 'A.4', tool: 'ganita_medical_get', grading: 'direct', args: (c) => ({ chart_id: c }) },
  { concept: 'Yoga catalog', cluster: 'A.4', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'yoga' }) },
  { concept: 'Yoga firings', cluster: 'A.4', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'yoga strength' }) },
  // NBRY (Neecha Bhanga Raja Yoga) grounds live in `ga_yoga_firings.grounds_jsonb` — no
  // chart_facts fact_category for the per-varga cancellation ledger. Probed directly.
  { concept: 'NBRY grounds (per-varga cancellation ledger)', cluster: 'A.4', tool: 'ganita_yoga_firings_get', grading: 'direct', args: (c) => ({ chart_id: c, yoga_canonical_id: 'neecha_bhanga_raja_yoga', bhanga_active: true }) },
  { concept: 'Doshas (incl. cancellations)', cluster: 'A.4', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'dosha' }) },

  // ── A.5 — dasha plurality, sade-sati, muhurta, panchanga ───────────────────────────────
  { concept: 'Dasha plurality (beyond Vimshottari)', cluster: 'A.5', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'dasha' }) },
  { concept: 'Sade-sati', cluster: 'A.5', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'sade sati' }) },
  { concept: 'Muhurta', cluster: 'A.5', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'muhurta' }) },
  { concept: 'Panchanga', cluster: 'A.5', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'panchanga' }) },

  // ── A.7 — bindus, special lagnas, upagrahas, sahams, sphutas (re-run cluster) ──────────
  { concept: 'Bindus (natal Sarvashtakavarga)', cluster: 'A.7', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'sarvashtakavarga' }) },
  { concept: 'Bindus (per-varga)', cluster: 'A.7', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'varga bindu' }) },
  { concept: 'Special lagnas', cluster: 'A.7', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'special lagna' }) },
  { concept: 'Upagrahas', cluster: 'A.7', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'upagraha' }) },
  { concept: 'Sahams', cluster: 'A.7', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'saham' }) },
  { concept: 'Sphutas', cluster: 'A.7', tool: 'ganita_chart_facts_get', grading: 'resolver', args: (c) => ({ chart_id: c, keyword: 'sphuta' }) },
]

/** Extracts a best-effort "row count" from a chart_facts_query-shaped payload. */
function chartFactsRowCount(payload: Record<string, unknown>): number {
  if (typeof payload['total'] === 'number') return payload['total'] as number
  const facts = payload['facts']
  const rows = payload['rows']
  if (Array.isArray(facts)) return facts.length
  if (Array.isArray(rows)) return rows.length
  return 0
}

/** Extracts a best-effort "row count" from a `divisional_facts` sub-section. */
function divisionalFactsRowCount(payload: Record<string, unknown>): number {
  const dv = payload['divisional_facts'] as Record<string, unknown> | undefined
  if (!dv) return 0
  if (typeof dv['returned_count'] === 'number') return dv['returned_count'] as number
  const rows = dv['rows']
  return Array.isArray(rows) ? rows.length : 0
}

/** Extracts a best-effort "row count" from get_medical_indications / get_yoga_firings shape. */
function plainRowCount(payload: Record<string, unknown>): number {
  const rows = payload['rows']
  return Array.isArray(rows) ? rows.length : 0
}

async function sleep(ms: number): Promise<void> {
  await new Promise((r) => setTimeout(r, ms))
}

function planResults(): GateResult[] {
  const results: GateResult[] = []
  results.push({
    id: 'w1-census:entry-count',
    title: `Census entry count (must be 46, per RETRIEVAL_AUDIT_REPORT_v1_0.md Appendix A+A.7 "46 concepts audited")`,
    status: CENSUS.length === 46 ? 'PASS' : 'FAIL',
    detail: `${CENSUS.length} entries found.`,
  })
  const dupes = CENSUS.map((e) => e.concept).filter((c, i, arr) => arr.indexOf(c) !== i)
  results.push({
    id: 'w1-census:no-duplicates',
    title: 'No duplicate concept names in the census',
    status: dupes.length === 0 ? 'PASS' : 'FAIL',
    detail: dupes.length === 0 ? 'unique' : `duplicates: ${dupes.join(', ')}`,
  })
  for (const entry of CENSUS) {
    results.push({
      id: `w1-census-plan:${entry.concept}`,
      title: `Call plan [${entry.cluster}] ${entry.concept}: ${entry.tool}(${JSON.stringify(entry.args(PRIMARY_CHART_ID))}) — grading=${entry.grading}`,
      status: 'SKIPPED',
      detail: 'PLAN mode — no MCP_SERVER_URL set, no live call executed.',
    })
  }
  return results
}

async function liveResultsForChart(
  client: ElevMcpClient,
  chartId: string,
  chartLabel: string,
): Promise<GateResult[]> {
  const results: GateResult[] = []
  for (const entry of CENSUS) {
    const args = entry.args(chartId)
    const outcome = await client.callTool(entry.tool, args, TOOL_TIMEOUT_MS)
    const id = `w1-census:${chartLabel}:${entry.concept}`
    const title = `[${entry.cluster}] ${entry.concept} — ${entry.tool}(${JSON.stringify(args)})`

    if (outcome.timed_out) {
      results.push({ id, title, status: 'FAIL', detail: `Timed out after ${TOOL_TIMEOUT_MS}ms.` })
      await sleep(MIN_GAP_MS)
      continue
    }
    if (!outcome.ok || outcome.status >= 400) {
      results.push({ id, title, status: 'FAIL', detail: `HTTP ${outcome.status}: ${outcome.body.slice(0, 300)}` })
      await sleep(MIN_GAP_MS)
      continue
    }
    const { payload, isToolError } = unwrapToolPayload(outcome)
    if (isToolError || typeof payload !== 'object' || payload === null) {
      results.push({ id, title, status: 'FAIL', detail: `Tool-level error or non-object payload: ${JSON.stringify(payload).slice(0, 300)}` })
      await sleep(MIN_GAP_MS)
      continue
    }
    const content = payload as Record<string, unknown>

    if (entry.grading === 'direct') {
      const count = entry.tool === 'ganita_chart_facts_get' ? divisionalFactsRowCount(content) : plainRowCount(content)
      results.push({
        id, title,
        status: count > 0 ? 'PASS' : 'FAIL',
        detail: count > 0
          ? `Non-bare: ${count} row(s) served directly (regression guard — this concept has no chart_facts category to resolve to).`
          : `BARE EMPTY: 0 rows served and this concept has no resolver path (not chart_facts-native) — this is a genuine regression against the Phase-0.7 census's SERVED finding.`,
      })
    } else {
      const rowCount = chartFactsRowCount(content)
      const suggestion = content['resolver_suggestion']
      const hasSuggestion = suggestion != null && typeof suggestion === 'object'
      const pass = rowCount > 0 || hasSuggestion
      results.push({
        id, title,
        status: pass ? 'PASS' : 'FAIL',
        detail: rowCount > 0
          ? `Non-bare: ${rowCount} real row(s) served.`
          : hasSuggestion
            ? `Non-bare via resolver_suggestion: ${JSON.stringify(suggestion).slice(0, 300)}`
            : `BARE EMPTY: 0 rows AND no resolver_suggestion. empty_reason=${JSON.stringify(content['empty_reason'] ?? null).slice(0, 200)}, resolver_suggestion_note=${JSON.stringify(content['resolver_suggestion_note'] ?? null).slice(0, 200)}`,
      })
    }
    await sleep(MIN_GAP_MS)
  }
  return results
}

async function main(): Promise<void> {
  const target = resolveMcpTarget()
  if (!target) {
    process.exit(printGateReport(
      'w1_bare_empty_census_gate (PLAN mode)',
      planResults(),
      'MCP_SERVER_URL not set — running in PLAN mode only (census validated statically, no ' +
        'live tool calls executed, exit 0 always). Pipeline invocation: ' +
        'export MCP_SERVER_URL=https://<host>/mcp (optionally MCP_BEARER=<token>) before ' +
        're-running for LIVE mode.',
    ))
    return
  }

  const client = new ElevMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()

  const primary = await liveResultsForChart(client, PRIMARY_CHART_ID, 'primary-482012f1')
  const crossCheck = await liveResultsForChart(client, CROSS_CHECK_CHART_ID, 'cross-check-1c826d5a')

  process.exit(printGateReport('w1_bare_empty_census_gate (LIVE)', [...primary, ...crossCheck]))
}

main().catch((err) => {
  console.error('w1_bare_empty_census_gate FATAL:', err)
  process.exit(2)
})
