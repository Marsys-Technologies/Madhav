/**
 * adapters/bulk_context/intent_classifier.ts
 *
 * Regex + Gemini Flash-Lite for query intent tagging.
 * Fast, cheap classification to determine which resources to pre-fetch.
 *
 * L0FR Stream A — authored 2026-06-07
 */

export type QueryIntent =
  | 'dasha_timing'
  | 'transit_analysis'
  | 'yoga_identification'
  | 'planet_strength'
  | 'house_analysis'
  | 'remedy_lookup'
  | 'panchanga'
  | 'classical_rule'
  | 'chart_overview'
  | 'prediction_calibration'
  | 'unknown'

export interface ClassificationResult {
  primary_intent: QueryIntent
  secondary_intents: QueryIntent[]
  confidence: number
  method: 'regex' | 'llm' | 'default'
}

// ── Regex-based fast classifier ───────────────────────────────────────────────

const INTENT_PATTERNS: Array<{ intent: QueryIntent; patterns: RegExp[] }> = [
  {
    intent: 'dasha_timing',
    patterns: [
      /\bdasha\b/i, /\bantardasha\b/i, /\bmahadasha\b/i, /\bvimshottari\b/i,
      /\bpratyantara\b/i, /\bperiod\b.*\bplanet\b/i,
    ],
  },
  {
    intent: 'transit_analysis',
    patterns: [
      /\btransit\b/i, /\bgochara\b/i, /\bsaturn\b.*\bmove\b/i,
      /\bjupiter\b.*\btransit\b/i, /\baspect\b.*\bnatal\b/i,
    ],
  },
  {
    intent: 'yoga_identification',
    patterns: [
      /\byoga\b/i, /\brajayoga\b/i, /\bdhana\b.*\byoga\b/i,
      /\bkemadruma\b/i, /\bgajkesari\b/i, /\bpancha\b.*\bmahapurusha\b/i,
    ],
  },
  {
    intent: 'planet_strength',
    patterns: [
      /\bshadbala\b/i, /\bashtakavarga\b/i, /\bstrength\b.*\bplanet\b/i,
      /\bexalt\b/i, /\bdebilitat\b/i, /\bdig\b.*\bbala\b/i,
    ],
  },
  {
    intent: 'house_analysis',
    patterns: [
      /\b(\d+)(st|nd|rd|th)?\s*house\b/i, /\bbhava\b/i,
      /\blagna\b/i, /\bdasamsha\b/i, /\bnavamsha\b/i,
    ],
  },
  {
    intent: 'remedy_lookup',
    patterns: [
      /\bremedy\b/i, /\bupaya\b/i, /\bmantra\b/i, /\bgemstone\b/i,
      /\bpuja\b/i, /\bdaan\b/i, /\bcharity\b/i,
    ],
  },
  {
    intent: 'panchanga',
    patterns: [
      /\btithi\b/i, /\bnakshatra\b/i, /\bvara\b/i, /\byoga\b.*\bday\b/i,
      /\bkarana\b/i, /\bmuhurta\b/i, /\bpanchang/i,
    ],
  },
  {
    intent: 'classical_rule',
    patterns: [
      /\bparashara\b/i, /\bjaimini\b/i, /\bbphs\b/i, /\bshloka\b/i,
      /\bclassical\b/i, /\bsutra\b/i, /\bsaravali\b/i,
    ],
  },
  {
    intent: 'prediction_calibration',
    patterns: [
      /\bpredict\b/i, /\bforecast\b/i, /\bwhen\b.*\b(will|shall)\b/i,
      /\bprobabilit\b/i, /\bcalibrat\b/i,
    ],
  },
  {
    intent: 'chart_overview',
    patterns: [
      /\boverview\b/i, /\bsummar\b/i, /\bwhole\s*chart\b/i,
      /\bgeneral\b/i, /\bcomprehensive\b/i,
    ],
  },
]

/**
 * Classify query intent using regex (fast, no API call).
 */
export function classifyByRegex(query: string): ClassificationResult {
  const matches: Map<QueryIntent, number> = new Map()

  for (const { intent, patterns } of INTENT_PATTERNS) {
    let score = 0
    for (const pattern of patterns) {
      if (pattern.test(query)) score++
    }
    if (score > 0) {
      matches.set(intent, score)
    }
  }

  if (matches.size === 0) {
    return {
      primary_intent: 'chart_overview',
      secondary_intents: [],
      confidence: 0.4,
      method: 'default',
    }
  }

  const sorted = [...matches.entries()].sort((a, b) => b[1] - a[1])
  const [primary, primaryScore] = sorted[0]!
  const secondary = sorted.slice(1, 3).map(([intent]) => intent)
  const confidence = Math.min(0.95, 0.5 + primaryScore * 0.15)

  return {
    primary_intent: primary,
    secondary_intents: secondary,
    confidence,
    method: 'regex',
  }
}

/**
 * Full classification: regex first; if confidence < 0.7, fall back to LLM.
 * (LLM call placeholder — wired up when Vertex AI client is available)
 */
export async function classifyIntent(query: string): Promise<ClassificationResult> {
  const regexResult = classifyByRegex(query)

  // If regex is confident enough, return immediately (no LLM cost)
  if (regexResult.confidence >= 0.7) {
    return regexResult
  }

  // TODO: LLM fallback (Gemini Flash-Lite) for ambiguous queries
  // const llmResult = await classifyWithLLM(query)
  // return llmResult

  return regexResult
}
