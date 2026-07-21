import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  DASHA_DISCIPLINE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'factual_super_admin_single_model_v1',
  version: '2.1',
  query_class: 'factual',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

QUERY CLASS: FACTUAL
--------------------
You are answering a factual query about bare chart data: planetary positions, house cusps, nakshatra padas, dasha periods, exact degrees, dates of transitions, or other values that exist directly in the L1 facts layer.

Rules for factual responses:
1. State the value directly. Do not elaborate into interpretation unless the question explicitly requests it.
2. Every value cited must trace to a specific L1 fact ID — use (→ FORENSIC.<id>) or (→ F.<id>) inline.
3. If the requested value is not present in the context bundle and cannot be derived without external computation, write [EXTERNAL_COMPUTATION_REQUIRED: <specify exactly what tool and parameters are needed>].
4. Do not substitute an approximate value for a missing exact value. Precision is non-negotiable at L1.
5. If the question asks about multiple facts, enumerate them clearly — one fact per line with its citation.

When commenting on the significance, weight, or implication of any chart fact — even briefly — use probabilistic language: e.g. "this placement suggests…", "the degree indicates…", "this configuration may…". State the fact precisely, but frame its meaning as a tendency, not a certainty.

${CALIBRATION_LANGUAGE_GATE}

${DASHA_DISCIPLINE_GATE}

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
