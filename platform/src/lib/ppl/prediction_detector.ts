/**
 * MARSYS Chat V2 — PPL Prediction Detector (γ3)
 *
 * Detects time-indexed prediction sentences in assistant output.
 *
 * Stage 1: Fast regex scan — runs synchronously on the final text.
 * Stage 2: Haiku classifier — runs async post-stream; does NOT block the user stream.
 *
 * The detector is called in the route's onFinish callback. It emits
 * prediction_candidate data parts (one per detected sentence) that the client
 * renders as "Log as prediction" affordances.
 *
 * Learning Layer rule #4: the detector NEVER captures outcomes.
 */

export interface PredictionCandidate {
  /** The sentence or phrase identified as a time-indexed prediction. */
  text: string
  /** Approximate character offset in the full answer (for UI highlighting). */
  offset: number
  /** Confidence that this is a genuine prediction (0–1, fast heuristic). */
  score: number
  /** Pre-extracted horizon if detectable from the text. */
  horizon: string | null
}

// Patterns indicating a time-indexed prediction
const TIME_HORIZON_PATTERNS = [
  /\b(?:by|before|within|around|in)\s+(?:\d+\s+(?:day|week|month|year|decade)s?|(?:early|mid|late)[-\s]\d{4}|\d{4})\b/i,
  /\b(?:in the next|over the next|during the next)\s+\d+\s+(?:day|week|month|year)s?\b/i,
  /\b(?:this|next)\s+(?:month|year|quarter|decade)\b/i,
  /\b(?:20\d{2})\b/,  // any 4-digit year 2000–2099
  /\bQ[1-4]\s+20\d{2}\b/i,  // Q3 2026 style
]

const PREDICTION_VERB_PATTERNS = [
  /\b(?:will|shall|expect|predict|anticipate|forecast|likely|probable|likely to|set to|poised to|destined to)\b/i,
  /\b(?:is expected|are expected|will likely|should (?:see|experience|achieve))\b/i,
]

const FALSIFIER_INDICATORS = [
  /\b(?:unless|if not|provided that|assuming|contingent on|barring)\b/i,
]

function extractHorizon(sentence: string): string | null {
  for (const pattern of TIME_HORIZON_PATTERNS) {
    const match = sentence.match(pattern)
    if (match) return match[0].trim()
  }
  return null
}

function isPredictionSentence(sentence: string): { isCandidate: boolean; score: number } {
  const hasTimeHorizon = TIME_HORIZON_PATTERNS.some(p => p.test(sentence))
  const hasPredictionVerb = PREDICTION_VERB_PATTERNS.some(p => p.test(sentence))

  if (!hasTimeHorizon) return { isCandidate: false, score: 0 }

  // Both signals → high confidence
  if (hasPredictionVerb) return { isCandidate: true, score: 0.85 }

  // Time horizon only → moderate (may be historical reference)
  return { isCandidate: true, score: 0.45 }
}

/**
 * Synchronous regex scan — runs in < 1ms on typical answer texts.
 * Returns candidates sorted by score descending.
 */
export function detectPredictionCandidates(text: string): PredictionCandidate[] {
  if (!text || text.length === 0) return []

  // Split on sentence boundaries (. ! ?)
  const sentencePattern = /[^.!?]+[.!?](?:\s|$)/g
  const candidates: PredictionCandidate[] = []

  let match: RegExpExecArray | null
  while ((match = sentencePattern.exec(text)) !== null) {
    const sentence = match[0].trim()
    if (sentence.length < 20) continue // skip very short fragments

    const { isCandidate, score } = isPredictionSentence(sentence)
    if (isCandidate) {
      candidates.push({
        text: sentence,
        offset: match.index,
        score,
        horizon: extractHorizon(sentence),
      })
    }
  }

  return candidates.sort((a, b) => b.score - a.score)
}

/**
 * Extract a suggested falsifier from a candidate sentence.
 * Returns null if no falsifier indicators found.
 */
export function extractSuggestedFalsifier(text: string): string | null {
  for (const pattern of FALSIFIER_INDICATORS) {
    const match = text.match(pattern)
    if (match) {
      // Return the clause starting from the indicator
      const idx = text.indexOf(match[0])
      return text.slice(idx).replace(/[.!?]$/, '').trim()
    }
  }
  return null
}
