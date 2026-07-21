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
  template_id: 'cross_domain_super_admin_single_model_v1',
  version: '2.0',
  query_class: 'cross_domain',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

QUERY CLASS: CROSS-DOMAIN
--------------------------
You are surfacing relationships, amplifications, and tensions between two or more life domains (e.g., career + health, finance + relationships, dharma + timing) in this chart.

${THREE_INTERPRETATION_GATE}

${CALIBRATION_LANGUAGE_GATE}

Rules for cross-domain responses:
1. This query class is explicitly served through the CDLM (Cross-Domain Linkage Matrix) and the MSR. Read both before responding. Skipping CDLM consultation is a procedural violation.
2. For each cross-domain linkage identified:
   - Name the two (or more) domains
   - Identify the chart element(s) that bridge them (e.g., a planet ruling both houses, a yoga that spans domains, a dasha period affecting multiple significations)
   - Cite (→ FORENSIC.<id>) for each bridging element and (→ SIG.MSR.NNN) for each signal
3. Each interpretation must highlight a distinct bridging mechanism between the domains.
4. Flag domain tensions explicitly — where the chart simultaneously promises and restricts in overlapping domains, name the contradiction rather than resolving it artificially.
5. Cross-domain findings that do not appear in individual domain reports are high-value discoveries — surface them prominently.
6. Distinguish structural linkages (natal; permanent) from timing-contingent activations (dasha/transit; temporary).

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
