/**
 * pariprashna/corpus/metrics/citation_density.ts — lane P2-N (G3-F), test
 * plan §7 dimension 4 ("Citation usefulness"): "citation density measured
 * per reading and reported" (seed baseline: historical EDIR E-005, "many
 * load-bearing claims, two citations" — an informal count, never previously
 * automated).
 *
 * Deliberately NOT one of the 13 `DIMENSION_IDS` in `../types.ts` /
 * `../dimensions/index.ts`: those are 0..1 pass/fail-shaped scores against a
 * detector; citation density is a raw MEASURED COUNT the test plan asks to
 * be "measured... and reported", not graded. Folding it into the 0..1
 * dimension registry would misrepresent a count as a verdict.
 *
 * Marker format: matches both reader-facing citation formats actually
 * observed live this session (2026-08-28) against the deployed pipeline —
 * `[n]` (the web door, `probe/ask.ts` output) and `[^n]` (the MCP door,
 * `prashna_ask` output) — see this module's own test file for the verbatim
 * captured prose both formats come from. `citations/rewriter.ts`'s
 * `reader_label` field is the authoritative source of the reader-facing
 * marker shape server-side; this module does not import from it (it
 * operates on already-served `proseText`, which is all a corpus run has),
 * so if a THIRD marker convention is ever introduced, this regex needs a
 * matching update — that is a known, disclosed limitation, not a hidden one.
 *
 * §N.8 discipline: `status: 'not_measurable'` (never a fabricated 0) when
 * there is no prose to measure at all (null or empty string) — a reading
 * with prose but genuinely zero citations is a REAL, honestly-measured
 * `0` density, not the same state as "nothing was measured."
 */

export type CitationDensityStatus = 'measured' | 'not_measurable'

export interface CitationDensityMeasurement {
  status: CitationDensityStatus
  /** Total citation marker occurrences in the prose (repeats of the same index count separately). */
  citationMarkerCount: number | null
  /** Count of distinct citation indices referenced (`[1]` and `[1]` again count once). */
  distinctCitationIndices: number | null
  /** Whitespace-delimited word count of the prose. */
  wordCount: number | null
  /** Sentence count, by a simple `.`/`!`/`?` boundary split — a coarse proxy, not a claim classifier. */
  sentenceCount: number | null
  citationsPer100Words: number | null
  citationsPerSentence: number | null
  /** Populated iff status is `not_measurable`. */
  reason: string | null
}

const CITATION_MARKER_RE = /\[\^?(\d+)\]/g

function countSentences(text: string): number {
  const matches = text.match(/[^.!?]+[.!?]+/g)
  if (matches && matches.length > 0) return matches.length
  // No terminal punctuation found but there is non-whitespace text — count as one sentence.
  return text.trim().length > 0 ? 1 : 0
}

function countWords(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean)
  return words.length
}

export function measureCitationDensity(proseText: string | null): CitationDensityMeasurement {
  const notMeasurable = (reason: string): CitationDensityMeasurement => ({
    status: 'not_measurable',
    citationMarkerCount: null,
    distinctCitationIndices: null,
    wordCount: null,
    sentenceCount: null,
    citationsPer100Words: null,
    citationsPerSentence: null,
    reason,
  })

  if (proseText === null) {
    return notMeasurable('no prose text was supplied for this observation')
  }
  if (proseText.trim().length === 0) {
    return notMeasurable('prose text was an empty string')
  }

  const markers = [...proseText.matchAll(CITATION_MARKER_RE)]
  const citationMarkerCount = markers.length
  const distinctCitationIndices = new Set(markers.map((m) => m[1])).size
  const wordCount = countWords(proseText)
  const sentenceCount = countSentences(proseText)

  return {
    status: 'measured',
    citationMarkerCount,
    distinctCitationIndices,
    wordCount,
    sentenceCount,
    citationsPer100Words: wordCount > 0 ? (citationMarkerCount / wordCount) * 100 : 0,
    citationsPerSentence: sentenceCount > 0 ? citationMarkerCount / sentenceCount : 0,
    reason: null,
  }
}
