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

export interface MortalityScanResult {
  /** The text with every offending SENTENCE removed. Safe to write. */
  clean: string
  hits: MortalityPhrasingHit[]
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

/**
 * Scan a completed prose span and remove any sentence pairing a mortality term
 * with a date shape or a duration-to-end phrase.
 *
 * Sentence-level redaction rather than token-level is deliberate: deleting
 * "2047" out of "you will die around 2047" leaves "you will die around", which
 * is worse prose AND still a mortality claim. The whole clause goes.
 */
export function scanMortalityPhrasing(text: string): MortalityScanResult {
  try {
    if (!text) return { clean: text, hits: [], scan_failed: false }
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
    const hits: MortalityPhrasingHit[] = []
    let clean = ''
    for (const sentence of splitSentences(text)) {
      const rule = sentenceHit(sentence)
      if (rule) {
        hits.push({
          rule,
          redacted_span_hash: spanHash(sentence),
          redacted_length: sentence.length,
        })
        continue
      }
      clean += sentence
    }
    return { clean, hits, scan_failed: false }
  } catch {
    // FAIL CLOSED — the inverse of lintReaderProse's contract, on purpose.
    return { clean: '', hits: [], scan_failed: true }
  }
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
  readonly hits: MortalityPhrasingHit[] = []
  scanFailed = false
  private readonly scan: (text: string) => MortalityScanResult

  /**
   * @param scan the span scanner. Defaults to `scanMortalityPhrasing`; the
   *   parameter exists so a test can drive the FAIL-CLOSED path of the
   *   streaming wrapper directly (hardening round, H-3). The underlying
   *   failure is real and separately proven — `scanMortalityPhrasing` throws on
   *   a non-string span — but reaching it through `push()` means getting a
   *   non-string past `this.buffer += delta`, which coerces. Injecting the
   *   collaborator tests the wrapper's own contract ("a failed span sets
   *   `scanFailed` AND emits nothing") without contorting the input to do it.
   */
  constructor(scan: (text: string) => MortalityScanResult = scanMortalityPhrasing) {
    this.scan = scan
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
    const result = this.scan(span)
    this.hits.push(...result.hits)
    // FAIL CLOSED, and say so. `scan_failed` means the span was never scanned,
    // so `result.clean` is `''` by that function's contract and nothing from
    // this span reaches the reader.
    if (result.scan_failed) {
      this.scanFailed = true
      return ''
    }
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
