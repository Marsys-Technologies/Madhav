/**
 * The window-opening ask — reading the reader's answer (lane P4-G).
 *
 * This is the module adversarial review will attack, so its contract is stated as narrowly as
 * it can be honestly stated:
 *
 *   THIS FUNCTION DECIDES WHETHER AN ANSWER IS UNAMBIGUOUS. IT DOES NOT DECIDE WHAT
 *   AMBIGUOUS ANSWERS PROBABLY MEAN.
 *
 * Everything below follows from that. The default is `not_an_answer`. A message must carry
 * exactly one unambiguous outcome signal and no conflicting one to be read as an outcome. Every
 * other shape — two signals disagreeing, a hedge next to a yes, a bare sentence with no signal
 * at all — resolves to `ambiguous` or `not_an_answer`, and NOTHING is written to the ledger.
 *
 * ── WHY SO CONSERVATIVE (the calibration-poisoning argument) ───────────────────────────────
 * The entire loop exists to produce a calibration series that is testable against lived
 * reality (CLAUDE.md §A). A wrong outcome is strictly worse than a missing one: a missing
 * outcome leaves a visible gap the review surface already reports as a neutral coverage
 * statistic, while a wrong outcome is indistinguishable from a right one forever after and
 * silently biases every Brier score computed from it. Recall is cheap to fix — the reader is
 * right there and the ask can be repeated. Precision is not.
 *
 * ── DISPUTE NON-FOLDING (binding, and enforced in three independent places) ────────────────
 * A disagreement the reader expresses must survive AS a disagreement. It must not be averaged
 * into a "partial", read as a "did_not_happen" because it sounded negative, or dropped because
 * it did not parse. Here that is enforced by:
 *   1. `dispute` being checked FIRST and WINNING outright — a message carrying both a dispute
 *      marker and an outcome marker is a dispute, full stop. There is no blend.
 *   2. `DISPUTE_IS_NEVER_AN_OUTCOME` (below) — `outcomeOf()` returns null for it by
 *      construction, so no caller can extract an outcome from a dispute even by mistake.
 *   3. `capture.ts` refusing to transition the ledger row on a dispute, leaving it
 *      `window_closed` — a DB-observable fact, not a promise. See that module.
 * Note the direction of the failure: a dispute suppresses an outcome that might otherwise have
 * been recorded. Non-folding costs recall, deliberately.
 *
 * ── WHY `did_not_happen` AND `dispute` ARE DIFFERENT THINGS ────────────────────────────────
 * "It didn't happen" is data: the claim was falsifiable, and it was falsified. That is a
 * GOOD outcome for a calibration series and must be recorded. "You have framed this wrong" is
 * not data about the world; it is data about the QUESTION. Scoring the second as the first
 * would record a falsification the reader never asserted — the exact fold this lane forbids.
 *
 * ISOMORPHIC (pure, no I/O, no model). The classifier shows its work: every matched phrase is
 * returned, so a disagreement about a reading is a disagreement about a listed regex and not
 * about an opaque judgement (§N.7 — narration traces to what it read).
 */

// ---------------------------------------------------------------------------
// Reading vocabulary
// ---------------------------------------------------------------------------

export const ANSWER_KINDS = [
  'happened',
  'did_not_happen',
  'partial',
  'cant_tell',
  'dispute',
  'ambiguous',
  'not_an_answer',
] as const
export type AnswerKind = (typeof ANSWER_KINDS)[number]

/** The three kinds that carry a scorable outcome. `cant_tell` is honest but unscorable. */
export const SCORABLE_ANSWER_KINDS: readonly AnswerKind[] = ['happened', 'did_not_happen', 'partial']

/**
 * Structural guarantee for the non-folding rule: these kinds can NEVER yield an outcome, no
 * matter what else a message contained. Asserted by the unit tests over the whole cross product
 * of markers, not just over hand-picked strings.
 */
export const DISPUTE_IS_NEVER_AN_OUTCOME = true as const

type Signal = 'affirm' | 'deny' | 'partial' | 'hedge' | 'dispute'

interface Marker {
  signal: Signal
  re: RegExp
  /** Bare tokens ("yes", "no") only count near the START of a short message — see below. */
  bareToken?: boolean
}

/**
 * Ordered marker table. Multi-word ANCHORED phrases wherever possible: a long message that
 * merely contains the word "no" somewhere is not an answer, and treating it as one is the
 * single most likely way this module would corrupt the ledger.
 *
 * `\b` word boundaries throughout, so "yes" does not match inside "yesterday" and "no" does not
 * match inside "nothing" / "note" / "now".
 */
const MARKERS: readonly Marker[] = [
  // ── DISPUTE — checked first, wins outright. About the QUESTION, not the world. ──
  { signal: 'dispute', re: /\byou(?:'ve| have)\s+(?:framed|got|described|characteri[sz]ed)\s+(?:this|that|it)\s+wrong\b/ },
  { signal: 'dispute', re: /\b(?:that(?:'s| is)|this is)\s+the\s+wrong\s+(?:question|framing|way\s+to\s+(?:ask|put)|thing\s+to\s+ask)\b/ },
  { signal: 'dispute', re: /\byou(?:'re| are)\s+asking\s+(?:the\s+wrong|about\s+the\s+wrong)\b/ },
  { signal: 'dispute', re: /\bi\s+never\s+(?:said|told\s+you|asked)\b/ },
  { signal: 'dispute', re: /\b(?:that(?:'s| is)|this is)\s+not\s+what\s+(?:i|you)\s+(?:said|meant|told)\b/ },
  { signal: 'dispute', re: /\bmischaracteri[sz]/ },
  { signal: 'dispute', re: /\bi\s+disagree\b/ },
  { signal: 'dispute', re: /\b(?:disagree|take\s+issue)\s+with\s+(?:the|your|this|that)\b/ },
  { signal: 'dispute', re: /\bcan(?:'t|not)\s+be\s+answered\s+(?:like\s+that|that\s+way|yes\s+or\s+no)\b/ },
  { signal: 'dispute', re: /\bwrong\s+premise\b/ },
  { signal: 'dispute', re: /\byou\s+(?:have\s+)?misread\b/ },

  // ── HEDGE (can't-tell). Honest non-answers, and ambiguity detectors when paired. ──
  { signal: 'hedge', re: /\bcan(?:'t|not)\s+(?:really\s+)?(?:tell|say|know)\b/ },
  { signal: 'hedge', re: /\bdo(?:n't| not)\s+(?:really\s+)?know\b/ },
  { signal: 'hedge', re: /\bno\s+(?:idea|way\s+to\s+know|way\s+of\s+knowing)\b/ },
  { signal: 'hedge', re: /\btoo\s+early\s+to\s+(?:tell|say|know)\b/ },
  { signal: 'hedge', re: /\bhard\s+to\s+(?:tell|say)\b/ },
  { signal: 'hedge', re: /\b(?:i(?:'m| am)\s+)?not\s+(?:really\s+)?sure\b/ },
  { signal: 'hedge', re: /\bunsure\b/ },
  { signal: 'hedge', re: /\bunclear\b/ },
  { signal: 'hedge', re: /\bi\s+couldn(?:'t| not)\s+say\b/ },
  { signal: 'hedge', re: /\bmaybe\b/ },
  { signal: 'hedge', re: /\bpossibly\b/ },
  { signal: 'hedge', re: /\bi\s+think\s+so\b/ },
  { signal: 'hedge', re: /\bprobably\b/ },

  // ── PARTIAL — the honest middle. Wins over a lone affirm/deny (see rules). ──
  { signal: 'partial', re: /\bpart(?:ly|ially)\b/ },
  { signal: 'partial', re: /\bin\s+part\b/ },
  { signal: 'partial', re: /\bsome\s+of\s+it\b/ },
  { signal: 'partial', re: /\bsomewhat\b/ },
  { signal: 'partial', re: /\bsort\s+of\b/ },
  { signal: 'partial', re: /\bkind\s+of\b/ },
  { signal: 'partial', re: /\bmore\s+or\s+less\b/ },
  { signal: 'partial', re: /\bto\s+(?:an|some)\s+extent\b/ },
  { signal: 'partial', re: /\bhalf(?:way)?\b/ },
  { signal: 'partial', re: /\bmixed\b/ },
  { signal: 'partial', re: /\bnot\s+entirely\b/ },
  { signal: 'partial', re: /\bup\s+to\s+a\s+point\b/ },

  // ── DENY. Note these are ANCHORED to happening, never to a bare negation. ──
  { signal: 'deny', re: /\b(?:it|that|this)\s+did\s*n(?:'|o)t\s+happen\b/ },
  { signal: 'deny', re: /\bdid\s+not\s+happen\b/ },
  { signal: 'deny', re: /\bdidn't\s+happen\b/ },
  { signal: 'deny', re: /\bnever\s+happened\b/ },
  { signal: 'deny', re: /\bnothing\s+(?:happened|came\s+of\s+(?:it|that))\b/ },
  { signal: 'deny', re: /\b(?:has|have)\s*n(?:'|o)t\s+happened\b/ },
  { signal: 'deny', re: /\bthat\s+never\s+came\b/ },
  { signal: 'deny', re: /\bit\s+did\s+not\b(?!\s+happen)/ },
  { signal: 'deny', re: /\bno,?\s+(?:it|that)\s+did\s*n(?:'|o)t\b/ },
  { signal: 'deny', re: /\bfell\s+through\b/ },
  { signal: 'deny', re: /\bcame\s+to\s+nothing\b/ },
  { signal: 'deny', re: /\bno\b/, bareToken: true },
  { signal: 'deny', re: /\bnope\b/, bareToken: true },
  { signal: 'deny', re: /\bnah\b/, bareToken: true },

  // ── AFFIRM ──
  { signal: 'affirm', re: /\b(?:it|that|this)\s+(?:did\s+)?happen(?:ed)?\b/ },
  { signal: 'affirm', re: /\b(?:it|that)\s+came\s+true\b/ },
  { signal: 'affirm', re: /\bcame\s+true\b/ },
  { signal: 'affirm', re: /\byou\s+(?:were|got\s+it)\s+right\b/ },
  { signal: 'affirm', re: /\b(?:that(?:'s| is)|this is)\s+(?:right|correct|exactly\s+right)\b/ },
  { signal: 'affirm', re: /\bexactly\s+(?:what|as)\s+(?:happened|you\s+said)\b/ },
  { signal: 'affirm', re: /\bit\s+played\s+out\b/ },
  { signal: 'affirm', re: /\byes\b/, bareToken: true },
  { signal: 'affirm', re: /\byeah\b/, bareToken: true },
  { signal: 'affirm', re: /\byep\b/, bareToken: true },
  { signal: 'affirm', re: /\bcorrect\b/, bareToken: true },
]

/**
 * A bare token ("yes" / "no") is only an answer when the message is SHORT or the token OPENS
 * it. Rationale: "No, tell me about Saturn instead" opens with a real refusal; "I was reading
 * about this and there's no doubt Saturn matters" merely contains the word. The window is
 * deliberately tight — 6 words — because a long message is a new question, not an answer.
 */
export const BARE_TOKEN_MAX_WORDS = 6

/** Normalize for matching: lowercase, unify apostrophes, punctuation → space, collapse. */
export function normalizeAnswer(text: string): string {
  return text
    .toLowerCase()
    .replace(/[‘’ʼ]/g, "'")
    .replace(/[^a-z0-9'\s]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export interface AnswerReading {
  kind: AnswerKind
  /** Every marker that fired, as `signal:source` — the audit trail for the decision. */
  matched: string[]
  /** Which decision rule produced `kind`. Stable strings; safe to assert on in tests. */
  rule: string
  /** True iff this reading may be written to the ledger as an outcome. */
  actionable: boolean
}

/**
 * Read a free-text answer. Pure; conservative; default `not_an_answer`.
 *
 * A caller MUST NOT re-interpret an `ambiguous` / `not_an_answer` / `dispute` reading into an
 * outcome. `capture.ts` is the only intended caller and does not.
 */
export function classifyWindowAnswer(text: string): AnswerReading {
  const norm = normalizeAnswer(text ?? '')
  if (!norm) {
    return { kind: 'not_an_answer', matched: [], rule: 'empty_message', actionable: false }
  }

  const words = norm.split(' ')
  const bareTokensAllowed = words.length <= BARE_TOKEN_MAX_WORDS

  const matched: string[] = []
  const signals = new Set<Signal>()

  for (const m of MARKERS) {
    const hit = m.re.exec(norm)
    if (!hit) continue
    if (m.bareToken) {
      // Allowed when the whole message is short, OR when the token opens the message.
      const opensMessage = hit.index === 0 || norm.slice(0, hit.index).trim() === ''
      if (!bareTokensAllowed && !opensMessage) continue
    }
    matched.push(`${m.signal}:${hit[0]}`)
    signals.add(m.signal)
  }

  // ── RULE 1 — dispute wins outright. No blending, ever. ──
  if (signals.has('dispute')) {
    return { kind: 'dispute', matched, rule: 'dispute_wins_outright', actionable: false }
  }

  const hasAffirm = signals.has('affirm')
  const hasDeny = signals.has('deny')
  const hasPartial = signals.has('partial')
  const hasHedge = signals.has('hedge')
  const outcomeSignals = [hasAffirm, hasDeny, hasPartial].filter(Boolean).length

  // ── RULE 2 — a hedge beside an outcome signal is AMBIGUOUS, never the outcome. ──
  // "I'm not sure, but I think it happened" is not a `happened`. Coercing it would be exactly
  // the calibration poisoning this module exists to prevent.
  if (hasHedge && outcomeSignals > 0) {
    return { kind: 'ambiguous', matched, rule: 'hedge_beside_outcome_not_coerced', actionable: false }
  }

  // ── RULE 3 — a clean hedge is an honest can't-tell. First-class, and writable. ──
  if (hasHedge) {
    return { kind: 'cant_tell', matched, rule: 'hedge_only', actionable: true }
  }

  // ── RULE 4 — affirm AND deny together is a contradiction we do not resolve. ──
  if (hasAffirm && hasDeny) {
    return { kind: 'ambiguous', matched, rule: 'affirm_and_deny_conflict', actionable: false }
  }

  // ── RULE 5 — partial is the honest middle and absorbs a lone affirm or deny.
  // "partly, yes" and "it happened, but only partly" are both `partial`, not `happened`. ──
  if (hasPartial) {
    return { kind: 'partial', matched, rule: 'partial_absorbs_single_polarity', actionable: true }
  }

  // ── RULE 6 — exactly one clean polarity. ──
  if (hasAffirm) return { kind: 'happened', matched, rule: 'affirm_only', actionable: true }
  if (hasDeny) return { kind: 'did_not_happen', matched, rule: 'deny_only', actionable: true }

  // ── RULE 7 — nothing recognised. The reader said something else entirely. ──
  return { kind: 'not_an_answer', matched, rule: 'no_signal', actionable: false }
}

/**
 * The ledger `outcome` a reading maps to, or null when it maps to none.
 *
 * `dispute`, `ambiguous` and `not_an_answer` return null BY CONSTRUCTION — this is the second
 * of the three non-folding enforcement points named in the module header. There is deliberately
 * no `else` branch that could ever produce a value for them.
 */
export function outcomeOf(reading: AnswerReading): 'happened' | 'did_not_happen' | 'partial' | 'unverifiable' | null {
  switch (reading.kind) {
    case 'happened':
      return 'happened'
    case 'did_not_happen':
      return 'did_not_happen'
    case 'partial':
      return 'partial'
    case 'cant_tell':
      return 'unverifiable'
    case 'dispute':
    case 'ambiguous':
    case 'not_an_answer':
      return null
  }
}
