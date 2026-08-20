/**
 * pariprashna/voice/voice_lint.ts — lane G3-D / P2-L (PPR-04, roadmap line 104).
 *
 * A LINT EXTENSION of `citations/register_leak_lint.ts` — same shape (a pure,
 * never-throwing function returning `{ clean, flags }`), same two call sites
 * (the per-delta lint in `pipeline/synthesis_stage.ts`, chained immediately
 * after the register-leak lint / citation-rewriter's own lint pass in BOTH the
 * citation-stream-on and citation-stream-off branches; the whole-block backstop
 * in `pipeline/reading_parts.ts`'s `commitBlock()`, chained immediately after
 * the register-leak lint there) — NOT a parallel scanner walking the text on
 * its own schedule. `register_leak_lint.ts`'s own detection logic is untouched;
 * this is a sibling module the two orchestration files above call alongside it.
 *
 * PPR-04's voice rule has three independently-testable parts, implemented here:
 *
 *  1. SECOND-PERSON-IMPERATIVE DETECTOR (remedial-class prose). "Remedial-class"
 *     is grounded in the REMEDY-ACTION VERB itself ("wear", "chant", "donate",
 *     ...) rather than a block-level classifier: `semantics/block_classifier.ts`
 *     (lane P2-A, already merged) classifies a paragraph's `WireReadingRole` as
 *     `verdict | elaboration | verse | caveat` — it has no remedy-adjacent role,
 *     so no finer-grained block classification exists in this codebase for this
 *     lane to reuse. This is TELEMETRY ONLY (never rewrites reader prose): no
 *     safe, generic, deterministic rewrite exists for an arbitrary imperative
 *     sentence the way `register_leak_lint.ts` can safely delete/substitute an
 *     id-shaped token. Flagging "you should wear a ruby" while leaving
 *     "the tradition prescribes wearing a ruby" untouched is the detector's
 *     whole job (roadmap line 104's own worked example).
 *
 *  2. PROBABILITY FRAMING (difficult findings only). A bare probability number
 *     ("a 72% chance") gets a deterministic qualitative-frame prefix bucketed
 *     by magnitude ("a strong 72% chance") — bounded to inserting one of four
 *     fixed words ahead of a number/noun pair already present, never inventing
 *     a new claim, and idempotent (a number already carrying a frame word is
 *     left alone) so re-running it at the whole-block backstop after the
 *     per-delta pass already framed it is a no-op.
 *
 *  3. UNCERTAINTY-BEFORE-SEVERITY ORDERING (difficult findings only). TELEMETRY
 *     ONLY: reordering sentences safely is not something a regex-level lint can
 *     do without risking a sentence that no longer reads correctly, so a
 *     severity/probability claim appearing with no preceding uncertainty frame
 *     is flagged for observability, not silently reordered.
 *
 * "Difficult finding" — no finer-grained per-block difficulty classifier
 * exists in this codebase either. The honest, real (not fabricated) proxy used
 * by both call sites is the turn's own G1-A `SafetyDecision`: `enforced` AND at
 * least one HS-class actually fired (`pacing.ts`'s `isDifficultFindingActive`).
 * This is coarser than block-level — it is turn-scoped — and that coarseness
 * is disclosed here rather than hidden behind a plausible-sounding narrower
 * claim (CLAUDE.md §N.8).
 */

export interface VoiceLintFlag {
  /** Stable wire flag code — never the matched text (gate 11 discipline). */
  code: string
  level: 'info' | 'warn' | 'error'
  detail: string
}

export interface VoiceLintResult {
  /** Reader-safe text after the bounded, idempotent probability-framing rewrite. */
  clean: string
  /** Every flag fired (telemetry + rewrite alike). */
  flags: VoiceLintFlag[]
  /** Convenience: total number of individual pattern hits across all checks. */
  hitCount: number
}

export interface VoiceLintOptions {
  /**
   * True when this turn's `SafetyDecision` shows an HS-class actually fired
   * (see `pacing.ts`'s `isDifficultFindingActive`) — the honest proxy for
   * "difficult finding" this codebase has today. Gates checks 2 and 3; check 1
   * (the imperative detector) runs unconditionally, matching the roadmap's
   * framing of it as a general voice rule, not a difficult-finding-only one.
   */
  difficultFinding: boolean
}

// ── 1. Second-person-imperative detector (remedial-class) ───────────────────

/**
 * Remedy-action verbs. Each IS the "remedial-class" scoping signal: a sentence
 * only matches the imperative patterns below when one of these verbs is the
 * one being commanded, so "you should know that Jupiter is exalted" or "you
 * must remember Saturn's transit" — imperative-shaped but NOT remedy content —
 * never fire.
 */
const REMEDY_VERBS =
  'wear|perform|chant|recite|donate|fast|worship|observe|offer|undertake|propitiate|conduct|light|feed|plant|tie|avoid|sponsor|keep'

/** "you should/must/need to/ought to/have to <remedy verb>" — a direct command
 *  to the reader. Deliberately excludes permissive modals ("may", "might",
 *  "could", "want to consider") and the generic pronoun "one" (impersonal
 *  advice, not a command to THIS reader) — both read as attributive/advisory,
 *  not imperative. */
const YOU_MODAL_IMPERATIVE = new RegExp(
  `\\byou\\s+(?:should|must|need to|ought to|have to)\\s+(?:\\w+\\s+){0,3}?(?:${REMEDY_VERBS})\\b`,
  'i',
)

/** A bare imperative sentence opening with a remedy verb ("Wear a pearl...",
 *  "Chant the Gayatri mantra..."). Sentence-initial only — a remedy verb
 *  appearing mid-sentence in a non-imperative construction ("...prescribes
 *  wearing a ruby...") does not match this pattern; it is a gerund/infinitive
 *  object, not a sentence-initial imperative verb. */
const BARE_IMPERATIVE_START = new RegExp(`^(?:${capitalizeAlternation(REMEDY_VERBS)})\\b`)

function capitalizeAlternation(alt: string): string {
  return alt
    .split('|')
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join('|')
}

/** Split into rough sentences, keeping trailing punctuation. Good enough for a
 *  telemetry-only per-sentence scan — no downstream text depends on this
 *  split being linguistically perfect. */
function splitSentences(text: string): string[] {
  const matches = text.match(/[^.!?]+[.!?]*(?:\s+|$)/g)
  if (matches) return matches.map((s) => s.trim()).filter(Boolean)
  const trimmed = text.trim()
  return trimmed ? [trimmed] : []
}

function countImperativeHits(text: string): number {
  let hits = 0
  for (const sentence of splitSentences(text)) {
    if (YOU_MODAL_IMPERATIVE.test(sentence) || BARE_IMPERATIVE_START.test(sentence)) hits += 1
  }
  return hits
}

// ── 2. Probability framing (difficult findings only) ────────────────────────

const QUALITATIVE_FRAME_WORDS = [
  'modest',
  'moderate',
  'elevated',
  'strong',
  'slight',
  'notable',
  'considerable',
  'meaningful',
  'limited',
  'high',
  'low',
  'significant',
  'substantial',
]
const QUALITATIVE_FRAME_RE = new RegExp(`\\b(?:${QUALITATIVE_FRAME_WORDS.join('|')})\\b`, 'i')

const FRAME_BY_BUCKET = {
  modest: { article: 'a', word: 'modest' },
  moderate: { article: 'a', word: 'moderate' },
  elevated: { article: 'an', word: 'elevated' },
  strong: { article: 'a', word: 'strong' },
} as const

function bucketFor(n: number): (typeof FRAME_BY_BUCKET)[keyof typeof FRAME_BY_BUCKET] {
  if (n >= 75) return FRAME_BY_BUCKET.strong
  if (n >= 50) return FRAME_BY_BUCKET.elevated
  if (n >= 25) return FRAME_BY_BUCKET.moderate
  return FRAME_BY_BUCKET.modest
}

/**
 * Prefix a bare "NN% chance/probability/likelihood/odds" with a deterministic
 * qualitative frame bucketed by magnitude, leading with the frame rather than
 * the bare number (PPR-04's own wording). A fresh RegExp is constructed per
 * call (never a shared `g`-flagged module const) — the same defensive pattern
 * `register_leak_lint.ts` uses, so a caller invoking this twice (per-delta,
 * then again at the whole-block backstop) never trips a stale `lastIndex`.
 * Idempotent: a number already preceded by a qualitative frame word within a
 * short window is left untouched, so re-running this on already-framed text
 * (the backstop re-scanning what the per-delta pass already rewrote) is a
 * no-op rather than a double prefix.
 */
function frameProbability(text: string): { clean: string; count: number } {
  let count = 0
  const pattern = /\b(a|an)?\s*(\d{1,3})\s*(%|percent)\s+(chance|probability|likelihood|odds)\b/gi
  const clean = text.replace(pattern, (whole: string, _article: string | undefined, numStr: string, pct: string, noun: string, offset: number, full: string) => {
    const windowStart = Math.max(0, offset - 24)
    const precedingWindow = full.slice(windowStart, offset)
    if (QUALITATIVE_FRAME_RE.test(precedingWindow)) return whole // already framed
    const n = Number(numStr)
    if (!Number.isFinite(n)) return whole
    const bucket = bucketFor(n)
    count += 1
    const unit = pct.toLowerCase() === 'percent' ? ' percent' : '%'
    return `${bucket.article} ${bucket.word} ${numStr}${unit} ${noun}`
  })
  return { clean, count }
}

// ── 3. Uncertainty-before-severity ordering (difficult findings only) ───────

const UNCERTAINTY_HEDGE =
  /\b(?:may|might|could|it'?s unclear|uncertain|not certain|difficult to say|hard to say|the picture is mixed|the evidence is mixed|cannot be certain|no certainty)\b/i
const SEVERITY_MARKER =
  /\b(?:severe|serious|critical|grave|significant risk|considerable risk|major concern|acute)\b/i

/**
 * True when a severity/probability-weight claim appears with no preceding
 * uncertainty hedge in the SAME text — either no hedge exists anywhere (a
 * difficult finding stating severity with zero uncertainty framing), or a
 * hedge exists but only AFTER the severity claim (severity-first ordering,
 * the exact inversion PPR-04 asks to avoid).
 */
function hasUncertaintyBeforeSeverityViolation(text: string): boolean {
  const severityMatch = SEVERITY_MARKER.exec(text)
  if (!severityMatch) return false
  const hedgeMatch = UNCERTAINTY_HEDGE.exec(text)
  if (!hedgeMatch) return true
  return hedgeMatch.index > severityMatch.index
}

// ── Entry point ───────────────────────────────────────────────────────────

/**
 * Run the voice-enforcement lint over a reader-prose fragment. Guaranteed to
 * return (never throws) — same backstop-of-the-backstop discipline as
 * `lintReaderProse`: on any internal error, pass the text through unchanged
 * and emit a telemetry flag rather than risk mangling or dropping the turn.
 */
export function lintVoiceProse(text: string, opts: VoiceLintOptions): VoiceLintResult {
  try {
    return lintVoiceInner(text, opts)
  } catch (err) {
    return {
      clean: text,
      flags: [
        {
          code: 'voice_lint_internal_error',
          level: 'warn',
          detail: String((err as Error)?.message ?? err),
        },
      ],
      hitCount: 0,
    }
  }
}

function lintVoiceInner(text: string, opts: VoiceLintOptions): VoiceLintResult {
  const flags: VoiceLintFlag[] = []
  let hitCount = 0
  let clean = text

  // 1. Imperative detector — TELEMETRY ONLY, runs regardless of difficulty.
  const imperativeHits = countImperativeHits(text)
  if (imperativeHits > 0) {
    hitCount += imperativeHits
    flags.push({
      code: 'voice_imperative_detected',
      level: 'warn',
      detail: `${imperativeHits} second-person-imperative remedy sentence(s) detected (telemetry only — not rewritten)`,
    })
  }

  if (opts.difficultFinding) {
    // 2. Probability framing — bounded, idempotent REWRITE.
    const framed = frameProbability(clean)
    if (framed.count > 0) {
      clean = framed.clean
      hitCount += framed.count
      flags.push({
        code: 'voice_probability_framed',
        level: 'info',
        detail: `${framed.count} bare-probability claim(s) prefixed with a qualitative frame`,
      })
    }

    // 3. Uncertainty-before-severity ordering — TELEMETRY ONLY.
    if (hasUncertaintyBeforeSeverityViolation(clean)) {
      hitCount += 1
      flags.push({
        code: 'voice_pacing_order_violation',
        level: 'warn',
        detail:
          'a severity/probability claim appears without a preceding uncertainty frame in a difficult-finding block',
      })
    }
  }

  return { clean, flags, hitCount }
}

/** Exposed for tests that want the pattern inventory without re-deriving it. */
export const VOICE_LINT_FLAG_CODES = [
  'voice_imperative_detected',
  'voice_probability_framed',
  'voice_pacing_order_violation',
  'voice_lint_internal_error',
] as const
