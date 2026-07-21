#!/usr/bin/env tsx
/**
 * planner_ab_compare.ts — Planner-Eval-S1 (repurposed from W2-EVAL-B AC.V.2)
 *
 * Runs both an **oracle** side (returns the golden set's expected_tools — the
 * theoretical recall=1.00 / precision=1.00 ceiling) and the new
 * `callPipelinePlanner()` (tool_calls output) against `planner_golden_set.json`,
 * then prints a side-by-side per-entry comparison plus aggregate metrics.
 *
 * The classify() router was deleted in Pipeline-Transform-S1 (2026-05-11);
 * the oracle baseline replaces it as the upper-bound comparison signal.
 *
 *   --dry-run   Skip live LLM calls. Skips the planner side entirely (no LLM call).
 *               Useful for validating the script wiring + comparison output
 *               without burning tokens.
 *
 * Env (live mode):
 *   PLANNER_MODEL_ID  (default: meta/llama-3.1-8b-instruct)
 *   CHART_ID          (default: test-native)
 *
 * Usage:
 *   npx tsx --conditions=react-server platform/tests/eval/planner_ab_compare.ts [--dry-run]
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  scoreEntry,
  aggregateResults,
  RECALL_THRESHOLD,
  PRECISION_THRESHOLD,
  type GoldenSet,
  type GoldenEntry,
  type EvalResult,
} from './planner_smoke_runner'

function loadGoldenSet(): GoldenSet {
  const here = path.dirname(fileURLToPath(import.meta.url))
  const p = path.resolve(here, 'planner_golden_set.json')
  return JSON.parse(readFileSync(p, 'utf-8')) as GoldenSet
}

interface SideResult {
  side: 'oracle' | 'planner'
  predicted_tools: string[]
  error?: string
}

function formatRow(entry: GoldenEntry, oracle: SideResult, planner: SideResult | null): string {
  const oScore = scoreEntry(entry, oracle.predicted_tools, oracle.error)
  const oLine =
    `  ${entry.id}  oracle:   [${oracle.predicted_tools.join(', ')}]` +
    `  recall=${oScore.tool_recall.toFixed(2)} precision=${oScore.tool_precision.toFixed(2)}` +
    (oScore.pass ? ' ✓' : '')

  if (!planner) {
    return `${oLine}\n          planner:  (skipped)`
  }
  const pScore = scoreEntry(entry, planner.predicted_tools, planner.error)
  const pLine =
    `          planner:  [${planner.predicted_tools.join(', ')}]` +
    `  recall=${pScore.tool_recall.toFixed(2)} precision=${pScore.tool_precision.toFixed(2)}` +
    (pScore.pass ? ' ✓' : '')
  return `${oLine}\n${pLine}`
}

interface CompareReport {
  oracle_results: EvalResult[]
  planner_results: EvalResult[] | null
  oracle_aggregate: ReturnType<typeof aggregateResults>
  planner_aggregate: ReturnType<typeof aggregateResults> | null
}

async function runCompare(opts: { dryRun: boolean }): Promise<CompareReport> {
  const goldenSet = loadGoldenSet()

  const oracleResults: EvalResult[] = []
  const plannerResults: EvalResult[] = []

  // Lazy-load LLM-bound module so --dry-run never imports server-only deps.
  const { callPipelinePlanner } = opts.dryRun
    ? { callPipelinePlanner: null }
    : await import('@/lib/pipeline/pipeline_planner')

  const modelId = process.env.PLANNER_MODEL_ID ?? 'meta/llama-3.1-8b-instruct'
  const chartId = process.env.CHART_ID ?? 'test-native'

  const lines: string[] = []

  for (const entry of goldenSet.entries) {
    // ── oracle side ────────────────────────────────────────────────────────
    const oracleSide: SideResult = {
      side: 'oracle',
      predicted_tools: entry.expected_tools,
    }
    oracleResults.push(scoreEntry(entry, oracleSide.predicted_tools, oracleSide.error))

    // ── planner side ───────────────────────────────────────────────────────
    let plannerSide: SideResult | null = null
    if (!opts.dryRun && callPipelinePlanner) {
      try {
        const outcome = await callPipelinePlanner(entry.query, [], modelId, chartId)
        // W4: planner returns a 3-way outcome; eval only scores the happy-path plan.
        const plan = outcome.outcome === 'plan' ? outcome.plan : { tool_calls: [] as Array<{ tool_name: string }> }
        plannerSide = {
          side: 'planner',
          predicted_tools: plan.tool_calls.map(tc => tc.tool_name),
        }
      } catch (err) {
        plannerSide = {
          side: 'planner',
          predicted_tools: [],
          error: err instanceof Error ? err.message : String(err),
        }
      }
      plannerResults.push(scoreEntry(entry, plannerSide.predicted_tools, plannerSide.error))
    }

    lines.push(formatRow(entry, oracleSide, plannerSide))
    lines.push('')
  }

  const oracleAgg = aggregateResults(oracleResults)
  const plannerAgg = opts.dryRun ? null : aggregateResults(plannerResults)

  // ── side-by-side body to stdout ──────────────────────────────────────────
  process.stdout.write(lines.join('\n'))

  // ── aggregate footer ─────────────────────────────────────────────────────
  const footer: string[] = []
  footer.push('AGGREGATE')
  footer.push(
    `  oracle    avg_recall=${oracleAgg.avg_tool_recall.toFixed(2)}` +
      `  avg_precision=${oracleAgg.avg_tool_precision.toFixed(2)}` +
      `  pass_rate=${oracleAgg.pass_rate.toFixed(2)}`,
  )
  if (plannerAgg) {
    const met =
      plannerAgg.avg_tool_recall >= RECALL_THRESHOLD &&
      plannerAgg.avg_tool_precision >= PRECISION_THRESHOLD
    footer.push(
      `  planner   avg_recall=${plannerAgg.avg_tool_recall.toFixed(2)}` +
        `  avg_precision=${plannerAgg.avg_tool_precision.toFixed(2)}` +
        `  pass_rate=${plannerAgg.pass_rate.toFixed(2)}` +
        (met ? '  ← THRESHOLD MET' : '  ← THRESHOLD NOT MET'),
    )
  } else {
    footer.push('  planner   (skipped — --dry-run)')
  }
  process.stdout.write('\n' + footer.join('\n') + '\n')

  return {
    oracle_results: oracleResults,
    planner_results: opts.dryRun ? null : plannerResults,
    oracle_aggregate: oracleAgg,
    planner_aggregate: plannerAgg,
  }
}

async function main(): Promise<void> {
  const dryRun = process.argv.includes('--dry-run')
  const report = await runCompare({ dryRun })

  // Exit 0 only when the planner hits the published thresholds (or when dry-run,
  // which is informational only and always exits 0 on a clean run).
  if (dryRun) {
    process.exit(0)
  }
  const ok =
    !!report.planner_aggregate &&
    report.planner_aggregate.avg_tool_recall >= RECALL_THRESHOLD &&
    report.planner_aggregate.avg_tool_precision >= PRECISION_THRESHOLD
  process.exit(ok ? 0 : 1)
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
