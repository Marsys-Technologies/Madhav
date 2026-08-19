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
  /** Diacritic-folded, lowercased, confusable-folded, whitespace-collapsed. */
  normalized: string
  /** `normalized` with every non `[a-z0-9]` character removed. */
  squashed: string
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
  s = s.replace(CONFUSABLE_RE, (ch) => CONFUSABLES[ch] ?? ch)
  s = collapseElongation(s)
  const normalized = s.replace(/\s+/g, ' ').trim()
  const squashed = normalized.replace(/[^a-z0-9]/g, '')
  return { normalized, squashed, literal }
}

/** sha256 hex of a matched span — the only form a match is ever persisted in. */
export function spanHash(span: string): string {
  return createHash('sha256').update(span, 'utf8').digest('hex')
}
