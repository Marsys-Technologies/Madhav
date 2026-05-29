/**
 * INF7-S3: Intent Classifier
 *
 * Classifies an incoming query into a primary intent, then selects:
 *   - optimal ayanamshas to query (subset vs all 5)
 *   - chart_facts categories to pre-fetch
 *   - tool priority ordering for the agentic loop
 *   - audience tier adjustments
 *
 * Rule-based (no LLM call) — deterministic, zero latency overhead.
 *
 * [BUILD-ORCH-J-08] INF7-S3
 */

// ── Intent taxonomy ───────────────────────────────────────────────────────────

export type QueryIntent =
  | 'chart_reading'
  | 'timing_query'
  | 'remedial_query'
  | 'comparison_query'
  | 'general_jyotish'
  | 'panchanga_query'
  | 'dasha_query'
  | 'yoga_query'
  | 'transit_query'
  | 'prediction_query'

// ── Classification result ─────────────────────────────────────────────────────

export interface IntentClassification {
  intent: QueryIntent
  confidence: number
  /** Ayanamshas to query — all 5 for timing; lahiri+kp for transit; etc. */
  recommended_ayanamshas: string[]
  /** chart_facts categories to pre-fetch as Layer-1 context. */
  prefetch_categories: string[]
  /** Tool names ordered by relevance for this intent. */
  tool_priority: string[]
  /** Whether cross-ayanamsha consensus is valuable for this intent. */
  suggest_cross_ayanamsha: boolean
}

// ── Keyword banks ─────────────────────────────────────────────────────────────

const INTENT_KEYWORDS: Record<QueryIntent, string[]> = {
  chart_reading: [
    'lagna', 'ascendant', 'rising', 'lord', 'house', 'placed', 'position', 'chart',
    'sign', 'planet', 'graha', 'dignity', 'exalt', 'debilitat', 'mooltrikon',
    'navamsa', 'varga', 'divisional', 'nakshatra', 'pada',
  ],
  timing_query: [
    'when', 'how long', 'duration', 'period', 'timing', 'predict', 'future',
    'coming', 'next', 'upcoming', 'year', 'month', 'transit', 'dasha',
    'antardasha', 'mahadasha', 'sub-period',
  ],
  dasha_query: [
    'dasha', 'mahadasha', 'antardasha', 'pratyantardasha', 'vimshottar',
    'jaimini', 'chara dasha', 'sthira', 'yogini', 'running period',
  ],
  remedial_query: [
    'remedy', 'remedies', 'mantra', 'gemstone', 'yantra', 'puja', 'donation',
    'charity', 'fasting', 'upay', 'strengthen', 'mitigate', 'pacify',
    'worship', 'stotra', 'kavach',
  ],
  comparison_query: [
    'compare', 'contrast', 'versus', 'vs', 'difference', 'lahiri vs',
    'kp vs', 'system', 'ayanamsha', 'tropical', 'sidereal',
    'tradition', 'school', 'parashari', 'jaimini', 'kp method',
  ],
  panchanga_query: [
    'tithi', 'vara', 'nakshatra day', 'panchang', 'muhurta', 'auspicious',
    'inauspicious', 'rahu kalam', 'yamaganda', 'gulika', 'hora', 'choghadiya',
    'sunrise', 'sunset', 'moon', 'lunar',
  ],
  general_jyotish: [
    'what is', 'explain', 'meaning', 'classical', 'tradition', 'shastra',
    'bphs', 'brihat parashara', 'phaladeepika', 'saravali',
  ],
  transit_query: [
    'transit', 'gochara', 'current position', 'today', 'now', 'transiting',
    'passing through', 'saturn transit', 'jupiter transit', 'rahu transit',
  ],
  yoga_query: [
    'yoga', 'raj yoga', 'dhan yoga', 'gajakesari', 'pancha mahapurusha',
    'vipareeta raja', 'neechabhanga', 'kala sarpa', 'dosha', 'mangal',
    'combination', 'conjunction',
  ],
  prediction_query: [
    'predict', 'forecast', 'when will', 'will i', 'outcome', 'result',
    'career', 'marriage', 'health', 'finance', 'relationship', 'abroad',
  ],
}

// ── Intent-to-config map ──────────────────────────────────────────────────────

const INTENT_CONFIG: Record<QueryIntent, Omit<IntentClassification, 'intent' | 'confidence'>> = {
  chart_reading: {
    recommended_ayanamshas: ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'],
    prefetch_categories: ['planet', 'planet_positions', 'house', 'house_positions', 'shadbala', 'ashtakavarga_bav'],
    tool_priority: ['query_chart_facts', 'get_shadbala_full', 'query_vargas', 'query_sensitive_points', 'msr_sql'],
    suggest_cross_ayanamsha: true,
  },
  timing_query: {
    recommended_ayanamshas: ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'],
    prefetch_categories: ['dasha_vimshottari', 'dasha_chara', 'planet', 'house'],
    tool_priority: ['query_dasha_periods', 'query_transit_event', 'query_transits_over_natal', 'query_chart_facts', 'temporal'],
    suggest_cross_ayanamsha: true,
  },
  dasha_query: {
    recommended_ayanamshas: ['lahiri', 'true_chitra', 'kp'],
    prefetch_categories: ['dasha_vimshottari', 'dasha_chara', 'dasha_yogini'],
    tool_priority: ['query_dasha_periods', 'query_chart_facts', 'query_planetary_period_predictions'],
    suggest_cross_ayanamsha: false,
  },
  remedial_query: {
    recommended_ayanamshas: ['lahiri'],
    prefetch_categories: ['planet', 'yoga', 'shadbala'],
    tool_priority: ['query_remedies_prescribed', 'remedial_codex_query', 'query_chart_facts', 'vector_search'],
    suggest_cross_ayanamsha: false,
  },
  comparison_query: {
    recommended_ayanamshas: ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'],
    prefetch_categories: ['planet', 'planet_positions', 'house'],
    tool_priority: ['cross_ayanamsha_consensus', 'query_chart_facts', 'classical_attribution_lookup_tool', 'vector_search'],
    suggest_cross_ayanamsha: true,
  },
  panchanga_query: {
    recommended_ayanamshas: ['lahiri'],
    prefetch_categories: ['panchang', 'panchanga_tithi', 'panchanga_vara', 'panchanga_nakshatra'],
    tool_priority: ['query_panchanga', 'query_muhurat'],
    suggest_cross_ayanamsha: false,
  },
  general_jyotish: {
    recommended_ayanamshas: ['lahiri'],
    prefetch_categories: [],
    tool_priority: ['vector_search', 'classical_attribution_lookup_tool', 'classical_text_search_tool'],
    suggest_cross_ayanamsha: false,
  },
  transit_query: {
    recommended_ayanamshas: ['lahiri', 'true_chitra'],
    prefetch_categories: ['planet', 'house', 'dasha_vimshottari'],
    tool_priority: ['query_transits_over_natal', 'query_transit_event', 'query_eclipse_transits', 'query_chart_facts'],
    suggest_cross_ayanamsha: false,
  },
  yoga_query: {
    recommended_ayanamshas: ['lahiri', 'true_chitra', 'kp'],
    prefetch_categories: ['yoga', 'planet', 'house'],
    tool_priority: ['query_yogas_active_now', 'query_chart_facts', 'classical_attribution_lookup_tool', 'vector_search'],
    suggest_cross_ayanamsha: true,
  },
  prediction_query: {
    recommended_ayanamshas: ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'],
    prefetch_categories: ['dasha_vimshottari', 'planet', 'yoga', 'house'],
    tool_priority: ['query_dasha_periods', 'query_planetary_period_predictions', 'query_chart_facts', 'temporal'],
    suggest_cross_ayanamsha: true,
  },
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Classify a query text and return routing configuration.
 */
export function classifyIntent(queryText: string): IntentClassification {
  const lower = queryText.toLowerCase()
  const scores = scoreIntents(lower)
  const topIntent = pickTopIntent(scores)
  const rawScore = scores[topIntent] ?? 0
  const maxKeywords = INTENT_KEYWORDS[topIntent]?.length ?? 1
  const confidence = Math.min(rawScore / maxKeywords, 1)
  const config = INTENT_CONFIG[topIntent]!

  return {
    intent: topIntent,
    confidence: Math.round(confidence * 100) / 100,
    ...config,
  }
}

/**
 * Filter ayanamshas to only those available for a chart, respecting intent recommendation.
 */
export function filterAyanamshas(
  recommended: string[],
  available: string[],
  audienceTier: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted',
): string[] {
  // Client tier: only lahiri unless they explicitly have others
  if (audienceTier === 'client') {
    const clientDefault = ['lahiri']
    return available.filter((a) => clientDefault.includes(a) || recommended.includes(a))
  }
  // All other tiers: recommended ∩ available, fallback to lahiri
  const filtered = recommended.filter((a) => available.includes(a))
  return filtered.length > 0 ? filtered : ['lahiri']
}

// ── Scoring internals ─────────────────────────────────────────────────────────

function scoreIntents(text: string): Record<QueryIntent, number> {
  const scores: Record<QueryIntent, number> = {} as Record<QueryIntent, number>

  for (const [intent, keywords] of Object.entries(INTENT_KEYWORDS) as Array<[QueryIntent, string[]]>) {
    let score = 0
    for (const kw of keywords) {
      if (text.includes(kw)) score += 1
    }
    scores[intent] = score
  }

  return scores
}

function pickTopIntent(scores: Record<QueryIntent, number>): QueryIntent {
  let top: QueryIntent = 'chart_reading'
  let topScore = -1

  for (const [intent, score] of Object.entries(scores) as Array<[QueryIntent, number]>) {
    if (score > topScore) {
      topScore = score
      top = intent
    }
  }

  // Default to chart_reading if no keywords matched
  return topScore === 0 ? 'chart_reading' : top
}
