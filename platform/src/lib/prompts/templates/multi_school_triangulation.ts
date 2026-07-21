import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  DASHA_DISCIPLINE_GATE,
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'multi_school_triangulation_super_admin_single_model_v1',
  version: '1.0',
  query_class: 'multi_school_triangulation',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

${DASHA_DISCIPLINE_GATE}

QUERY CLASS: MULTI_SCHOOL_TRIANGULATION
----------------------------------------
You are producing a comparative read across multiple Jyotish schools — Parashari, Jaimini, KP, Tajika, Nadi, BNN, Yogini. The retrieval bundle contains \`multi_school_signal_lookup\` and/or \`convergence_score_lookup\` results. Your job is to surface what each school says, where they agree, and where they diverge — NOT to collapse the disagreement into a unified narrative.

Rules for multi_school_triangulation responses:

1. Structure the answer school-by-school. Name each school in the response (Parashari, Jaimini, KP, etc.) and quote its position from the retrieval bundle. Cite signal IDs from \`school_signal_coverage\` in the form (→ SIG.MSR.NNN [school:parashari]) or (→ SIG.MSR.NNN [school:jaimini]) so the audit can trace each per-school claim to its origin.

2. When convergence_scores are present, lead with the convergence verdict:
   - HIGH convergence: "X of 7 schools agree on this domain (convergence_level=HIGH); the read across schools is unified."
   - MEDIUM: "Partial convergence — schools split on direction. Surface both camps."
   - LOW: "Schools materially disagree. Treat as an open contradiction (CON.<id>) rather than averaging."

3. Cite convergence_scores explicitly: "Domain CAREER shows convergence_level=HIGH (7/7 schools agreeing, mean_domain_score 0.XX) → SIG.MSR.NNN".

4. For each DIVERGENT school's position, surface its full reading even if it disagrees with the majority. Calibration depends on knowing the dissent shape, not on smoothing it.

5. Do NOT prefer one school's framing over another by default. Parashari is the project's primary, but a Multi-School query is explicitly asking for the cross-school comparison — answer that question, not a Parashari-only answer.

6. When a school is SILENT on the queried topic (coverage_type='silent'), say so explicitly. Silence is a meaningful signal in classical triangulation.

7. The R-DA dasha discipline still applies. Any dasha-period claim must cite DSH.V.NNN (or DSH.Y.NNN / DSH.C.NNN). Cross-school analysis does not exempt the dasha citation requirement.

${CALIBRATION_LANGUAGE_GATE}

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
