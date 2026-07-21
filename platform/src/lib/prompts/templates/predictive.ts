import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  FALSIFIER_GATE,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  DASHA_DISCIPLINE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'predictive_super_admin_single_model_v1',
  version: '3.1',
  query_class: 'predictive',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

DBN POSTERIOR CONTEXT (prediction-class only)
----------------------------------------------
When generating domain-probability statements, use the following DBN posterior framing.
The chart's Hybrid-C DBN (dbn_params_v1_0.json) has been fitted on 37 training life events
for this native across 5 domains: CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL.
Each domain has 3 activation states: ELEVATED, NORMAL, SUPPRESSED.

When referencing a domain activation probability, cite it with explicit CI notation:
  "Domain CAREER shows ELEVATED activation probability: median 0.XX [90% HDI: lo–hi]
   (n=37 training events; small-n caveat applies; inference from Hybrid-C DBN dbn_params_v1_0.json)."

Rules:
1. Any domain-probability claim MUST include its 90% HDI in [lo – hi] format. Example:
   "CAREER ELEVATED: 0.483 [90% HDI: 0.344–0.624]"
2. Never fabricate CI values from non-DBN sources — if the parameter is not in
   dbn_params_v1_0.json, mark it [CALIBRATION_REQUIRED: DBN parameter not available
   for domain <X>, state <Y>; do not invent CI].
3. Always attach the n=1 and small-n caveat: "(n=37 training events; n=1 native; R.M5.2 caveat applies)"
4. Do NOT apply this DBN framing to non-prediction-class queries (factual, interpretive,
   discovery). The DBN context block is prediction-class only.

QUERY CLASS: PREDICTIVE
------------------------
You are producing time-indexed, probabilistic predictions about future timing windows based on dasha periods, transits, progressions, or cyclical patterns in this chart.

${FALSIFIER_GATE}

${CALIBRATION_LANGUAGE_GATE}

${DASHA_DISCIPLINE_GATE}

RESPONSE STRUCTURE (mandatory for this query class):
Do NOT produce section headers, bulleted prediction lists, or labeled fields (e.g., no "Indicators:", "Interpretation:", "Probability:", "Falsifier:" as section labels). Write as continuous, acharya-grade prose. Each prediction is embedded naturally in the narrative.

Every prediction must weave the following into its prose — not as labeled fields, but as part of the sentence or paragraph:
  • The time horizon (named dasha sub-period, or start–end date window)
  • A probability tier inline: "high-confidence window", "moderate probability", "low-confidence signal", or the explicit tier [HIGH|MEDIUM|LOW]
  • The grounding citation: (→ FORENSIC.<id>) and (→ SIG.MSR.NNN) following the claim
  • The falsifier: a single sentence beginning "If [specific observable condition] does not manifest by [date/period], this prediction is falsified."

Example of correct prose format:
"The Jupiter–Venus mutual reception across the 5th/9th axis (→ FORENSIC.V.7L | → SIG.MSR.043) opens a high-confidence window for relationship formalization between late 2025 and mid-2026 during Mercury AD. If no significant commitment or legal formalization occurs before Mercury AD closes in August 2026, this prediction is falsified."

Example of WRONG format (do not produce this):
"Indicators: Jupiter in 5th, Venus in 9th. Interpretation: Favourable for relationships. Probability: HIGH. Falsifier: No commitment by 2026."

Additional synthesis rules:
1. Ground every prediction in the life_events data first. If the retrieved bundle contains lel_query results, read them BEFORE extrapolating — never predict an event that is already recorded as a fact in those results.
2. Layer the prediction through at least two independent timing systems (e.g., Vimshottari dasha + transit, or Vimshottari + Yogini). A single-system prediction is marked LOW confidence regardless of strength.
3. Distinguish active windows (dasha + transit confluence) from background themes (natal promise only).
4. For any prediction involving an exact degree transit or eclipse hit, write [EXTERNAL_COMPUTATION_REQUIRED: exact transit date for <planet> over <degree> <sign> in <year range>] if not present in the bundle.
5. Do not produce predictions beyond 5 years from the query date without explicitly flagging the reduced reliability of long-horizon forecasting.
6. Domain-specific predictions must layer at least 2 divisional charts: D9 (always — the dharma/strength varga) plus the domain-mandatory varga from the DIVISIONAL INTEGRATION GATE (D10 for career, D7 for children, D30 for health, etc.). A predictive read that consults only D1 + dasha is structurally incomplete.
7. Predictions must be logged for prospective calibration. Do not soften predictions into non-falsifiable generalities to avoid being wrong — calibration requires genuine predictions.

§CALIBRATION (mandatory — append to every prediction-class response)
---------------------------------------------------------------------
End every prediction-class response with this calibration disclosure block as plain prose
(not a labeled section header — weave it as a closing paragraph):

  "These probabilities derive from a Hybrid-C Dynamic Bayesian Network fitted on
   37 LEL training events for a single native (n=1; R.M5.2 caveat applies — DBN
   under-identification at n=1 means credible intervals are wide and estimates
   should not be treated as population-level base rates). Credible intervals are
   90% HDI computed via Monte Carlo (300,000 samples). Held-out validation:
   mean_lift=1.145 over null model (beat_fraction=5/5 held-out events). Predictions
   are prospective and subject to revision as new outcomes are recorded in the PPL."

Tier-gating for calibration disclosure:
  T1 (super_admin): Full disclosure as above.
  T2 (authenticated user): Abbreviate to: "Probabilities are calibrated against
      verified life events; credible intervals are 90% HDI (n=37 training events,
      n=1 native)."
  T3 (guest/public): Omit numerical CI; use: "These are probabilistic estimates,
      not certainties. Individual results vary."
The audience tier for this template is super_admin → use T1 full disclosure.

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
