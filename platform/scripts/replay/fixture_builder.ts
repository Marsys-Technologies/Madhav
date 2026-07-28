/**
 * Paripraśna replay harness — fixture authoring DSL.
 *
 * Small helper for hand-authoring fixture event lists without repeating
 * `id`/`seq`/`t` bookkeeping at every call site. Each `Turn` instance owns a
 * monotonic seq counter and a synthetic clock; `.push(type, fields, delayMs)`
 * appends one timed event.
 */
import type { FixtureEventEntry, FixtureSpec } from './fixture_types'
// Integration note (PB-1/integrate, schema-drift fix): this harness speaks its
// OWN internal event vocabulary, NOT S-1's real wire protocol
// (`src/lib/pariprashna/protocol/events.ts`). This is deliberate and
// pre-existing — see `tests/pariprashna/reducer/reducer.mjs`'s "TERMINOLOGY"
// note, which documents e.g. `citation_anchor.open` / `citation_anchor.set`
// (a harness-internal char-offset anchor primitive) being named to AVOID
// colliding with S-1's real `seam.open` / `seam.set` (an unrelated
// pass-boundary event). The committed fixture JSONs, the reference reducer
// (`reducer.mjs`), the DOM harness (`tests/pariprashna/harness/public/client.mjs`),
// and every Playwright gate spec are ALL written against this harness
// vocabulary — none of them decode via `PariprashnaEventSchema`.
//
// A prior integration pass re-pointed this file's import to S-1's real schema
// module and called `PariprashnaEventSchema.parse()` on every authored event.
// That throws on essentially every fixture: the two vocabularies diverge in
// event TYPES (`citation_anchor.*` doesn't exist on the real wire at all),
// enum values (`phase`: 'planning'/'synthesizing' here vs real
// 'plan'/'synthesize'; `activity.upsert.status`: 'pending'/'active' here vs
// real 'running'/'error'), and field names (`final_text` vs real `text`,
// `reason` vs real `status`+`ms`, `block_count`/`citation_count` vs real
// `message_id`/`assistant_chars`). Re-authoring the WHOLE harness (fixtures +
// reducer.mjs + client.mjs + every gate spec) to speak the real wire is
// tracked as a follow-up, not in scope for this fix. `push()` below keeps a
// light structural sanity check instead (so an obvious fixture-authoring typo
// still surfaces at build time) without asserting the incompatible real
// schema.

export class Turn {
  private seq = 0
  private clock = 0
  readonly turnId: string
  readonly entries: FixtureEventEntry[] = []

  constructor(turnId: string) {
    this.turnId = turnId
  }

  /** Append a well-formed harness event. Throws immediately (at fixture-build
   *  time, not test time) if the payload is missing the basic envelope shape
   *  every event in this harness's own vocabulary needs — this keeps fixtures
   *  honest without asserting S-1's incompatible real wire schema (see the
   *  file-level note above for why). */
  push(
    type: string,
    fields: Record<string, unknown>,
    delayMs = 20,
  ): this {
    this.clock += delayMs
    // Kept for forward-compat realism with S-1's real `turn.open` request-
    // binding fields (conversation_id/chart_id/model_id/length_tier), even
    // though this harness's own reducer/DOM-client vocabulary doesn't
    // consume them. Fixture authors only care about the fields that vary per
    // fixture (turn_id, reading_depth); these are fixed synthetic defaults
    // for the rest, overridable per call site via `fields`.
    const turnOpenDefaults =
      type === 'turn.open'
        ? {
            conversation_id: `conv-${this.turnId}`,
            chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
            model_id: 'gemini-2.5-pro',
            length_tier: 'standard',
          }
        : {}
    const base = {
      id: `${this.turnId}-${this.seq}`,
      seq: this.seq,
      t: this.clock,
      type,
      ...turnOpenDefaults,
      ...fields,
    }
    this.seq += 1
    // Structural sanity check only (NOT `PariprashnaEventSchema.parse` — see
    // file-level note): every event in this harness's vocabulary must carry
    // a non-empty `type` string and numeric `seq`/`t` envelope fields. Catches
    // an obvious authoring typo (e.g. a call site accidentally clobbering the
    // envelope via `fields`) at build time.
    if (typeof base.type !== 'string' || base.type.length === 0) {
      throw new Error(`Turn.push: event missing a valid 'type' (got ${JSON.stringify(base.type)})`)
    }
    if (typeof base.seq !== 'number' || typeof base.t !== 'number') {
      throw new Error(`Turn.push: event missing numeric seq/t envelope fields (type=${type})`)
    }
    this.entries.push({ delay_ms: delayMs, event: base })
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
