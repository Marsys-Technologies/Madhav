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
 * pattern against both.
 *
 * ── WHY TWO WHOLE-STRING SURFACES WERE NOT ENOUGH (round 3, M-2/C-2) ─────────
 * The paragraph above used to continue: "Per-word ambiguity is handled for
 * free: a pattern only needs ONE surface to match it, so `d1e and ki11 myself`
 * is caught by `die` on the i-surface and `kill myself` on the l-surface, with
 * no cartesian blow-up." That reasoning holds only when each PATTERN needs one
 * reading. It fails the moment a single pattern spans two words that need
 * DIFFERENT readings, because both readings were applied to the whole string at
 * once:
 *
 *     "k1ll myse1f"  needs  k1ll → kill   (the i-reading)
 *                    AND    myse1f → myself (the l-reading)
 *
 * — and neither whole-string surface delivers both. Exhaustive enumeration of
 * the 16 ways to leet-substitute "kill myself" found 7 misses (43.8%):
 * `k11l myself`, `k1l1 myself`, `k111 myself`, `k1ll myse1f`, `k11l myse1f`,
 * `k1l1 myse1f`, `k111 myse1f`. The first three are single-word cases the
 * whole-string reading also cannot express: `k111` needs i,l,l at three
 * positions IN ONE WORD.
 *
 * So the expansion is now PER POSITION, not per string. Each token gets the
 * powerset of its own ambiguous positions (`tokenReadings`), and the surfaces
 * are the cartesian product of the tokens' readings — bounded by
 * `MAX_NORMALIZED_SURFACES`, with the two whole-string uniform readings ALWAYS
 * emitted first so the output is a strict SUPERSET of the previous behaviour no
 * matter how the bound bites. That superset property is the module's safety
 * invariant and `normalize_ambiguity_round3.test.ts` asserts it directly.
 *
 * A note on the compounding bug this interacts with: `collapseElongation`
 * rewrites a run of 3+ identical characters to one, so the uniform l-reading of
 * `k1ll` is `klll` → `kl`, which matches nothing. That is exactly why a uniform
 * reading cannot be the only mechanism, and exactly why the per-position
 * expansion produces `kill` DIRECTLY rather than relying on a collapse to
 * recover it. Elongation collapse still runs, per surface, after assembly.
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

/**
 * The UNAMBIGUOUS substitutions only — every entry of `CONFUSABLES` whose glyph
 * is not in `AMBIGUOUS_I_L_GLYPHS`.
 *
 * Applied first and uniformly (round 3, M-2), so the per-position expansion
 * below has exactly one kind of choice to make. Derived, never hand-listed, for
 * the same reason `CONFUSABLES_L` is.
 */
const CONFUSABLES_UNAMBIGUOUS: Record<string, string> = Object.fromEntries(
  Object.entries(CONFUSABLES).filter(([g]) => !AMBIGUOUS_I_L_GLYPHS.includes(g)),
)

const CONFUSABLE_RE = /[0134577@$!|£€¡]/g

/** The ambiguous glyphs as a set, for O(1) per-character tests. */
const AMBIGUOUS_SET = new Set<string>(AMBIGUOUS_I_L_GLYPHS)

/**
 * Ceiling on the number of normalized surfaces one query may expand to.
 *
 * The expansion is a cartesian product, so it needs a bound or a string of
 * exclamation marks becomes a denial-of-service. When the bound would be
 * exceeded, the offending token degrades to its two uniform readings and then,
 * if still over, to its i-reading only — and the two whole-string uniform
 * readings are emitted regardless, so degrading can never drop below the
 * pre-round-3 behaviour.
 *
 * 32 comfortably covers the real evasion space: the worst enumerated case,
 * `k111 myse1f`, needs 8 × 2 = 16.
 */
export const MAX_NORMALIZED_SURFACES = 32

/**
 * Per-token ceiling on positions expanded exhaustively. A token with more
 * ambiguous glyphs than this contributes only its two uniform readings — at 5+
 * ambiguous glyphs inside ONE word the input is no longer a spelling of a real
 * word, and the powerset is pure cost.
 */
export const MAX_AMBIGUOUS_POSITIONS_PER_TOKEN = 4

/**
 * Every reading of ONE token: the powerset of its ambiguous positions.
 *
 * `k1ll` → `kill`, `klll`. `k111` → all 8 of `kiii`…`klll`, which includes the
 * one that matters, `kill`. A token with no ambiguous glyph returns itself, so
 * the common case allocates nothing extra.
 */
function tokenReadings(token: string): string[] {
  const positions: number[] = []
  for (let i = 0; i < token.length; i++) if (AMBIGUOUS_SET.has(token[i])) positions.push(i)
  if (positions.length === 0) return [token]

  const apply = (choose: (bit: number) => string): string => {
    const ch = [...token]
    positions.forEach((p, bit) => {
      ch[p] = choose(bit)
    })
    return ch.join('')
  }
  const uniform = [apply(() => 'i'), apply(() => 'l')]
  if (positions.length > MAX_AMBIGUOUS_POSITIONS_PER_TOKEN) return dedupe(uniform)

  const out: string[] = []
  for (let mask = 0; mask < 1 << positions.length; mask++) {
    out.push(apply((bit) => (((mask >> bit) & 1) === 1 ? 'l' : 'i')))
  }
  // Uniform readings first so the degradation path and the full path agree on
  // which surfaces are the "baseline" two.
  return dedupe([...uniform, ...out])
}

function dedupe(xs: readonly string[]): string[] {
  return Array.from(new Set(xs))
}

/**
 * Expand every token's readings into whole-string surfaces.
 *
 * Left-to-right with a running bound: a token whose readings would push the
 * product past `MAX_NORMALIZED_SURFACES` is degraded (uniform pair → i-reading
 * only) rather than truncating the product mid-way, so the surfaces that ARE
 * produced stay complete strings.
 */
function expandAmbiguity(text: string): string[] {
  // Split KEEPING the separators, so re-joining is exact.
  const parts = text.split(/(\s+)/)
  let surfaces: string[] = ['']
  for (const part of parts) {
    let readings = tokenReadings(part)
    if (surfaces.length * readings.length > MAX_NORMALIZED_SURFACES) {
      readings = dedupe(readings.slice(0, 2))
      if (surfaces.length * readings.length > MAX_NORMALIZED_SURFACES) readings = readings.slice(0, 1)
    }
    surfaces =
      readings.length === 1
        ? surfaces.map((s) => s + readings[0])
        : surfaces.flatMap((s) => readings.map((r) => s + r))
  }
  return surfaces
}

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

  // ── PER-POSITION EXPANSION (round 3, M-2/C-2) ─────────────────────────────
  // The unambiguous confusables are folded uniformly first; what remains for
  // `expandAmbiguity` to choose about is exactly `1`, `!` and `|`. The two
  // uniform whole-string readings lead the list unconditionally — they are the
  // pre-round-3 output, and leading with them makes `normalizedAll[0] ===
  // normalized` (which `squashed` and every pre-hardening consumer rely on)
  // true by construction rather than by luck.
  const withUnambiguous = s.replace(CONFUSABLE_RE, (ch) => CONFUSABLES_UNAMBIGUOUS[ch] ?? ch)
  const settle = (n: string): string => collapseElongation(n).replace(/\s+/g, ' ').trim()
  const normalizedAll = Array.from(
    new Set([normalized, normalizedL, ...expandAmbiguity(withUnambiguous).map(settle)]),
  )
  const squashedAll = Array.from(new Set(normalizedAll.map((n) => n.replace(/[^a-z0-9]/g, ''))))

  return { normalized, squashed: squashedAll[0], normalizedAll, squashedAll, literal }
}

/** sha256 hex of a matched span — the only form a match is ever persisted in. */
export function spanHash(span: string): string {
  return createHash('sha256').update(span, 'utf8').digest('hex')
}
