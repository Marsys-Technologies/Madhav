import type { AiInquiryProposal, InquiryScopeTuple } from './types'

export const BEYOND_ACARYA_CORPUS_VERSION = 'beyond-acarya-inquiry-corpus-v1' as const

export interface BeyondAcaryaAcceptanceCase {
  readonly case_id: string
  readonly question: string
  readonly scope_tuple: InquiryScopeTuple
  /** Independently curated from the product acceptance matrix, not planner output. */
  readonly expected_required_scu_ids: readonly string[]
  /** Reviewed graph relations that must be traversed for this combination. */
  readonly expected_edge_keys: readonly string[]
  /** Applicable capabilities outside the intent's deterministic floor. */
  readonly expected_novel_scu_ids: readonly string[]
  readonly ai_proposal?: AiInquiryProposal
}

const deep = {
  width: 'panoramic',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: false,
  entitlement: 'native',
} as const

export const BEYOND_ACARYA_ACCEPTANCE_CASES: readonly BeyondAcaryaAcceptanceCase[] = [
  {
    case_id: 'wealth_mechanism_timing_contradiction',
    question: 'Give me a complete wealth outlook including inhibitors, timing, varga contradictions and classical support.',
    scope_tuple: { ...deep, intent: 'wealth_deepdive', domains: ['wealth'] },
    expected_required_scu_ids: [
      'scu.finance.prosperity_assessment',
      'scu.bodha.mechanism.network',
      'scu.catalog.get_divisionals',
      'scu.yoga.firing_and_cancellation',
      'scu.kala.temporal_activation',
      'scu.catalog.get_dashas',
      'scu.catalog.query_planet_transit',
      'scu.catalog.query_classical_texts',
      'scu.catalog.judgment_query',
      'scu.catalog.query_contradictions',
    ],
    expected_edge_keys: [
      'scu.finance.prosperity_assessment|requires|scu.kala.temporal_activation',
      'scu.kala.temporal_activation|requires|scu.catalog.get_dashas',
    ],
    expected_novel_scu_ids: [
      'scu.catalog.judgment_query',
      'scu.catalog.query_contradictions',
    ],
  },
  {
    case_id: 'career_bhava_varga_timing',
    question: 'Deep career outlook: examine bhava, varga, current timing, contradictions and alternatives.',
    scope_tuple: { ...deep, intent: 'career_deepdive', domains: ['career'] },
    expected_required_scu_ids: [
      'scu.catalog.assess_career',
      'scu.catalog.judgment_query',
      'scu.catalog.get_divisionals',
      'scu.kala.temporal_activation',
      'scu.catalog.query_contradictions',
    ],
    expected_edge_keys: [
      'scu.catalog.assess_career|enables|scu.catalog.query_contradictions',
    ],
    expected_novel_scu_ids: [
      'scu.catalog.judgment_query',
      'scu.catalog.get_divisionals',
      'scu.kala.temporal_activation',
      'scu.catalog.query_contradictions',
    ],
  },
  {
    case_id: 'marriage_varga_cancellation_timing',
    question: 'Complete marriage outlook now: examine house, varga, timing, cancellations and contradictions.',
    scope_tuple: { ...deep, intent: 'marriage_deepdive', domains: ['marriage'] },
    expected_required_scu_ids: [
      'scu.catalog.assess_marriage',
      'scu.catalog.judgment_query',
      'scu.catalog.get_divisionals',
      'scu.kala.temporal_activation',
      'scu.catalog.query_contradictions',
    ],
    expected_edge_keys: [
      'scu.catalog.assess_marriage|enables|scu.catalog.query_contradictions',
    ],
    expected_novel_scu_ids: [
      'scu.catalog.judgment_query',
      'scu.catalog.get_divisionals',
      'scu.kala.temporal_activation',
      'scu.catalog.query_contradictions',
    ],
  },
  {
    case_id: 'house_yoga_later_hop',
    question: 'Explain this house yoga, its decisive cancellation, later-hop mechanisms and timing.',
    scope_tuple: {
      ...deep,
      intent: 'house_analysis',
      domains: ['general'],
      horizon: 'current',
    },
    expected_required_scu_ids: [
      'scu.catalog.judgment_query',
      'scu.yoga.firing_and_cancellation',
      'scu.catalog.get_dashas',
    ],
    expected_edge_keys: [
      'scu.catalog.judgment_query|enables|scu.catalog.get_dashas',
    ],
    expected_novel_scu_ids: [
      'scu.yoga.firing_and_cancellation',
      'scu.catalog.get_dashas',
    ],
  },
] as const
