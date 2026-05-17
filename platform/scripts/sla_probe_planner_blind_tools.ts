#!/usr/bin/env tsx
/**
 * sla_probe_planner_blind_tools.ts — live SLA probe for the four tools
 * restored to RETRIEVAL_CAPABILITY_SPEC on 2026-05-17.
 *
 * Invokes each tool's retrieve() directly against the live DB (via the local
 * Cloud SQL Auth Proxy on port 5433) and reports:
 *   - latency_ms (wall-clock per call)
 *   - rows_returned
 *   - status: ok | zero_rows | degraded | error
 *   - sample contract assertions (ToolBundle shape valid)
 *
 * Why direct retrieve() and not via the planner pipeline:
 *   The fix that wires these into RETRIEVAL_CAPABILITY_SPEC is not deployed
 *   yet, so the production planner cannot select them. This probe measures
 *   the underlying retrieve() function's SLA so we know what the planner-
 *   driven SLA ceiling will be once deployed.
 *
 * Usage:
 *   1. In a separate terminal: bash platform/scripts/start_db_proxy.sh
 *      (Cloud SQL Auth Proxy on 127.0.0.1:5433)
 *   2. From platform/: npm run sla:probe-planner-blind
 *      (or: npx tsx --conditions=react-server --env-file-if-exists=../.env.rag
 *           scripts/sla_probe_planner_blind_tools.ts)
 *      Optional: SCENARIO_COUNT=3 (default 1) for P50/P95-ish numbers
 *                WARMUP_RUNS=2  (default 1) for additional cold-pool absorption
 *                WARMUP_RUNS=0  to disable warmup (matches the original behavior)
 *
 * Output:
 *   platform/scripts/eval/sla_probe_planner_blind_tools_<ISO_TS>.json
 *
 * Exit code: 0 if every scenario returns ok | zero_rows; 1 if any error;
 *            2 if the DB proxy is unreachable.
 */

import { writeFileSync, mkdirSync, existsSync } from 'node:fs'
import path from 'node:path'

import { tool as lelQuery } from '../src/lib/retrieve/lel_query'
import { tool as querySignalState } from '../src/lib/retrieve/query_signal_state'
import { tool as queryKpRulingPlanets } from '../src/lib/retrieve/query_kp_ruling_planets'
import { tool as queryVarshaphala } from '../src/lib/retrieve/query_varshaphala'
import type { QueryPlan, RetrievalTool, ToolBundle } from '../src/lib/retrieve/types'

// ─────────────────────────────────────────────────────────────────────────────
// Config
// ─────────────────────────────────────────────────────────────────────────────

const SCENARIO_COUNT = Number(process.env.SCENARIO_COUNT ?? '1')
const WARMUP_RUNS = Number(process.env.WARMUP_RUNS ?? '1')
const CHART_ID = process.env.CHART_ID ?? 'abhisek_mohanty_primary'
const NOW_ISO = new Date().toISOString()
const OUTPUT_DIR = path.join(__dirname, 'eval')
const OUTPUT_FILE = path.join(
  OUTPUT_DIR,
  `sla_probe_planner_blind_tools_${NOW_ISO.replace(/[:.]/g, '-')}.json`
)

// SLA budgets — conservative ceilings sourced from the SLO_PROBE rule of thumb
// for DB-only retrieval tools (no LLM call). Tuned to fire if a tool degrades.
const SLA_BUDGETS_MS: Record<string, number> = {
  lel_query: 250,                // simple table scan, 36 rows max
  query_signal_state: 400,       // indexed query with optional ANY() arrays
  query_kp_ruling_planets: 200,  // 9-row sort, indexed by chart_id+ayanamsha
  query_varshaphala: 250,        // year-range scan, ~78 rows max for native
}

// ─────────────────────────────────────────────────────────────────────────────
// Scenarios — exercise each tool with the planner's "optimal_patterns"
// (mirror the RetrievalCapabilityEntry.optimal_patterns we registered)
// ─────────────────────────────────────────────────────────────────────────────

interface Scenario {
  tool: RetrievalTool
  scenario_name: string
  params: Record<string, unknown>
  expect_rows_min?: number  // soft assertion; warns if violated, doesn't fail
}

const SCENARIOS: Scenario[] = [
  // lel_query (4 scenarios mirroring optimal_patterns)
  {
    tool: lelQuery,
    scenario_name: 'lel_query · career major events',
    params: { category: 'career', significance: 'major' },
    expect_rows_min: 1,
  },
  {
    tool: lelQuery,
    scenario_name: 'lel_query · all major events',
    params: { significance: 'major', limit: 50 },
    expect_rows_min: 5,
  },
  {
    tool: lelQuery,
    scenario_name: 'lel_query · decade window 2010-2020',
    params: { start_date: '2010-01-01', end_date: '2020-12-31' },
    expect_rows_min: 1,
  },
  {
    tool: lelQuery,
    scenario_name: 'lel_query · empty filter (all rows)',
    params: {},
    expect_rows_min: 10,
  },

  // query_signal_state (4 scenarios)
  {
    tool: querySignalState,
    scenario_name: 'query_signal_state · current lit/ripening',
    params: { chart_id: CHART_ID, states: ['lit', 'ripening'], limit: 50 },
  },
  {
    tool: querySignalState,
    scenario_name: 'query_signal_state · window scan 2026',
    params: {
      chart_id: CHART_ID,
      query_date: '2026-01-01',
      end_date: '2026-12-31',
      states: ['lit'],
      limit: 100,
    },
  },
  {
    tool: querySignalState,
    scenario_name: 'query_signal_state · today only',
    params: { chart_id: CHART_ID, limit: 50 },
  },
  {
    tool: querySignalState,
    scenario_name: 'query_signal_state · ripening watchlist vimshottari',
    params: {
      chart_id: CHART_ID,
      states: ['ripening'],
      dasha_system: 'vimshottari',
      limit: 30,
    },
  },

  // query_kp_ruling_planets (3 scenarios)
  {
    tool: queryKpRulingPlanets,
    scenario_name: 'query_kp_ruling_planets · full graha table',
    params: { chart_id: CHART_ID },
    expect_rows_min: 9,
  },
  {
    tool: queryKpRulingPlanets,
    scenario_name: 'query_kp_ruling_planets · Saturn only',
    params: { chart_id: CHART_ID, planet: 'Saturn' },
    expect_rows_min: 1,
  },
  {
    tool: queryKpRulingPlanets,
    scenario_name: 'query_kp_ruling_planets · cross-ayanamsha (krishnamurti)',
    params: { chart_id: CHART_ID, ayanamsha: 'krishnamurti' },
  },

  // query_varshaphala (4 scenarios)
  {
    tool: queryVarshaphala,
    scenario_name: 'query_varshaphala · 2026 only',
    params: { chart_id: CHART_ID, year: 2026 },
    expect_rows_min: 1,
  },
  {
    tool: queryVarshaphala,
    scenario_name: 'query_varshaphala · 5-year window 2024-2028',
    params: { chart_id: CHART_ID, year_start: 2024, year_end: 2028 },
    expect_rows_min: 5,
  },
  {
    tool: queryVarshaphala,
    scenario_name: 'query_varshaphala · plan.time_window fallback',
    params: { chart_id: CHART_ID },  // year derived from plan.time_window
    expect_rows_min: 1,
  },
  {
    tool: queryVarshaphala,
    scenario_name: 'query_varshaphala · plan.time_window 2026-2028',
    params: { chart_id: CHART_ID },
    expect_rows_min: 1,
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Probe helpers
// ─────────────────────────────────────────────────────────────────────────────

function buildBasePlan(tool_name: string, time_window?: { start: string; end: string }): QueryPlan {
  return {
    query_plan_id: '00000000-0000-0000-0000-000000000001',
    query_text: `[sla_probe] ${tool_name}`,
    query_class: 'factual',
    domains: [],
    forward_looking: false,
    audience_tier: 'super_admin',
    tools_authorized: [tool_name],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'sla_probe',
    schema_version: '1.0',
    time_window,
  }
}

interface ProbeResult {
  scenario_name: string
  tool_name: string
  params: Record<string, unknown>
  status: 'ok' | 'zero_rows' | 'degraded' | 'error' | 'budget_exceeded'
  latency_ms: number
  rows_returned: number
  tool_bundle_shape_valid: boolean
  result_hash: string | null
  served_from_cache: boolean
  error: string | null
  budget_ms: number
  budget_overhead_ms: number
  expect_rows_min?: number
  rows_min_met?: boolean
}

async function probeOne(scenario: Scenario, run_index: number): Promise<ProbeResult> {
  const tool = scenario.tool
  const isVarshaphalaTimeWindow =
    scenario.scenario_name.includes('plan.time_window 2026-2028')
  const time_window = isVarshaphalaTimeWindow
    ? { start: '2026-01-01', end: '2028-12-31' }
    : isVarshaphala_fallback(scenario)
      ? { start: '2026-01-01', end: '2026-12-31' }
      : undefined

  const plan = buildBasePlan(tool.name, time_window)
  const budget = SLA_BUDGETS_MS[tool.name] ?? 500

  const start = Date.now()
  try {
    const bundle: ToolBundle = await tool.retrieve(plan, scenario.params)
    const latency_ms = Date.now() - start

    const rows = bundle.results.length
    const shape_valid =
      typeof bundle.tool_bundle_id === 'string' &&
      typeof bundle.tool_name === 'string' &&
      Array.isArray(bundle.results) &&
      typeof bundle.result_hash === 'string' &&
      typeof bundle.latency_ms === 'number'

    let status: ProbeResult['status'] = 'ok'
    if (rows === 0) status = 'zero_rows'
    if (latency_ms > budget) status = 'budget_exceeded'

    const rows_min_met = scenario.expect_rows_min
      ? rows >= scenario.expect_rows_min
      : undefined

    return {
      scenario_name: scenario.scenario_name,
      tool_name: tool.name,
      params: scenario.params,
      status,
      latency_ms,
      rows_returned: rows,
      tool_bundle_shape_valid: shape_valid,
      result_hash: bundle.result_hash,
      served_from_cache: bundle.served_from_cache,
      error: null,
      budget_ms: budget,
      budget_overhead_ms: latency_ms - budget,
      expect_rows_min: scenario.expect_rows_min,
      rows_min_met,
    }
  } catch (err) {
    const latency_ms = Date.now() - start
    return {
      scenario_name: scenario.scenario_name,
      tool_name: tool.name,
      params: scenario.params,
      status: 'error',
      latency_ms,
      rows_returned: 0,
      tool_bundle_shape_valid: false,
      result_hash: null,
      served_from_cache: false,
      error: err instanceof Error ? err.message : String(err),
      budget_ms: budget,
      budget_overhead_ms: latency_ms - budget,
      expect_rows_min: scenario.expect_rows_min,
      rows_min_met: false,
    }
  }
}

function isVarshaphala_fallback(s: Scenario): boolean {
  return (
    s.tool.name === 'query_varshaphala' &&
    s.scenario_name.includes('plan.time_window fallback')
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  console.log('━'.repeat(80))
  console.log('SLA Probe — Planner-Blind Tools Restored 2026-05-17')
  console.log('━'.repeat(80))
  console.log(`Chart:     ${CHART_ID}`)
  console.log(`Run time:  ${NOW_ISO}`)
  console.log(`Scenarios: ${SCENARIOS.length} × ${SCENARIO_COUNT} measured run(s)`)
  console.log(`Warmup:    ${WARMUP_RUNS} run(s) — discarded, absorbs cold pg pool init`)
  console.log('')

  // ── Warmup pass(es) — discarded so cold-start latency from a freshly
  // initialized pg connection pool (local Cloud SQL Auth Proxy on first hit)
  // is absorbed and does not pollute the steady-state SLA measurement.
  // Production Cloud Run already has a warm pool from prior request traffic,
  // so the measured runs alone reflect the real production SLA ceiling.
  for (let w = 0; w < WARMUP_RUNS; w++) {
    process.stdout.write(`  Warmup ${w + 1}/${WARMUP_RUNS} … `)
    const warmupStart = Date.now()
    for (const scenario of SCENARIOS) {
      try {
        await scenario.tool.retrieve(buildBasePlan(scenario.tool.name), scenario.params)
      } catch {
        // swallow — warmup failures are informational only
      }
    }
    console.log(`done (${Date.now() - warmupStart}ms total)`)
  }
  if (WARMUP_RUNS > 0) console.log('')

  const results: ProbeResult[] = []
  for (let run = 0; run < SCENARIO_COUNT; run++) {
    if (SCENARIO_COUNT > 1) console.log(`\n──── Run ${run + 1} / ${SCENARIO_COUNT} ────`)
    for (const scenario of SCENARIOS) {
      const r = await probeOne(scenario, run)
      results.push(r)
      const symbol =
        r.status === 'ok'
          ? '✓'
          : r.status === 'zero_rows'
            ? '∅'
            : r.status === 'budget_exceeded'
              ? '⚠'
              : '✗'
      const budget_marker = r.budget_overhead_ms > 0 ? ` (+${r.budget_overhead_ms}ms over)` : ''
      const rows_marker =
        r.expect_rows_min !== undefined && !r.rows_min_met
          ? ` ⚠ rows<${r.expect_rows_min}`
          : ''
      console.log(
        `  ${symbol} [${r.latency_ms.toString().padStart(4)}ms / ${r.budget_ms}ms${budget_marker}] ` +
          `${r.rows_returned.toString().padStart(3)} rows${rows_marker}  ${r.scenario_name}`
      )
      if (r.error) console.log(`      └─ ${r.error}`)
    }
  }

  // ── Aggregate ──
  console.log('\n' + '━'.repeat(80))
  console.log('AGGREGATE')
  console.log('━'.repeat(80))

  const byTool: Record<string, ProbeResult[]> = {}
  for (const r of results) {
    if (!byTool[r.tool_name]) byTool[r.tool_name] = []
    byTool[r.tool_name].push(r)
  }

  const aggregate: Record<string, unknown> = {}
  for (const [toolName, rs] of Object.entries(byTool)) {
    const latencies = rs.map(r => r.latency_ms).sort((a, b) => a - b)
    const ok = rs.filter(r => r.status === 'ok' || r.status === 'zero_rows').length
    const errored = rs.filter(r => r.status === 'error').length
    const exceeded = rs.filter(r => r.status === 'budget_exceeded').length
    const p50 = latencies[Math.floor(latencies.length * 0.5)]
    const p95 = latencies[Math.floor(latencies.length * 0.95)] ?? latencies[latencies.length - 1]
    const max = latencies[latencies.length - 1]
    const budget = SLA_BUDGETS_MS[toolName] ?? 500
    const reachability = (ok / rs.length) * 100

    aggregate[toolName] = {
      runs: rs.length,
      ok,
      errored,
      budget_exceeded: exceeded,
      latency_p50_ms: p50,
      latency_p95_ms: p95,
      latency_max_ms: max,
      budget_ms: budget,
      reachability_pct: Math.round(reachability * 10) / 10,
    }

    console.log(
      `  ${toolName.padEnd(28)}  reach=${reachability.toFixed(1)}%  ` +
        `p50=${p50}ms  p95=${p95}ms  max=${max}ms  budget=${budget}ms` +
        (exceeded > 0 ? `  ⚠${exceeded} over` : '') +
        (errored > 0 ? `  ✗${errored} errors` : '')
    )
  }

  // ── Write JSON ──
  if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true })
  const report = {
    probe_name: 'planner_blind_tools_restored_2026_05_17',
    run_at: NOW_ISO,
    chart_id: CHART_ID,
    scenario_count: SCENARIOS.length,
    runs_per_scenario: SCENARIO_COUNT,
    warmup_runs: WARMUP_RUNS,
    sla_budgets_ms: SLA_BUDGETS_MS,
    results,
    aggregate,
  }
  writeFileSync(OUTPUT_FILE, JSON.stringify(report, null, 2))
  console.log(`\n📄 Report → ${path.relative(process.cwd(), OUTPUT_FILE)}`)

  const totalErrors = results.filter(r => r.status === 'error').length
  const totalExceeded = results.filter(r => r.status === 'budget_exceeded').length

  if (totalErrors > 0) {
    console.log(`\n❌ ${totalErrors} error(s). Check the report's "error" fields.`)
    process.exit(1)
  }
  if (totalExceeded > 0) {
    console.log(`\n⚠️  ${totalExceeded} scenario(s) exceeded SLA budget. Investigate.`)
    process.exit(0)
  }
  console.log('\n✅ All scenarios within SLA budget.')
  process.exit(0)
}

main().catch((err) => {
  console.error('Fatal:', err)
  const reachable = (err instanceof Error ? err.message : String(err)).toLowerCase()
  if (
    reachable.includes('econnrefused') ||
    reachable.includes('5433') ||
    reachable.includes('proxy')
  ) {
    console.error(
      '\nLooks like the Cloud SQL Auth Proxy is not running on 127.0.0.1:5433.\n' +
        'Start it: bash platform/scripts/start_db_proxy.sh\n'
    )
    process.exit(2)
  }
  process.exit(1)
})
