/**
 * stats.ts — pure percentile/aggregation math for the W6 load harness. No I/O, no
 * fetch, no server — this is the part of the harness that's fully unit-testable
 * without a live target, and `lib.test.ts` verifies it against hand-computed values.
 */
import type { LatencyStats, RequestResult } from './types'

/** Linear-interpolation percentile (the common "R-7" method used by e.g. numpy's
 *  default). `p` in [0, 100]. Returns 0 for an empty input. */
export function percentile(values: readonly number[], p: number): number {
  if (values.length === 0) return 0
  const sorted = [...values].sort((a, b) => a - b)
  if (sorted.length === 1) return sorted[0]
  const rank = (p / 100) * (sorted.length - 1)
  const lo = Math.floor(rank)
  const hi = Math.ceil(rank)
  if (lo === hi) return sorted[lo]
  const frac = rank - lo
  return sorted[lo] + (sorted[hi] - sorted[lo]) * frac
}

export function summarizeLatencies(latenciesMs: readonly number[]): LatencyStats {
  if (latenciesMs.length === 0) {
    return { n: 0, p50: 0, p95: 0, p99: 0, mean: 0, min: 0, max: 0 }
  }
  const sum = latenciesMs.reduce((a, b) => a + b, 0)
  return {
    n: latenciesMs.length,
    p50: percentile(latenciesMs, 50),
    p95: percentile(latenciesMs, 95),
    p99: percentile(latenciesMs, 99),
    mean: sum / latenciesMs.length,
    min: Math.min(...latenciesMs),
    max: Math.max(...latenciesMs),
  }
}

export function cacheHitRate(results: readonly Pick<RequestResult, 'cacheHit' | 'ok'>[]): number {
  const attempted = results.filter((r) => r.ok)
  if (attempted.length === 0) return 0
  return attempted.filter((r) => r.cacheHit).length / attempted.length
}

export function successRate(results: readonly Pick<RequestResult, 'ok'>[]): number {
  if (results.length === 0) return 0
  return results.filter((r) => r.ok).length / results.length
}

/** Read a `.`-separated dot-path out of a parsed JSON value, returning `undefined` if
 *  any segment is missing or the traversal hits a non-object. */
export function getByPath(obj: unknown, path: string): unknown {
  const segments = path.split('.').filter(Boolean)
  let cur: unknown = obj
  for (const seg of segments) {
    if (cur === null || typeof cur !== 'object') return undefined
    cur = (cur as Record<string, unknown>)[seg]
  }
  return cur
}
