/**
 * Suggested question templates keyed by build asset ID.
 *
 * Used by QuestionSuggester to surface contextual starter questions
 * based on which assets have been built for a chart.
 *
 * [PHASE-D-05]
 */

export const QUESTION_TEMPLATES: Record<string, string[]> = {
  A3: [
    'What is the strength of the Lagna lord and where is it placed?',
    'Which planets occupy the Lagna (1st house) and what is their dignity?',
  ],
  A7: [
    'What Maha-dasha and Antar-dasha am I currently running?',
    'When does my next major dasha transition occur?',
  ],
  A8: [
    'What are the dominant yogas in this chart?',
    'Which planets have the highest Shadbala?',
  ],
  A10: [
    'What are the top 5 strongest signals in the Signal Catalog?',
    'Which life domains are most strongly activated?',
  ],
  A15: [
    'What are the upcoming convergence windows in the next 12 months?',
    'When is the next peak activation period?',
  ],
}

/**
 * Returns up to `count` suggested questions from the ready assets.
 * Iterates asset IDs in order, pulling templates until the quota is met.
 */
export function getSuggestedQuestions(readyAssets: string[], count = 5): string[] {
  const questions: string[] = []
  for (const assetId of readyAssets) {
    const templates = QUESTION_TEMPLATES[assetId] ?? []
    questions.push(...templates)
    if (questions.length >= count) break
  }
  return questions.slice(0, count)
}
