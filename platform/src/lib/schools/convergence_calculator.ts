/**
 * M9 Convergence Calculator
 * NAP.M9.2: HIGH ≥ 5/7 schools agree direction; MEDIUM = 4/7; LOW < 4/7.
 * NAP.M9.3: Divergence flagged when ≥ 2 schools contradict plurality direction.
 * M9-B-S1 (2026-05-14).
 */

import type {
  SchoolResult, Domain, ConvergenceScore, ConvergenceLevel,
  Direction, SchoolName
} from './types'
import { mean, stddev, mode, availableResults, isAvailableResult } from './engine_utils'

export interface DivergenceRecord {
  domain: Domain
  pluralityDirection: Direction
  schoolsAgreeing: SchoolName[]
  schoolsContradict: SchoolName[]
  schoolsSilent: SchoolName[]     // scored but direction === plurality? no; neutral here
  /** Not available (no live signals): never counted as agreeing, contradicting or silent. */
  schoolsUnavailable: SchoolName[]
  isDivergent: boolean            // true if ≥ 2 schools contradict plurality
}

function directionMode(directions: Direction[]): Direction {
  // 'mixed' is a return of ConvergenceScore; within SchoolResult we have positive/negative/neutral
  return mode(directions)
}

/**
 * Computes convergence across a set of school results for a single domain.
 *
 * Schools that are not available (no live signals) are SKIPPED: they never count as
 * agreement, never enter the mean, and are not part of schoolsTotal ("n of 7"). They are
 * reported in schoolsUnavailable. Tajika is additionally excluded from schoolsTotal when its
 * VARSHA_KUNDALI_PENDING flag is set. When no school is available, no convergence is claimed
 * (convergenceLevel 'NOT_AVAILABLE', null mean/std).
 */
export function computeConvergence(
  results: SchoolResult[],
  domain: Domain
): ConvergenceScore {
  if (results.length === 0) {
    throw new Error('computeConvergence: results array is empty')
  }

  const available = availableResults(results)
  const schoolsUnavailable = results.filter(r => !isAvailableResult(r)).map(r => r.school)

  // Exclude Tajika from convergence count if it has the VARSHA_KUNDALI_PENDING flag
  const effectiveResults = available.filter(r => {
    if (r.school === 'tajika') {
      return !(r.pendingFlags?.includes('[VARSHA_KUNDALI_PENDING]') ?? false)
    }
    return true
  })

  const perSchoolScores: Partial<Record<SchoolName, number>> = {}
  for (const r of available) {
    perSchoolScores[r.school] = r.domainScore
  }

  const common = {
    domain,
    schoolsEvaluated: results.length,
    schoolsAvailable: available.length,
    schoolsUnavailable,
    perSchoolScores,
  }

  if (effectiveResults.length === 0) {
    return {
      ...common,
      schoolsAgreeing: 0,
      schoolsTotal: 0,
      convergenceLevel: 'NOT_AVAILABLE',
      meanDomainScore: null,
      stdDomainScore: null,
      direction: 'not_available',
    }
  }

  const schoolsTotal = effectiveResults.length
  const directions = effectiveResults.map(r => r.direction)
  const pluralityDirection = directionMode(directions)
  const schoolsAgreeing = directions.filter(d => d === pluralityDirection).length

  const convergenceLevel: ConvergenceLevel =
    schoolsAgreeing >= 5 ? 'HIGH' :
    schoolsAgreeing >= 4 ? 'MEDIUM' : 'LOW'

  const scores = effectiveResults.map(r => r.domainScore)
  const meanScore = mean(scores)
  const stdScore = stddev(scores)

  // Determine overall direction: if unanimous or near-unanimous use that; otherwise 'mixed'
  const overallDirection: Direction | 'mixed' =
    schoolsAgreeing >= Math.ceil(schoolsTotal * 0.7) ? pluralityDirection : 'mixed'

  return {
    ...common,
    schoolsAgreeing,
    schoolsTotal,
    convergenceLevel,
    meanDomainScore: Math.round(meanScore * 1000) / 1000,
    stdDomainScore: Math.round(stdScore * 1000) / 1000,
    direction: overallDirection,
  }
}

/**
 * Detects divergence: whether ≥ 2 schools contradict the plurality direction.
 * NAP.M9.3: divergence_threshold ≥ 2.
 */
export function detectDivergence(
  results: SchoolResult[],
  convergence: ConvergenceScore
): DivergenceRecord {
  const pluralityDirection = typeof convergence.direction === 'string' && convergence.direction !== 'mixed'
    ? convergence.direction as Direction
    : 'neutral'

  const schoolsAgreeing: SchoolName[] = []
  const schoolsContradict: SchoolName[] = []
  const schoolsSilent: SchoolName[] = []
  const schoolsUnavailable: SchoolName[] = []

  for (const r of results) {
    if (!isAvailableResult(r)) {
      schoolsUnavailable.push(r.school)
    } else if (r.direction === pluralityDirection) {
      schoolsAgreeing.push(r.school)
    } else if (r.direction === 'neutral') {
      schoolsSilent.push(r.school)
    } else {
      schoolsContradict.push(r.school)
    }
  }

  return {
    domain: convergence.domain,
    pluralityDirection,
    schoolsAgreeing,
    schoolsContradict,
    schoolsSilent,
    schoolsUnavailable,
    isDivergent: schoolsContradict.length >= 2,
  }
}

/**
 * Generates a plain-language convergence narrative suitable for synthesis.
 * Always states how many schools were available ("n of N schools available").
 */
export function buildConvergenceNarrative(
  convergence: ConvergenceScore,
  divergence: DivergenceRecord
): string {
  const { domain, convergenceLevel, schoolsAgreeing, schoolsTotal, schoolsAvailable, schoolsEvaluated } = convergence
  const availability = `${schoolsAvailable} of ${schoolsEvaluated} schools available`
  const unavailableNote = convergence.schoolsUnavailable.length > 0
    ? ` (not available, no live signals: ${convergence.schoolsUnavailable.join(', ')})`
    : ''

  if (convergenceLevel === 'NOT_AVAILABLE' || convergence.meanDomainScore === null || convergence.stdDomainScore === null) {
    return `${domain}: convergence not available — ${availability}${unavailableNote}; no inter-school agreement or score is claimed.`
  }

  const levelProse = {
    HIGH: 'strong inter-school agreement',
    MEDIUM: 'moderate inter-school agreement',
    LOW: 'low inter-school agreement',
  }[convergenceLevel]

  const directionProse = convergence.direction === 'mixed'
    ? 'mixed (schools disagree on direction)'
    : convergence.direction

  const parts: string[] = [
    `${domain}: ${levelProse} — ${schoolsAgreeing}/${schoolsTotal} counted schools read direction as "${directionProse}"; ${availability}${unavailableNote}.`,
    `Mean domain score across available schools: ${convergence.meanDomainScore.toFixed(2)} / 5.0 (σ=${convergence.stdDomainScore.toFixed(2)}).`,
  ]

  if (divergence.isDivergent) {
    parts.push(
      `DIVERGENCE DETECTED: ${divergence.schoolsContradict.join(', ')} contradict the plurality — cross-school disagreement should be surfaced in the answer.`
    )
  }

  const pendingExcluded = schoolsAvailable - schoolsTotal
  if (pendingExcluded > 0) {
    parts.push(
      `Note: ${pendingExcluded} available school(s) excluded from the convergence count due to pending data flags (VARSHA_KUNDALI_PENDING).`
    )
  }

  return parts.join(' ')
}
