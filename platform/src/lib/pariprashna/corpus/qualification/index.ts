/**
 * pariprashna/corpus/qualification/index.ts — lane P2-O (G3-G, PPR-32).
 * Barrel export for the model-qualification module. See `work_classes.ts`,
 * `bars.ts`, `gate.ts`, `registry.ts`, `fallback.ts` for the individual
 * pieces and their docblocks.
 */

export {
  WORK_CLASSES,
  QUERY_CLASS_WORK_CLASS_MAP,
  getWorkClassForQueryClass,
  getFixturesForWorkClass,
  type WorkClass,
  type QueryClassMapping,
} from './work_classes'

export {
  QUALIFICATION_PASS_THRESHOLD,
  SENSITIVE_SAFETY_STRICT_THRESHOLD,
  PREDICTIVE_CALIBRATION_THRESHOLD,
  QUALIFICATION_BARS,
  type DimensionRequirement,
  type QualificationBar,
} from './bars'

export {
  QUALIFICATION_GATE_VERSION,
  evaluateQualification,
  qualifyModelForWorkClass,
  type DimensionCheckResult,
  type QualificationStatus,
  type ModelQualificationResult,
} from './gate'

export {
  QUALIFICATION_REGISTRY_VERSION,
  buildQualificationRegistry,
  getQualificationRecord,
  isQualified,
  qualifiedModelIds,
  type QualificationRegistry,
} from './registry'

export {
  MODEL_SELECTION_MECHANISM_VERSION,
  selectModelForWorkClass,
  type ModelSelectionOutcome,
  type ModelSelectionResult,
} from './fallback'
