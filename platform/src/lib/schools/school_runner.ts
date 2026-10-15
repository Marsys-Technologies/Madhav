/**
 * School Runner — orchestrates all 7 school engines in parallel.
 * Returns MultiSchoolResult per domain with convergence scores.
 *
 * U4 (2026-06-22): accepts liveSignals map so each engine receives real L2 signals.
 * The caller (build route or test fixture) pre-builds the signals map via
 * buildSchoolSignals() from chart_data_adapter.ts.
 *
 * SS N-362/N-363: there are NO default signals. Per school the signals argument has three
 * explicit states: undefined (not supplied), [] (supplied but empty), non-empty (analyse).
 * The first two both yield an honest not-available result (reason 'no_live_signals'); such
 * schools are skipped by convergence and weighting and are never counted in "n of 7".
 *
 * DB calls live in the build route, NOT here. This module stays DB-free.
 */

import type { ChartData, Domain, MultiSchoolResult, SchoolResult, SchoolName, SignalScore } from './types'
import { parashari_engine } from './parashari_engine'
import { jaimini_engine } from './jaimini_engine'
import { tajika_engine } from './tajika_engine'
import { kp_engine } from './kp_engine'
import { nadi_engine } from './nadi_engine'
import { bnn_engine } from './bnn_engine'
import { yogini_engine } from './yogini_engine'
import { computeConvergence, buildConvergenceNarrative, detectDivergence } from './convergence_calculator'
import { DOMAIN_AUTHORITY_WEIGHTS } from './chart_data_adapter'
import { availableResults, classifySignalSupply, unavailableResult } from './engine_utils'

const ALL_ENGINES = [
  parashari_engine,
  jaimini_engine,
  tajika_engine,
  kp_engine,
  nadi_engine,
  bnn_engine,
  yogini_engine,
]

const ALL_DOMAINS: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']

export interface SchoolRunOptions {
  domains?: Domain[]
  includeNarratives?: boolean
  /** Pre-fetched live signals per school. Absent key or [] => that school is not available (no defaults). */
  liveSignals?: Partial<Record<SchoolName, SignalScore[]>>
}

/**
 * Runs all 7 school engines against the given chart for a single domain.
 * All 7 engines execute in parallel.
 *
 * U4: passes liveSignals[engine.school] to each engine. A school without live signals
 * (key absent or []) is reported not available; there are no default signals.
 */
export async function runSchoolsForDomain(
  chartData: ChartData,
  domain: Domain,
  options: SchoolRunOptions = {}
): Promise<MultiSchoolResult> {
  const { liveSignals } = options
  const results: SchoolResult[] = await Promise.all(
    ALL_ENGINES.map(engine => {
      const signals = liveSignals?.[engine.school as SchoolName]
      // Explicit three-state handling: undefined = not supplied, [] = supplied but empty,
      // non-empty = analyse. The first two are an honest not-available result, never a default.
      const supply = classifySignalSupply(signals)
      if (supply !== 'supplied') {
        return Promise.resolve(unavailableResult(engine.school, domain, supply))
      }
      return engine.analyze(chartData, domain, signals)
    })
  )

  const convergence = computeConvergence(results, domain)
  const divergence = detectDivergence(results, convergence)

  if (options.includeNarratives ?? true) {
    convergence.convergenceNarrative = buildConvergenceNarrative(convergence, divergence)
  }

  // E2: compute per-domain authority-weighted consensus score over AVAILABLE schools only
  // (renormalised by the authority weight actually present; unavailable schools carry no weight).
  const domainWeights = DOMAIN_AUTHORITY_WEIGHTS[domain]
  let weightedSum = 0
  let weightSum = 0
  let weightedSchoolsAgreeing = 0
  const perSchoolWeighted: Partial<Record<SchoolName, number>> = {}
  const analysed = availableResults(results)
  for (const r of analysed) {
    const w = domainWeights[r.school as SchoolName] ?? (1 / 7)
    const ws = r.domainScore * w
    perSchoolWeighted[r.school as SchoolName] = ws
    weightedSum += ws
    weightSum += w
    if (r.domainScore >= 3.0) weightedSchoolsAgreeing++
  }

  return {
    chartId: chartData.chartId,
    runDate: new Date().toISOString().split('T')[0],
    domain,
    schoolResults: results,
    convergence,
    // E2/E3 extensions (carried through to persistence)
    weightedMeanScore: analysed.length > 0 && weightSum > 0 ? Math.round((weightedSum / weightSum) * 1000) / 1000 : null,
    perSchoolWeighted,
    weightedSchoolsAgreeing,
  }
}

/**
 * Full multi-school triangulation: runs all 7 schools across all 5 domains.
 * Returns one MultiSchoolResult per domain (5 total).
 */
export async function runFullTriangulation(
  chartData: ChartData,
  options: SchoolRunOptions = {}
): Promise<MultiSchoolResult[]> {
  const domains = options.domains ?? ALL_DOMAINS
  return Promise.all(domains.map(domain => runSchoolsForDomain(chartData, domain, options)))
}

/**
 * Summary helper: extract convergence levels across all domains.
 */
export function summarizeConvergence(results: MultiSchoolResult[]): {
  highConvergenceDomains: Domain[]
  mediumConvergenceDomains: Domain[]
  lowConvergenceDomains: Domain[]
  overallAgreementSignal: string
} {
  const high = results.filter(r => r.convergence.convergenceLevel === 'HIGH').map(r => r.domain)
  const medium = results.filter(r => r.convergence.convergenceLevel === 'MEDIUM').map(r => r.domain)
  const low = results.filter(r => r.convergence.convergenceLevel === 'LOW').map(r => r.domain)

  const overallSignal =
    high.length >= 3 ? 'STRONG — majority of domains show inter-school consensus' :
    high.length + medium.length >= 3 ? 'MODERATE — partial inter-school consensus' :
    'WEAK — schools diverge significantly; domain-specific analysis required'

  return {
    highConvergenceDomains: high,
    mediumConvergenceDomains: medium,
    lowConvergenceDomains: low,
    overallAgreementSignal: overallSignal,
  }
}
