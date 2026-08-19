/**
 * Paripraśna safety — THE PRE-WIRE PHRASING SCAN (lane G1-A, HS-1 point (c)).
 *
 * SAFETY_PRIVACY_TENANCY §2 HS-1, third enforcement point: "pre-wire output
 * scan — date-adjacent mortality phrasing detector on remedial/predictive/
 * sensitive blocks." §3 adds: "the pre-wire scan extends the existing
 * register-leak lint pass (same infrastructure, new pattern classes)."
 *
 * This is a SIBLING to `citations/register_leak_lint.ts`, not an edit of it, and
 * the reason is a real behavioural difference the two cannot share:
 *
 *   · `lintReaderProse` is explicitly "never a turn-killer": on internal error
 *     it PASSES THE TEXT THROUGH, because a mangled turn is worse than a logged
 *     near-miss. Correct for an internal-identifier leak.
 *   · This scan must FAIL CLOSED. If it cannot decide, the text does not go out.
 *     A date of death reaching a reader is not a logged near-miss.
 *
 * Folding an inverted failure mode into the existing lint would have made one
 * function with two contradictory contracts. They are kept apart and both run.
 *
 * ── THE DELTA-BOUNDARY RESIDUAL, AND WHY THIS FILE CLOSES IT ─────────────────
 * The register-leak lint documents a residual: "a leak pattern split exactly
 * across a delta chunk boundary can still slip through". For an internal
 * identifier that residual is acceptable — the block-commit backstop scrubs the
 * PERSISTED text and only the live stream saw it. For HS-1 it is not: the live
 * stream is the reader. `StreamingMortalityScanner` therefore holds prose back
 * to the last SENTENCE boundary (bounded — see MAX_HOLDBACK_CHARS) so every
 * scan runs over whole sentences and no match can straddle the seam. The cost
 * is that prose arrives sentence-wise rather than token-wise while the gate is
 * armed. That is a deliberate trade, stated here rather than discovered later.
 *
 * ── THE SAME-SENTENCE ASSUMPTION, AND WHY IT IS GONE (round 3, M-3 / H-4) ────
 * Both halves of this file used to require the mortality term and the date to
 * sit in ONE sentence, and a period or a newline was a hard boundary. Two
 * consequences, both reproduced:
 *
 *   (b) NON-STREAMING. `scanMortalityPhrasing('The native will meet death. It
 *       falls in 2047.')` returned zero hits and the text unchanged. So did
 *       `'The native will meet death\nin the year 2047'` — a newline is a
 *       terminator here, so the model only has to wrap a line to walk past the
 *       scan. This is the plain, non-streaming path.
 *
 *   (a) STREAMING. Each released span was scanned in ISOLATION, so a term in
 *       one span and its date in the next were never seen together. The
 *       round-2 fix for this was `FORCED_RELEASE_OVERLAP_CHARS` — hold back the
 *       last 200 characters of a forced release — which closes the window it
 *       covers and nothing beyond it. A sweep over alignments with the term and
 *       the date more than 200 characters apart leaked the COMPLETE claim (term
 *       AND date both reaching the reader) in the majority of alignments.
 *
 * Both are the same defect: the scan's unit of context was too small. The unit
 * is now a SLIDING WINDOW of `CROSS_SENTENCE_WINDOW` consecutive sentences, and
 * the streaming wrapper carries the tail of what it has already emitted
 * (`MAX_CARRY_CONTEXT_CHARS`) into the next scan as CONTEXT — scanned, never
 * re-emitted. A date arriving in a later chunk is therefore paired against a
 * term the reader has already seen, and the sentence carrying the date is
 * redacted before it is written.
 *
 * ── THE GUARANTEE, STATED AT ITS ACTUAL WIDTH ────────────────────────────────
 * The old header said, unconditionally, "a date paired with a term now cannot
 * be emitted". That was true only inside the 200-character window. What is true
 * now, and all that is true:
 *
 *   · A term and a date within CROSS_SENTENCE_WINDOW consecutive sentences of
 *     each other are BOTH redacted (non-streaming), or the later one is
 *     withheld (streaming). Two sentences, not one — a third sentence between
 *     them is out of scope and is a KNOWN residual, not a covered case.
 *   · Across a stream seam, that window reaches back at most
 *     MAX_CARRY_CONTEXT_CHARS of already-emitted prose. Beyond that distance a
 *     pair is not detected. `phrasing_scan_round3.test.ts` sweeps the boundary
 *     and fails if either constant shrinks.
 *   · Nothing retracts a term already sent. The residual remains "a reader may
 *     see a mortality term whose date is then withheld", never "a reader may
 *     see a complete mortality claim" within the stated window.
 *
 * ── LANE G1-G (PPR-13): A SECOND PATTERN CLASS IN THE SAME PASS ──────────────
 * The roadmap's G1-G row says the answer-side entitlement scan is "folded into
 * the existing pre-wire lint pass", and TA §14A.1 says the same thing in the
 * other direction: "the register lint already walks the text; entitlement
 * checking is a second pattern class in the same pass."
 *
 * That fold is additive and it is a COMPOSITION, not an edit of anything above.
 * Nothing in the mortality rules — `MORTALITY_OUTPUT_TERMS`, `DATE_SHAPED`,
 * `DURATION_TO_END`, `sentenceHit`, the sliding window, the carry mechanism,
 * the constants, the splitter — is touched by G1-G. What G1-G adds is:
 *
 *   · `MortalityScanOptions.extraRules` — extra SENTENCE-LEVEL predicates that
 *     share this function's sentence splitting, its redaction unit, its
 *     hash-not-content reporting, and above all its FAIL-CLOSED catch. A rule
 *     that throws takes the whole span down with it, which is the correct
 *     direction for a cross-tenant confidentiality check.
 *   · `MortalityScanResult.extra_hits` — a SEPARATE channel, so `hits` keeps
 *     meaning exactly "mortality-phrasing hits" and no existing reader of it
 *     starts silently counting something else.
 *   · `MortalityScanOptions.mortalityRulesEnabled` — because the two pattern
 *     classes are gated by two DIFFERENT feature flags
 *     (`PARIPRASHNA_SAFETY_GATE_ENABLED` vs `PARIPRASHNA_INJECTION_CONTAINMENT`)
 *     and arming one must not silently arm the other. Defaults to `true`, so
 *     every pre-G1-G call site is byte-for-byte unchanged.
 *
 * THE EXTRA RULES ARE WINDOWED TOO, and the first version of this file said the
 * opposite — that a chart id is "a single self-contained token" with no pairing
 * semantics, so a window would only over-redact. A review reproduced two
 * counterexamples: a token split by a sentence terminator (the newline the
 * streaming forced release lands on) leaked a COMPLETE foreign id across the
 * seam, and the abbreviated-id rule turned out to be a genuine pair (a cue word
 * plus a hex run) that splits across sentences as easily as term-plus-date. The
 * window is now shared. See the extra-rule block below for the one place the
 * two halves' window logic deliberately differs.
 */

import { normalizeForClassification, spanHash } from './normalize'

/** Bounded hold-back: emit anyway past this, rather than buffer unboundedly. */
export const MAX_HOLDBACK_CHARS = 1200

/**
 * How much of the buffer a FORCED release keeps back (hardening round, H-4).
 *
 * The forced release — `MAX_HOLDBACK_CHARS` exceeded with no sentence
 * terminator anywhere — used to emit the ENTIRE buffer and reset to empty. The
 * header below called that "the one place a cross-seam match remains possible",
 * which was true, and then called it "far outside the length of any realistic
 * mortality sentence", which was not: the release point is a fixed character
 * offset, not a sentence boundary, so for long unpunctuated prose it lands
 * mid-sentence by construction and recurs every 1201 characters. A reviewer
 * measured it — roughly 2.4% of alignments put a mortality term on one side of
 * the cut and its paired date on the other, and both halves reached the reader.
 *
 * Keeping a tail back means the next scan window CONTAINS the tail, so a
 * term/date pair straddling the cut is scanned together and the sentence
 * carrying it is redacted before the second half is ever emitted.
 *
 * ── WHAT THIS DOES AND DOES NOT CLOSE, STATED PRECISELY ──────────────────────
 * It closes the DATE half, which is the half that makes the claim specific: a
 * date paired with a term now cannot be emitted. It does NOT retract the term
 * half if the term was in the already-released chunk — nothing in a stream can
 * un-send a byte. So the residual after this fix is "a reader may see a
 * mortality term whose date is then withheld", not "a reader may see a complete
 * mortality claim". That is a real reduction, not an elimination, and it is
 * written down as such rather than rounded up.
 *
 * 200 is comfortably longer than any realistic single clause and leaves each
 * forced release advancing by at least 1000 characters, so the stream cannot
 * stall.
 */
export const FORCED_RELEASE_OVERLAP_CHARS = 200

/**
 * How many CONSECUTIVE sentences the term/date pairing may span (round 3, M-3).
 *
 * 2, and the number is a real trade rather than a placeholder. At 1 — the
 * pre-round-3 behaviour — "The native will meet death. It falls in 2047." is
 * two sentences and passes clean, which is the defect. Raising it further keeps
 * buying coverage, but each increment also redacts more prose that merely
 * happens to mention a date near a mortality word: at 2, a mortality term and
 * an unrelated date must be ADJACENT to be caught together, which is already
 * the shape a leaked claim takes; at 4 or 5 an entire paragraph of legitimate
 * maraka analysis disappears because someone dated a dasha at the end of it.
 *
 * A pair separated by an intervening third sentence is therefore NOT detected.
 * That is a stated residual, not an oversight — see the module header.
 */
export const CROSS_SENTENCE_WINDOW = 2

/**
 * How much already-emitted prose the streaming scanner carries forward as
 * detection CONTEXT (round 3, M-3(a)).
 *
 * Equal to `MAX_HOLDBACK_CHARS` on purpose: the holdback bounds how far AHEAD
 * the scanner can look before it must release, so matching it bounds how far
 * BEHIND the scanner can look after it has. Together they mean a term/date pair
 * within one holdback-length of unpunctuated prose is caught on whichever side
 * of the release point it falls.
 *
 * The context is scanned and never re-emitted, so this costs one extra regex
 * pass over at most 1200 characters per chunk — not one extra byte of latency,
 * which is what made this the better fix than growing
 * `FORCED_RELEASE_OVERLAP_CHARS` (that one delays the reader; this one does
 * not).
 */
export const MAX_CARRY_CONTEXT_CHARS = MAX_HOLDBACK_CHARS

/** Mortality-outcome vocabulary, as it appears in GENERATED prose. */
const MORTALITY_OUTPUT_TERMS =
  /\b(death|dies|die|dying|died|demise|deceased|passing|passes away|passed away|pass away|perish\w*|expire[sd]?|end of life|final years|last years|mortality|maraka\w*|mrityu|mrtyu|mrutyu|ayurdaya|alpayu|madhyayu|purnayu|life ?span|life expectancy|longevity)\b/i

/**
 * Date-shaped tokens. Note `\b(19|20|21)\d{2}\b` covers a bare year, which is
 * the single most likely form a leaked date-of-death takes ("around 2047").
 */
const DATE_SHAPED =
  /\b((19|20|21)\d{2}|age\s+\d{1,3}|\d{1,3}\s*(years?\s*(of\s*age|old))|\d{1,3}(st|nd|rd|th)\s+year|(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}?,?\s*(19|20|21)?\d{0,4}|\d{1,2}\/\d{1,2}\/\d{2,4}|\d{4}-\d{2}-\d{2})\b/i

/**
 * Duration-to-end phrasing that carries no digit at all — the form that walks
 * past a naive "mortality term near a number" rule. "…only a few years remain",
 * "…the end comes in the next Saturn period".
 */
const DURATION_TO_END =
  /\b(within|in|after|before|around|about|approximately|roughly|by)\s+(the\s+)?(next\s+)?(few|several|couple|many|\d{1,3})?\s*(\w+\s+)?(years?|months?|decades?|dasha|dasa|mahadasha|antardasha|bhukti|period)\b/i

export interface MortalityPhrasingHit {
  rule: 'mortality_term_x_date_shape' | 'mortality_term_x_duration_to_end'
  /** sha256 of the redacted sentence. NEVER the sentence itself (C1 rule). */
  redacted_span_hash: string
  /** Character length of what was removed — reportable without content. */
  redacted_length: number
}

/**
 * An extra sentence-level predicate folded into this same pass (lane G1-G).
 *
 * The contract a rule must honour:
 *   · `rule` is a STABLE ID, never free text and never derived from the
 *     sentence — it is reported on the wire and in audit rows.
 *   · `test` is pure and side-effect-free. It MAY throw; if it does, the whole
 *     span fails closed and nothing from it reaches the reader. That is the
 *     intended direction for a confidentiality check and the reason these rules
 *     live inside this function's try/catch rather than beside it.
 */
export interface PreWireSentenceRule {
  readonly rule: string
  test(sentence: string): boolean
}

/** One firing of one `PreWireSentenceRule`. Same no-content discipline as above. */
export interface PreWireExtraHit {
  rule: string
  /** sha256 of the sentence the rule fired on. NEVER the sentence itself. */
  redacted_span_hash: string
  redacted_length: number
  /**
   * False when the sentence was ALREADY being redacted by a mortality rule, so
   * this hit is a detection record rather than the cause of a removal. Keeping
   * the distinction means "how many sentences did the entitlement scan remove"
   * and "how many sentences did it fire on" stay different questions with
   * different answers, which is what an audit needs.
   */
  caused_redaction: boolean
}

export interface MortalityScanResult {
  /** The text with every offending SENTENCE removed. Safe to write. */
  clean: string
  hits: MortalityPhrasingHit[]
  /**
   * Firings of the caller-supplied `extraRules` (lane G1-G). A SEPARATE channel
   * from `hits` on purpose: `hits` means "mortality phrasing" to every existing
   * reader of it and must not quietly start meaning something wider.
   */
  extra_hits: PreWireExtraHit[]
  /**
   * True when the scan itself failed. FAIL CLOSED: `clean` is `''` in this
   * case, not the input. The caller must treat this as "nothing goes out",
   * never as "nothing was found".
   */
  scan_failed: boolean
}

/**
 * Split on sentence terminators, KEEPING the terminator with its sentence.
 * Deliberately simple: an over-eager split makes the scan look at smaller
 * windows and MISS a cross-sentence pairing, so the splitter errs toward long
 * spans (no split on abbreviations, decimals, or ellipses).
 */
export function splitSentences(text: string): string[] {
  const out: string[] = []
  let start = 0
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (ch !== '.' && ch !== '!' && ch !== '?' && ch !== '\n') continue
    if (ch === '.' && /\d/.test(text[i - 1] ?? '') && /\d/.test(text[i + 1] ?? '')) continue // 3.5
    // Consume a run of terminators + following whitespace into this sentence.
    let j = i
    while (j + 1 < text.length && /[.!?\n\s]/.test(text[j + 1])) j++
    out.push(text.slice(start, j + 1))
    start = j + 1
    i = j
  }
  if (start < text.length) out.push(text.slice(start))
  return out
}

function sentenceHit(sentence: string): MortalityPhrasingHit['rule'] | null {
  // `literal`, NOT `normalized`: the confusable folding that lets the classifier
  // read `d1e` as `die` also turns the year `2047` into `2oat`, which would make
  // this scan blind to exactly the thing it exists to catch. Both terms are
  // checked against BOTH forms so a leet-spelled mortality word next to a real
  // year is caught too.
  const { normalized, literal } = normalizeForClassification(sentence)
  const mortality = MORTALITY_OUTPUT_TERMS.test(literal) || MORTALITY_OUTPUT_TERMS.test(normalized)
  if (!mortality) return null
  if (DATE_SHAPED.test(literal)) return 'mortality_term_x_date_shape'
  if (DURATION_TO_END.test(literal) || DURATION_TO_END.test(normalized)) {
    return 'mortality_term_x_duration_to_end'
  }
  return null
}

export interface MortalityScanOptions {
  /**
   * Prose the reader has ALREADY been shown, scanned as context and never
   * re-emitted (round 3, M-3(a)).
   *
   * This is what lets a date arriving in a later stream chunk be paired with a
   * term that left in an earlier one. Nothing in the prefix can be redacted —
   * it is already gone — but a sentence in `text` that completes a claim the
   * prefix started is redacted before it is written.
   */
  contextPrefix?: string
  /**
   * Extra sentence-level rules folded into this pass (lane G1-G, PPR-13).
   *
   * Single-sentence only — see the module header for why the cross-sentence
   * window is mortality-specific and is not extended to these.
   */
  extraRules?: readonly PreWireSentenceRule[]
  /**
   * Whether the MORTALITY rules run (lane G1-G). Defaults to `true`, so every
   * call site that predates G1-G is byte-for-byte unchanged.
   *
   * It exists because the two pattern classes are armed by two different
   * feature flags. A caller running with injection containment ON and the
   * safety gate OFF must get the entitlement rules WITHOUT silently acquiring
   * mortality redaction it never turned on.
   */
  mortalityRulesEnabled?: boolean
}

/**
 * Scan a completed prose span and remove any sentence pairing a mortality term
 * with a date shape or a duration-to-end phrase — WITHIN ITSELF, or within a
 * window of `CROSS_SENTENCE_WINDOW` consecutive sentences.
 *
 * Sentence-level redaction rather than token-level is deliberate: deleting
 * "2047" out of "you will die around 2047" leaves "you will die around", which
 * is worse prose AND still a mortality claim. The whole clause goes. When a
 * pair straddles two sentences BOTH sentences go, for the same reason: leaving
 * the half that says "the native will meet death" behind is still the claim.
 */
export function scanMortalityPhrasing(
  text: string,
  options: MortalityScanOptions = {},
): MortalityScanResult {
  try {
    if (!text) return { clean: text, hits: [], extra_hits: [], scan_failed: false }
    // HARDENING ROUND, H-3 — this line is why `scan_failed` is a real signal.
    //
    // Before it, `scan_failed: true` had NO reachable code path: the six
    // malformed-input probes the suite tried (null/undefined/{}/[]/0/symbol)
    // all short-circuited above or slid through the loop harmlessly, and the
    // one test in the area asserted `scan_failed === false` under a heading
    // that said "FAILS CLOSED". Per §N.8 a flag whose true state nothing can
    // produce is not a clean result; it is an unimplemented check wearing one.
    //
    // It is also a correctness fix, not just a testability one. A non-string
    // reaching here used to yield `{clean: '', scan_failed: false}` — "the scan
    // ran and the output is legitimately empty" — which is precisely the false
    // green §N.8 names. The honest answer is "the scan could not run", and the
    // caller's fail-closed branch (`reading_parts.ts`, `synthesis_stage.ts`)
    // already knows what to do with that.
    if (typeof text !== 'string') {
      throw new TypeError(
        `[pariprashna/safety] scanMortalityPhrasing requires a string; received ${typeof text}. ` +
          'Failing closed — an unscannable span is never a scanned-clean span.',
      )
    }
    // Context sentences are scanned alongside the span's own but can never be
    // emitted or redacted — they left already. `emitFrom` is the index at which
    // the span's own sentences begin.
    const contextSentences =
      typeof options.contextPrefix === 'string' && options.contextPrefix
        ? splitSentences(options.contextPrefix)
        : []
    const own = splitSentences(text)
    const sentences = [...contextSentences, ...own]
    const emitFrom = contextSentences.length

    // ── THE SLIDING WINDOW (round 3, M-3) ─────────────────────────────────
    // Single-sentence hits first, then every window of CROSS_SENTENCE_WINDOW
    // consecutive sentences. A window hit redacts EVERY sentence in the window
    // that the span still owns — the pair is the claim, and keeping either half
    // keeps the claim.
    const ruleFor = new Map<number, MortalityPhrasingHit['rule']>()
    const mortalityRulesEnabled = options.mortalityRulesEnabled !== false
    for (let i = 0; mortalityRulesEnabled && i < sentences.length; i++) {
      const rule = sentenceHit(sentences[i])
      if (rule) ruleFor.set(i, rule)
    }
    for (let width = 2; mortalityRulesEnabled && width <= CROSS_SENTENCE_WINDOW; width++) {
      for (let i = 0; i + width <= sentences.length; i++) {
        // A window CONTAINING an already-redacted sentence is skipped, and this
        // is the line that keeps the rule from over-redacting. If one sentence
        // carries the whole claim, removing that sentence removes the claim;
        // the neighbours contributed nothing and must survive — "Your chart
        // indicates you will die around 2047. Saturn supports steady
        // consolidation." must lose the first sentence and keep the second.
        // The window rule exists only for pairs where NEITHER half is a claim
        // on its own, which is exactly the leak it was added to close.
        let alreadyRedacted = false
        for (let k = 0; k < width; k++) if (ruleFor.has(i + k)) alreadyRedacted = true
        if (alreadyRedacted) continue

        const rule = sentenceHit(sentences.slice(i, i + width).join(''))
        if (!rule) continue
        for (let k = 0; k < width; k++) ruleFor.set(i + k, rule)
      }
    }

    // ── THE EXTRA PATTERN CLASS (lane G1-G, PPR-13) ───────────────────────
    // Runs over the SAME sentence array, and — like the mortality rules — over
    // a sliding window of CROSS_SENTENCE_WINDOW consecutive sentences.
    //
    // The window was NOT here originally, on the reasoning that "an entitlement
    // leak is not a pair, a chart id is one self-contained token". A review
    // reproduced two counterexamples and the reasoning was simply wrong:
    //
    //   · A chart id SPLIT by a sentence terminator — most importantly the
    //     newline the streaming scanner's forced release lands on — puts half
    //     the token in the carried context and half in the new span. Scanned
    //     apart, neither half is an id; scanned together, the token reassembles
    //     and matches. This was a real leak of a COMPLETE foreign id across a
    //     stream seam, and the window is what closes it.
    //   · The abbreviated-id rule IS a pair (a chart cue word plus a hex run),
    //     so "Consider the other chart. Its identifier is 1c826d5a." split the
    //     pair across two sentences and passed clean.
    //
    // A window hit redacts every sentence in the window THIS SPAN OWNS. Context
    // sentences are scanned so the pairing can be seen, and skipped for
    // redaction because they already left — nothing can un-send them. That is
    // the same asymmetry the mortality half lives with, and the same honest
    // residual: the reader may have seen a fragment, never the whole token.
    const extraRules = options.extraRules ?? []
    const extraRuleFor = new Map<number, string>()
    const extraFiringsFor = new Map<number, string[]>()
    const markExtra = (index: number, rule: string): void => {
      if (index < emitFrom) return
      const fired = extraFiringsFor.get(index) ?? []
      if (!fired.includes(rule)) fired.push(rule)
      extraFiringsFor.set(index, fired)
      if (!extraRuleFor.has(index)) extraRuleFor.set(index, rule)
    }
    if (extraRules.length > 0) {
      for (let i = 0; i < sentences.length; i++) {
        for (const r of extraRules) if (r.test(sentences[i])) markExtra(i, r.rule)
      }
      for (let width = 2; width <= CROSS_SENTENCE_WINDOW; width++) {
        for (let i = 0; i + width <= sentences.length; i++) {
          // Unlike the mortality window this does NOT skip a window containing
          // an already-marked sentence. A split token's two halves can each
          // ALSO carry an independent reference, and the join is the only place
          // the split one is visible at all — skipping would reintroduce the
          // exact leak this window was added for.
          const joined = sentences.slice(i, i + width).join('')
          for (const r of extraRules) {
            if (!r.test(joined)) continue
            // Only mark when the JOIN is what fired: if a single sentence in
            // the window already matched this rule on its own, the neighbours
            // contributed nothing and must survive.
            if (sentences.slice(i, i + width).some((s) => r.test(s))) continue
            for (let k = 0; k < width; k++) markExtra(i + k, r.rule)
          }
        }
      }
    }

    const hits: MortalityPhrasingHit[] = []
    const extra_hits: PreWireExtraHit[] = []
    let clean = ''
    for (let i = emitFrom; i < sentences.length; i++) {
      const sentence = sentences[i]
      const rule = ruleFor.get(i)
      const firedExtras = extraFiringsFor.get(i)
      if (firedExtras) {
        for (const fired of firedExtras) {
          extra_hits.push({
            rule: fired,
            redacted_span_hash: spanHash(sentence),
            redacted_length: sentence.length,
            caused_redaction: !rule,
          })
        }
      }
      if (rule) {
        hits.push({
          rule,
          redacted_span_hash: spanHash(sentence),
          redacted_length: sentence.length,
        })
        continue
      }
      if (extraRuleFor.has(i)) continue
      clean += sentence
    }
    return { clean, hits, extra_hits, scan_failed: false }
  } catch {
    // FAIL CLOSED — the inverse of lintReaderProse's contract, on purpose.
    // Covers a throwing `extraRules` entry too: an entitlement rule that cannot
    // decide must withhold the span, never pass it.
    return { clean: '', hits: [], extra_hits: [], scan_failed: true }
  }
}

/**
 * The tail of already-emitted prose that the next scan sees as context.
 *
 * The last `CROSS_SENTENCE_WINDOW - 1` sentences, so the streaming window and
 * the non-streaming window are the SAME window — a term/date pair split across
 * a stream seam is treated exactly as one split across a sentence boundary in a
 * completed span. Hard-truncated to `MAX_CARRY_CONTEXT_CHARS` because in the
 * forced-release path there is no sentence boundary to slice at and "the last
 * sentence" would otherwise mean "everything emitted so far".
 */
function tailContext(emitted: string): string {
  const sentences = splitSentences(emitted)
  const ctx = sentences.slice(-(CROSS_SENTENCE_WINDOW - 1)).join('')
  return ctx.length > MAX_CARRY_CONTEXT_CHARS ? ctx.slice(-MAX_CARRY_CONTEXT_CHARS) : ctx
}

/**
 * The streaming wrapper. Holds prose back to the last sentence boundary so a
 * match can never straddle a delta seam.
 *
 * Usage: `push(delta)` returns the text that is safe to write NOW (possibly
 * empty); `flush()` returns whatever is left at end of block. Hits accumulate
 * on `.hits` across the whole block.
 */
export class StreamingMortalityScanner {
  private buffer = ''
  /**
   * The tail of what has already been EMITTED, carried into the next scan as
   * context (round 3, M-3(a)). Bounded by `MAX_CARRY_CONTEXT_CHARS`.
   *
   * Only clean, emitted text goes in here. A sentence that was redacted never
   * reached the reader, so it cannot complete a claim for the reader either,
   * and carrying it would only manufacture redactions.
   */
  private carry = ''
  readonly hits: MortalityPhrasingHit[] = []
  /** Firings of the G1-G `extraRules`, accumulated across the whole block. */
  readonly extraHits: PreWireExtraHit[] = []
  scanFailed = false
  private readonly scan: (text: string, options?: MortalityScanOptions) => MortalityScanResult
  private readonly extraRules: readonly PreWireSentenceRule[]
  private readonly mortalityRulesEnabled: boolean

  /**
   * @param scan the span scanner. Defaults to `scanMortalityPhrasing`; the
   *   parameter exists so a test can drive the FAIL-CLOSED path of the
   *   streaming wrapper directly (hardening round, H-3). The underlying
   *   failure is real and separately proven — `scanMortalityPhrasing` throws on
   *   a non-string span — but reaching it through `push()` means getting a
   *   non-string past `this.buffer += delta`, which coerces. Injecting the
   *   collaborator tests the wrapper's own contract ("a failed span sets
   *   `scanFailed` AND emits nothing") without contorting the input to do it.
   * @param options lane G1-G. `extraRules` folds an additional sentence-level
   *   pattern class into the SAME streamed pass — same holdback, same carry,
   *   same fail-closed path — and `mortalityRulesEnabled` lets a caller arm
   *   that class WITHOUT arming G1-A's, since the two are gated on different
   *   feature flags. Both default to today's behaviour exactly.
   */
  constructor(
    scan: (text: string, options?: MortalityScanOptions) => MortalityScanResult = scanMortalityPhrasing,
    options: {
      extraRules?: readonly PreWireSentenceRule[]
      mortalityRulesEnabled?: boolean
    } = {},
  ) {
    this.scan = scan
    this.extraRules = options.extraRules ?? []
    this.mortalityRulesEnabled = options.mortalityRulesEnabled !== false
  }

  /** Feed one delta. Returns the reader-safe text to emit right now. */
  push(delta: string): string {
    this.buffer += delta
    const cut = this.lastSafeCut()
    if (cut <= 0) return ''
    const ready = this.buffer.slice(0, cut)
    this.buffer = this.buffer.slice(cut)
    return this.scanAndRecord(ready)
  }

  /** Emit whatever remains. Call once, at block commit. */
  flush(): string {
    if (!this.buffer) return ''
    const rest = this.buffer
    this.buffer = ''
    return this.scanAndRecord(rest)
  }

  private scanAndRecord(span: string): string {
    const result = this.scan(span, {
      contextPrefix: this.carry,
      extraRules: this.extraRules,
      mortalityRulesEnabled: this.mortalityRulesEnabled,
    })
    this.hits.push(...result.hits)
    // `?? []` rather than a bare spread: the injectable `scan` collaborator is a
    // test seam, and an older/hand-rolled double that predates `extra_hits`
    // must not crash the wrapper it is being used to exercise.
    this.extraHits.push(...(result.extra_hits ?? []))
    // FAIL CLOSED, and say so. `scan_failed` means the span was never scanned,
    // so `result.clean` is `''` by that function's contract and nothing from
    // this span reaches the reader.
    if (result.scan_failed) {
      this.scanFailed = true
      return ''
    }
    this.carry = tailContext(this.carry + result.clean)
    return result.clean
  }

  /**
   * The index up to which the buffer is safe to scan: just past the last
   * sentence terminator.
   *
   * When no terminator exists and the buffer has passed MAX_HOLDBACK_CHARS,
   * this releases everything EXCEPT a trailing `FORCED_RELEASE_OVERLAP_CHARS`
   * window, so the stream still cannot stall on one enormous unpunctuated span
   * while a term/date pair straddling the release point is still scanned
   * together on the next chunk. See `FORCED_RELEASE_OVERLAP_CHARS` for what
   * that does and does not close.
   *
   * The retained tail is held, not emitted: `flush()` releases it at block
   * commit, after one more scan. No text is emitted twice.
   */
  private lastSafeCut(): number {
    for (let i = this.buffer.length - 1; i >= 0; i--) {
      const ch = this.buffer[i]
      if (ch === '.' || ch === '!' || ch === '?' || ch === '\n') return i + 1
    }
    if (this.buffer.length <= MAX_HOLDBACK_CHARS) return 0
    // MAX_HOLDBACK_CHARS > FORCED_RELEASE_OVERLAP_CHARS, so this is always
    // positive and every forced release makes real forward progress.
    return this.buffer.length - FORCED_RELEASE_OVERLAP_CHARS
  }
}
