/**
 * Paripraśna safety — TEXT NORMALIZATION for the deterministic classifier.
 *
 * A keyword classifier that reads the raw string is a classifier that anyone
 * can walk past with a period between the letters. This module is the reason
 * the classifier's patterns can stay readable: every evasion that is a SPELLING
 * transformation is undone here, once, before any pattern runs.
 *
 * Two outputs, because they answer different questions:
 *
 *   · `normalized` — human-shaped text with word boundaries INTACT. Short
 *     tokens (`die`, `dead`) must be matched here with `\b`, or `deadline` and
 *     `diet` become self-harm detections.
 *   · `squashed`   — every non-alphanumeric removed, so `s.u.i.c.i.d.e`,
 *     `k i l l   m y s e l f` and `end-my-life` all collapse onto the same
 *     string. Substring matching here has NO word boundaries, so it is
 *     restricted by contract to patterns of >= MIN_SQUASHED_PATTERN_LENGTH
 *     characters (`classifier.ts` asserts this at module load, so a future
 *     short pattern is a startup failure, not a silent false-positive source).
 *
 * WHAT THIS MODULE DELIBERATELY DOES NOT DO: it never removes, weakens, or
 * "cleans away" a match. Normalization only ever makes MORE text visible to the
 * patterns. There is no path through this file on which a string that would
 * have matched stops matching.
 *
 * ── THE `1` AMBIGUITY, AND WHY THERE ARE TWO SURFACES (hardening round, C-2) ──
 * The paragraph above used to be FALSE, and the counter-example cost two
 * keystrokes: `CONFUSABLES` mapped `1 → i` and nothing else, so `ki11 myself`
 * folded to `ki myself` (`kiii` → elongation-collapsed to `ki`) and `end my
 * 1ife` folded to `end my iife`. Both are HS-2 phrases that the un-evaded
 * spelling matches; both stopped matching after normalization. Choosing ONE
 * expansion for a genuinely ambiguous glyph does not widen what the patterns
 * see — it DESTROYS the other reading.
 *
 * The fix is to stop choosing. `1`, `|` and `!` are ambiguous between `i` and
 * `l`, so this module emits BOTH expansions and the classifier runs every
 * pattern against both. Per-word ambiguity is handled for free: a pattern only
 * needs ONE surface to match it, so `d1e and ki11 myself` is caught by `die` on
 * the i-surface and `kill myself` on the l-surface, with no cartesian blow-up.
 *
 * The claim in the paragraph above is now true again, and `normalize.test.ts`
 * holds it: for every ambiguous glyph, the un-evaded spelling survives on at
 * least one emitted surface.
 */

import { createHash } from 'node:crypto'

/** Substring matching against `squashed` has no word boundaries; short patterns are banned. */
export const MIN_SQUASHED_PATTERN_LENGTH = 8

/**
 * Confusable/leet substitutions, applied AFTER diacritic folding.
 *
 * Only substitutions that map a non-letter onto a letter are listed. Letter →
 * letter "corrections" (e.g. `ph` → `f`) are deliberately absent: they would
 * make the normalizer lossy in a way that could COLLAPSE two distinct real
 * words, and the goal here is to widen what patterns see, never to guess.
 *
 * This is the `i` reading of the ambiguous glyphs. See `CONFUSABLES_L` for the
 * `l` reading and the module header for why both are emitted.
 */
const CONFUSABLES: Record<string, string> = {
  '0': 'o',
  '1': 'i',
  '3': 'e',
  '4': 'a',
  '5': 's',
  '7': 't',
  '@': 'a',
  $: 's',
  '!': 'i',
  '|': 'i',
  '£': 'l',
  '€': 'e',
  '¡': 'i',
}

/**
 * The glyphs that are genuinely ambiguous between `i` and `l`.
 *
 * Named as a set rather than inlined so the two maps below cannot drift apart
 * and so the invariant test can enumerate exactly what it must cover.
 */
export const AMBIGUOUS_I_L_GLYPHS: readonly string[] = ['1', '!', '|'] as const

/**
 * The `l` reading. Identical to `CONFUSABLES` except on `AMBIGUOUS_I_L_GLYPHS`
 * — derived from it rather than written out a second time, so adding a
 * substitution to `CONFUSABLES` cannot leave this map silently behind.
 */
const CONFUSABLES_L: Record<string, string> = {
  ...CONFUSABLES,
  ...Object.fromEntries(AMBIGUOUS_I_L_GLYPHS.map((g) => [g, 'l'])),
}

const CONFUSABLE_RE = /[0134577@$!|£€¡]/g

/** Zero-width and invisible separators used to break up a token. */
const INVISIBLES = /[­᠎​-‏‪-‮⁠-⁤﻿]/g

/** Combining marks left behind by NFKD decomposition. */
const COMBINING_MARKS = /[̀-ͯ]/g

/** Unicode quote/dash/space variants folded to their ASCII form. */
const PUNCT_FOLD: Array<[RegExp, string]> = [
  [/[‘’‚‛′]/g, "'"],
  [/[“”„‟″]/g, '"'],
  [/[‐-―−]/g, '-'],
  [/[  -   　]/g, ' '],
]

export interface NormalizedQueryText {
  /**
   * Diacritic-folded, lowercased, confusable-folded, whitespace-collapsed —
   * with the ambiguous `1|!` glyphs read as `i`.
   *
   * Kept as the primary field (rather than replaced by the array below) because
   * it is the surface a human debugging a match wants to see, and because every
   * pre-hardening consumer already names it.
   */
  normalized: string
  /** `normalized` with every non `[a-z0-9]` character removed. */
  squashed: string
  /**
   * EVERY normalized surface, deduped: the `i` reading first, then the `l`
   * reading when the two differ. A pattern that matches on ANY entry is a
   * match — that is what makes the `1 → {i,l}` ambiguity non-destructive.
   *
   * Length 1 for the overwhelming majority of real queries (no ambiguous glyph
   * present), so the extra pass costs nothing on the hot path.
   */
  normalizedAll: readonly string[]
  /** The squashed form of each entry in `normalizedAll`, same order, deduped. */
  squashedAll: readonly string[]
  /**
   * Everything `normalized` has EXCEPT the confusable folding — so real digits
   * survive as digits.
   *
   * This exists because the two consumers need opposite things from the same
   * pipeline. The CLASSIFIER wants `d1e` to read as `die`, which means folding
   * `1 → i`; but that same fold turns the year `2047` into `2oat`, and the
   * PRE-WIRE SCAN's entire job is spotting a mortality term next to a year.
   * Running the scan on the folded form made it blind to every date — a real
   * defect this lane's own test suite caught before the scan shipped. Both
   * forms are produced once, and each consumer names the one it needs.
   */
  literal: string
}

/**
 * Collapse a run of 3+ identical letters to one.
 *
 * Three, not two: English has real doubles (`kill`, `still`, `all`), and
 * collapsing those would break the patterns themselves. `diiiiie` → `die`.
 */
function collapseElongation(s: string): string {
  return s.replace(/([a-z0-9])\1{2,}/g, '$1')
}

export function normalizeForClassification(raw: string): NormalizedQueryText {
  let s = (raw ?? '').normalize('NFKD')
  s = s.replace(COMBINING_MARKS, '')
  s = s.replace(INVISIBLES, '')
  for (const [re, to] of PUNCT_FOLD) s = s.replace(re, to)
  s = s.toLowerCase()
  const literal = collapseElongation(s).replace(/\s+/g, ' ').trim()

  // Both readings of the ambiguous glyphs. `fold` is applied to the SAME
  // pre-confusable string, so the two surfaces differ only where they must.
  const fold = (map: Record<string, string>): string =>
    collapseElongation(s.replace(CONFUSABLE_RE, (ch) => map[ch] ?? ch))
      .replace(/\s+/g, ' ')
      .trim()

  const normalized = fold(CONFUSABLES)
  const normalizedL = fold(CONFUSABLES_L)
  // Deduped: identical for any input containing no ambiguous glyph, which is
  // almost every real query.
  const normalizedAll = normalizedL === normalized ? [normalized] : [normalized, normalizedL]
  const squashedAll = Array.from(new Set(normalizedAll.map((n) => n.replace(/[^a-z0-9]/g, ''))))

  return { normalized, squashed: squashedAll[0], normalizedAll, squashedAll, literal }
}

/** sha256 hex of a matched span — the only form a match is ever persisted in. */
export function spanHash(span: string): string {
  return createHash('sha256').update(span, 'utf8').digest('hex')
}
