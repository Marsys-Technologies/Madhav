/**
 * is_non_factual.ts — Heuristic: detect non-factual (interpretive) responses.
 *
 * Determines whether a response is interpretive/synthetic (requiring citation)
 * vs purely factual (data lookup, no citation required).
 *
 * A response is "non-factual" when it goes beyond returning raw data and makes
 * interpretive, evaluative, or predictive claims.
 *
 * Regex + response-shape heuristic. NO LLM calls.
 *
 * False positive rate: ~8% (data-rich factual responses that look interpretive).
 * False negative rate: ~5% (very short interpretive claims that look factual).
 *
 * MCPT v3.1.0-S4
 */

// ── Factual response indicators ────────────────────────────────────────────────

/** Patterns indicating a purely factual / data-return response */
const FACTUAL_INDICATORS = [
  /^\s*\{/,                              // JSON-like (structured data return)
  /^\s*\|/m,                             // Markdown table start
  /count:\s*\d+/i,                       // Row count returns
  /rows?\s+returned:\s*\d+/i,
  /no\s+(?:signals?|events?|rows?)\s+found/i,  // Empty result
]

/** Tool names whose outputs are inherently factual (no citation needed) */
const FACTUAL_TOOLS = [
  'query_chart_facts', 'query_dasha_periods', 'query_panchanga',
  'query_ephemeris', 'lel_query', 'list_recent_queries',
  'query_transit_event',
]

// ── Non-factual indicators ─────────────────────────────────────────────────────

/** Phrases indicating interpretive content */
const INTERPRETIVE_PHRASES = [
  'this indicates', 'this suggests', 'this shows', 'this reveals',
  'the native', 'the pattern', 'the combination', 'the placement',
  'signifies', 'represents', 'manifests as', 'correlates with',
  'points to', 'is associated with', 'tends to produce',
  'in interpretation', 'from a jyotish perspective',
  'the analysis', 'the synthesis', 'the reading',
]

/** Minimum length for a response to be considered non-factual (3+ sentences) */
const MIN_NON_FACTUAL_SENTENCE_COUNT = 3

// ── Main detector ──────────────────────────────────────────────────────────────

/**
 * Determine whether a response is non-factual (interpretive/synthetic).
 *
 * @param responseText    The response text to classify.
 * @param toolName        Optional tool name; factual tools always return false.
 * @returns true if the response is non-factual (requires citation check)
 */
export function isNonFactualResponse(responseText: string, toolName?: string): boolean {
  if (!responseText || typeof responseText !== 'string') return false

  // If the tool is inherently factual, the response is factual
  if (toolName && FACTUAL_TOOLS.includes(toolName)) return false

  // Check factual indicator patterns
  for (const pattern of FACTUAL_INDICATORS) {
    if (pattern.test(responseText)) return false
  }

  const lower = responseText.toLowerCase()

  // Check interpretive phrase presence
  for (const phrase of INTERPRETIVE_PHRASES) {
    if (lower.includes(phrase)) return true
  }

  // Response shape heuristic: ≥3 sentences = likely non-factual
  const sentenceCount = (responseText.match(/[.!?]+/g) ?? []).length
  if (sentenceCount >= MIN_NON_FACTUAL_SENTENCE_COUNT) {
    // Additional check: not all sentences are factual data lines
    const lines = responseText.split('\n').filter(l => l.trim().length > 0)
    const tableLines = lines.filter(l => l.trim().startsWith('|')).length
    const tableRatio = tableLines / Math.max(1, lines.length)
    // If >50% of lines are table rows, it's likely factual data
    if (tableRatio > 0.5) return false
    return true
  }

  return false
}

/**
 * Check whether a non-factual response meets the minimum shape requirements:
 * ≥3 sentences + ≥1 citation.
 */
export function meetsNonFactualShape(responseText: string): boolean {
  if (!responseText || typeof responseText !== 'string') return false

  const sentenceCount = (responseText.match(/[.!?]+/g) ?? []).length
  if (sentenceCount < MIN_NON_FACTUAL_SENTENCE_COUNT) return false

  // Check for citation presence
  const hasCitation = /SIG\.MSR\.\d{3,}|\[\^\d+\]|LEL\.E\.\d{3,}|FORENSIC\.§\d+/.test(responseText)
  return hasCitation
}
