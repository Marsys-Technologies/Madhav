/**
 * modes.ts — the four §9.7 measurement modes (W-28 cache, W-29 concurrency, W-30
 * QoS/backpressure, W-31 SLO-per-query-class), each a pure function over a `LoadTarget`
 * + `sendOne`. No CLI parsing, no process.exit, no server lifecycle here — `harness.ts`
 * owns all of that; this module is what `lib.test.ts` unit-tests against the local
 * mock server.
 */
import { BATTERY_CHARTS, BATTERY_QUERIES } from '../w5_battery/queries'
import { sendOne } from './http_client'
import { cacheHitRate, successRate, summarizeLatencies } from './stats'
import type {
  CacheHitRateReport,
  ConcurrencyCapacityReport,
  ConcurrencyLevelResult,
  LoadTarget,
  LoadThresholds,
  QosBackpressureReport,
  RequestResult,
  SloQueryClassResult,
  SloReport,
} from './types'

// ── W-28: cache hit-rate ──────────────────────────────────────────────────────────

/**
 * Fire the SAME request body `n` times, sequentially (deliberately — this mode wants
 * to observe repeat-identical-request cache behavior, not concurrency; that is W-29's
 * job). The first call is expected to be a genuine miss; every subsequent call SHOULD
 * hit if the target's deterministic response cache (W-28) is working.
 */
export async function measureCacheHitRate(
  target: LoadTarget,
  thresholds: LoadThresholds,
  opts: { n?: number; body?: Record<string, unknown> } = {},
): Promise<CacheHitRateReport> {
  const n = opts.n ?? 20
  const body = opts.body ?? { query: BATTERY_QUERIES[0].query, chart_id: BATTERY_CHARTS[0].chart_id, family: BATTERY_QUERIES[0].family }

  const results: RequestResult[] = []
  for (let i = 0; i < n; i++) {
    results.push(await sendOne(target, body))
  }

  const ok = results.filter((r) => r.ok)
  const hits = ok.filter((r) => r.cacheHit)
  const misses = ok.filter((r) => !r.cacheHit)
  const errors = results.length - ok.length
  const hitRate = cacheHitRate(results)

  return {
    n,
    hits: hits.length,
    misses: misses.length,
    errors,
    hitRate,
    missLatency: misses.length > 0 ? summarizeLatencies(misses.map((r) => r.latencyMs)) : null,
    hitLatency: hits.length > 0 ? summarizeLatencies(hits.map((r) => r.latencyMs)) : null,
    pass: hitRate >= thresholds.minCacheHitRate,
  }
}

// ── W-29: concurrency capacity ────────────────────────────────────────────────────

/**
 * Ramp concurrency through `levels` (default a geometric ramp), firing
 * `requestsPerLevel` DISTINCT (non-cache-colliding) requests per level via
 * `Promise.all`, and recording success rate + latency percentiles at each level.
 */
export async function measureConcurrencyCapacity(
  target: LoadTarget,
  thresholds: LoadThresholds,
  opts: { levels?: readonly number[]; requestsPerLevel?: number } = {},
): Promise<ConcurrencyCapacityReport> {
  const levels = opts.levels ?? [1, 2, 4, 8, 16, 32]
  const requestsPerLevel = opts.requestsPerLevel ?? 20

  const levelResults: ConcurrencyLevelResult[] = []
  let uniqueCounter = 0

  for (const concurrency of levels) {
    const batches = Math.ceil(requestsPerLevel / concurrency)
    const allResults: RequestResult[] = []
    for (let b = 0; b < batches; b++) {
      const batchSize = Math.min(concurrency, requestsPerLevel - allResults.length)
      const calls = Array.from({ length: batchSize }, () => {
        uniqueCounter++
        const chart = BATTERY_CHARTS[uniqueCounter % BATTERY_CHARTS.length]
        const query = BATTERY_QUERIES[uniqueCounter % BATTERY_QUERIES.length]
        // Unique nonce keeps each request distinct so this mode measures raw
        // concurrency/throughput behavior, not incidentally re-exercising W-28's cache.
        return sendOne(target, { query: query.query, chart_id: chart.chart_id, family: query.family, nonce: uniqueCounter })
      })
      allResults.push(...(await Promise.all(calls)))
    }

    levelResults.push({
      concurrency,
      requests: allResults.length,
      successes: allResults.filter((r) => r.ok).length,
      errors: allResults.filter((r) => !r.ok).length,
      successRate: successRate(allResults),
      latency: summarizeLatencies(allResults.map((r) => r.latencyMs)),
    })
  }

  const first = levelResults[0]
  const last = levelResults[levelResults.length - 1]
  const latencyDegradationFactor = first && first.latency.p95 > 0 ? last.latency.p95 / first.latency.p95 : 0

  return {
    levels: levelResults,
    successRateAtMaxConcurrency: last?.successRate ?? 0,
    latencyDegradationFactor,
    pass:
      (last?.successRate ?? 0) >= thresholds.minSuccessRateAtMaxConcurrency &&
      latencyDegradationFactor <= thresholds.maxLatencyDegradationFactor,
  }
}

// ── W-30: QoS / backpressure ──────────────────────────────────────────────────────

/**
 * Fire a burst of requests from multiple distinct principals, split across the two
 * named priority classes ('interactive' / 'background'), at a volume deliberately
 * chosen to exceed the target's own admission capacity — then classify every
 * response into one of: succeeded / honestlyRefused (explicit 429/503 +
 * `honest_refusal` marker) / silentlyDegraded (200 but missing the fields a normal
 * successful response carries — the "thinned quality" failure mode the doctrine
 * explicitly forbids) / otherError (anything else, e.g. timeout/5xx without the
 * honest-refusal marker).
 *
 * If the target implements NO QoS/backpressure mechanism at all, every over-capacity
 * request will either hang/timeout (otherError) or come back thinned — this mode
 * reports that honestly via `qosMechanismObserved: 'no_qos_signal_detected'` rather
 * than assuming a queue exists.
 */
export async function measureQosBackpressure(
  target: LoadTarget,
  thresholds: LoadThresholds,
  opts: { principals?: number; requestsPerPrincipal?: number } = {},
): Promise<QosBackpressureReport> {
  const principals = opts.principals ?? 8
  const requestsPerPrincipal = opts.requestsPerPrincipal ?? 6

  const calls: Promise<RequestResult>[] = []
  for (let p = 0; p < principals; p++) {
    const priorityClass = p % 2 === 0 ? 'interactive' : 'background'
    for (let r = 0; r < requestsPerPrincipal; r++) {
      const chart = BATTERY_CHARTS[r % BATTERY_CHARTS.length]
      const query = BATTERY_QUERIES[(p * requestsPerPrincipal + r) % BATTERY_QUERIES.length]
      calls.push(
        sendOne(target, {
          query: query.query,
          chart_id: chart.chart_id,
          family: query.family,
          principalId: `principal-${p}`,
          priorityClass,
          nonce: p * 1000 + r,
        }),
      )
    }
  }
  // Fire the whole burst simultaneously — the contention scenario this mode measures.
  const results = await Promise.all(calls)

  const succeeded = results.filter((r) => r.ok)
  const honestlyRefused = results.filter((r) => !r.ok && r.honestlyRefused === true)
  // "Silently degraded" = a 200 that is missing the response's own declared
  // query_class field — the one machine-checkable signal this generic harness has
  // for "this looks thinned" without knowing the target's full response schema.
  const silentlyDegraded = succeeded.filter((r) => r.queryClass === undefined)
  const otherErrors = results.filter((r) => !r.ok && r.honestlyRefused !== true)

  const byClass: QosBackpressureReport['byPriorityClass'] = {
    interactive: { requests: 0, succeeded: 0, honestlyRefused: 0, successRate: 0 },
    background: { requests: 0, succeeded: 0, honestlyRefused: 0, successRate: 0 },
  }
  for (const cls of ['interactive', 'background'] as const) {
    const rows = results.filter((r) => r.priorityClass === cls)
    const rowsOk = rows.filter((r) => r.ok)
    byClass[cls] = {
      requests: rows.length,
      succeeded: rowsOk.length,
      honestlyRefused: rows.filter((r) => r.honestlyRefused === true).length,
      successRate: rows.length > 0 ? rowsOk.length / rows.length : 0,
    }
  }

  const interactivePrioritizedOverBackground =
    byClass.interactive.requests > 0 && byClass.background.requests > 0
      ? byClass.interactive.successRate >= byClass.background.successRate
      : null

  const attemptable = results.length - succeeded.length
  const honestDegradationRate = attemptable === 0 ? 1 : honestlyRefused.length / attemptable

  return {
    totalRequests: results.length,
    succeeded: succeeded.length,
    honestlyRefused: honestlyRefused.length,
    silentlyDegraded: silentlyDegraded.length,
    otherErrors: otherErrors.length,
    honestDegradationRate,
    byPriorityClass: byClass,
    interactivePrioritizedOverBackground,
    qosMechanismObserved: honestlyRefused.length > 0 ? 'real_dispatch_queue' : 'no_qos_signal_detected',
    pass: silentlyDegraded.length === 0 && honestDegradationRate >= thresholds.minHonestDegradationRate,
  }
}

// ── W-31: SLO per query class ─────────────────────────────────────────────────────

/**
 * Run the existing w5_battery query corpus (all 30 queries × both charts = 60 combos)
 * at the given concurrency, group latencies by `family` (the query-class axis this
 * repo already uses — `queries.ts`), and compare each family's p95 against the
 * configured budget.
 */
export async function measureSloPerQueryClass(
  target: LoadTarget,
  thresholds: LoadThresholds,
  opts: { concurrency?: number } = {},
): Promise<SloReport> {
  const concurrency = opts.concurrency ?? 8
  const combos: { query: (typeof BATTERY_QUERIES)[number]; chart: (typeof BATTERY_CHARTS)[number] }[] = []
  for (const query of BATTERY_QUERIES) for (const chart of BATTERY_CHARTS) combos.push({ query, chart })

  const results: RequestResult[] = []
  for (let i = 0; i < combos.length; i += concurrency) {
    const batch = combos.slice(i, i + concurrency)
    const batchResults = await Promise.all(
      batch.map(({ query, chart }) =>
        sendOne(
          target,
          { query: query.query, chart_id: chart.chart_id, family: query.family },
          { queryClass: query.family },
        ),
      ),
    )
    results.push(...batchResults)
  }

  const families = Array.from(new Set(BATTERY_QUERIES.map((q) => q.family))).sort()
  const byQueryClass: SloQueryClassResult[] = families.map((family) => {
    const rows = results.filter((r) => (r.queryClass ?? 'unknown') === family)
    const latency = summarizeLatencies(rows.map((r) => r.latencyMs))
    return {
      queryClass: family,
      latency,
      successRate: successRate(rows),
      withinBudget: latency.p95 <= thresholds.maxP95LatencyMs,
    }
  })

  return {
    concurrency,
    byQueryClass,
    overallPass: byQueryClass.every((r) => r.withinBudget && r.successRate >= thresholds.minSuccessRateAtMaxConcurrency),
    baselineComparisonNote:
      'W5_BATTERY_BASELINE_v1_0.md records routing-accuracy/mapped-fraction/isolation ' +
      'metrics for a synchronous in-process compile path, not HTTP latency percentiles. ' +
      'There is no latency figure in that baseline to diff against — this report is a ' +
      'fresh latency measurement, not a regression comparison, until a real load-test ' +
      'baseline exists (Task 13 residual).',
  }
}
