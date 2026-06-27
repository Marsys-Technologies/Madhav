/**
 * D2 Query Router — Rule-Driven Classifier
 * ==========================================
 * Classifies a query into one of the five route classes plus a traversal level.
 *
 * Architecture decision (D2 brief §1):
 * "rule-driven core (deterministic, auditable, fits deterministic-first) with
 * an optional model-classifier fallback for ambiguous queries; record which fired."
 *
 * This file implements the rule-driven core.
 * The model fallback (when confidence is 'low') is handled in router.ts.
 *
 * Rules are ordered by SPECIFICITY — most specific first.
 * Each rule fires at most once; the first match wins.
 * Every rule records its name for trajectory/D8 logging.
 */

import type { ClassifierResult } from './types'

// ── Rule type ─────────────────────────────────────────────────────────────────

interface ClassifierRule {
  /** Short identifier for trajectory logging */
  name: string
  /** Test whether this rule matches the query */
  test: (query: string, queryLower: string) => boolean
  /** The result to emit when the rule matches */
  result: Omit<ClassifierResult, 'rule_fired'>
}

// ── Keyword vocabularies ──────────────────────────────────────────────────────

// numeric_exact: direct positional / numerical / computed-value lookups
// NOTE: keywords must be specific enough to avoid false positives.
// - Use 'which sign' / 'what sign' not bare 'sign' (appears in 'signals')
// - Use 'own sign' as a phrase, not bare 'sign'
const NUMERIC_KEYWORDS = [
  'longitude', 'degree', 'position', 'nakshatra pad', 'pada',
  'house number', 'bhava', 'shadbala', 'bala', 'ishta', 'kashta',
  'ashtakavarga', 'bindus', 'dignity', 'exaltation', 'debility',
  'mulatrikona', 'own sign', 'neecha', 'uccha', 'avastha', 'jagrat', 'swapna',
  'sushupti', 'drishti', 'dispositor', 'lord of', 'ruling planet',
  'what planet', 'which planet', 'which sign', 'what sign', 'what house',
  'tithi', 'yoga number', 'karana', 'panchanga',
  'argala', 'virodha argala', 'eclipse',
  // 'strength' and 'score' and 'aspect' are too generic — removed to avoid false positives
  // 'vara' is too generic — removed ('varahamihira' would match)
]

// relational: contradictions, convergences, cross-domain, graph traversal
const RELATIONAL_KEYWORDS = [
  'contradict', 'contradiction', 'conflict', 'tension', 'paradox',
  'converge', 'convergence', 'agree', 'reinforce', 'corroborate',
  'across', 'cross-domain', 'cross domain', 'relationship between',
  'connect', 'connected', 'path from', 'path between', 'chain',
  'cluster', 'subgraph', 'graph', 'neighbor', 'neighbours',
  'link', 'linkage', 'cdlm', 'cgm', 'bimba', 'karanajala',
  'compare … and', 'compare … with', 'which signals',
  'all signals', 'all patterns', 'overall picture',
]

// narrative: classical text retrieval, citations, verse, rule corpus
const NARRATIVE_KEYWORDS = [
  'what does', 'what do', 'classical', 'tradition says', 'sutra',
  'verse', 'sloka', 'shloka', 'brihat', 'parashara', 'jaimini',
  'hora shastra', 'uttara kalamrita', 'phala deepika', 'saravali',
  'bphs', 'rule says', 'text says', 'source', 'citation',
  'classical basis', 'grantha', 'shastra', 'smriti',
  'remedy', 'upaya', 'parihar', 'gemstone', 'mantra', 'yantra',
  'classical remedy', 'traditional remedy',
]

// simple: whole-chart orientation / top-level digest (the UCD umbrella)
const SIMPLE_KEYWORDS = [
  'orientation', 'orient', 'overview', 'summary', 'digest', 'snapshot',
  'top signals', 'main signals', 'key signals', 'salient', 'most important',
  'give me the chart', 'tell me about this chart', 'what is this chart',
  'chart at a glance', 'quick summary', 'brief', 'high level',
  'chart overview', 'chart summary', 'overall chart',
  'dominant', 'standout', 'highlight',
]

// multi_hop: multi-step, multi-domain, time-sensitive, agentic
const MULTI_HOP_KEYWORDS = [
  'then', 'after that', 'next', 'step by step', 'detailed analysis',
  'full reading', 'complete reading', 'comprehensive', 'in depth', 'deep dive',
  'both … and', 'compare and contrast', 'resolve', 'reconcile',
  'time period', 'dasha period', 'antardasha', 'transit', 'progression',
  'timing', 'when will', 'how will', 'what will happen',
  'predict', 'prognosis', 'future', 'upcoming', 'forecast',
  'multiple domain', 'several domain', 'all domain',
  'holistic', 'whole', 'entire chart', 'everything about',
]

// ── Helper ────────────────────────────────────────────────────────────────────

function hasAny(queryLower: string, keywords: string[]): boolean {
  return keywords.some((kw) => queryLower.includes(kw))
}

/**
 * Score a query by counting how many keywords from a list it matches.
 * Used to break ties between multi-keyword route classes.
 */
function countMatches(queryLower: string, keywords: string[]): number {
  return keywords.filter((kw) => queryLower.includes(kw)).length
}

// ── Rule table ────────────────────────────────────────────────────────────────

/**
 * Ordered rule table. Rules are evaluated in order; first match wins.
 *
 * Ordering rationale:
 * 1. numeric_exact is most specific — exact data lookups have unmistakable markers
 * 2. relational next — contradiction / graph terms are domain-specific
 * 3. narrative — classical-text markers are distinctive
 * 4. multi_hop before simple — "full reading" trumps "overview"
 * 5. simple — catch-all for orientation/digest queries
 */
const RULES: ClassifierRule[] = [
  // ── R1: Numeric exact ──────────────────────────────────────────────────────
  {
    name: 'R1_numeric_keywords',
    test: (_q, ql) => hasAny(ql, NUMERIC_KEYWORDS),
    result: {
      route_class: 'numeric_exact',
      traversal_level: 'L-SIGNAL',
      confidence: 'high',
    },
  },

  // ── R2: Relational / graph ────────────────────────────────────────────────
  {
    name: 'R2_relational_keywords',
    test: (_q, ql) => hasAny(ql, RELATIONAL_KEYWORDS),
    result: {
      route_class: 'relational',
      traversal_level: 'L-SIGNAL',
      confidence: 'high',
    },
  },

  // ── R3: Narrative / classical text ────────────────────────────────────────
  {
    name: 'R3_narrative_keywords',
    test: (_q, ql) => hasAny(ql, NARRATIVE_KEYWORDS),
    result: {
      route_class: 'narrative',
      traversal_level: 'L-SOURCE',
      confidence: 'high',
    },
  },

  // ── R4: Multi-hop (before simple — "detailed" beats "overview") ────────────
  {
    name: 'R4_multi_hop_keywords',
    test: (_q, ql) => {
      const count = countMatches(ql, MULTI_HOP_KEYWORDS)
      return count >= 2  // Require ≥2 matches to avoid false positives
    },
    result: {
      route_class: 'multi_hop',
      traversal_level: 'L-DOMAIN',
      confidence: 'high',
    },
  },

  // ── R5: Simple / umbrella orientation ────────────────────────────────────
  {
    name: 'R5_simple_orientation',
    test: (_q, ql) => hasAny(ql, SIMPLE_KEYWORDS),
    result: {
      route_class: 'simple',
      traversal_level: 'L-ORIENT',
      confidence: 'high',
    },
  },

  // ── R6: Short query heuristic — very short queries default to simple ────────
  {
    name: 'R6_short_query_simple',
    test: (q, _ql) => q.trim().split(/\s+/).length <= 6,
    result: {
      route_class: 'simple',
      traversal_level: 'L-ORIENT',
      confidence: 'low',  // Low confidence — eligible for model fallback
    },
  },
]

/** Fallback when no rule matches */
const FALLBACK: ClassifierResult = {
  route_class: 'simple',
  traversal_level: 'L-ORIENT',
  rule_fired: 'FALLBACK_default_orient',
  confidence: 'low',
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Run the rule-driven classifier over a query string.
 *
 * Returns a ClassifierResult with:
 * - route_class: which of the 5 classes was chosen
 * - traversal_level: the traversal level for this route
 * - rule_fired: name of the rule that matched (for logging)
 * - confidence: 'high' (rule is definitive) or 'low' (eligible for model fallback)
 *
 * This function is pure and deterministic (no I/O, no model calls).
 */
export function classifyQuery(query: string): ClassifierResult {
  const queryLower = query.toLowerCase()

  for (const rule of RULES) {
    if (rule.test(query, queryLower)) {
      return {
        ...rule.result,
        rule_fired: rule.name,
      }
    }
  }

  return FALLBACK
}

/**
 * Check whether a classifier result is eligible for model fallback.
 * Caller can use this to decide whether to invoke the optional LLM classifier.
 */
export function isModelFallbackEligible(result: ClassifierResult): boolean {
  return result.confidence === 'low'
}
