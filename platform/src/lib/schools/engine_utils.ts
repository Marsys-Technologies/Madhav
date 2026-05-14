/**
 * Shared utilities for all 7 school engines.
 * M9-B-S1 (2026-05-14).
 */

import type { Direction, SignalScore } from './types'

export function computeWeightedScore(signals: SignalScore[]): number {
  if (signals.length === 0) return 2.5  // neutral mid-point when no signals
  const totalWeight = signals.reduce((s, sig) => s + sig.weight, 0)
  if (totalWeight === 0) return 2.5
  const weighted = signals.reduce((s, sig) => s + sig.score * sig.weight, 0)
  return Math.min(5.0, Math.max(0.0, weighted / totalWeight))
}

export function scoreToDirection(score: number): Direction {
  if (score >= 3.2) return 'positive'
  if (score <= 1.8) return 'negative'
  return 'neutral'
}

export function topN(signals: SignalScore[], n: number): SignalScore[] {
  return [...signals]
    .sort((a, b) => b.score * b.weight - a.score * a.weight)
    .slice(0, n)
}

// Mean of an array; returns 0 for empty arrays
export function mean(values: number[]): number {
  if (values.length === 0) return 0
  return values.reduce((s, v) => s + v, 0) / values.length
}

// Population standard deviation
export function stddev(values: number[]): number {
  if (values.length < 2) return 0
  const m = mean(values)
  const variance = values.reduce((s, v) => s + (v - m) ** 2, 0) / values.length
  return Math.sqrt(variance)
}

// Statistical mode (most frequent); returns first if tie
export function mode<T>(items: T[]): T {
  if (items.length === 0) throw new Error('mode of empty array')
  const freq = new Map<T, number>()
  for (const item of items) freq.set(item, (freq.get(item) ?? 0) + 1)
  let best = items[0]
  let bestCount = 0
  for (const [item, count] of freq) {
    if (count > bestCount) { bestCount = count; best = item }
  }
  return best
}
