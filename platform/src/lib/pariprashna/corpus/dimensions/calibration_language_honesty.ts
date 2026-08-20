/**
 * pariprashna/corpus/dimensions/calibration_language_honesty.ts — lane P2-N
 * (G3-F).
 *
 * Grounded in G3-A's `calibration_disclosure` (merged, PR #1363) — always
 * `measured` (schema.ts documents no unavailable branch: the scan of
 * `validToolResults` against `CALIBRATION_BEARING_TOOL_NAMES` always runs).
 * When nothing L5-calibration-bearing was consulted, the receipt carries the
 * fixed `STRUCTURAL_MODE_CALIBRATION_NOTE` (CLAUDE.md §E: L5 sealed in
 * STRUCTURAL mode, no empirical calibration yet). This dimension checks the
 * one thing the disclosure alone cannot: whether the PROSE actually honors
 * that disclosure, via a hard-certainty phrase lexicon scanned over the
 * turn's own served text — the same "does the sentence match what the
 * receipt claims" check §N.7 item 5 names ("verified fact ≠ verified
 * prose").
 *
 * The lexicon is intentionally narrow (unhedged certainty about a FUTURE
 * predictive outcome) to avoid false-positiving on legitimate hedged
 * language ("suggests", "classically indicates", "the pattern points
 * toward") — this is a corpus-owned heuristic, not G3-C's future typed-
 * confidence enforcement (see `typed_confidence_honesty.ts`'s stub for that
 * dependency).
 */

import type { DimensionResult, TurnObservation } from '../types'

export const CALIBRATION_LANGUAGE_HONESTY_DIMENSION = 'calibration_language_honesty' as const

/** Unhedged certainty about a future outcome — the language STRUCTURAL mode forbids. */
const HARD_CERTAINTY_PATTERNS: RegExp[] = [
  /\bwill definitely\b/i,
  /\b(is|are) guaranteed to\b/i,
  /\b100%\s*(certain|sure|guaranteed)\b/i,
  /\bwithout (any\s+)?doubt\b/i,
  /\bwill (certainly|surely) (happen|occur)\b/i,
]

export function scoreCalibrationLanguageHonesty(obs: TurnObservation): DimensionResult {
  const { receipt, proseText } = obs
  if (!receipt) {
    return {
      dimension: CALIBRATION_LANGUAGE_HONESTY_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no AcharyaReadingReceipt was supplied for this observation',
      findings: [],
    }
  }

  const disclosure = receipt.calibration_disclosure
  const findings: string[] = []

  if (proseText === null) {
    findings.push('no prose text supplied for this turn — certainty-language scan skipped')
    // Disclosure itself is always measured (schema.ts), so we can still say
    // SOMETHING real: was a disclosure note present at all.
    return {
      dimension: CALIBRATION_LANGUAGE_HONESTY_DIMENSION,
      status: 'scored',
      score: disclosure.disclosure_note.length > 0 ? 0.5 : 0,
      reason: null,
      findings,
    }
  }

  const hits = HARD_CERTAINTY_PATTERNS.filter((re) => re.test(proseText))
  if (hits.length === 0) {
    return { dimension: CALIBRATION_LANGUAGE_HONESTY_DIMENSION, status: 'scored', score: 1, reason: null, findings: [] }
  }

  for (const re of hits) {
    findings.push(`hard-certainty phrase matched (${re.source}) while calibration_disclosure.consulted=${disclosure.consulted}`)
  }

  // Any hard-certainty hit is a real overclaim regardless of whether L5 was
  // consulted — L5 STRUCTURAL mode means even a consulted calibration tool
  // does not license unhedged certainty (assemble.ts's own
  // CALIBRATION_CONSULTED_NOTE: "does not imply every predictive claim ...
  // is empirically calibrated").
  const score = Math.max(0, 1 - hits.length / HARD_CERTAINTY_PATTERNS.length)
  return { dimension: CALIBRATION_LANGUAGE_HONESTY_DIMENSION, status: 'scored', score, reason: null, findings }
}
