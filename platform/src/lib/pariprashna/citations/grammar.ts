/**
 * pariprashna/citations/grammar.ts — PB-1 lane S-3.
 *
 * Tolerant sentinel grammar. The synthesis model is INSTRUCTED to emit the
 * canonical inline form:
 *
 *     ⟦cite: <ref>⟧          (U+27E6 MATHEMATICAL LEFT WHITE SQUARE BRACKET …
 *                             … U+27E7 right)
 *
 * but models drift, so the parser accepts a family of variants and NORMALIZES
 * them all to the canonical form, LOGGING (never dropping) each normalization so
 * the drift is observable rather than silently absorbed.
 *
 * Accepted variants:
 *   • bracket family: ⟦…⟧  or  [[…]]  (and mixed ⟦…]] / [[…⟧)
 *   • keyword case:   cite / CITE / Cite / cItE …
 *   • spacing:        ⟦cite:X⟧ / ⟦ cite : X ⟧ / ⟦cite:  X  ⟧ (leading/trailing/around ':')
 *
 * The `cite` keyword + `:` separator are REQUIRED — a bare `[[foo]]` (e.g. a
 * wiki link) is deliberately NOT a citation and parse returns { ok: false } so
 * the caller emits it as plain prose.
 */

/** Canonical opener / closer code points. */
export const CANON_OPEN = '⟦' // U+27E6
export const CANON_CLOSE = '⟧' // U+27E7

/** All recognized opener token strings. */
export const OPENERS = ['[[', CANON_OPEN] as const
/** All recognized closer token strings. */
export const CLOSERS = [']]', CANON_CLOSE] as const

/**
 * One tolerant regex over a COMPLETE candidate sentinel (opener … closer).
 * Group 1 captures the raw reference (later trimmed). The ref body excludes the
 * closer characters so `[[cite:foo]]` stops at `]]`.
 */
const SENTINEL_RE = new RegExp(
  '^(?:\\[\\[|\\u27E6)\\s*cite\\s*:\\s*([^\\u27E7\\]]+?)\\s*(?:\\]\\]|\\u27E7)$',
  'i',
)

export interface SentinelParseOk {
  ok: true
  ref: string
  /** Canonical rendering of this sentinel. */
  canonical: string
  /** True when the raw form differed from canonical (→ log a normalization). */
  normalized: boolean
  /** Human note describing what was normalized (bracket/case/spacing). */
  note: string
}
export interface SentinelParseFail {
  ok: false
}
export type SentinelParseResult = SentinelParseOk | SentinelParseFail

/**
 * Parse a COMPLETE candidate sentinel string (from opener through closer).
 * Returns the normalized ref + a normalization note, or { ok: false } when the
 * candidate is not a well-formed citation sentinel.
 */
export function parseSentinel(raw: string): SentinelParseResult {
  const m = SENTINEL_RE.exec(raw)
  if (!m) return { ok: false }
  const ref = m[1].trim()
  if (ref.length === 0) return { ok: false }

  const canonical = `${CANON_OPEN}cite: ${ref}${CANON_CLOSE}`
  const normalized = raw !== canonical

  const notes: string[] = []
  const usedSquare = raw.includes('[[') || raw.includes(']]')
  const usedCanonBracket = raw.includes(CANON_OPEN) || raw.includes(CANON_CLOSE)
  if (usedSquare && usedCanonBracket) notes.push('mixed-bracket')
  else if (usedSquare) notes.push('square-bracket-variant')
  if (!raw.includes('cite')) notes.push('keyword-case') // literal 'cite' absent → case variant
  // spacing variance = normalized for a reason other than brackets/case.
  const bracketOrCaseNormalizedForm = raw
    .replace(/\[\[/g, CANON_OPEN)
    .replace(/\]\]/g, CANON_CLOSE)
    .toLowerCase()
  const bracketOrCaseOnly =
    notes.length > 0 && bracketOrCaseNormalizedForm === canonical.toLowerCase()
  if (normalized && !bracketOrCaseOnly) notes.push('spacing')

  return {
    ok: true,
    ref,
    canonical,
    normalized,
    note: notes.length ? notes.join('+') : 'canonical',
  }
}

/**
 * Locate the earliest opener in `s` at or after `from`.
 * Returns the index + which opener token matched, or null.
 */
export function findOpener(
  s: string,
  from = 0,
): { index: number; token: string } | null {
  let best: { index: number; token: string } | null = null
  for (const tok of OPENERS) {
    const i = s.indexOf(tok, from)
    if (i !== -1 && (best === null || i < best.index)) {
      best = { index: i, token: tok }
    }
  }
  return best
}

/**
 * Locate the earliest closer in `s` at or after `from`.
 * Tolerant: matches EITHER closer regardless of which opener began the hold,
 * so `⟦cite:x]]` still closes.
 */
export function findCloser(
  s: string,
  from = 0,
): { index: number; token: string } | null {
  let best: { index: number; token: string } | null = null
  for (const tok of CLOSERS) {
    const i = s.indexOf(tok, from)
    if (i !== -1 && (best === null || i < best.index)) {
      best = { index: i, token: tok }
    }
  }
  return best
}
