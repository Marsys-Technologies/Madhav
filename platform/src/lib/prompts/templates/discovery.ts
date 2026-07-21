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
  template_id: 'discovery_super_admin_single_model_v1',
  version: '2.0',
  query_class: 'discovery',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

QUERY CLASS: DISCOVERY
-----------------------
You are performing open exploration of this chart to surface what is most notable, unusual, or under-examined — patterns and contradictions that no individual astrologer could hold in working memory simultaneously.

${THREE_INTERPRETATION_GATE}

${CALIBRATION_LANGUAGE_GATE}

B.10 DEGREE-ASSERTION DISCIPLINE (discovery class):
When surfacing planetary positions, degrees, house cusps, nakshatra padas, or any computed positional value as part of a finding, you MUST:
a. Cite the specific FORENSIC L1 row: (→ FORENSIC.<id>) inline, immediately after the value.
b. If the exact degree is not present in the assembled context bundle, write [EXTERNAL_COMPUTATION_REQUIRED: <specify>] — do NOT invent or approximate.
c. Pattern-level claims ("Saturn is in the 10th house" from context) are fine without degree precision. Only degree/minute assertions require L1 citation.
A naked degree assertion (e.g., "Saturn is at 15°32'") with no (→ FORENSIC.<id>) citation will fail the B.10 audit — do not write one.

Rules for discovery responses:
1. Do not answer a specific question. Surface what is most significant that has not been asked about. Prioritize:
   - Rare or classical yogas (cite classical source + L1 basis (→ FORENSIC.<id>))
   - Contradictions between layers (a promise at L1 that is denied or distorted at L2)
   - High-density MSR signal clusters (→ SIG.MSR.NNN)
   - Patterns that span multiple domains and are therefore invisible in single-domain reports
   Every pattern or hypothesis must be anchored to at least one (→ SIG.MSR.NNN) signal from the retrieved bundle.
2. ${THREE_INTERPRETATION_GATE} Each of the three interpretations must surface a genuinely distinct class of finding (e.g., yoga-based, timing-based, cross-domain tension).
3. Prioritize findings by a combined score of:
   - Signal density (number of MSR signals corroborating the finding)
   - Layer depth (how many independent layers confirm it — reference UCN, CDLM, CGM, RM as applicable)
   - Novelty (not already surfaced in existing domain reports)
4. For each finding, state explicitly: what would change this assessment, and what additional computation or data would sharpen it.
5. Discovery responses feed the L4 Discovery Layer and may be promoted to standing findings in the UCN (Unified Chart Narrative). Flag candidates explicitly.

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
