/**
 * Shared utilities for all 7 school engines.
 * M9-B-S1 (2026-05-14).
 */

import type {
  Direction, Domain, SchoolName, SchoolResult, SignalScore, SignalSupply, UnavailableReason,
} from './types'

/**
 * Weighted mean of the signals passed in. Returns null (never a neutral default) when no
 * weighted score can be formed: empty list or total weight 0 (CLAUDE.md §N.7).
 */
export function computeWeightedScore(signals: SignalScore[]): number | null {
  if (signals.length === 0) return null
  const totalWeight = signals.reduce((s, sig) => s + sig.weight, 0)
  if (!(totalWeight > 0)) return null
  const weighted = signals.reduce((s, sig) => s + sig.score * sig.weight, 0)
  return Math.min(5.0, Math.max(0.0, weighted / totalWeight))
}

/**
 * The three states of a signals argument (SS N-363). undefined/null = not supplied,
 * [] = supplied but empty, non-empty = analyse. The first two both read as not available.
 */
export function classifySignalSupply(signals: SignalScore[] | null | undefined): SignalSupply {
  if (signals === undefined || signals === null) return 'not_supplied'
  if (signals.length === 0) return 'supplied_empty'
  return 'supplied'
}

const SCHOOL_LABEL: Record<SchoolName, string> = {
  parashari: 'Parashari',
  jaimini: 'Jaimini',
  tajika: 'Tajika',
  kp: 'KP',
  nadi: 'Nadi',
  bnn: 'BNN',
  yogini: 'Yogini',
}

export function schoolLabel(school: SchoolName): string {
  return SCHOOL_LABEL[school]
}

/**
 * Honest not-available result: the engine made no judgment. Score and direction are null,
 * coverage is 'silent', and the verdict says why. Engines never invent signals.
 */
export function unavailableResult(
  school: SchoolName,
  domain: Domain,
  signalSupply: SignalSupply,
  reason: UnavailableReason = 'no_live_signals',
  pendingFlags?: string[],
): SchoolResult {
  const why = reason === 'no_live_signals'
    ? (signalSupply === 'supplied_empty'
        ? 'an empty signal list was supplied'
        : 'no live signals were supplied')
    : 'the supplied signals carry zero total weight'
  const result: SchoolResult = {
    school,
    domain,
    domainScore: null,
    direction: null,
    topSignals: [],
    schoolVerdict: `${schoolLabel(school)}: not available for ${domain} — ${why}, so no judgment is made.`,
    signalCoverage: 'silent',
    available: false,
    unavailableReason: reason,
    signalSupply,
  }
  if (pendingFlags && pendingFlags.length > 0) result.pendingFlags = pendingFlags
  return result
}

/** True unless the engine explicitly marked the result not available. */
export function isAvailableResult(r: SchoolResult): boolean {
  return r.available !== false && r.domainScore !== null && r.direction !== null
}

/** An analysed result: score and direction are known. */
export type AvailableSchoolResult = SchoolResult & { domainScore: number; direction: Direction }

export function availableResults(results: SchoolResult[]): AvailableSchoolResult[] {
  return results.filter((r): r is AvailableSchoolResult => isAvailableResult(r))
}

/** Names of the strongest signals, for chart-agnostic prose derived from the signals passed in. */
export function topSignalNames(top: SignalScore[]): string {
  return top.map(s => s.signalName).join('; ')
}

export interface AnalyzeFromSignalsOptions {
  school: SchoolName
  domain: Domain
  /** The signals argument exactly as the caller passed it (undefined, [] or non-empty). */
  signals: SignalScore[] | null | undefined
  /** Optional transform of the live signals (e.g. school-specific weighting). Never adds signals. */
  prepare?: (live: SignalScore[]) => SignalScore[]
  /** Chart-agnostic prose built from the score and the signals that were passed in. */
  verdict: (score: number, top: SignalScore[], used: SignalScore[]) => string
  pendingFlags?: string[]
}

/**
 * Shared engine core. undefined and [] both return the honest not-available result
 * (reason 'no_live_signals'); a non-empty list is analysed from those signals only.
 * There is no default signal set anywhere (SS N-362/N-363, CLAUDE.md §N.7).
 */
export function analyzeFromSignals(opts: AnalyzeFromSignalsOptions): SchoolResult {
  const supply = classifySignalSupply(opts.signals)
  if (supply !== 'supplied') {
    return unavailableResult(opts.school, opts.domain, supply, 'no_live_signals', opts.pendingFlags)
  }
  const used = opts.prepare ? opts.prepare(opts.signals as SignalScore[]) : (opts.signals as SignalScore[])
  const score = computeWeightedScore(used)
  if (score === null) {
    return unavailableResult(opts.school, opts.domain, supply, 'zero_signal_weight', opts.pendingFlags)
  }
  const top = topN(used, 3)
  const result: SchoolResult = {
    school: opts.school,
    domain: opts.domain,
    domainScore: Math.round(score * 1000) / 1000,
    direction: scoreToDirection(score),
    topSignals: top,
    schoolVerdict: opts.verdict(score, top, used),
    signalCoverage: 'primary',
    available: true,
    signalSupply: supply,
  }
  if (opts.pendingFlags !== undefined) result.pendingFlags = opts.pendingFlags
  return result
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
