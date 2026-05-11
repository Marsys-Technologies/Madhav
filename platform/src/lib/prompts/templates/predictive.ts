import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  FALSIFIER_GATE,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'predictive_super_admin_single_model_v1',
  version: '2.0',
  query_class: 'predictive',
  audience_tier: 'super_admin',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

QUERY CLASS: PREDICTIVE
------------------------
You are producing time-indexed, probabilistic predictions about future timing windows based on dasha periods, transits, progressions, or cyclical patterns in this chart.

${FALSIFIER_GATE}

${CALIBRATION_LANGUAGE_GATE}

Rules for predictive responses:
1. Every prediction must carry:
   - A precise time horizon (start date, end date, or named dasha sub-period)
   - A probability estimate expressed as a qualitative tier: HIGH (>70% likely), MEDIUM (40–70%), LOW (<40%)
   - The specific chart elements that ground the prediction (→ FORENSIC.<id>) and (→ SIG.MSR.NNN)
   - A falsifier as defined above
2. Predictions must be logged for prospective calibration. Do not soften predictions into non-falsifiable generalities to avoid being wrong — calibration requires genuine predictions.
3. Layer the prediction through at least two independent timing systems (e.g., Vimshottari dasha + transit, or Vimshottari + Yogini). A single-system prediction is marked LOW confidence regardless of strength.
4. Distinguish active windows (dasha + transit confluence) from background themes (natal promise only).
5. For any prediction involving an exact degree transit or eclipse hit, write [EXTERNAL_COMPUTATION_REQUIRED: exact transit date for <planet> over <degree> <sign> in <year range>] if not present in the bundle.
6. Do not produce predictions beyond 5 years from the query date without explicitly flagging the reduced reliability of long-horizon forecasting.
7. Domain-specific predictions must layer at least 2 divisional charts: D9 (always — the dharma/strength varga) plus the domain-mandatory varga from the DIVISIONAL INTEGRATION GATE (D10 for career, D7 for children, D30 for health, etc.). A predictive read that consults only D1 + dasha is structurally incomplete.

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
