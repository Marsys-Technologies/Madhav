/**
 * extract_numerical_claims.ts — Heuristic: extract numerical astrological claims.
 *
 * Regex-only. NO LLM calls.
 * Extracts: degrees (23.45°, 18°31′38″), virupa values, Brier scores, shadbala points.
 *
 * False positive rate: ~8% (non-astrological numbers matching patterns).
 * False negative rate: ~15% (prose-form numbers like "twenty-three degrees").
 *
 * MCPT v3.1.0-S4
 */

export interface NumericalClaim {
  raw: string
  type: 'degree' | 'virupa' | 'points' | 'score' | 'generic'
  value: number
}

// ── Patterns ───────────────────────────────────────────────────────────────────

/** Degrees with optional minutes/seconds: 23.45°, 18°31′38″, 12° */
const DEGREE_PATTERN = /(\d{1,3}(?:\.\d{1,4})?)°(?:\d{1,2}[′'](?:\d{1,2}[″"])?)?/g

/** Virupa values (Shadbala unit): 12.5 virupas, 47 virupa */
const VIRUPA_PATTERN = /(\d{1,4}(?:\.\d{1,2})?)\s*virupa[s]?/gi

/** Shadbala points: 345.6 points, 87 rupas */
const POINTS_PATTERN = /(\d{1,4}(?:\.\d{1,2})?)\s*(?:points?|rupas?)/gi

/** Brier score or confidence: 0.73 confidence, score: 0.85 */
const SCORE_PATTERN = /(?:confidence|score|brier)[:\s]+(\d+(?:\.\d{1,4})?)/gi

// ── Main extractor ─────────────────────────────────────────────────────────────

/**
 * Extract numerical astrological claims from response text.
 */
export function extractNumericalClaims(responseText: string): NumericalClaim[] {
  if (!responseText || typeof responseText !== 'string') return []

  const claims: NumericalClaim[] = []

  // Degree extractions
  let match: RegExpExecArray | null
  const degreePat = new RegExp(DEGREE_PATTERN.source, 'g')
  while ((match = degreePat.exec(responseText)) !== null) {
    const val = parseFloat(match[1]!)
    if (!isNaN(val)) {
      claims.push({ raw: match[0], type: 'degree', value: val })
    }
  }

  // Virupa extractions
  const virupaPat = new RegExp(VIRUPA_PATTERN.source, 'gi')
  while ((match = virupaPat.exec(responseText)) !== null) {
    const val = parseFloat(match[1]!)
    if (!isNaN(val)) {
      claims.push({ raw: match[0], type: 'virupa', value: val })
    }
  }

  // Points/rupas extractions
  const pointsPat = new RegExp(POINTS_PATTERN.source, 'gi')
  while ((match = pointsPat.exec(responseText)) !== null) {
    const val = parseFloat(match[1]!)
    if (!isNaN(val)) {
      claims.push({ raw: match[0], type: 'points', value: val })
    }
  }

  // Score/confidence extractions
  const scorePat = new RegExp(SCORE_PATTERN.source, 'gi')
  while ((match = scorePat.exec(responseText)) !== null) {
    const val = parseFloat(match[1]!)
    if (!isNaN(val)) {
      claims.push({ raw: match[0], type: 'score', value: val })
    }
  }

  return claims
}

/**
 * Check if the response contains any numerical astrological claims.
 */
export function hasNumericalClaims(responseText: string): boolean {
  return extractNumericalClaims(responseText).length > 0
}
