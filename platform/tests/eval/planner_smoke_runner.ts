#!/usr/bin/env tsx
/**
 * planner_smoke_runner.ts — W2-EVAL-B AC.V.1
 *
 * CLI scorer for `callLlmPlanner` against `planner_golden_set.json`. Computes
 * per-entry tool_recall / tool_precision plus required/forbidden gate
 * outcomes, aggregates them, and exits non-zero when the macro-averaged
 * thresholds are not met.
 *
 *   tool_recall    = |predicted ∩ expected| / |expected|
 *   tool_precision = |predicted ∩ expected| / |predicted|
 *
 * Exit code 0 iff `avg_tool_recall ≥ 0.80 AND avg_tool_precision ≥ 0.90`.
 * JSON report to stdout, human-readable summary to stderr.
 *
 * Env:
 *   PLANNER_MODEL_ID  (default: nvidia/llama-3.3-nemotron-super-49b-v1)
 *   CHART_ID          (default: test-native)
 *
 * Usage: npx tsx --conditions=react-server platform/tests/eval/planner_smoke_runner.ts
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

// ────────────────────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────────────────────

export interface GoldenEntry {
  id: string
  query: string
  query_class: string
  category: string
  expected_tools: string[]
  required_tools: string[]
  forbidden_tools: string[]
  required_asset_ids?: string[]
  notes?: string
}

export interface GoldenSet {
  entries: GoldenEntry[]
}

export interface EvalResult {
  id: string
  query: string
  expected_tools: string[]
  predicted_tools: string[]
  required_tools: string[]
  forbidden_tools: string[]
  tool_recall: number
  tool_precision: number
  required_hit: boolean
  forbidden_violation: boolean
  pass: boolean
  error?: string
  asset_bundle_ids?: string[]
  asset_bundle_recall?: number
  asset_bundle_floor_ok?: boolean
}

export interface AggregateResult {
  total: number
  passed: number
  failed: number
  avg_tool_recall: number
  avg_tool_precision: number
  forbidden_violations: number
  required_misses: number
  pass_rate: number
  avg_asset_bundle_recall?: number
  asset_bundle_floor_violations?: number
}

export type PlannerFn = (
  query: string,
  history: Array<{ role: string; content: string }>,
  modelId: string,
  chartId: string,
) => Promise<{
  tool_calls: Array<{ tool_name: string }>
  asset_bundle?: Array<{ asset_id: string }>
}>

// ────────────────────────────────────────────────────────────────────────────
// Thresholds (must match tests/eval/README.md)
// ────────────────────────────────────────────────────────────────────────────

export const RECALL_THRESHOLD = 0.8
export const PRECISION_THRESHOLD = 0.9

// ────────────────────────────────────────────────────────────────────────────
// Pure scoring helpers (testable without LLM)
// ────────────────────────────────────────────────────────────────────────────

export function scoreEntry(
  entry: GoldenEntry,
  predicted: string[],
  error?: string,
  predictedAssets?: string[],
): EvalResult {
  const expectedSet = new Set(entry.expected_tools)
  const predictedSet = new Set(predicted)
  const intersectionCount = Array.from(predictedSet).filter(t => expectedSet.has(t)).length

  const tool_recall =
    entry.expected_tools.length === 0
      ? 1
      : intersectionCount / entry.expected_tools.length

  const tool_precision =
    predictedSet.size === 0
      ? entry.expected_tools.length === 0
        ? 1
        : 0
      : intersectionCount / predictedSet.size

  const required_hit = entry.required_tools.every(t => predictedSet.has(t))
  const forbidden_violation = entry.forbidden_tools.some(t => predictedSet.has(t))

  const pass =
    !error &&
    tool_recall >= RECALL_THRESHOLD &&
    tool_precision >= PRECISION_THRESHOLD &&
    required_hit &&
    !forbidden_violation

  let asset_bundle_ids: string[] | undefined
  let asset_bundle_recall: number | undefined
  let asset_bundle_floor_ok: boolean | undefined

  if (predictedAssets !== undefined) {
    asset_bundle_ids = predictedAssets
    const floor = ['FORENSIC', 'CGM']
    asset_bundle_floor_ok = floor.every(id => predictedAssets.includes(id))
    const required = entry.required_asset_ids ?? floor
    const hit = required.filter(id => predictedAssets.includes(id)).length
    asset_bundle_recall = required.length > 0 ? hit / required.length : 1
  }

  return {
    id: entry.id,
    query: entry.query,
    expected_tools: entry.expected_tools,
    predicted_tools: Array.from(predictedSet),
    required_tools: entry.required_tools,
    forbidden_tools: entry.forbidden_tools,
    tool_recall,
    tool_precision,
    required_hit,
    forbidden_violation,
    pass,
    error,
    asset_bundle_ids,
    asset_bundle_recall,
    asset_bundle_floor_ok,
  }
}

export function aggregateResults(results: EvalResult[]): AggregateResult {
  const total = results.length
  const passed = results.filter(r => r.pass).length
  const sumRecall = results.reduce((s, r) => s + r.tool_recall, 0)
  const sumPrecision = results.reduce((s, r) => s + r.tool_precision, 0)

  const assetScored = results.filter(r => r.asset_bundle_recall !== undefined)
  const avg_asset_bundle_recall = assetScored.length
    ? assetScored.reduce((s, r) => s + (r.asset_bundle_recall ?? 0), 0) / assetScored.length
    : undefined
  const asset_bundle_floor_violations = assetScored.length
    ? assetScored.filter(r => r.asset_bundle_floor_ok === false).length
    : undefined

  return {
    total,
    passed,
    failed: total - passed,
    avg_tool_recall: total ? sumRecall / total : 0,
    avg_tool_precision: total ? sumPrecision / total : 0,
    forbidden_violations: results.filter(r => r.forbidden_violation).length,
    required_misses: results.filter(r => !r.required_hit).length,
    pass_rate: total ? passed / total : 0,
    avg_asset_bundle_recall,
    asset_bundle_floor_violations,
  }
}

export function thresholdsMet(aggregate: AggregateResult): boolean {
  return (
    aggregate.avg_tool_recall >= RECALL_THRESHOLD &&
    aggregate.avg_tool_precision >= PRECISION_THRESHOLD
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Runner — accepts an injectable planner so the regression gate can pass a
// fixture-backed mock instead of `callLlmPlanner`.
// ────────────────────────────────────────────────────────────────────────────

export async function runSmoke(
  goldenSet: GoldenSet,
  plannerFn: PlannerFn,
  modelId: string,
  chartId: string,
): Promise<{ results: EvalResult[]; aggregate: AggregateResult }> {
  const results: EvalResult[] = []
  for (const entry of goldenSet.entries) {
    let predicted: string[] = []
    let predictedAssets: string[] | undefined
    let error: string | undefined
    try {
      const plan = await plannerFn(entry.query, [], modelId, chartId)
      predicted = plan.tool_calls.map(tc => tc.tool_name)
      predictedAssets = plan.asset_bundle?.map(a => a.asset_id)
    } catch (err) {
      error = err instanceof Error ? err.message : String(err)
    }
    results.push(scoreEntry(entry, predicted, error, predictedAssets))
  }
  return { results, aggregate: aggregateResults(results) }
}

// ────────────────────────────────────────────────────────────────────────────
// Filesystem loader (CLI-only; tests construct GoldenSet inline)
// ────────────────────────────────────────────────────────────────────────────

export function loadGoldenSet(filePath?: string): GoldenSet {
  const here = path.dirname(fileURLToPath(import.meta.url))
  const resolved = filePath ?? path.resolve(here, 'planner_golden_set.json')
  return JSON.parse(readFileSync(resolved, 'utf-8')) as GoldenSet
}

// ────────────────────────────────────────────────────────────────────────────
// Human-readable summary
// ────────────────────────────────────────────────────────────────────────────

export function formatSummary(aggregate: AggregateResult, results: EvalResult[]): string {
  const lines: string[] = []
  lines.push('=== Planner Smoke Eval Summary ===')
  lines.push(`Total:                ${aggregate.total}`)
  lines.push(`Passed:               ${aggregate.passed}`)
  lines.push(`Failed:               ${aggregate.failed}`)
  lines.push(`Pass rate:            ${aggregate.pass_rate.toFixed(3)}`)
  lines.push(
    `Avg tool_recall:      ${aggregate.avg_tool_recall.toFixed(3)} (threshold ${RECALL_THRESHOLD.toFixed(2)})`,
  )
  lines.push(
    `Avg tool_precision:   ${aggregate.avg_tool_precision.toFixed(3)} (threshold ${PRECISION_THRESHOLD.toFixed(2)})`,
  )
  lines.push(`Forbidden violations: ${aggregate.forbidden_violations}`)
  lines.push(`Required misses:      ${aggregate.required_misses}`)

  if (aggregate.avg_asset_bundle_recall !== undefined) {
    lines.push('')
    lines.push('ASSET BUNDLE RECALL')
    lines.push(`  avg_asset_bundle_recall: ${aggregate.avg_asset_bundle_recall.toFixed(3)}   (threshold: ≥ 0.90)`)
    lines.push(`  floor_violations (missing FORENSIC or CGM): ${aggregate.asset_bundle_floor_violations ?? 0}`)
  }

  const failures = results.filter(r => !r.pass)
  if (failures.length > 0) {
    lines.push('')
    lines.push('--- Failures ---')
    for (const f of failures) {
      const reasons: string[] = []
      if (f.error) reasons.push(`error="${f.error}"`)
      if (f.tool_recall < RECALL_THRESHOLD) reasons.push(`recall=${f.tool_recall.toFixed(2)}`)
      if (f.tool_precision < PRECISION_THRESHOLD) reasons.push(`precision=${f.tool_precision.toFixed(2)}`)
      if (!f.required_hit) reasons.push('required_miss')
      if (f.forbidden_violation) reasons.push('forbidden_violation')
      lines.push(
        `  ${f.id}  [${reasons.join(' ')}]  predicted=[${f.predicted_tools.join(', ')}]`,
      )
    }
  }

  lines.push('')
  lines.push(thresholdsMet(aggregate) ? 'THRESHOLDS MET ✓' : 'THRESHOLDS NOT MET ✗')
  return lines.join('\n')
}

// ────────────────────────────────────────────────────────────────────────────
// CLI entrypoint — dynamic import keeps server-only deps out of vitest
// ────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const modelId = process.env.PLANNER_MODEL_ID ?? 'gemini-2.5-flash'
  const chartId = process.env.CHART_ID ?? 'test-native'

  // Lazy import: pulls server-only deps (resolver) only at CLI runtime.
  const { callPipelinePlanner } = await import('@/lib/pipeline/pipeline_planner')

  // W4: unwrap the 3-way PlannerOutcome to the plan shape PlannerFn expects;
  // non-'plan' outcomes (clarification/fault) score as an empty plan for eval.
  const plannerFn: PlannerFn = async (query, history, modelIdArg, chartIdArg) => {
    const outcome = await callPipelinePlanner(query, history, modelIdArg, chartIdArg)
    return outcome.outcome === 'plan' ? outcome.plan : { tool_calls: [] }
  }

  const goldenSet = loadGoldenSet()
  const { results, aggregate } = await runSmoke(goldenSet, plannerFn, modelId, chartId)

  process.stdout.write(JSON.stringify({ aggregate, results }, null, 2) + '\n')
  process.stderr.write(formatSummary(aggregate, results) + '\n')

  process.exit(thresholdsMet(aggregate) ? 0 : 1)
}

const invokedAsCli =
  typeof process.argv[1] === 'string' &&
  import.meta.url === pathToFileURL(process.argv[1]).href

if (invokedAsCli) {
  main().catch(err => {
    console.error(err)
    process.exit(1)
  })
}
