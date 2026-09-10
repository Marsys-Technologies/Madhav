/**
 * pariprashna/citations/stream_wiring.ts — G2-B "Citations at first paint"
 * (PPR-08, FD-2/FD-6; PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md line 75).
 *
 * Wires the already-built S-3 `CitationStreamRewriter` into a live delta loop
 * as one small, directly-testable unit — separated from `pipeline/
 * synthesis_stage.ts` so the wiring logic can be exercised without mocking a
 * provider adapter or the whole route.
 *
 * Three jobs, all load-bearing:
 *
 *   1. Feed raw model text through the rewriter and hand back reader-safe
 *      text (sentinel resolved to the inline marker, register-leak-linted —
 *      the rewriter's own `lintEmit` is the SINGLE lint/emit exit, see
 *      rewriter.ts's class docblock).
 *   2. Map every internal `citation.define` / `flag` event the rewriter
 *      produces onto S-1's wire vocabulary (`protocol_adapter.ts`) and hand
 *      it to the caller's `onWireEvent` — the caller (the emitter) supplies
 *      its own seq/t stamping, so this module strips the adapter's dummy
 *      envelope before forwarding.
 *   3. Track every RESOLVED citation (ref, reader_label, grade) turn-wide.
 *      This is what closes the P0C-R5 dead path: persistence used to
 *      re-derive citations by regex-scanning the ALREADY-SCRUBBED accumulated
 *      text (`reading_parts.ts`'s `detectTurnCitations`), which structurally
 *      finds nothing once the per-delta register-leak lint has redacted every
 *      `SIG.MSR.NNN`-shaped token out of that text. `resolvedCitations` here
 *      is the turn's own resolution ledger — the thing persistence should
 *      read instead of re-scanning scrubbed prose.
 *
 * Timeout enforcement without a live timer: `CitationStreamRewriter.write`
 * already re-checks the hold-back timeout as the FIRST branch of
 * `processHold` before doing anything else with new bytes (rewriter.ts).
 * Calling `write('', nowMs)` — or the `tick()` alias below — therefore lets a
 * held sentinel's 400ms clock be re-evaluated at any checkpoint using the
 * CURRENT wall-clock time, with zero new code path and zero timer/interval to
 * clean up in a serverless streaming handler. `synthesis_stage.ts` calls
 * `tick()` at every event the provider emits (thinking/tool events, not just
 * text), so a stream with events roughly as frequent as most provider
 * streaming (sub-second) enforces the 400ms budget in practice; the 64-byte
 * ceiling is the hard backstop for a provider that goes fully silent, and
 * `end()` is the terminal flush guaranteed to run once the stream closes.
 * Documented residual: a provider that emits NO events at all for >400ms
 * mid-sentinel will hold slightly longer than 400ms wall-clock (until the
 * next event or stream end) — never longer than the byte ceiling allows
 * bytes to accumulate, and never past `end()`.
 */

import { CitationStreamRewriter, type RewriterOptions } from './rewriter'
import { toWireEvents, type CitationWireEvent } from './protocol_adapter'
import type { CitationGrade, PariprashnaCitationEvent } from './types'

/** One citation this turn's rewriter actually resolved, in first-seen order. */
export interface ResolvedTurnCitation {
  index: number
  signal_id: string
  layer: string
  snippet: string
  grade: CitationGrade
}

/**
 * Plain `Omit` over a union collapses it to the MEMBERS' COMMON keys (a
 * well-known TS gotcha — `Omit<A|B,K>` is `Pick<A|B, Exclude<keyof (A|B),K>>`,
 * and `keyof (A|B)` is only the shared keys). This distributes the `Omit`
 * per-member instead, so the result stays a proper discriminated union.
 */
type DistributiveOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never

/** A wire event with the envelope (seq/t) stripped — the caller stamps its own. */
export type UnstampedCitationWireEvent = DistributiveOmit<CitationWireEvent, 'seq' | 't'>

/** Drop the dummy `seq`/`t` this module stamps — the real emitter stamps its own. */
function stripEnvelope(event: CitationWireEvent): UnstampedCitationWireEvent {
  const rest: Record<string, unknown> = { ...event }
  delete rest.seq
  delete rest.t
  return rest as UnstampedCitationWireEvent
}

export interface TurnCitationStreamOptions extends RewriterOptions {
  /** Forward one wire-shaped event to the live stream. */
  onWireEvent: (event: UnstampedCitationWireEvent) => void
  /** Injectable clock — defaults to `Date.now`. Tests pin this. */
  now?: () => number
}

/**
 * Stateful, turn-scoped wrapper around `CitationStreamRewriter`. One instance
 * per synthesis stream (constructed once, `write`/`tick`d for every event,
 * `end`ed exactly once when the stream closes).
 */
export class TurnCitationStream {
  private readonly rewriter: CitationStreamRewriter
  private readonly onWireEvent: TurnCitationStreamOptions['onWireEvent']
  private readonly now: () => number
  private readonly resolved: ResolvedTurnCitation[] = []
  private ended = false

  constructor(opts: TurnCitationStreamOptions) {
    const { onWireEvent, now, ...rewriterOpts } = opts
    this.rewriter = new CitationStreamRewriter(rewriterOpts)
    this.onWireEvent = onWireEvent
    this.now = now ?? Date.now
  }

  /** Feed one raw model text delta. Returns the reader-safe text to append. */
  write(delta: string): string {
    const chunk = this.rewriter.write(delta, this.now())
    this.handleEvents(chunk.events)
    return chunk.text
  }

  /**
   * Re-check the hold-back timeout with no new bytes (see module docblock).
   * Safe to call unconditionally on any stream event — a no-op in pass mode.
   * Returns any text the timeout flush produced (empty string otherwise).
   */
  tick(): string {
    if (!this.rewriter.isHolding()) return ''
    return this.write('')
  }

  /** Terminal flush — call exactly once, when the underlying stream closes. */
  end(): string {
    if (this.ended) return ''
    this.ended = true
    const chunk = this.rewriter.end()
    this.handleEvents(chunk.events)
    return chunk.text
  }

  /** Per-model hallucination tally (unresolved sentinels this turn). */
  get hallucinationCount(): number {
    return this.rewriter.hallucinationCount()
  }

  /** Every citation resolved (a `citation.define` fired) so far, wire order. */
  get resolvedCitations(): readonly ResolvedTurnCitation[] {
    return this.resolved
  }

  private handleEvents(events: readonly PariprashnaCitationEvent[]): void {
    for (const internalEvent of events) {
      if (internalEvent.type === 'citation.define') {
        this.resolved.push({
          index: internalEvent.n,
          signal_id: internalEvent.ref,
          layer: internalEvent.layer ?? 'L2.5',
          snippet: internalEvent.reader_label,
          grade: internalEvent.grade,
        })
      }
      // Dummy envelope — this module never owns seq/t; the caller's emitter
      // stamps both when it actually writes to the wire.
      const wireEvents = toWireEvents(internalEvent, { nextSeq: () => 0, t: this.now() })
      for (const we of wireEvents) this.onWireEvent(stripEnvelope(we))
    }
  }
}
