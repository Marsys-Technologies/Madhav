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
  type TurnPersistedEvent,
  type TurnCloseEvent,
  type ErrorEvent,
  type SnapshotApplyEvent,
} from './events'
import { assertNoCalibrationLeak } from '../no_leakage/calibration_leak_guard'

/**
 * Write an ALREADY-STAMPED event (i.e. one carrying its own `seq`/`t`, read
 * back verbatim from the PB-2/M-5 ring buffer) directly onto a controller —
 * used by the `/api/pariprashna/resume` replay path, which must preserve the
 * ORIGINAL seq of a historical event rather than assign it a new one (the
 * client's seen-set dedup keys on `seq`; re-stamping would break idempotent
 * replay). Validates via `serializeEvent` exactly like `PariprashnaEmitter`.
 * Returns `false` (never throws) if the controller is already closed.
 */
export function writeRawEvent(
  controller: ReadableStreamDefaultController<Uint8Array>,
  event: PariprashnaEvent,
  encoder: TextEncoder = new TextEncoder(),
): boolean {
  try {
    controller.enqueue(encoder.encode(serializeEvent(event)))
    return true
  } catch {
    return false
  }
}

/** The stamped-by-the-emitter envelope fields, omitted from every builder arg. */
type Stamped = 'seq' | 't'
/** A builder arg is the event minus its discriminant and stamped envelope. */
type Body<E extends PariprashnaEvent, L extends E['type']> = Omit<
  Extract<E, { type: L }>,
  'type' | Stamped
>

export class PariprashnaEmitter {
  private seq: number
  private closed = false
  private readonly encoder = new TextEncoder()

  /**
   * @param controller the stream controller to write to.
   * @param onEmit PB-2/M-5 ADDITIVE hook: fired with every event AFTER it is
   *   successfully enqueued (never on a closed/failed write). The route uses
   *   this to mirror each event into the per-turn ring buffer (fire-and-forget)
   *   without this module needing to know anything about buffering/storage.
   *   Defaults to a no-op so every pre-existing call site is unaffected.
   * @param startSeq PB-2/M-5 ADDITIVE: seed the monotonic seq counter at a
   *   value other than 0. Used by the resume route to mint NEW synthetic
   *   events (a `flag`/`snapshot.apply` pair, or a grace-window `turn.close`)
   *   that continue a turn's seq sequence after replaying/tailing raw
   *   historical events (which are written via `writeRawEvent`, bypassing
   *   this counter entirely, so they keep their original seq).
   */
  constructor(
    private readonly controller: ReadableStreamDefaultController<Uint8Array>,
    private readonly onEmit: (event: PariprashnaEvent) => void = () => {},
    startSeq = 0,
  ) {
    this.seq = startSeq
  }

  /** Whether `close()` (or a terminal enqueue failure) has fired. */
  get isClosed(): boolean {
    return this.closed
  }

  /**
   * COLLECT-ONLY runtime guard (G5 — SAMĀPTI §8.1 / BRIEF_PB-3.1 G5; §14.6 C1 / W-3).
   *
   * Every Paripraśna event crosses this one method, so this single call site covers
   * the entire served reading stream. It throws (rather than stripping or flagging)
   * by design: W-3 says a served reading must be byte-identical whether or not
   * calibration data exists, so a reading that has already been contaminated is not
   * a reading worth finishing — failing loudly is the honest outcome, and it is what
   * `assertNoCalibrationLeak`'s contract promises.
   *
   * `writeRawEvent` (the resume/replay path) deliberately does NOT re-run this: it
   * replays events that already passed this guard when they were first emitted, and
   * re-asserting on replay would turn a historical contamination into an unrecoverable
   * resume rather than a diagnosable one.
   */
  private assertServable(event: PariprashnaEvent): void {
    assertNoCalibrationLeak(event, `pariprashna:${event.type}`)
  }

  private write(event: PariprashnaEvent): void {
    if (this.closed) return
    this.assertServable(event)
    try {
      this.controller.enqueue(this.encoder.encode(serializeEvent(event)))
    } catch {
      // Controller already closed by a client disconnect — stop writing.
      this.closed = true
      return
    }
    try {
      this.onEmit(event)
    } catch {
      // A buffering hook must never be able to break the live stream.
    }
  }

  private envelope(): { seq: number; t: number } {
    return { seq: this.seq++, t: Date.now() }
  }

  turnOpen(body: Body<TurnOpenEvent, 'turn.open'>): void {
    // P2-D: `protocol_version` is caller-opt-in, NOT auto-stamped here.
    // Every pre-existing call site (route.ts) never sets it and therefore
    // emits byte-identical frames to before this field existed — the P0-C
    // golden-stream harness (tests/pariprashna/route_ports/
    // route_golden_stream.test.ts) asserts EXACT baseline equality on the
    // live route's real output, so a default injected here would be a wire
    // change disguised as an additive one. `protocolVersionOf` (events.ts)
    // already reads an absent field as version 1, which is the correct
    // "old-version messages still parse" contract without needing every
    // frame to carry the field explicitly.
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

  /** P2-D (PPR-10/FD-9): the settled_visual/durably_persisted split — see events.ts. */
  turnPersisted(body: Body<TurnPersistedEvent, 'turn.persisted'>): void {
    this.write({ type: 'turn.persisted', ...this.envelope(), ...body })
  }

  turnClose(body: Body<TurnCloseEvent, 'turn.close'>): void {
    this.write({ type: 'turn.close', ...this.envelope(), ...body })
  }

  error(body: Body<ErrorEvent, 'error'>): void {
    this.write({ type: 'error', ...this.envelope(), ...body })
  }

  snapshotApply(body: Body<SnapshotApplyEvent, 'snapshot.apply'>): void {
    this.write({ type: 'snapshot.apply', ...this.envelope(), ...body })
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
