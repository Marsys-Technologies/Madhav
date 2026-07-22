/**
 * types.ts — W6 load-generation harness, shared types.
 *
 * Task 12 (this harness) builds and dry-run-verifies the four-point load test named
 * `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` §9 tracking register as "§9.7" (W-28..W-31).
 * Running it for real against the deployed `amjis-mcp`/`amjis-web` connector is a
 * separate, later task (named residual for a human operator with a live credential) —
 * see `harness.ts`'s banner for the full boundary note.
 */

/** One HTTP target this harness fires requests against. `local` mode never leaves the
 *  process (an in-process mock server per `mock_server.ts`); a real target is a bare
 *  base URL + path, with optional auth header supplied out-of-band via env var — this
 *  harness never embeds or requests a production credential itself. */
export interface LoadTarget {
  readonly baseUrl: string
  readonly path: string
  readonly method: 'GET' | 'POST'
  readonly headers: Record<string, string>
  /** Dot-path into the parsed JSON response body where the cache-hit signal lives.
   *  Defaults to `served_from_cache` — the actual field name carried on `ToolBundle`
   *  (`platform/src/lib/retrieval/shared_types.ts`) and asserted throughout
   *  `platform/src/lib/cache/with_cache.ts` / its tests. This harness reuses that
   *  field rather than inventing a new cache-hit signal. */
  readonly cacheHitField: string
  /** Per-request timeout in ms before the harness gives up and counts the call as a
   *  timeout error (distinct from a server-returned error status). */
  readonly timeoutMs: number
}

export interface RequestResult {
  readonly ok: boolean
  /** HTTP status, or -1 if the request never got a response (network error/timeout). */
  readonly status: number
  readonly latencyMs: number
  readonly cacheHit: boolean
  /** `query_class` / family the target reported back, when available (SLO mode keys
   *  its per-class percentile buckets off this — falls back to the caller-supplied
   *  label if the response doesn't echo one). */
  readonly queryClass?: string
  readonly principalId?: string
  readonly priorityClass?: 'interactive' | 'background'
  /** Set when the harness itself detected the honest-degradation signal — an explicit
   *  refusal (429/503 + a machine-readable reason) rather than a 200 with thinned
   *  content. `undefined` when not applicable (non-QoS modes). */
  readonly honestlyRefused?: boolean
  readonly error?: string
}

export interface LatencyStats {
  readonly n: number
  readonly p50: number
  readonly p95: number
  readonly p99: number
  readonly mean: number
  readonly min: number
  readonly max: number
}

/**
 * Threshold configuration for pass/fail gating.
 *
 * IMPORTANT — per the master brief's ground truth (confirmed by search, not assumed):
 * NO concrete numeric pass/fail threshold (target RPS, p95 latency budget, cache
 * hit-rate %) is written down anywhere in the source doctrine for §9.7. The doctrine
 * describes categories (cache/concurrency/QoS/quality-under-load), not numbers. Every
 * field below is therefore an explicit, labeled, OVERRIDABLE default — a reasonable
 * placeholder pending a native ruling, not a fact derived from any brief. A caller
 * MUST be able to see, in the emitted report, that these are configuration inputs and
 * not asserted doctrine.
 */
export interface LoadThresholds {
  /** W-28 cache hit-rate: minimum acceptable fraction of repeat-identical-request
   *  probes served from cache. NO SOURCE-DOCUMENTED THRESHOLD FOUND — placeholder. */
  readonly minCacheHitRate: number
  /** W-29 concurrency capacity: minimum acceptable success rate at the harness's
   *  configured max concurrency level. NO SOURCE-DOCUMENTED THRESHOLD FOUND — placeholder. */
  readonly minSuccessRateAtMaxConcurrency: number
  /** W-29 concurrency capacity: max acceptable ratio of p95 latency at max concurrency
   *  to p95 latency at concurrency=1 (a "how much does tail latency degrade under load"
   *  proxy). NO SOURCE-DOCUMENTED THRESHOLD FOUND — placeholder. */
  readonly maxLatencyDegradationFactor: number
  /** W-30 QoS/backpressure: under contention, the fraction of over-capacity requests
   *  that must be HONESTLY refused (429/503 + reason) rather than silently degraded
   *  (200 with thinned/absent content) or hung. NO SOURCE-DOCUMENTED THRESHOLD FOUND
   *  — placeholder; 1.0 encodes the doctrine's own qualitative rule ("queue/refuse,
   *  never thin quality") as a hard 100% requirement among the requests this harness
   *  can positively identify as over-capacity. */
  readonly minHonestDegradationRate: number
  /** W-31 quality-under-load: per-query-class p95 latency budget in ms. NO
   *  SOURCE-DOCUMENTED THRESHOLD FOUND — placeholder. */
  readonly maxP95LatencyMs: number
}

export const DEFAULT_THRESHOLDS: LoadThresholds = {
  minCacheHitRate: 0.5,
  minSuccessRateAtMaxConcurrency: 0.95,
  maxLatencyDegradationFactor: 5,
  minHonestDegradationRate: 1.0,
  maxP95LatencyMs: 5000,
}

export interface CacheHitRateReport {
  readonly n: number
  readonly hits: number
  readonly misses: number
  readonly errors: number
  readonly hitRate: number
  readonly missLatency: LatencyStats | null
  readonly hitLatency: LatencyStats | null
  readonly pass: boolean
}

export interface ConcurrencyLevelResult {
  readonly concurrency: number
  readonly requests: number
  readonly successes: number
  readonly errors: number
  readonly successRate: number
  readonly latency: LatencyStats
}

export interface ConcurrencyCapacityReport {
  readonly levels: readonly ConcurrencyLevelResult[]
  readonly successRateAtMaxConcurrency: number
  readonly latencyDegradationFactor: number
  readonly pass: boolean
}

export interface QosBackpressureReport {
  readonly totalRequests: number
  readonly succeeded: number
  readonly honestlyRefused: number
  readonly silentlyDegraded: number
  readonly otherErrors: number
  readonly honestDegradationRate: number
  /** False when nothing failed at all — i.e. the burst never produced real
   *  contention. In that case `honestDegradationRate` trivially reads 1.0
   *  and `pass` can read PASS without W-30's backpressure path having been
   *  exercised at all. A report reader (and the human operator running this
   *  for real in Task 13) MUST check this before trusting a QoS PASS. */
  readonly contentionObserved: boolean
  readonly byPriorityClass: Record<
    'interactive' | 'background',
    { requests: number; succeeded: number; honestlyRefused: number; successRate: number }
  >
  /** True iff interactive success rate ≥ background success rate (the doctrine's
   *  "interactive > background" ordering, checked, not assumed) whenever both lanes
   *  saw contention. `null` if one lane had zero requests (nothing to compare). */
  readonly interactivePrioritizedOverBackground: boolean | null
  readonly qosMechanismObserved: 'real_dispatch_queue' | 'no_qos_signal_detected'
  readonly pass: boolean
}

export interface SloQueryClassResult {
  readonly queryClass: string
  readonly latency: LatencyStats
  readonly successRate: number
  readonly withinBudget: boolean
}

export interface SloReport {
  readonly concurrency: number
  readonly byQueryClass: readonly SloQueryClassResult[];
  readonly overallPass: boolean
  /** Honest note: the W5 battery baseline this mode compares against
   *  (`W5_BATTERY_BASELINE_v1_0.md`) recorded routing-accuracy/coverage metrics for a
   *  synchronous in-process compile path, NOT HTTP latency percentiles — there is no
   *  latency figure in that baseline to diff against. This field says so plainly
   *  rather than fabricating a comparison. */
  readonly baselineComparisonNote: string
}

export interface LoadHarnessReport {
  readonly captured_at: string
  readonly target_kind: 'local_mock' | 'remote'
  readonly thresholds: LoadThresholds
  readonly thresholds_note: string
  readonly modes_run: readonly string[]
  readonly cache?: CacheHitRateReport
  readonly concurrency?: ConcurrencyCapacityReport
  readonly qos?: QosBackpressureReport
  readonly slo?: SloReport
  readonly gate: {
    readonly pass: boolean
    readonly per_mode: Record<string, boolean>
  }
}
