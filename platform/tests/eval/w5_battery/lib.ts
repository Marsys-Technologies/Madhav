/**
 * lib.ts — W5 Lane L10 readback + tool-selection battery, pure scoring/execution core.
 *
 * Extends the existing baseline-probe / rubric-battery pattern rather than inventing a
 * new one:
 *   - tool-SELECTION scoring is the same recall/precision-over-a-labeled-set shape as
 *     `platform/tests/eval/planner_smoke_runner.ts` (W2-EVAL-B), adapted to the
 *     deterministic Vidhi router instead of the LLM planner (see §2 of the companion
 *     BASELINE artifact for why: the LLM planner path needs live model credentials and
 *     is explicitly out of scope for a local/dev battery run per this lane's boundary;
 *     the deterministic `classifyScope` → `compileFloorForPlan` router is the actual W4
 *     "One Planner" production path and is fully exercisable locally, no network/DB);
 *   - "READBACK" is a literal port of `RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md
 *     §B.1`'s baseline-probe methodology (`BASELINE_PROBES.md`): capture a served
 *     artifact's shape/hash now, diff future runs against it — here the "served
 *     artifact" is the compiled Vidhi contract (floor + machine_band + completeness
 *     receipt), the actual W4/W5 unit of work, rather than a raw MCP tool response
 *     (calling live MCP tools against production is explicitly out of this lane's scope
 *     — see the artifact's boundary note);
 *   - the concurrency/isolation check targets the exact class of bug this campaign's
 *     docs treat as the standing cautionary tale (LCA-17 cross-chart substitution,
 *     referenced throughout STATE.md/CURRENT_STATE): the W-28 floor-precompilation
 *     cache (`platform/src/lib/vidhi/floor_cache.ts`) caches a chart-AGNOSTIC core and
 *     substitutes the real chart_id per call — exactly the shared-mutable-state shape
 *     where a concurrency bug could leak one chart's id into another chart's compiled
 *     tool_args. This module asserts that never happens under concurrent execution.
 */
import { createHash } from 'node:crypto'
import { classifyScope, type ScopeTuple as ClassifierScopeTuple } from '@/lib/vidhi/scope_classifier'
import {
  classifierIntentToCompilerIntent,
  classifierTupleToCompilerTuple,
  compileFloorForPlan,
} from '@/lib/pipeline/compiled_floor_adapter'
import { compileContractCached } from '@/lib/vidhi/floor_cache'
import { defaultRegistry } from '@/lib/vidhi/compiler'
import { emitCompletenessReceipt, type CompletenessReceipt } from '@/lib/vidhi/completeness_receipt'
import type { CompiledContract } from '@/lib/vidhi/types'
import type { BatteryQuery } from './queries'

// ── Stable hashing (readback fingerprints) ──────────────────────────────────────

/** Key-sorted JSON so identical content hashes identically regardless of object key order. */
export function stableStringify(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null'
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`
  const obj = value as Record<string, unknown>
  const keys = Object.keys(obj).sort()
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(obj[k])}`).join(',')}}`
}

export function contractFingerprint(contract: CompiledContract): string {
  return createHash('sha256').update(stableStringify(contract)).digest('hex').slice(0, 24)
}

// ── One battery entry, run for one (query, chart) pair ──────────────────────────

export interface BatteryRunResult {
  readonly id: string
  readonly family: BatteryQuery['family']
  readonly chart_label: string
  readonly chart_id: string
  readonly query: string
  readonly classified_intent: string
  readonly confidence: number
  readonly routing_correct: boolean
  readonly compiled_intent: string
  readonly floor_item_total: number
  readonly mapped_primitive_count: number
  readonly unmapped_primitive_count: number
  readonly dark_count: number
  readonly empty_count: number
  readonly compile_failed: boolean
  readonly fingerprint: string
  /** True iff every substituted tool_arg literally carrying a chart_id equals `chart_id` —
   *  the cross-chart-contamination guard (LCA-17-style check). */
  readonly chart_isolation_ok: boolean
  readonly latency_ms: number
}

const CHART_ID_ARG_KEYS = ['chart_id', 'chartId', 'chart']

/** Scan a compiled contract's tool_args for any value that looks like a UUID and assert
 *  it is either the expected chart_id or not a chart-id-shaped value at all. Catches the
 *  shared-cache-object mutation/leak failure mode directly, not just "the reported
 *  chart_id field is right" (which a shallow check could pass while a stale nested value
 *  leaked from a concurrently-substituted cache entry). */
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function checkChartIsolation(contract: CompiledContract, expectedChartId: string): boolean {
  for (const item of [...contract.floor, ...contract.machine_band]) {
    for (const [k, v] of Object.entries(item.tool_args)) {
      if (typeof v !== 'string') continue
      const looksLikeChartId = CHART_ID_ARG_KEYS.includes(k) || UUID_RE.test(v)
      if (looksLikeChartId && UUID_RE.test(v) && v !== expectedChartId) return false
    }
  }
  return true
}

export function runOne(entry: BatteryQuery, chart: { label: string; chart_id: string }): BatteryRunResult {
  const t0 = performance.now()
  const classification = classifyScope(entry.query)
  const classifierTuple: ClassifierScopeTuple = classification.scope_tuple
  const compiledIntent = classifierIntentToCompilerIntent(classifierTuple)
  const routing_correct = compiledIntent === entry.expected_intent

  const floorResult = compileFloorForPlan(classifierTuple, chart.chart_id)

  const compilerTuple = classifierTupleToCompilerTuple(classifierTuple)
  let contract: CompiledContract
  let compile_failed = false
  try {
    contract = compileContractCached(compilerTuple, defaultRegistry(), chart.chart_id)
  } catch {
    compile_failed = true
    contract = compileContractCached(
      { ...compilerTuple, intent: 'general_synthesis' },
      defaultRegistry(),
      chart.chart_id,
    )
  }

  const receipt: CompletenessReceipt = emitCompletenessReceipt(contract)
  const latency_ms = performance.now() - t0

  return {
    id: entry.id,
    family: entry.family,
    chart_label: chart.label,
    chart_id: chart.chart_id,
    query: entry.query,
    classified_intent: classification.scope_tuple.intent,
    confidence: classification.confidence,
    routing_correct,
    compiled_intent: compiledIntent,
    floor_item_total: receipt.coverage.floor_item_total,
    mapped_primitive_count: floorResult.mappedPrimitives.length,
    unmapped_primitive_count: floorResult.unmappedPrimitives.length,
    dark_count: receipt.coverage.dark,
    empty_count: receipt.coverage.empty,
    compile_failed: compile_failed || floorResult.compileFailed,
    fingerprint: contractFingerprint(contract),
    chart_isolation_ok: checkChartIsolation(contract, chart.chart_id),
    latency_ms,
  }
}

// ── Aggregation ──────────────────────────────────────────────────────────────────

export interface FamilyAggregate {
  readonly family: string
  readonly n: number
  readonly routing_accuracy: number
  readonly avg_mapped_fraction: number
  readonly avg_dark_count: number
  readonly avg_confidence: number
}

export function aggregateByFamily(results: readonly BatteryRunResult[]): FamilyAggregate[] {
  const families = Array.from(new Set(results.map((r) => r.family))).sort()
  return families.map((family) => {
    const rows = results.filter((r) => r.family === family)
    const n = rows.length
    const routing_accuracy = rows.filter((r) => r.routing_correct).length / n
    const avg_mapped_fraction =
      rows.reduce((acc, r) => {
        const total = r.mapped_primitive_count + r.unmapped_primitive_count
        return acc + (total === 0 ? 0 : r.mapped_primitive_count / total)
      }, 0) / n
    const avg_dark_count = rows.reduce((acc, r) => acc + r.dark_count, 0) / n
    const avg_confidence = rows.reduce((acc, r) => acc + r.confidence, 0) / n
    return { family, n, routing_accuracy, avg_mapped_fraction, avg_dark_count, avg_confidence }
  })
}

export interface OverallAggregate {
  readonly n: number
  readonly routing_accuracy: number
  readonly chart_isolation_violations: number
  readonly compile_failures: number
}

export function aggregateOverall(results: readonly BatteryRunResult[]): OverallAggregate {
  const n = results.length
  return {
    n,
    routing_accuracy: results.filter((r) => r.routing_correct).length / n,
    chart_isolation_violations: results.filter((r) => !r.chart_isolation_ok).length,
    compile_failures: results.filter((r) => r.compile_failed).length,
  }
}

/** Readback: diff a set of results against previously-recorded fingerprints (baseline
 *  keyed by `${id}|${chart_label}`). Returns the ids whose compiled contract changed. */
export function readbackDiff(
  results: readonly BatteryRunResult[],
  baseline: ReadonlyMap<string, string>,
): string[] {
  const changed: string[] = []
  for (const r of results) {
    const key = `${r.id}|${r.chart_label}`
    const prior = baseline.get(key)
    if (prior !== undefined && prior !== r.fingerprint) changed.push(key)
  }
  return changed
}

export function fingerprintMap(results: readonly BatteryRunResult[]): Map<string, string> {
  const m = new Map<string, string>()
  for (const r of results) m.set(`${r.id}|${r.chart_label}`, r.fingerprint)
  return m
}
