/**
 * School Runner — orchestrates all 7 school engines in parallel.
 * Returns MultiSchoolResult per domain with convergence scores.
 *
 * U4 (2026-06-22): accepts liveSignals map so each engine receives real L2 signals
 * rather than hitting defaultSignals. The caller (build route or test fixture) pre-builds
 * the signals map via buildSchoolSignals() from chart_data_adapter.ts.
 * When liveSignals is absent for a school, the engine falls back to defaultSignals
 * (FALLBACK-OF-LAST-RESORT — logs a warning).
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
  /** Pre-fetched live signals per school. If absent for a school, engine falls back to defaultSignals. */
  liveSignals?: Partial<Record<SchoolName, SignalScore[]>>
}

/**
 * Runs all 7 school engines against the given chart for a single domain.
 * All 7 engines execute in parallel.
 *
 * U4: passes liveSignals[engine.school] to each engine so the engine never
 * hits defaultSignals for a chart that has L2 signal coverage.
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
      // Pass signals if present; engine.analyze falls back to defaultSignals (with warning) when absent.
      return engine.analyze(chartData, domain, signals)
    })
  )

  const convergence = computeConvergence(results, domain)
  const divergence = detectDivergence(results, convergence)

  if (options.includeNarratives ?? true) {
    convergence.convergenceNarrative = buildConvergenceNarrative(convergence, divergence)
  }

  // E2: compute per-domain authority-weighted consensus score
  const domainWeights = DOMAIN_AUTHORITY_WEIGHTS[domain]
  let weightedSum = 0
  let weightedSchoolsAgreeing = 0
  const perSchoolWeighted: Partial<Record<SchoolName, number>> = {}
  for (const r of results) {
    const w = domainWeights[r.school as SchoolName] ?? (1 / 7)
    const ws = r.domainScore * w
    perSchoolWeighted[r.school as SchoolName] = ws
    weightedSum += ws
    if (r.domainScore >= 3.0) weightedSchoolsAgreeing++
  }

  return {
    chartId: chartData.chartId,
    runDate: new Date().toISOString().split('T')[0],
    domain,
    schoolResults: results,
    convergence,
    // E2/E3 extensions (carried through to persistence)
    weightedMeanScore: Math.round(weightedSum * 1000) / 1000,
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
