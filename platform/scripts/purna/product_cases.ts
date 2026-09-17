import type { InquiryScopeTuple } from '../../src/lib/vidhi/inquiry/types'

export type ProductCaseExpected = 'supported_complete' | 'honest_insufficient'

export interface FrozenProductCase {
  readonly case_id: string
  readonly description: string
  readonly question: string
  readonly scope_tuple: InquiryScopeTuple
  readonly required_dimensions: readonly string[]
  readonly deterministic_gates: readonly string[]
  readonly expected: ProductCaseExpected
}

const deep = { depth: 'interpretive', horizon: 'multi_year' } as const
const focused = { depth: 'retrieval', horizon: 'current' } as const
const complete = ['inquiry_closure_receipt', 'response_accountability', 'citation_resolution', 'required_evidence_dimensions'] as const
const insufficient = ['inquiry_closure_receipt', 'response_accountability', 'named_missing_evidence', 'bounded_insufficiency'] as const

function cases(
  family: string,
  domain: string,
  dimensions: readonly string[],
  prompts: readonly [string, string, string, string, string],
): readonly FrozenProductCase[] {
  const codes = ['1', '2', '3', '4', '5'] as const
  return prompts.map((question, index) => ({
    case_id: `${family.toLowerCase()}_${codes[index]}`,
    description: `${family} ${['focused fact', 'deep family inquiry', 'cross-domain contradiction', 'time-bounded inquiry', 'deliberately insufficient evidence'][index]}`,
    question,
    scope_tuple: index === 0 ? { ...focused, intent: 'assess', domains: [domain] } : { ...deep, intent: 'assess', domains: [domain] },
    required_dimensions: index === 4 ? [...dimensions, 'named_missing_evidence', 'bounded_conclusion'] : dimensions,
    deterministic_gates: index === 4 ? insufficient : complete,
    expected: index === 4 ? 'honest_insufficient' : 'supported_complete',
  }))
}

/**
 * The immutable additional denominator from plan section 13.  These prompts are
 * product inputs, not planner output; a run configuration supplies chart and
 * temporal anchors.  The fifth case in each family uses a controlled missing
 * input/receipt fixture and must not be satisfied by abstention on cases 1-4.
 */
export const FROZEN_PRODUCT_CASES: readonly FrozenProductCase[] = [
  ...cases('Wealth', 'wealth', ['natal_promise', 'wealth_mechanisms', 'strength', 'vargas', 'cancellation', 'timing'], [
    'Which source-backed combinations support financial promise?',
    'Explain the financial promise, constraints, and business implications using all material evidence.',
    'Reconcile strong wealth indications with evidence of strain or loss.',
    'What is the nearest supported activation window within the supplied horizon, and what could prevent manifestation?',
    'With required timing evidence unavailable, distinguish structural promise from timing that cannot be established.',
  ]),
  ...cases('Career', 'career', ['profession_bhava_links', 'd10', 'strength', 'yoga', 'period_or_transit', 'contradictions'], [
    'Which current period and chart factors are relevant to career?',
    'Explain the career trajectory and advancement constraints.',
    'Reconcile promotion prospects with business and financial indicators.',
    'Which supported promotion windows fall within the supplied horizon?',
    'With required professional-divisional evidence absent, identify what cannot be concluded.',
  ]),
  ...cases('Marriage', 'marriage', ['relevant_houses_and_lords', 'karakas', 'd9', 'mechanisms', 'cancellation', 'timing'], [
    'Which source-backed relationship factors are present?',
    'Explain relationship promise and tensions jointly.',
    'Reconcile conflicting natal and divisional indications.',
    'Which supported relationship or marriage windows fall within the supplied horizon?',
    'With birth-time-sensitive evidence unreliable, bound the interpretation instead of inventing timing.',
  ]),
  ...cases('Family', 'family', ['relevant_bhavas_and_lords', 'd7', 'strength', 'family_mechanisms', 'timing'], [
    'Which factors are relevant to children and family?',
    'Explain the family and children indications and limitations.',
    'Reconcile supportive promise with inhibiting indicators.',
    'Identify supported family-event windows within the horizon, without promising a pregnancy or birth.',
    'With required divisional and timing data missing, explain the limits and needed inputs.',
  ]),
  ...cases('Health', 'health', ['vulnerability_and_resilience', 'bhavat_bhavam', 'vargas', 'timing', 'uncertainty'], [
    'Which chart factors are relevant to resilience and vulnerability?',
    'Explain the pattern without diagnosis or certainty.',
    'Reconcile protective indicators with adverse timing signals.',
    'Identify astrologically indicated periods for additional attention, not medical predictions presented as fact.',
    'Reject precise disease or diagnosis claims unsupported by the data and state the appropriate limits.',
  ]),
  ...cases('Events', 'cross_domain', ['event_provenance', 'frozen_chronology', 'structural_mechanisms', 'cancellation', 'activation', 'counterevidence'], [
    'Which recorded events and yoga findings are available to this inquiry?',
    'Compare supplied event history with chart mechanisms, including mismatches.',
    'Distinguish plausible alignment, ambiguous fit, and contradiction; do not force every event to match.',
    'Identify the nearest and subsequent supported trigger windows for the supplied named yoga, including cancellation checks.',
    'With no authorized event log or missing yoga identity, ask for the missing information and do not invent an alignment.',
  ]),
]

if (FROZEN_PRODUCT_CASES.length !== 30 || new Set(FROZEN_PRODUCT_CASES.map((item) => item.case_id)).size !== 30) {
  throw new Error('PURNA_PRODUCT_CASE_DENOMINATOR_INVALID')
}
