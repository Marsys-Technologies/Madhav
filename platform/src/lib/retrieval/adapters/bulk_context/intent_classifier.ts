/**
 * Bulk Context Adapter — Intent Classifier
 * ==========================================
 * Regex + Gemini Flash-Lite for query intent tagging.
 * Tags determine which resources to pre-fetch.
 */

export type IntentTag =
  | 'entity_lookup'      // Looking up a specific graha, nakshatra, sign, etc.
  | 'rule_query'         // Asking about classical rules (sutravali)
  | 'remedy_query'       // Asking about remedies (upayas)
  | 'temporal_query'     // Asking about time periods, dashas, transits
  | 'chart_analysis'     // Full chart reading request
  | 'text_reference'     // Looking up specific classical text reference
  | 'calculation'        // Requesting astronomical calculation
  | 'general'            // Catch-all

export interface IntentResult {
  tags: IntentTag[]
  confidence: number
  primary_intent: IntentTag
}

// ── Regex patterns for fast intent detection ──────────────────────────────────

const INTENT_PATTERNS: Array<{ pattern: RegExp; tag: IntentTag }> = [
  // Entity lookup
  { pattern: /\b(sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu|graha|nakshatra|rasi|sign|ascendant|lagna)\b/i, tag: 'entity_lookup' },
  { pattern: /\b(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)\b/i, tag: 'entity_lookup' },
  { pattern: /\b(ashwini|bharani|krittika|rohini|mrigashira|ardra|punarvasu|pushya|ashlesha|magha|purva|uttara|hasta|chitra|swati|vishakha|anuradha|jyeshtha|mula|purvashadha|uttarashadha|shravana|dhanishtha|shatabhisha|purvabhadra|uttarabhadra|revati)\b/i, tag: 'entity_lookup' },

  // Rule query
  { pattern: /\b(rule|sutra|shloka|verse|principle|classical|parashara|jaimini|brihat|phaladeepika|saravali)\b/i, tag: 'rule_query' },
  { pattern: /\b(when|what happens|effect|result|indication|signification)\b/i, tag: 'rule_query' },

  // Remedy query
  { pattern: /\b(remedy|upaya|mantra|gemstone|donation|charity|puja|worship|strengthen)\b/i, tag: 'remedy_query' },

  // Temporal query
  { pattern: /\b(dasha|bhukti|antardasha|transit|mahadasha|period|timing|when will|prediction)\b/i, tag: 'temporal_query' },

  // Chart analysis
  { pattern: /\b(chart|horoscope|kundali|birth chart|natal|reading|analysis)\b/i, tag: 'chart_analysis' },

  // Text reference
  { pattern: /\b(quote|citation|source|reference|according to|text|chapter|shloka)\b/i, tag: 'text_reference' },

  // Calculation
  { pattern: /\b(calculate|compute|degree|longitude|position|ephemeris|exact)\b/i, tag: 'calculation' },
]

/**
 * Classify query intent using regex patterns.
 * Fast, deterministic, no LLM cost.
 */
export function classifyIntentSync(query: string): IntentResult {
  const matched_tags = new Set<IntentTag>()
  let total_pattern_score = 0

  for (const { pattern, tag } of INTENT_PATTERNS) {
    if (pattern.test(query)) {
      matched_tags.add(tag)
      total_pattern_score++
    }
  }

  const tags: IntentTag[] = matched_tags.size > 0
    ? Array.from(matched_tags)
    : ['general']

  // Primary intent = first matched tag (patterns are ordered by specificity)
  const primary_intent = tags[0]

  // Confidence: more pattern matches = higher confidence
  const confidence = Math.min(total_pattern_score / 3, 1.0)

  return { tags, confidence, primary_intent }
}

/**
 * Classify query intent, with optional LLM fallback for low-confidence cases.
 * The LLM path uses Gemini Flash-Lite and is async.
 *
 * Per deterministic-first principle: regex runs first; LLM only if confidence < 0.4
 * and explicitly enabled.
 */
export async function classifyIntent(
  query: string,
  options?: { use_llm_fallback?: boolean }
): Promise<IntentResult> {
  const regex_result = classifyIntentSync(query)

  // If regex is confident enough, return immediately (no LLM cost)
  if (regex_result.confidence >= 0.4 || !options?.use_llm_fallback) {
    return regex_result
  }

  // LLM fallback path (Gemini Flash-Lite — low cost)
  try {
    const llm_result = await classifyIntentWithLLM(query)
    // Merge: take LLM tags + regex tags
    const merged_tags = Array.from(new Set([...llm_result.tags, ...regex_result.tags]))
    return {
      tags: merged_tags,
      confidence: Math.max(llm_result.confidence, regex_result.confidence),
      primary_intent: llm_result.primary_intent,
    }
  } catch {
    // LLM failed — return regex result
    return regex_result
  }
}

/**
 * LLM-based intent classification using Gemini Flash-Lite.
 * Only called when regex confidence is low.
 */
async function classifyIntentWithLLM(query: string): Promise<IntentResult> {
  // This will be implemented when Vertex AI client is available in the retrieval stack.
  // For now: return the regex result as a safe fallback.
  return classifyIntentSync(query)
}
