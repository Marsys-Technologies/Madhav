#!/usr/bin/env tsx
/**
 * run_battery.ts — W5 Lane L10: readback + tool-selection battery CLI (incl. concurrency
 * runs, plan §9.7 W-31 "quality-under-load proof" — the local, pre-infra half of it; see
 * the companion baseline artifact for what W-29/W-30 infra work this still needs before a
 * true production load test can run).
 *
 * Two passes, both against the SAME 60 (query × chart) combinations
 * (`queries.ts` BATTERY_QUERIES × BATTERY_CHARTS):
 *
 *   1. SEQUENTIAL — one at a time, in id order. Establishes the baseline: routing
 *      accuracy per family, floor-coverage stats, and a content-hash fingerprint per
 *      (query, chart) pair (the "readback" reference).
 *   2. CONCURRENT — the same 60 combinations, fired in batches of `--concurrency`
 *      (default 8; see baseline artifact §4 for the justification) via `Promise.all`.
 *      Every concurrent result's fingerprint is diffed against the sequential baseline
 *      (readback: must be byte-identical — this is a synchronous/deterministic pipeline,
 *      so ANY diff is a real regression, not scheduling noise) and every result's
 *      chart-isolation check is asserted (no cross-chart tool_arg leakage under
 *      concurrent cache access — the LCA-17-shaped risk this lane's brief called out).
 *
 * Usage: npx tsx --conditions=react-server tests/eval/w5_battery/run_battery.ts [--concurrency=N] [--out=path.json]
 *
 * Exit code: 0 if routing_accuracy ≥ 0.9 overall AND zero chart-isolation violations AND
 * zero readback diffs between the sequential and concurrent pass. Non-zero otherwise —
 * this IS the regression gate the wave's V5 close will eventually wire into CI.
 */
import { writeFileSync } from 'node:fs'
import { BATTERY_QUERIES, BATTERY_CHARTS } from './queries'
import {
  runOne,
  aggregateByFamily,
  aggregateOverall,
  fingerprintMap,
  readbackDiff,
  type BatteryRunResult,
} from './lib'

function parseArgs(argv: readonly string[]): { concurrency: number; out?: string } {
  let concurrency = 8
  let out: string | undefined
  for (const arg of argv) {
    const c = arg.match(/^--concurrency=(\d+)$/)
    if (c) concurrency = Number(c[1])
    const o = arg.match(/^--out=(.+)$/)
    if (o) out = o[1]
  }
  return { concurrency, out }
}

// All 60 (query, chart) combinations, in stable id×chart order.
function allCombos(): Array<{ query: (typeof BATTERY_QUERIES)[number]; chart: (typeof BATTERY_CHARTS)[number] }> {
  const combos: Array<{ query: (typeof BATTERY_QUERIES)[number]; chart: (typeof BATTERY_CHARTS)[number] }> = []
  for (const query of BATTERY_QUERIES) {
    for (const chart of BATTERY_CHARTS) {
      combos.push({ query, chart })
    }
  }
  return combos
}

async function runSequential(): Promise<{ results: BatteryRunResult[]; wallMs: number }> {
  const t0 = performance.now()
  const results: BatteryRunResult[] = []
  for (const { query, chart } of allCombos()) {
    results.push(runOne(query, chart))
  }
  return { results, wallMs: performance.now() - t0 }
}

async function runConcurrent(concurrency: number): Promise<{ results: BatteryRunResult[]; wallMs: number }> {
  const combos = allCombos()
  // Interleave chart_ids across the batch boundary deliberately (rather than grouping by
  // chart) so every batch of `concurrency` calls mixes BOTH charts — the isolation check
  // is only meaningful if concurrent calls for different charts actually overlap in time.
  const interleaved: typeof combos = []
  const byChart = BATTERY_CHARTS.map((chart) => combos.filter((c) => c.chart.chart_id === chart.chart_id))
  const maxLen = Math.max(...byChart.map((b) => b.length))
  for (let i = 0; i < maxLen; i++) {
    for (const bucket of byChart) {
      if (bucket[i]) interleaved.push(bucket[i])
    }
  }

  const t0 = performance.now()
  const results: BatteryRunResult[] = []
  for (let i = 0; i < interleaved.length; i += concurrency) {
    const batch = interleaved.slice(i, i + concurrency)
    const batchResults = await Promise.all(batch.map(({ query, chart }) => Promise.resolve(runOne(query, chart))))
    results.push(...batchResults)
  }
  return { results, wallMs: performance.now() - t0 }
}

async function main() {
  const { concurrency, out } = parseArgs(process.argv.slice(2))

  console.error(`[1/2] Sequential pass — ${BATTERY_QUERIES.length} queries × ${BATTERY_CHARTS.length} charts = ${BATTERY_QUERIES.length * BATTERY_CHARTS.length} combos…`)
  const seq = await runSequential()
  const seqFingerprints = fingerprintMap(seq.results)

  console.error(`[2/2] Concurrent pass — concurrency=${concurrency}…`)
  const conc = await runConcurrent(concurrency)

  const diffs = readbackDiff(conc.results, seqFingerprints)
  const isolationViolations = conc.results.filter((r) => !r.chart_isolation_ok)
  const overallSeq = aggregateOverall(seq.results)
  const overallConc = aggregateOverall(conc.results)
  const byFamilySeq = aggregateByFamily(seq.results)

  const report = {
    captured_at: new Date().toISOString(),
    concurrency,
    combos: seq.results.length,
    sequential: {
      wall_ms: Math.round(seq.wallMs * 100) / 100,
      overall: overallSeq,
      by_family: byFamilySeq,
      results: seq.results,
    },
    concurrent: {
      wall_ms: Math.round(conc.wallMs * 100) / 100,
      overall: overallConc,
      results: conc.results,
    },
    readback: {
      diffs_vs_sequential: diffs,
      diff_count: diffs.length,
    },
    isolation: {
      violation_count: isolationViolations.length,
      violations: isolationViolations.map((r) => ({ id: r.id, chart_label: r.chart_label })),
    },
    gate: {
      routing_accuracy_threshold: 0.9,
      routing_accuracy_actual: overallSeq.routing_accuracy,
      pass:
        overallSeq.routing_accuracy >= 0.9 &&
        isolationViolations.length === 0 &&
        diffs.length === 0 &&
        overallSeq.compile_failures === 0,
    },
  }

  const json = JSON.stringify(report, null, 2)
  if (out) {
    writeFileSync(out, json, 'utf-8')
    console.error(`Report written to ${out}`)
  } else {
    console.log(json)
  }

  console.error('\n── Summary ──')
  console.error(`Sequential: n=${overallSeq.n} routing_accuracy=${(overallSeq.routing_accuracy * 100).toFixed(1)}% wall_ms=${seq.wallMs.toFixed(2)} compile_failures=${overallSeq.compile_failures}`)
  for (const f of byFamilySeq) {
    console.error(`  ${f.family.padEnd(20)} n=${f.n} routing_accuracy=${(f.routing_accuracy * 100).toFixed(1)}% avg_mapped_fraction=${(f.avg_mapped_fraction * 100).toFixed(1)}% avg_dark=${f.avg_dark_count.toFixed(2)}`)
  }
  console.error(`Concurrent (N=${concurrency}): n=${overallConc.n} routing_accuracy=${(overallConc.routing_accuracy * 100).toFixed(1)}% wall_ms=${conc.wallMs.toFixed(2)} isolation_violations=${isolationViolations.length}`)
  console.error(`Readback diffs vs sequential baseline: ${diffs.length}`)
  console.error(`GATE: ${report.gate.pass ? 'PASS' : 'FAIL'}`)

  if (!report.gate.pass) process.exitCode = 1
}

main().catch((err) => {
  console.error('run_battery.ts fatal error:', err)
  process.exitCode = 2
})
