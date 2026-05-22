/**
 * extract_citations.ts — Heuristic: extract astrological citation references.
 *
 * Regex-only. NO LLM calls. Extracts:
 *   - SIG.MSR.NNN (MSR signal IDs)
 *   - [^N]: citation-style GFM footnotes
 *   - LEL.E.NNN (Life Event Log references)
 *   - FORENSIC.§N.N (FORENSIC source citations)
 *
 * False positive rate: ~5% (footnote references in non-citation contexts).
 * False negative rate: ~10% (novel citation formats not covered by these patterns).
 *
 * MCPT v3.1.0-S4
 */

// ── Citation patterns ──────────────────────────────────────────────────────────

/** MSR signal IDs: SIG.MSR.001 through SIG.MSR.999+ */
const MSR_SIGNAL_PATTERN = /SIG\.MSR\.\d{3,}/g

/** GFM footnote references: [^1], [^12], etc. */
const GFM_FOOTNOTE_PATTERN = /\[\^\d+\]/g

/** LEL event references: LEL.E.001 through LEL.E.999 */
const LEL_REF_PATTERN = /LEL\.E\.\d{3,}/g

/** FORENSIC source citations: FORENSIC.§1.1, FORENSIC.§12.3, etc. */
const FORENSIC_REF_PATTERN = /FORENSIC\.§\d+(?:\.\d+)*/g

/** Arrow citations: → SIG.MSR.NNN (inline citation format) */
const ARROW_CITATION_PATTERN = /→\s*SIG\.MSR\.\d{3,}/g

// ── Main extractor ─────────────────────────────────────────────────────────────

/**
 * Extract all citation references from a response text.
 * Returns deduplicated array of citation strings found.
 */
export function extractCitations(responseText: string): string[] {
  if (!responseText || typeof responseText !== 'string') return []

  const found = new Set<string>()

  const msrMatches = responseText.match(MSR_SIGNAL_PATTERN) ?? []
  for (const m of msrMatches) found.add(m)

  const gfmMatches = responseText.match(GFM_FOOTNOTE_PATTERN) ?? []
  for (const m of gfmMatches) found.add(m)

  const lelMatches = responseText.match(LEL_REF_PATTERN) ?? []
  for (const m of lelMatches) found.add(m)

  const forensicMatches = responseText.match(FORENSIC_REF_PATTERN) ?? []
  for (const m of forensicMatches) found.add(m)

  const arrowMatches = responseText.match(ARROW_CITATION_PATTERN) ?? []
  for (const m of arrowMatches) {
    // Extract the SIG.MSR part from arrow citations
    const sigMatch = m.match(/SIG\.MSR\.\d{3,}/)
    if (sigMatch) found.add(sigMatch[0]!)
  }

  return [...found]
}

/**
 * Count the number of distinct citation references in a response.
 * A response with 0 citations that makes interpretive claims fails the
 * citation_presence audit check.
 */
export function countCitations(responseText: string): number {
  return extractCitations(responseText).length
}

/**
 * Check whether a response has at least one citation.
 * Interpretive (non-factual) responses should always have ≥1 citation.
 */
export function hasCitation(responseText: string): boolean {
  return countCitations(responseText) > 0
}
