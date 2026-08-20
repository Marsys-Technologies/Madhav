/**
 * pariprashna/corpus/dimensions/index.ts — the 13-dimension registry (lane
 * P2-N, roadmap id G3-F). PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md line
 * 106 names 8 dimensions verbatim ("incl. derivation integrity, B.11
 * coverage, falsifier quality, citation precision/recall, calibration-
 * language honesty, safety compliance, reader comprehension, register
 * leakage") and says "13 scored dimensions" — an open set. This registry
 * closes it at 13 by splitting "citation precision/recall" into its two
 * named halves (2 dimensions) and adding 5 more, each traceable to a
 * concrete roadmap line rather than invented from nothing:
 *
 *   - `honest_gaps_disclosure`   — G3-A's own `honest_gaps` receipt field.
 *   - `voice_enforcement`        — G3-D (PPR-04), named explicitly in Gate 3.
 *   - `cross_domain_contradiction_surfaced` — the Gate 3 evidence line
 *     itself: "a planted-contradiction fixture surfaced, not smoothed."
 *   - `typed_confidence_honesty` — G3-C (PPR-03), named explicitly in Gate 3.
 *   - (falsifier_quality, citation precision, citation recall, calibration-
 *     language honesty, safety compliance, register leakage, reader
 *     comprehension, b11_coverage — the roadmap's original 8, minus the
 *     precision/recall merge, plus the split.)
 *
 * 10 of the 13 have a REAL scoring function grounded in already-merged code
 * (G3-A's receipt, G2-B's citation ledger, P2-E's turn metrics, G1-A's
 * classifier — or a corpus-owned heuristic clearly marked as a stand-in for
 * a not-yet-landed lane's future detector). 3 are honest `not_yet_measurable`
 * stubs (`falsifier_quality`, `typed_confidence_honesty`,
 * `reader_comprehension`) — see each module's own docblock for exactly what
 * it is missing and why fabricating a placeholder score was rejected
 * (§N.8).
 */

import type { DimensionId, DimensionResult, DimensionScorer, TurnObservation } from '../types'

import { scoreDerivationIntegrity, DERIVATION_INTEGRITY_DIMENSION } from './derivation_integrity'
import { scoreB11Coverage, B11_COVERAGE_DIMENSION } from './b11_coverage'
import { scoreCitationPrecision, CITATION_PRECISION_DIMENSION } from './citation_precision'
import { scoreCitationRecall, CITATION_RECALL_DIMENSION } from './citation_recall'
import {
  scoreCalibrationLanguageHonesty,
  CALIBRATION_LANGUAGE_HONESTY_DIMENSION,
} from './calibration_language_honesty'
import { scoreSafetyCompliance, SAFETY_COMPLIANCE_DIMENSION } from './safety_compliance'
import { scoreRegisterLeakage, REGISTER_LEAKAGE_DIMENSION } from './register_leakage'
import { scoreHonestGapsDisclosure, HONEST_GAPS_DISCLOSURE_DIMENSION } from './honest_gaps_disclosure'
import { scoreVoiceEnforcement, VOICE_ENFORCEMENT_DIMENSION } from './voice_enforcement'
import {
  scoreCrossDomainContradictionSurfaced,
  CROSS_DOMAIN_CONTRADICTION_SURFACED_DIMENSION,
} from './cross_domain_contradiction_surfaced'
import { scoreFalsifierQuality, FALSIFIER_QUALITY_DIMENSION } from './falsifier_quality'
import { scoreTypedConfidenceHonesty, TYPED_CONFIDENCE_HONESTY_DIMENSION } from './typed_confidence_honesty'
import { scoreReaderComprehension, READER_COMPREHENSION_DIMENSION } from './reader_comprehension'

/** Bumped whenever a scoring function's logic changes (independent of fixture-set version). */
export const CORPUS_SCORING_HARNESS_VERSION = 1

export const DIMENSION_REGISTRY: ReadonlyMap<DimensionId, DimensionScorer> = new Map<DimensionId, DimensionScorer>([
  [DERIVATION_INTEGRITY_DIMENSION, scoreDerivationIntegrity],
  [B11_COVERAGE_DIMENSION, scoreB11Coverage],
  [CITATION_PRECISION_DIMENSION, scoreCitationPrecision],
  [CITATION_RECALL_DIMENSION, scoreCitationRecall],
  [CALIBRATION_LANGUAGE_HONESTY_DIMENSION, scoreCalibrationLanguageHonesty],
  [SAFETY_COMPLIANCE_DIMENSION, scoreSafetyCompliance],
  [REGISTER_LEAKAGE_DIMENSION, scoreRegisterLeakage],
  [HONEST_GAPS_DISCLOSURE_DIMENSION, scoreHonestGapsDisclosure],
  [VOICE_ENFORCEMENT_DIMENSION, scoreVoiceEnforcement],
  [CROSS_DOMAIN_CONTRADICTION_SURFACED_DIMENSION, scoreCrossDomainContradictionSurfaced],
  [FALSIFIER_QUALITY_DIMENSION, scoreFalsifierQuality],
  [TYPED_CONFIDENCE_HONESTY_DIMENSION, scoreTypedConfidenceHonesty],
  [READER_COMPREHENSION_DIMENSION, scoreReaderComprehension],
])

/** Dimensions with a real, non-stub detector as of `CORPUS_SCORING_HARNESS_VERSION`. */
export const REAL_DETECTOR_DIMENSIONS: readonly DimensionId[] = [
  DERIVATION_INTEGRITY_DIMENSION,
  B11_COVERAGE_DIMENSION,
  CITATION_PRECISION_DIMENSION,
  CITATION_RECALL_DIMENSION,
  CALIBRATION_LANGUAGE_HONESTY_DIMENSION,
  SAFETY_COMPLIANCE_DIMENSION,
  REGISTER_LEAKAGE_DIMENSION,
  HONEST_GAPS_DISCLOSURE_DIMENSION,
  VOICE_ENFORCEMENT_DIMENSION,
  CROSS_DOMAIN_CONTRADICTION_SURFACED_DIMENSION,
]

/** Always-`not_yet_measurable` stubs pending a later lane. */
export const UNSCORED_STUB_DIMENSIONS: readonly DimensionId[] = [
  FALSIFIER_QUALITY_DIMENSION,
  TYPED_CONFIDENCE_HONESTY_DIMENSION,
  READER_COMPREHENSION_DIMENSION,
]

/** Runs every registered dimension scorer against one observation. */
export function scoreAllDimensions(obs: TurnObservation): DimensionResult[] {
  return [...DIMENSION_REGISTRY.values()].map((scorer) => scorer(obs))
}
