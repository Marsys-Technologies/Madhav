#!/usr/bin/env tsx
/**
 * sla_probe_temporal.ts — live SLA probe for the temporal retrieval tool.
 *
 * Calls temporal.retrieve() directly against a live Python sidecar
 * (PYTHON_SIDECAR_URL env var) and measures latency for all five sub-modes:
 *   dasha_context, transit, sade_sati, eclipse, retrograde
 *
 * Usage:
 *   1. Ensure PYTHON_SIDECAR_URL is set (e.g. http://localhost:8000)
 *   2. From platform/: npm run sla:probe-temporal
 *      (or: npx tsx --conditions=react-server --env-file-if-exists=../.env.rag
 *           scripts/sla_probe_temporal.ts)
 *      Optional: SCENARIO_COUNT=3 (default 1)
 *                WARMUP_RUNS=1 (default 1)
 *
 * If the sidecar is unavailable, temporal degrades gracefully (returns a
 * warning bundle instead of throwing). Those runs are marked 'degraded'.
 *
 * Exit code: 0 if all within budget; 0 with ⚠ if any budget_exceeded;
 *            1 if any hard error; 2 if PYTHON_SIDECAR_URL is not set.
 */

import { writeFileSync, mkdirSync, existsSync } from 'node:fs'
import path from 'node:path'

import { tool as temporal } from '../src/lib/retrieve/temporal'
import type { QueryPlan, RetrievalTool, ToolBundle } from '../src/lib/retrieve/types'

// ─────────────────────────────────────────────────────────────────────────────
// Config
// ─────────────────────────────────────────────────────────────────────────────

const SCENARIO_COUNT = Number(process.env.SCENARIO_COUNT ?? '1')
const WARMUP_RUNS    = Number(process.env.WARMUP_RUNS    ?? '1')
const NOW_ISO        = new Date().toISOString()
const OUTPUT_DIR     = path.join(__dirname, 'eval')
const OUTPUT_FILE    = path.join(
  OUTPUT_DIR,
  `sla_probe_temporal_${NOW_ISO.replace(/[:.]/g, '-')}.json`
)

const TODAY      = new Date().toISOString().slice(0, 10)
const IN_30_DAYS = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10)
const IN_1_YEAR  = new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10)

const SLA_BUDGETS_MS: Record<string, number> = {
  dasha_context: 200,
  transit:       400,
  sade_sati:     100,
  eclipse:       150,
  retrograde:    150,
}

// ─────────────────────────────────────────────────────────────────────────────
// Scenarios — one per sub-mode; plan properties drive endpoint selection
// ─────────────────────────────────────────────────────────────────────────────

interface Scenario {
  tool: RetrievalTool
  scenario_name: string
  sub_mode: string
  plan_override: Partial<QueryPlan>
}

const SCENARIOS: Scenario[] = [
  {
    tool: temporal,
    scenario_name: 'temporal · transit (forward_looking + time_window)',
    sub_mode: 'transit',
    plan_override: {
      forward_looking: true,
      time_window: { start: TODAY, end: IN_30_DAYS },
    },
  },
  {
    tool: temporal,
    scenario_name: 'temporal · dasha_context (dasha_context_required)',
    sub_mode: 'dasha_context',
    plan_override: {
      dasha_context_required: true,
      time_window: { start: TODAY, end: IN_30_DAYS },
    },
  },
  {
    tool: temporal,
    scenario_name: 'temporal · sade_sati (sade_sati_query)',
    sub_mode: 'sade_sati',
    plan_override: {
      sade_sati_query: true,
    },
  },
  {
    tool: temporal,
    scenario_name: 'temporal · eclipse (eclipse_query + time_window)',
    sub_mode: 'eclipse',
    plan_override: {
      eclipse_query: true,
      time_window: { start: TODAY, end: IN_1_YEAR },
    },
  },
  {
    tool: temporal,
    scenario_name: 'temporal · retrograde (retrograde_query + planet)',
    sub_mode: 'retrograde',
    plan_override: {
      retrograde_query: true,
      retrograde_planet: 'Saturn',
    },
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Probe helpers
// ─────────────────────────────────────────────────────────────────────────────

function buildPlan(scenario: Scenario): QueryPlan {
  return {
    query_plan_id: '00000000-0000-0000-0000-000000000001',
    query_text: `[sla_probe] temporal:${scenario.sub_mode}`,
    query_class: 'predictive',
    domains: [],
    forward_looking: false,
    audience_tier: 'super_admin',
    tools_authorized: ['temporal'],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'sla_probe',
    schema_version: '1.0',
    ...scenario.plan_override,
  }
}

function isDegradedBundle(bundle: ToolBundle): boolean {
  return bundle.results.some(r => r.content.includes('Temporal data unavailable'))
}

interface ProbeResult {
  scenario_name: string
  sub_mode: string
  tool_name: string
  status: 'ok' | 'zero_rows' | 'degraded' | 'error' | 'budget_exceeded'
  latency_ms: number
  rows_returned: number
  tool_bundle_shape_valid: boolean
  result_hash: string | null
  served_from_cache: boolean
  error: string | null
  budget_ms: number
  budget_overhead_ms: number
}

async function probeOne(scenario: Scenario): Promise<ProbeResult> {
  const budget = SLA_BUDGETS_MS[scenario.sub_mode] ?? 500
  const plan   = buildPlan(scenario)
  const start  = Date.now()

  try {
    const bundle: ToolBundle = await scenario.tool.retrieve(plan, {})
    const latency_ms = Date.now() - start
    const rows = bundle.results.length

    const shape_valid =
      typeof bundle.tool_bundle_id === 'string' &&
      typeof bundle.tool_name      === 'string' &&
      Array.isArray(bundle.results)              &&
      typeof bundle.result_hash    === 'string'  &&
      typeof bundle.latency_ms     === 'number'

    let status: ProbeResult['status'] = 'ok'
    if (rows === 0)              status = 'zero_rows'
    if (isDegradedBundle(bundle)) status = 'degraded'
    if (latency_ms > budget)     status = 'budget_exceeded'

    return {
      scenario_name: scenario.scenario_name,
      sub_mode: scenario.sub_mode,
      tool_name: scenario.tool.name,
      status,
      latency_ms,
      rows_returned: rows,
      tool_bundle_shape_valid: shape_valid,
      result_hash: bundle.result_hash,
      served_from_cache: bundle.served_from_cache,
      error: null,
      budget_ms: budget,
      budget_overhead_ms: latency_ms - budget,
    }
  } catch (err) {
    const latency_ms = Date.now() - start
    return {
      scenario_name: scenario.scenario_name,
      sub_mode: scenario.sub_mode,
      tool_name: scenario.tool.name,
      status: 'error',
      latency_ms,
      rows_returned: 0,
      tool_bundle_shape_valid: false,
      result_hash: null,
      served_from_cache: false,
      error: err instanceof Error ? err.message : String(err),
      budget_ms: budget,
      budget_overhead_ms: latency_ms - budget,
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  if (!process.env.PYTHON_SIDECAR_URL) {
    console.error(
      'PYTHON_SIDECAR_URL is not set.\n' +
      'The temporal tool requires a Python sidecar URL.\n' +
      'Set PYTHON_SIDECAR_URL=http://localhost:8000 (or wherever your sidecar is running).\n'
    )
    process.exit(2)
  }

  console.log('━'.repeat(80))
  console.log('SLA Probe — temporal tool (Phase 2C, 2026-05-18)')
  console.log('━'.repeat(80))
  console.log(`Sidecar:   ${process.env.PYTHON_SIDECAR_URL}`)
  console.log(`Run time:  ${NOW_ISO}`)
  console.log(`Scenarios: ${SCENARIOS.length} × ${SCENARIO_COUNT} measured run(s)`)
  console.log(`Warmup:    ${WARMUP_RUNS} run(s) — discarded`)
  console.log('')

  for (let w = 0; w < WARMUP_RUNS; w++) {
    process.stdout.write(`  Warmup ${w + 1}/${WARMUP_RUNS} … `)
    const warmupStart = Date.now()
    for (const scenario of SCENARIOS) {
      try { await scenario.tool.retrieve(buildPlan(scenario), {}) } catch { /* swallow */ }
    }
    console.log(`done (${Date.now() - warmupStart}ms total)`)
  }
  if (WARMUP_RUNS > 0) console.log('')

  const results: ProbeResult[] = []
  for (let run = 0; run < SCENARIO_COUNT; run++) {
    if (SCENARIO_COUNT > 1) console.log(`\n──── Run ${run + 1} / ${SCENARIO_COUNT} ────`)
    for (const scenario of SCENARIOS) {
      const r = await probeOne(scenario)
      results.push(r)
      const symbol =
        r.status === 'ok'              ? '✓' :
        r.status === 'zero_rows'       ? '∅' :
        r.status === 'degraded'        ? '⚠' :
        r.status === 'budget_exceeded' ? '⚠' : '✗'
      const over = r.budget_overhead_ms > 0 ? ` (+${r.budget_overhead_ms}ms over)` : ''
      console.log(
        `  ${symbol} [${r.latency_ms.toString().padStart(4)}ms / ${r.budget_ms}ms${over}]` +
        `  ${r.rows_returned} result(s)  ${r.scenario_name}` +
        (r.status === 'degraded' ? '  [sidecar unavailable — degraded]' : '')
      )
      if (r.error) console.log(`      └─ ${r.error}`)
    }
  }

  // ── Aggregate ──
  console.log('\n' + '━'.repeat(80))
  console.log('AGGREGATE')
  console.log('━'.repeat(80))

  const byMode: Record<string, ProbeResult[]> = {}
  for (const r of results) {
    if (!byMode[r.sub_mode]) byMode[r.sub_mode] = []
    byMode[r.sub_mode].push(r)
  }

  const aggregate: Record<string, unknown> = {}
  for (const [mode, rs] of Object.entries(byMode)) {
    const lats = rs.map(r => r.latency_ms).sort((a, b) => a - b)
    const ok   = rs.filter(r => r.status === 'ok' || r.status === 'zero_rows' || r.status === 'degraded').length
    const errs = rs.filter(r => r.status === 'error').length
    const over = rs.filter(r => r.status === 'budget_exceeded').length
    const p50  = lats[Math.floor(lats.length * 0.5)]
    const p95  = lats[Math.floor(lats.length * 0.95)] ?? lats[lats.length - 1]
    const max  = lats[lats.length - 1]
    const budget = SLA_BUDGETS_MS[mode] ?? 500
    const reach  = (ok / rs.length) * 100

    aggregate[mode] = { runs: rs.length, ok, errored: errs, budget_exceeded: over,
      latency_p50_ms: p50, latency_p95_ms: p95, latency_max_ms: max,
      budget_ms: budget, reachability_pct: Math.round(reach * 10) / 10 }

    console.log(
      `  ${mode.padEnd(14)}  reach=${reach.toFixed(1)}%` +
      `  p50=${p50}ms  p95=${p95}ms  max=${max}ms  budget=${budget}ms` +
      (over  > 0 ? `  ⚠${over} over`    : '') +
      (errs  > 0 ? `  ✗${errs} errors`  : '')
    )
  }

  // ── Write JSON ──
  if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true })
  const report = {
    probe_name:          'temporal_2026_05_18',
    run_at:              NOW_ISO,
    python_sidecar_url:  process.env.PYTHON_SIDECAR_URL,
    scenario_count:      SCENARIOS.length,
    runs_per_scenario:   SCENARIO_COUNT,
    warmup_runs:         WARMUP_RUNS,
    sla_budgets_ms:      SLA_BUDGETS_MS,
    results,
    aggregate,
  }
  writeFileSync(OUTPUT_FILE, JSON.stringify(report, null, 2))
  console.log(`\n📄 Report → ${path.relative(process.cwd(), OUTPUT_FILE)}`)

  const totalErrors   = results.filter(r => r.status === 'error').length
  const totalExceeded = results.filter(r => r.status === 'budget_exceeded').length
  const totalDegraded = results.filter(r => r.status === 'degraded').length

  if (totalErrors > 0) {
    console.log(`\n❌ ${totalErrors} error(s). Check the report's "error" fields.`)
    process.exit(1)
  }
  if (totalDegraded > 0) {
    console.log(`\n⚠️  ${totalDegraded} scenario(s) ran in degraded mode (sidecar unavailable).`)
    console.log('   Latency measured against graceful-degradation path; not a production SLA.')
    process.exit(0)
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
  const msg = (err instanceof Error ? err.message : String(err)).toLowerCase()
  if (msg.includes('python_sidecar_url') || msg.includes('econnrefused')) {
    console.error(
      '\nLooks like the Python sidecar is not reachable.\n' +
      `Set PYTHON_SIDECAR_URL and ensure the sidecar is running.\n`
    )
    process.exit(2)
  }
  process.exit(1)
})
