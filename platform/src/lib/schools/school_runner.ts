/**
 * M9 School Runner — orchestrates all 7 school engines in parallel.
 * Returns MultiSchoolResult per domain with convergence scores.
 * M9-B-S1 (2026-05-14).
 */

import type { ChartData, Domain, MultiSchoolResult, SchoolResult } from './types'
import { parashari_engine } from './parashari_engine'
import { jaimini_engine } from './jaimini_engine'
import { tajika_engine } from './tajika_engine'
import { kp_engine } from './kp_engine'
import { nadi_engine } from './nadi_engine'
import { bnn_engine } from './bnn_engine'
import { yogini_engine } from './yogini_engine'
import { computeConvergence, buildConvergenceNarrative, detectDivergence } from './convergence_calculator'

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
}

/**
 * Runs all 7 school engines against the given chart for a single domain.
 * All 7 engines execute in parallel.
 */
export async function runSchoolsForDomain(
  chartData: ChartData,
  domain: Domain,
  options: SchoolRunOptions = {}
): Promise<MultiSchoolResult> {
  const results: SchoolResult[] = await Promise.all(
    ALL_ENGINES.map(engine => engine.analyze(chartData, domain))
  )

  const convergence = computeConvergence(results, domain)
  const divergence = detectDivergence(results, convergence)

  if (options.includeNarratives ?? true) {
    convergence.convergenceNarrative = buildConvergenceNarrative(convergence, divergence)
  }

  return {
    chartId: chartData.chartId,
    runDate: new Date().toISOString().split('T')[0],
    domain,
    schoolResults: results,
    convergence,
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
