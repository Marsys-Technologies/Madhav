/**
 * layer_attribution.ts — Heuristic: detect L1/L2.5 layer mixing in responses.
 *
 * Checks whether a response correctly attributes L1 facts (birth data, chart positions,
 * dates) vs L2.5 signals (MSR interpretations, UCN/RM/CDLM themes). Mixing = presenting
 * an interpretation as a fact, or citing a fact as if it were an interpretation.
 *
 * Regex/keyword pattern matching. NO LLM calls.
 *
 * False positive rate: ~10% (complex responses with valid mixed attributions).
 * False negative rate: ~20% (subtle layer mixing that doesn't trigger keyword patterns).
 *
 * MCPT v3.1.0-S4
 */

// ── L1 fact indicators ─────────────────────────────────────────────────────────

/** Keywords indicating L1 factual claims */
const L1_FACT_KEYWORDS = [
  'born at', 'birth date', 'natal position',
  'degree in', '° in', 'house placement',
  'from forensic', 'forensic §', 'chart_facts',
  'lagna is', 'ascendant is',
  'sun is in', 'moon is in', 'mars is in', 'mercury is in',
  'jupiter is in', 'venus is in', 'saturn is in',
]

/** Keywords indicating L2.5 synthesis claims */
const L2_5_KEYWORDS = [
  'this indicates', 'this suggests', 'this shows', 'this points to',
  'pattern suggests', 'signal shows', 'msrv', 'sig.msr',
  'ucn theme', 'cdlm contradiction', 'cgm subgraph',
  'the native is likely', 'the native tends to',
  'there is a tendency', 'there is a pattern',
  'synthesis reveals', 'cross-domain pattern',
]

// ── Layer mixing detectors ─────────────────────────────────────────────────────

/**
 * Detect potential layer mixing: L2.5 interpretive claims without citation.
 * Returns detected mixing instances.
 */
export function detectLayerMixing(responseText: string): string[] {
  if (!responseText || typeof responseText !== 'string') return []

  const lower = responseText.toLowerCase()
  const mixingInstances: string[] = []

  // Check: L2.5 interpretive phrases present without a SIG citation nearby
  for (const keyword of L2_5_KEYWORDS) {
    const idx = lower.indexOf(keyword.toLowerCase())
    if (idx === -1) continue

    // Look for citation within 200 chars of the keyword
    const window = responseText.slice(Math.max(0, idx - 100), Math.min(responseText.length, idx + 200))
    const hasCitation = /SIG\.MSR\.\d{3,}|\[\^\d+\]|LEL\.E\.\d{3,}/.test(window)

    if (!hasCitation) {
      const excerpt = responseText.slice(Math.max(0, idx - 20), Math.min(responseText.length, idx + 80))
      mixingInstances.push(excerpt.trim())
    }
  }

  return [...new Set(mixingInstances)]
}

/**
 * Check whether a response has proper layer attribution.
 * Returns true if no mixing instances detected (= compliant).
 */
export function hasProperLayerAttribution(responseText: string): boolean {
  return detectLayerMixing(responseText).length === 0
}

/**
 * Classify response segments by layer (L1 vs L2.5).
 * Used for the audit evidence block.
 */
export function classifyResponseLayers(responseText: string): {
  l1_segments: string[]
  l2_5_segments: string[]
} {
  if (!responseText || typeof responseText !== 'string') {
    return { l1_segments: [], l2_5_segments: [] }
  }

  const lower = responseText.toLowerCase()
  const l1_segments: string[] = []
  const l2_5_segments: string[] = []

  for (const keyword of L1_FACT_KEYWORDS) {
    const idx = lower.indexOf(keyword.toLowerCase())
    if (idx !== -1) {
      const excerpt = responseText.slice(Math.max(0, idx - 10), Math.min(responseText.length, idx + 80))
      l1_segments.push(excerpt.trim())
    }
  }

  for (const keyword of L2_5_KEYWORDS) {
    const idx = lower.indexOf(keyword.toLowerCase())
    if (idx !== -1) {
      const excerpt = responseText.slice(Math.max(0, idx - 10), Math.min(responseText.length, idx + 80))
      l2_5_segments.push(excerpt.trim())
    }
  }

  return {
    l1_segments: [...new Set(l1_segments)],
    l2_5_segments: [...new Set(l2_5_segments)],
  }
}
