/**
 * pariprashna/citations/rewriter.ts — PB-1 lane S-3.
 *
 * Server-side streaming citation rewriter. Sits in the Paripraśna prose-delta
 * path: prose deltas from the synthesis model flow in; reader-safe text + a
 * side-channel of protocol events flow out.
 *
 * Responsibilities:
 *   1. Watch for the sentinel-open character `⟦` (and the tolerant `[[`
 *      variant). From that point, HOLD BACK emitted text until the sentinel
 *      closes — but bounded, so the stream can NEVER stall:
 *         MAX_HOLDBACK = 64 bytes  → exceed without a close ⇒ DROP the held
 *                                    segment (fail closed) + flag
 *         TIMEOUT      = 400 ms    → elapse without a close ⇒ DROP the held
 *                                    segment (fail closed) + flag
 *   2. On a well-formed close, resolve the reference and emit a
 *      `citation.define{ n, reader_label, grade, audit_detail }` event, and
 *      replace the sentinel in prose with a clean inline marker `[n]`.
 *   3. An UNRESOLVABLE reference gets grade `unverified` and increments the
 *      per-model hallucination counter.
 *   4. EVERY text fragment that leaves this module — pass-through prose, the
 *      inline marker — is first run through the register-leak lint so no
 *      internal id can reach the wire by ANY path.
 *
 * ── FAIL-CLOSED FIX (V3-E-061, 2026-08-30) ───────────────────────────────────
 * Live-reproduced twice in production against the real native's chart
 * (482012f1-…): a citation sentinel the model was mid-emitting on an internal
 * fact-id-namespace token (`register_leak:redact` fired on `fact_id_namespace`
 * INSIDE the same hold — proof the model really was citing internal content)
 * timed out before its closer arrived. The pre-fix `flushHold` ran the
 * register-leak lint over the held bytes and forwarded WHATEVER SURVIVED THE
 * LINT (`lint.clean`) straight into `out.text` — reasoning that "lint-cleaned"
 * meant "reader-safe". It does not: the lint's pattern list strips KNOWN
 * internal-id shapes (signal ids, table names, register acronyms, fact-id
 * namespaces) but has NO pattern for the sentinel markup itself (`⟦`, `cite:`,
 * `⟧`), so every malformed flush forwarded that raw bracket syntax verbatim —
 * observed live as the literal malformed token `⟦cite: ⟧` sitting in reader
 * prose. Worse: had the internal token inside the hold been a SHAPE the lint's
 * pattern list did not yet cover, the flush would have forwarded that raw
 * content too — the lint is a pattern-matching backstop, not a structural
 * guarantee, and a fail-OPEN path built on top of it inherits every gap in
 * its pattern coverage.
 *
 * The fix does not depend on the lint's coverage at all: a malformed hold
 * (timeout / byte-limit / eof-unclosed) — or a well-formed canonical `⟦…⟧`
 * sentinel that closes but fails to PARSE as a citation (e.g. an empty ref)
 * — is now DROPPED IN ITS ENTIRETY. No byte of the held buffer, lint-cleaned
 * or not, ever reaches `out.text`. The lint still runs over the held bytes
 * for audit/telemetry (its flags remain useful for tuning the model prompt
 * and for security review), but its `clean` text is discarded rather than
 * emitted — see `flushHold` and `resolveSentinel` below.
 *
 * Determinism: time is injected via `nowMs` arguments, so hold-back timeout
 * behavior is unit-testable without real timers.
 */

import { findCloser, findOpener, parseSentinel, CANON_OPEN } from './grammar'
import { lintReaderProse } from './register_leak_lint'
import type { HallucinationCounter } from './hallucination_counter'
import { createHallucinationCounter } from './hallucination_counter'
import type {
  CitationResolver,
  MalformedSentinelReason,
  PariprashnaCitationEvent,
  ResolvedCitation,
  RewriteChunk,
} from './types'

export const MAX_HOLDBACK_BYTES = 64
export const TIMEOUT_MS = 400

const utf8 = new TextEncoder()
const byteLen = (s: string): number => utf8.encode(s).length

export interface RewriterOptions {
  resolver: CitationResolver
  /** Model id for hallucination-counter keying. */
  modelId: string
  /** Shared or isolated counter. Defaults to a fresh isolated instance. */
  hallucinationCounter?: HallucinationCounter
  /** Inline marker rendered in place of a resolved sentinel. Default `[n]`. */
  renderMarker?: (n: number) => string
  /** Byte ceiling for a held sentinel. Default MAX_HOLDBACK_BYTES. */
  maxHoldbackBytes?: number
  /** Time budget for a held sentinel. Default TIMEOUT_MS. */
  timeoutMs?: number
}

type Mode = 'pass' | 'hold'

interface HoldStep {
  closed: boolean
  /** Leftover text to continue scanning in pass mode after a close/flush. */
  tail: string
}

export class CitationStreamRewriter {
  private readonly resolver: CitationResolver
  private readonly modelId: string
  private readonly counter: HallucinationCounter
  private readonly renderMarker: (n: number) => string
  private readonly maxHoldback: number
  private readonly timeoutMs: number

  private mode: Mode = 'pass'
  /** Undecided suffix in pass mode (at most a trailing partial `[`). */
  private carry = ''
  /** Accumulated raw sentinel bytes while holding (includes the opener). */
  private holdBuffer = ''
  /** Timestamp (ms) the current hold began. */
  private holdStartMs = 0
  /**
   * Prose staging buffer. Reader prose is accumulated here and released only up
   * to the last whitespace, holding back the trailing partial WORD. This is the
   * defense against a hard-pattern token (which never contains whitespace, e.g.
   * `SIG.MSR.001`, `bodha_msr_signals`) being split across streaming deltas and
   * slipping past the per-fragment lint. A held partial word is released once
   * the next whitespace arrives, or at end().
   */
  private proseStage = ''

  /** ref → assigned citation number (stable, dedup across the stream). */
  private readonly refToN = new Map<string, number>()
  /** Refs already emitted as citation.define (emit-once). */
  private readonly definedRefs = new Set<string>()
  private nextN = 1

  constructor(opts: RewriterOptions) {
    this.resolver = opts.resolver
    this.modelId = opts.modelId
    this.counter = opts.hallucinationCounter ?? createHallucinationCounter()
    this.renderMarker = opts.renderMarker ?? ((n) => `[${n}]`)
    this.maxHoldback = opts.maxHoldbackBytes ?? MAX_HOLDBACK_BYTES
    this.timeoutMs = opts.timeoutMs ?? TIMEOUT_MS
  }

  /** Current per-model hallucination tally. */
  hallucinationCount(): number {
    return this.counter.get(this.modelId)
  }

  /** True while mid-sentinel (bytes are being held back). */
  isHolding(): boolean {
    return this.mode === 'hold'
  }

  /**
   * Feed one prose delta. `nowMs` is the current time (defaults to Date.now()).
   * Returns reader-safe text + protocol events produced by this delta.
   */
  write(delta: string, nowMs: number = Date.now()): RewriteChunk {
    const out: RewriteChunk = { text: '', events: [] }
    let work = this.carry + delta
    this.carry = ''

    while (true) {
      if (this.mode === 'hold') {
        this.holdBuffer += work
        work = ''
        const step = this.processHold(nowMs, out)
        if (!step.closed) break // still holding, within budget
        work = step.tail
        continue
      }

      // pass mode: find the next opener.
      const opener = findOpener(work)
      if (!opener) {
        const { emit, keep } = splitTrailingPartialOpener(work)
        this.stageProse(emit, out)
        this.carry = keep
        break
      }

      // Emit prose before the opener, then enter hold mode.
      this.stageProse(work.slice(0, opener.index), out)
      this.mode = 'hold'
      this.holdBuffer = ''
      this.holdStartMs = nowMs
      work = work.slice(opener.index) // becomes the opening of holdBuffer
    }

    return out
  }

  /**
   * External timer hook: call on a ~TIMEOUT cadence so a hold that receives no
   * further deltas still flushes. Returns any flush output.
   */
  checkTimeout(nowMs: number = Date.now()): RewriteChunk {
    const out: RewriteChunk = { text: '', events: [] }
    this.maybeTimeout(nowMs, out)
    return out
  }

  /** End of stream: flush any held/partial bytes as reader-safe text. */
  end(): RewriteChunk {
    const out: RewriteChunk = { text: '', events: [] }
    if (this.mode === 'hold') this.flushHold('eof_unclosed', out)
    if (this.carry) {
      this.stageProse(this.carry, out)
      this.carry = ''
    }
    this.flushStage(out) // release any held trailing partial word
    return out
  }

  // ── internals ──────────────────────────────────────────────────────────────

  /**
   * Advance the current hold using the accumulated `holdBuffer`.
   * Precedence: timeout → close → byte-limit → keep holding.
   */
  private processHold(nowMs: number, out: RewriteChunk): HoldStep {
    // Never stall: timeout wins over everything.
    if (this.maybeTimeout(nowMs, out)) return { closed: true, tail: '' }

    const openerTok = this.holdBuffer.startsWith('[[') ? '[[' : CANON_OPEN
    const closer = findCloser(this.holdBuffer, openerTok.length)

    if (closer) {
      const end = closer.index + closer.token.length
      const candidate = this.holdBuffer.slice(0, end)
      const tail = this.holdBuffer.slice(end)
      this.resolveSentinel(candidate, out)
      this.mode = 'pass'
      this.holdBuffer = ''
      return { closed: true, tail }
    }

    // No closer yet — enforce the byte ceiling so we never wait forever.
    if (byteLen(this.holdBuffer) > this.maxHoldback) {
      this.flushHold('byte_limit', out)
      return { closed: true, tail: '' }
    }

    return { closed: false, tail: '' } // keep holding
  }

  /**
   * Drop the held buffer on a malformed-sentinel condition — FAIL CLOSED
   * (V3-E-061 fix). The held bytes are internal protocol state (a half-formed
   * `⟦cite: …⟧` sentinel, possibly still carrying an internal id/register
   * token the model was mid-citation on) and are NEVER forwarded to reader
   * prose, regardless of what the register-leak lint's pattern list does or
   * does not recognize inside them — see the module header comment. The lint
   * still runs, purely for its audit-channel flags (telemetry / tuning); its
   * `clean` text is intentionally discarded, never appended to `out.text`.
   */
  private flushHold(reason: MalformedSentinelReason, out: RewriteChunk): void {
    const raw = this.holdBuffer
    this.dropSegment(reason, raw, out)
    this.mode = 'pass'
    this.holdBuffer = ''
  }

  /**
   * Shared fail-closed drop path for BOTH a malformed hold (timeout /
   * byte_limit / eof_unclosed, via `flushHold`) and a closed-but-unparseable
   * canonical sentinel (`parse_failed`, via `resolveSentinel`). Releases any
   * staged prose first (ordering), lints `raw` for audit-channel flags only,
   * and appends NOTHING derived from `raw` to `out.text` — the segment is
   * dropped in its entirety. See the module header FAIL-CLOSED FIX note.
   */
  private dropSegment(reason: MalformedSentinelReason, raw: string, out: RewriteChunk): void {
    this.flushStage(out)
    const lint = lintReaderProse(raw, this.resolver)
    out.events.push(...lint.flags)
    out.events.push({ type: 'flag', flag: 'malformed_sentinel', reason, raw: lint.clean })
  }

  /** Returns true if a timeout flush occurred. */
  private maybeTimeout(nowMs: number, out: RewriteChunk): boolean {
    if (this.mode === 'hold' && nowMs - this.holdStartMs > this.timeoutMs) {
      this.flushHold('timeout', out)
      return true
    }
    return false
  }

  /** Parse + resolve a complete candidate sentinel, emitting events/marker. */
  private resolveSentinel(candidate: string, out: RewriteChunk): void {
    const parsed = parseSentinel(candidate)
    if (!parsed.ok) {
      // The tolerant `[[…]]` bracket family is genuinely ambiguous with a
      // real reader-facing wiki-style link (grammar.ts's own contract: "a
      // bare [[foo]] is deliberately NOT a citation"), so it is safe — and
      // correct — to emit as ordinary prose.
      //
      // The CANONICAL `⟦…⟧` opener (U+27E6/U+27E7) is never ambiguous: it is
      // reserved, unmistakable internal protocol markup that a model should
      // never emit for genuine prose. A closed-but-unparseable canonical
      // sentinel (e.g. an empty ref, `⟦cite: ⟧`) is therefore the SAME
      // fail-closed case as a malformed hold, not prose — see the module
      // header FAIL-CLOSED FIX note (V3-E-061). Falling through to
      // `stageProse` here would forward the raw bracket markup (and any
      // partial internal content inside it) through the ordinary lint, which
      // has no pattern for sentinel syntax itself.
      if (candidate.startsWith(CANON_OPEN)) {
        this.dropSegment('parse_failed', candidate, out)
        return
      }
      // Not actually a citation (e.g. a bare [[wiki]] link). Emit as prose.
      this.stageProse(candidate, out)
      return
    }

    if (parsed.normalized) {
      out.events.push({
        type: 'flag',
        flag: 'normalization',
        original: candidate,
        normalized: parsed.canonical,
        note: parsed.note,
      })
    }

    const n = this.numberFor(parsed.ref)

    if (!this.definedRefs.has(parsed.ref)) {
      this.definedRefs.add(parsed.ref)
      const resolved: ResolvedCitation | null = safeResolve(this.resolver, parsed.ref)
      if (resolved) {
        out.events.push({
          type: 'citation.define',
          n,
          reader_label: resolved.reader_label,
          grade: resolved.grade,
          audit_detail: resolved.audit_detail,
          ref: parsed.ref,
        })
      } else {
        // Unresolvable → unverified grade + hallucination counter.
        this.counter.increment(this.modelId)
        out.events.push({
          type: 'citation.define',
          n,
          reader_label: `[unverified citation ${n}]`,
          grade: 'unverified',
          audit_detail: `no source matched reference "${parsed.ref}" (model=${this.modelId})`,
          ref: parsed.ref,
        })
      }
    }

    // Inline marker is a clean reader token; emit it directly (after releasing
    // any staged prose so order is preserved), still lint-guarded defensively.
    this.emitDirect(this.renderMarker(n), out)
  }

  private numberFor(ref: string): number {
    const existing = this.refToN.get(ref)
    if (existing !== undefined) return existing
    const n = this.nextN++
    this.refToN.set(ref, n)
    return n
  }

  /**
   * Stage reader prose. Releases everything up to (and including) the last
   * whitespace and holds back the trailing partial word — so a hard-pattern
   * token cannot be split across two lint passes and slip through.
   */
  private stageProse(text: string, out: RewriteChunk): void {
    if (!text) return
    this.proseStage += text
    const idx = lastWhitespaceIndex(this.proseStage)
    if (idx >= 0) {
      const release = this.proseStage.slice(0, idx + 1)
      this.proseStage = this.proseStage.slice(idx + 1)
      this.lintEmit(release, out)
    }
  }

  /** Release the entire staged prose buffer (word boundary no longer needed). */
  private flushStage(out: RewriteChunk): void {
    if (this.proseStage) {
      this.lintEmit(this.proseStage, out)
      this.proseStage = ''
    }
  }

  /**
   * Emit a self-contained, whitespace-independent fragment (an inline marker,
   * or a malformed flush). Releases staged prose first to preserve order.
   */
  private emitDirect(text: string, out: RewriteChunk): void {
    this.flushStage(out)
    this.lintEmit(text, out)
  }

  /** Lint a fragment and append it to the output. The SINGLE lint/emit exit. */
  private lintEmit(text: string, out: RewriteChunk): void {
    if (!text) return
    const lint = lintReaderProse(text, this.resolver)
    out.text += lint.clean
    out.events.push(...lint.flags)
  }
}

// ── free helpers ───────────────────────────────────────────────────────────

/**
 * In pass mode, a trailing lone `[` might be the first char of a `[[` opener
 * arriving across a delta boundary. Hold it back one char; everything else is
 * safe to emit. (`⟦` is a single code point, so it is never a partial.)
 */
/** Index of the last whitespace char in `s`, or -1 if none. */
function lastWhitespaceIndex(s: string): number {
  for (let i = s.length - 1; i >= 0; i--) {
    if (/\s/.test(s[i])) return i
  }
  return -1
}

function splitTrailingPartialOpener(s: string): { emit: string; keep: string } {
  if (s.endsWith('[') && !s.endsWith('[[')) {
    return { emit: s.slice(0, -1), keep: '[' }
  }
  return { emit: s, keep: '' }
}

function safeResolve(resolver: CitationResolver, ref: string): ResolvedCitation | null {
  try {
    return resolver.resolve(ref)
  } catch {
    return null
  }
}

export type { PariprashnaCitationEvent }
