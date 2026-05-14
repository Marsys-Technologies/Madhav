/**
 * class_suggestions.ts — Gate III §11.
 *
 * Hardcoded class-grouped example queries shown in the empty-state "By type"
 * tab. Edit freely; this is the single source of truth.
 */

import type { QueryClass } from '@/lib/jyotish/domain_labels'
import { QUERY_CLASS_LABELS } from '@/lib/jyotish/domain_labels'

export const CLASS_SUGGESTIONS: Record<QueryClass, string[]> = {
  factual: [
    'What house is my Moon in?',
    "What's my Atmakaraka?",
    'Which planets in my chart are vargottama?',
    'List the planets that are debilitated.',
  ],
  interpretive: [
    'What does my Saturn–Moon affliction mean for my emotional life?',
    'How do I read the strength of my Lagna lord?',
    'What does the 9th-house Jupiter say about my dharma?',
    'Interpret the role of Mars in my 10th house.',
  ],
  predictive: [
    'What does my current Mahadasha–Antardasha indicate for the next 18 months?',
    'How will the upcoming Jupiter transit affect my 10th house?',
    'When does my next Saturn return begin?',
    'What can I expect from the Venus–Rahu period?',
  ],
  cross_domain: [
    'How do my career and marriage indicators interact?',
    'Compare the timing of professional shifts with health markers.',
  ],
  discovery: [
    "What unusual patterns show up across my divisional charts?",
    'Which yogas in my chart are most active right now?',
    'What contradictions does the corpus surface about my chart?',
  ],
  holistic: [
    'Give me an overall reading of where I am right now.',
    'Synthesize the dominant theme across my Rasi, Navamsa, and current dasha.',
    'What is the core arc of the next three years?',
  ],
  remedial: [
    'What classical remedies match my Saturn affliction?',
    'Are there gemstones suitable for strengthening my Lagna lord?',
  ],
  cross_native: [
    'How does my chart compare with my partner\'s across the 7th house?',
  ],
  classical_grounding: [
    'Which classical texts support the Sasha Mahapurusha Yoga in my chart?',
    'What does BPHS say about Saturn exalted in Libra in the 10th house?',
    'Find classical attributions for the Venus–Rahu conjunction interpretation.',
  ],
}

export const CLASS_TAB_ORDER: QueryClass[] = [
  'holistic',
  'interpretive',
  'predictive',
  'discovery',
  'remedial',
  'factual',
  'cross_domain',
  'cross_native',
]

export function classLabel(c: QueryClass): string {
  return QUERY_CLASS_LABELS[c]
}
