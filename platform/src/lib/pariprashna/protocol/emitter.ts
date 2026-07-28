/**
 * Paripraśna server-side stream emitter (lane PB-1/S-1).
 *
 * A thin, fully-typed writer over a `ReadableStreamDefaultController<Uint8Array>`.
 * Every method builds a statically-typed event object (from the Zod-inferred
 * types in `./events`), stamps the monotonic `seq` + timestamp, validates via
 * `serializeEvent`, and enqueues the encoded SSE frame.
 *
 * Gate assertion: ZERO `as any` in this writer path. Each builder's argument is
 * an `Omit<…Event, 'type' | 'seq' | 't'>`, so the compiler enforces the exact
 * event shape at every call site — a malformed emit does not typecheck.
 *
 * This module is server-oriented (it holds a stream controller) and is kept
 * separate from the isomorphic `./events` schema module, which client code
 * imports for decoding.
 */

import {
  serializeEvent,
  type PariprashnaEvent,
  type TurnOpenEvent,
  type PhaseEvent,
  type ActivityUpsertEvent,
  type BlockOpenEvent,
  type BlockDeltaEvent,
  type BlockCommitEvent,
  type SeamOpenEvent,
  type SeamSetEvent,
  type CitationDefineEvent,
  type FlagEvent,
  type GradeEvent,
  type TurnCommitEvent,
  type TurnCloseEvent,
  type ErrorEvent,
} from './events'

/** The stamped-by-the-emitter envelope fields, omitted from every builder arg. */
type Stamped = 'seq' | 't'
/** A builder arg is the event minus its discriminant and stamped envelope. */
type Body<E extends PariprashnaEvent, L extends E['type']> = Omit<
  Extract<E, { type: L }>,
  'type' | Stamped
>

export class PariprashnaEmitter {
  private seq = 0
  private closed = false
  private readonly encoder = new TextEncoder()

  constructor(private readonly controller: ReadableStreamDefaultController<Uint8Array>) {}

  /** Whether `close()` (or a terminal enqueue failure) has fired. */
  get isClosed(): boolean {
    return this.closed
  }

  private write(event: PariprashnaEvent): void {
    if (this.closed) return
    try {
      this.controller.enqueue(this.encoder.encode(serializeEvent(event)))
    } catch {
      // Controller already closed by a client disconnect — stop writing.
      this.closed = true
    }
  }

  private envelope(): { seq: number; t: number } {
    return { seq: this.seq++, t: Date.now() }
  }

  turnOpen(body: Body<TurnOpenEvent, 'turn.open'>): void {
    this.write({ type: 'turn.open', ...this.envelope(), ...body })
  }

  phase(body: Body<PhaseEvent, 'phase'>): void {
    this.write({ type: 'phase', ...this.envelope(), ...body })
  }

  activity(body: Body<ActivityUpsertEvent, 'activity.upsert'>): void {
    this.write({ type: 'activity.upsert', ...this.envelope(), ...body })
  }

  blockOpen(body: Body<BlockOpenEvent, 'block.open'>): void {
    this.write({ type: 'block.open', ...this.envelope(), ...body })
  }

  blockDelta(body: Body<BlockDeltaEvent, 'block.delta'>): void {
    this.write({ type: 'block.delta', ...this.envelope(), ...body })
  }

  blockCommit(body: Body<BlockCommitEvent, 'block.commit'>): void {
    this.write({ type: 'block.commit', ...this.envelope(), ...body })
  }

  seamOpen(body: Body<SeamOpenEvent, 'seam.open'>): void {
    this.write({ type: 'seam.open', ...this.envelope(), ...body })
  }

  seamSet(body: Body<SeamSetEvent, 'seam.set'>): void {
    this.write({ type: 'seam.set', ...this.envelope(), ...body })
  }

  citationDefine(body: Body<CitationDefineEvent, 'citation.define'>): void {
    this.write({ type: 'citation.define', ...this.envelope(), ...body })
  }

  flag(body: Body<FlagEvent, 'flag'>): void {
    this.write({ type: 'flag', ...this.envelope(), ...body })
  }

  grade(body: Body<GradeEvent, 'grade'>): void {
    this.write({ type: 'grade', ...this.envelope(), ...body })
  }

  turnCommit(body: Body<TurnCommitEvent, 'turn.commit'>): void {
    this.write({ type: 'turn.commit', ...this.envelope(), ...body })
  }

  turnClose(body: Body<TurnCloseEvent, 'turn.close'>): void {
    this.write({ type: 'turn.close', ...this.envelope(), ...body })
  }

  error(body: Body<ErrorEvent, 'error'>): void {
    this.write({ type: 'error', ...this.envelope(), ...body })
  }

  /** Close the underlying controller exactly once. */
  close(): void {
    if (this.closed) return
    this.closed = true
    try {
      this.controller.close()
    } catch {
      /* already closed */
    }
  }
}
