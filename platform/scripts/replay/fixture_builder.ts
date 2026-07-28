/**
 * Paripraśna replay harness — fixture authoring DSL.
 *
 * Small helper for hand-authoring fixture event lists without repeating
 * `id`/`seq`/`t` bookkeeping at every call site. Each `Turn` instance owns a
 * monotonic seq counter and a synthetic clock; `.push(type, fields, delayMs)`
 * appends one timed event.
 */
import type { FixtureEventEntry, FixtureSpec } from './fixture_types'
// Integration note (PB-1/integrate): re-pointed to S-1's canonical protocol.
// S-1 exports the schema VALUE as `PariprashnaEventSchema` and the TYPE as
// `PariprashnaEvent` (C-2's draft named these `PariprashnaEvent` /
// `PariprashnaEventT`). The committed JSON fixtures under
// `tests/pariprashna/fixtures/` were authored against C-2's draft shape and are
// FROZEN — the live gate/golden path reads them from disk and does NOT rebuild
// them here. Regenerating fixtures against S-1's real schema would require
// re-authoring each fixture's events to S-1's field shapes; that is out of
// scope for the PB-1 integration (tracked as a known follow-up).
import { PariprashnaEventSchema, type PariprashnaEvent } from '../../src/lib/pariprashna/protocol/events'

export class Turn {
  private seq = 0
  private clock = 0
  readonly turnId: string
  readonly entries: FixtureEventEntry[] = []

  constructor(turnId: string) {
    this.turnId = turnId
  }

  /** Append a well-formed, schema-validated event. Throws immediately (at
   *  fixture-build time, not test time) if the payload doesn't match the
   *  canonical schema — this keeps fixtures honest as the schema evolves. */
  push(
    type: PariprashnaEvent['type'],
    fields: Record<string, unknown>,
    delayMs = 20,
  ): this {
    this.clock += delayMs
    const base = {
      id: `${this.turnId}-${this.seq}`,
      seq: this.seq,
      t: this.clock,
      type,
      ...fields,
    }
    this.seq += 1
    // Validate against the canonical schema so a fixture bug surfaces at
    // build time (`npm run pariprashna:fixtures:build`), not silently inside
    // a Playwright run.
    const parsed = PariprashnaEventSchema.parse(base)
    this.entries.push({ delay_ms: delayMs, event: parsed })
    return this
  }

  /** Append a deliberately-invalid raw payload (no schema validation) — the
   *  one sanctioned way to build malformed-sentinel-variants fixtures. Still
   *  consumes a seq number so downstream events keep monotonic seq. */
  pushRaw(raw: Record<string, unknown>, delayMs = 20): this {
    this.clock += delayMs
    this.seq += 1
    this.entries.push({ delay_ms: delayMs, event: raw })
    return this
  }

  /** Re-emit the most recently pushed entry verbatim (same id/seq/t) — used
   *  to construct duplicate-delivery scenarios for reducer idempotency
   *  tests. Does not advance the seq counter. */
  pushDuplicateOfLast(delayMs = 5): this {
    const last = this.entries[this.entries.length - 1]
    if (!last) throw new Error('pushDuplicateOfLast: no prior entry to duplicate')
    this.entries.push({ delay_ms: delayMs, event: last.event })
    return this
  }

  get lastSeq(): number {
    return this.seq - 1
  }
}

export function buildFixture(
  name: string,
  description: string,
  build: (turn: Turn) => void,
  opts: { chunk_bytes?: number; abrupt_end_after_seq?: number } = {},
): FixtureSpec {
  const turn = new Turn(name)
  build(turn)
  return {
    name,
    description,
    events: turn.entries,
    ...opts,
  }
}
