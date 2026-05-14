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
import { mean, stddev, mode } from './engine_utils'

export interface DivergenceRecord {
  domain: Domain
  pluralityDirection: Direction
  schoolsAgreeing: SchoolName[]
  schoolsContradict: SchoolName[]
  schoolsSilent: SchoolName[]     // scored but direction === plurality? no; neutral here
  isDivergent: boolean            // true if ≥ 2 schools contradict plurality
}

function directionMode(directions: Direction[]): Direction {
  // 'mixed' is a return of ConvergenceScore; within SchoolResult we have positive/negative/neutral
  return mode(directions)
}

/**
 * Computes convergence across a set of school results for a single domain.
 * Tajika is excluded from schoolsTotal when its VARSHA_KUNDALI_PENDING flag is set.
 */
export function computeConvergence(
  results: SchoolResult[],
  domain: Domain
): ConvergenceScore {
  if (results.length === 0) {
    throw new Error('computeConvergence: results array is empty')
  }

  // Exclude Tajika from convergence count if it has the VARSHA_KUNDALI_PENDING flag
  const effectiveResults = results.filter(r => {
    if (r.school === 'tajika') {
      return !(r.pendingFlags?.includes('[VARSHA_KUNDALI_PENDING]') ?? false)
    }
    return true
  })

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

  const perSchoolScores: Record<string, number> = {}
  for (const r of results) {
    perSchoolScores[r.school] = r.domainScore
  }

  return {
    domain,
    schoolsAgreeing,
    schoolsTotal,
    convergenceLevel,
    meanDomainScore: Math.round(meanScore * 1000) / 1000,
    stdDomainScore: Math.round(stdScore * 1000) / 1000,
    direction: overallDirection,
    perSchoolScores: perSchoolScores as Record<SchoolName, number>,
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

  for (const r of results) {
    if (r.direction === pluralityDirection) {
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
    isDivergent: schoolsContradict.length >= 2,
  }
}

/**
 * Generates a plain-language convergence narrative suitable for synthesis.
 */
export function buildConvergenceNarrative(
  convergence: ConvergenceScore,
  divergence: DivergenceRecord
): string {
  const { domain, convergenceLevel, schoolsAgreeing, schoolsTotal, meanDomainScore } = convergence
  const levelProse = {
    HIGH: 'strong inter-school agreement',
    MEDIUM: 'moderate inter-school agreement',
    LOW: 'low inter-school agreement',
  }[convergenceLevel]

  const directionProse = convergence.direction === 'mixed'
    ? 'mixed (schools disagree on direction)'
    : convergence.direction

  const parts: string[] = [
    `${domain}: ${levelProse} — ${schoolsAgreeing}/${schoolsTotal} schools read direction as "${directionProse}".`,
    `Mean domain score across schools: ${meanDomainScore.toFixed(2)} / 5.0 (σ=${convergence.stdDomainScore.toFixed(2)}).`,
  ]

  if (divergence.isDivergent) {
    parts.push(
      `DIVERGENCE DETECTED: ${divergence.schoolsContradict.join(', ')} contradict the plurality — cross-school disagreement should be surfaced in the answer.`
    )
  }

  if (convergence.schoolsTotal < 7) {
    parts.push(
      `Note: ${7 - convergence.schoolsTotal} school(s) excluded from convergence count due to pending data flags (VARSHA_KUNDALI_PENDING or TRANSIT_DATA_PENDING).`
    )
  }

  return parts.join(' ')
}
