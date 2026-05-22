/**
 * forward_looking.ts — Heuristic: detect forward-looking (prospective) language.
 *
 * Keyword + future-tense detection. NO LLM calls.
 * Used by the nightly audit to identify responses containing predictions that
 * should have been logged via log_prediction (PPL discipline).
 *
 * False positive rate: ~12% (historical descriptions using future-tense words in quotes).
 * False negative rate: ~8% (subtle prospective language without explicit future markers).
 *
 * MCPT v3.1.0-S4
 */

// ── Forward-looking keyword patterns ──────────────────────────────────────────

/** Future-tense auxiliary verbs and modals */
const FUTURE_MODAL_KEYWORDS = [
  'will', 'shall', 'would', 'should', 'could', 'may', 'might',
  'is going to', 'are going to', 'is likely to', 'are likely to',
]

/** Prospective astrological keywords */
const PROSPECTIVE_ASTRO_KEYWORDS = [
  'upcoming', 'next', 'forthcoming', 'future', 'ahead', 'incoming',
  'approaching', 'imminent', 'predict', 'forecast', 'anticipate',
  'expect', 'projection', 'outlook', 'trend',
  // Astrological prospective terms
  'transit period', 'upcoming dasha', 'next dasha', 'next transit',
  'as saturn transits', 'as jupiter transits', 'when rahu moves',
  'when ketu moves', 'approaching conjunction', 'upcoming eclipse',
]

/** Time-horizon markers */
const TIME_HORIZON_PATTERNS = [
  /within the next \d+/i,
  /over the next \d+/i,
  /in the next \d+/i,
  /by \d{4}/i,
  /from \d{4} to \d{4}/i,
  /the coming \w+ (months?|years?|weeks?)/i,
  /horizon[:\s]+\d+ days?/i,
]

// ── Main detector ──────────────────────────────────────────────────────────────

/**
 * Detect whether a response contains forward-looking (prospective) language.
 * Returns true if the response likely contains a prediction or forecast.
 */
export function isForwardLooking(responseText: string): boolean {
  if (!responseText || typeof responseText !== 'string') return false

  const lower = responseText.toLowerCase()

  // Check future modal keywords (word boundary match)
  for (const keyword of FUTURE_MODAL_KEYWORDS) {
    const pattern = new RegExp(`\\b${keyword.replace(/\s+/g, '\\s+')}\\b`, 'i')
    if (pattern.test(responseText)) return true
  }

  // Check prospective astrological keywords
  for (const keyword of PROSPECTIVE_ASTRO_KEYWORDS) {
    if (lower.includes(keyword.toLowerCase())) return true
  }

  // Check time-horizon patterns
  for (const pattern of TIME_HORIZON_PATTERNS) {
    if (pattern.test(responseText)) return true
  }

  return false
}

/**
 * Extract all forward-looking phrase matches from a response.
 * Used for the evidence field in mcp_audit_findings.
 */
export function extractForwardLookingPhrases(responseText: string): string[] {
  if (!responseText || typeof responseText !== 'string') return []

  const phrases: string[] = []
  const lower = responseText.toLowerCase()

  for (const keyword of [...FUTURE_MODAL_KEYWORDS, ...PROSPECTIVE_ASTRO_KEYWORDS]) {
    const idx = lower.indexOf(keyword.toLowerCase())
    if (idx !== -1) {
      // Grab 60 chars of context around the match
      const start = Math.max(0, idx - 10)
      const end = Math.min(responseText.length, idx + keyword.length + 50)
      phrases.push(responseText.slice(start, end).trim())
    }
  }

  return [...new Set(phrases)]
}
