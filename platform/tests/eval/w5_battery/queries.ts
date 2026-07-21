/**
 * queries.ts — W5 Lane L10 readback + tool-selection battery, query corpus.
 *
 * Family list confirmed from the LIVE Vidhi floor registry
 * (`platform/src/lib/vidhi/registry_data.ts` `VIDHI_INTENT_FLOORS`), NOT guessed:
 * the six domain/breadth/general floors the W4 floor-completeness campaign
 * (STATE.md "W4 CLOSE") explicitly brought to the §B0.4 mandatory tag set are
 * `wealth_deepdive`, `career_deepdive`, `health_deepdive`, `marriage_deepdive`,
 * `panoramic_breadth`, `general_synthesis` — i.e. career/wealth/health/marriage/
 * panoramic/general, exactly as the lane brief anticipated. (`structure_read` and
 * `retrieval_only` are two further registered floors, deliberately out of this
 * battery's family list: they are depth/structural variants, not domain families,
 * and are already exercised indirectly via the `depth` dimension in
 * `compiled_floor_adapter.test.ts`.)
 *
 * Every query below was verified live against `classifyScope()` +
 * `classifierIntentToCompilerIntent()` (the actual deterministic W4 routing path,
 * `platform/src/lib/pipeline/compiled_floor_adapter.ts`) before being committed here
 * — see the W5_BATTERY_BASELINE artifact §1 for the verification note. 5 queries per
 * family × 6 families = 30 entries, run against both required charts
 * (482012f1-710e-4a25-994a-93821f5871aa canonical native, 1c826d5a-41cb-4450-b4dc-
 * 59d440e5f75a SAFE non-native) = 60 (query × chart) combinations per battery pass.
 */
import type { IntentClass } from '@/lib/vidhi/types'

export interface BatteryQuery {
  readonly id: string
  readonly family: 'wealth' | 'career' | 'health' | 'marriage' | 'panoramic' | 'general'
  /** The compiler IntentClass a correct deterministic routing MUST produce for this query. */
  readonly expected_intent: IntentClass
  readonly query: string
}

export const BATTERY_QUERIES: readonly BatteryQuery[] = [
  // ── wealth ──────────────────────────────────────────────────────────────────
  { id: 'W5B.001', family: 'wealth', expected_intent: 'wealth_deepdive', query: 'What does my chart show about long-term wealth and financial prosperity?' },
  { id: 'W5B.002', family: 'wealth', expected_intent: 'wealth_deepdive', query: 'Will my income and savings grow this year?' },
  { id: 'W5B.003', family: 'wealth', expected_intent: 'wealth_deepdive', query: 'Explain the dhana yogas affecting my finances.' },
  { id: 'W5B.004', family: 'wealth', expected_intent: 'wealth_deepdive', query: 'How strong is my capacity for financial gains in this life?' },
  { id: 'W5B.005', family: 'wealth', expected_intent: 'wealth_deepdive', query: 'What is my prosperity and wealth potential in this life?' },

  // ── career ──────────────────────────────────────────────────────────────────
  { id: 'W5B.006', family: 'career', expected_intent: 'career_deepdive', query: 'What career path suits me best given my 10th house?' },
  { id: 'W5B.007', family: 'career', expected_intent: 'career_deepdive', query: 'Will I get a promotion at work soon?' },
  { id: 'W5B.008', family: 'career', expected_intent: 'career_deepdive', query: 'What does my chart say about my profession and business success?' },
  { id: 'W5B.009', family: 'career', expected_intent: 'career_deepdive', query: 'Is this a good time for a job change?' },
  { id: 'W5B.010', family: 'career', expected_intent: 'career_deepdive', query: 'How strong is my career potential long term?' },

  // ── health ──────────────────────────────────────────────────────────────────
  { id: 'W5B.011', family: 'health', expected_intent: 'health_deepdive', query: 'What does my chart reveal about my health and longevity?' },
  { id: 'W5B.012', family: 'health', expected_intent: 'health_deepdive', query: 'Are there any disease indicators I should be aware of?' },
  { id: 'W5B.013', family: 'health', expected_intent: 'health_deepdive', query: 'What is my ayurdaya and vitality like?' },
  { id: 'W5B.014', family: 'health', expected_intent: 'health_deepdive', query: 'Should I be concerned about any medical issues this year?' },
  { id: 'W5B.015', family: 'health', expected_intent: 'health_deepdive', query: 'How is my physical health and vitality per my chart?' },

  // ── marriage ────────────────────────────────────────────────────────────────
  { id: 'W5B.016', family: 'marriage', expected_intent: 'marriage_deepdive', query: 'When will I marry, and what does my chart say about the timing?' },
  { id: 'W5B.017', family: 'marriage', expected_intent: 'marriage_deepdive', query: 'What does my chart say about my spouse and relationship compatibility?' },
  { id: 'W5B.018', family: 'marriage', expected_intent: 'marriage_deepdive', query: 'Is there a risk of divorce or marital discord?' },
  { id: 'W5B.019', family: 'marriage', expected_intent: 'marriage_deepdive', query: 'How strong is my 7th house for marriage happiness?' },
  { id: 'W5B.020', family: 'marriage', expected_intent: 'marriage_deepdive', query: 'Tell me about my romantic relationships and love life.' },

  // ── panoramic (broad width, domain-agnostic sweep) ──────────────────────────
  { id: 'W5B.021', family: 'panoramic', expected_intent: 'panoramic_breadth', query: 'Give me a comprehensive, whole-chart life reading covering everything.' },
  { id: 'W5B.022', family: 'panoramic', expected_intent: 'panoramic_breadth', query: 'I want the complete picture across career, wealth, marriage, and health.' },
  { id: 'W5B.023', family: 'panoramic', expected_intent: 'panoramic_breadth', query: 'What is the big picture of my entire life based on my birth chart?' },
  { id: 'W5B.024', family: 'panoramic', expected_intent: 'panoramic_breadth', query: 'Provide a holistic 360 overview of my whole chart.' },
  { id: 'W5B.025', family: 'panoramic', expected_intent: 'panoramic_breadth', query: 'Walk me through my full life story across every major domain.' },

  // ── general (no domain keyword, standard width/depth — the fallback floor) ──
  { id: 'W5B.026', family: 'general', expected_intent: 'general_synthesis', query: 'What is the deeper meaning behind the patterns in my chart?' },
  { id: 'W5B.027', family: 'general', expected_intent: 'general_synthesis', query: 'Help me understand my personality and life purpose.' },
  { id: 'W5B.028', family: 'general', expected_intent: 'general_synthesis', query: 'What contradictions exist across my chart that I should know about?' },
  { id: 'W5B.029', family: 'general', expected_intent: 'general_synthesis', query: 'Explain the key themes running through my life story.' },
  { id: 'W5B.030', family: 'general', expected_intent: 'general_synthesis', query: 'What should I understand about myself from this chart?' },
] as const

/** The two campaign-required charts (CLAUDE.md §B canonical native + the SAFE non-native
 *  used throughout this campaign's docs for multi-chart / cross-contamination checks). */
export const BATTERY_CHARTS: readonly { readonly label: string; readonly chart_id: string }[] = [
  { label: 'abhisek_canonical', chart_id: '482012f1-710e-4a25-994a-93821f5871aa' },
  { label: 'abhinandan_safe', chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a' },
]
