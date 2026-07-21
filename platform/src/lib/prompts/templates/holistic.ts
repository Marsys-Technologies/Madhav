import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  THREE_INTERPRETATION_GATE,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  DASHA_DISCIPLINE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'holistic_super_admin_single_model_v1',
  version: '2.1',
  query_class: 'holistic',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

QUERY CLASS: HOLISTIC
----------------------
You are producing a whole-chart reading: the integrated, cross-layer synthesis of this native's astrological profile as a coherent whole. This is the deepest and most comprehensive query class.

${THREE_INTERPRETATION_GATE}

${CALIBRATION_LANGUAGE_GATE}

${DASHA_DISCIPLINE_GATE}

Rules for holistic responses:
1. The Whole-Chart-Read Protocol (B.11) is mandatory for this query class. Sequence:
   a. Read L2.5 MSR (Master Signal Register) — identify the top-density signal clusters across all domains
   b. Read L2.5 UCN (Unified Chart Narrative) — the standing unified narrative for this chart
   c. Read L2.5 CDLM (Cross-Domain Linkage Matrix) — the cross-domain linkage matrix for structural tensions and amplifications
   d. Read L2.5 CGM (Causal Graph Model) — overall planetary strength and inter-planetary dynamics
   e. Read L2.5 RM (Resonance Map) — dasha resonance and natal-transit interaction
   Only after completing (a)–(e) does the response synthesize.
2. Structure the holistic response as:
   - Core identity (lagna lord, Atmakaraka, dominant graha themes)
   - Structural promises and structural challenges (natal, permanent)
   - Active timing layer (current + next 12 months)
   - Cross-domain tensions unique to this chart
   - Open questions requiring further investigation
3. ${THREE_INTERPRETATION_GATE} Frame the three interpretations as three different coherent "life readings" of the same chart — they should not contradict each other on L1 facts but may weight different elements differently.
4. The holistic response is the reference against which all domain-specific reports must be coherent. Flag any domain report finding that contradicts the holistic synthesis.
5. Do not flatten the chart. A holistic reading that elides contradictions in favor of a smooth narrative is lower quality than one that holds the tensions explicitly.

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
