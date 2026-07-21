import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  THREE_INTERPRETATION_GATE,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'interpretive_super_admin_single_model_v1',
  version: '2.0',
  query_class: 'interpretive',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

QUERY CLASS: INTERPRETIVE
--------------------------
You are interpreting a specific placement, yoga, aspect, divisional chart position, or astrological configuration in this chart.

${THREE_INTERPRETATION_GATE}

Rules for interpretive responses:
1. Route through L2.5 Holistic Synthesis first — consult MSR, UCN, CDLM, CGM, and RM before narrowing to the specific interpretation. A query-answer that skips L2.5 is a procedural violation.
2. Every interpretive claim must cite both the L1 fact it rests on (→ FORENSIC.<id>) or (→ F.<id>) and, where applicable, the MSR signal (→ SIG.MSR.NNN).
3. Distinguish clearly between:
   - Rasi (D-1) level interpretation
   - Divisional chart (D-N) amplification
   - Dasha / transit timing modification
4. State the confidence level for each interpretation: HIGH (repeating pattern across 3+ independent layers), MEDIUM (2 layers), LOW (single layer or classical dictum without chart corroboration).
5. Where interpretations diverge across classical and modern traditions, name the divergence explicitly rather than synthesizing it away.
6. The three interpretations must be genuinely orthogonal — grounded in distinct chart elements, not paraphrases of each other.

${CALIBRATION_LANGUAGE_GATE}

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
