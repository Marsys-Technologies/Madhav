/**
 * Paripraśna wire-protocol round-trip + validation tests (lane PB-1/S-1).
 *
 * Proves the S-1 acceptance clause "the event stream Zod-validates end-to-end":
 *   • every event type serializes to a well-formed SSE frame and decodes back
 *     to an equal, typed object;
 *   • a malformed event is REJECTED at serialize time (fail-fast);
 *   • the emitter produces a valid, ordered frame sequence over a real
 *     ReadableStream, with `turn.open` as the first frame.
 */

import { describe, it, expect } from 'vitest'

import {
  serializeEvent,
  decodeEvent,
  PariprashnaEventSchema,
  type PariprashnaEvent,
} from './events'
import { PariprashnaEmitter } from './emitter'

const ONE_OF_EACH: PariprashnaEvent[] = [
  { type: 'turn.open', seq: 0, t: 1, turn_id: 'T', conversation_id: 'C', chart_id: 'X', model_id: 'm', reading_depth: 'deep_dive', length_tier: 'standard' },
  { type: 'phase', seq: 1, t: 1, phase: 'plan', status: 'start' },
  { type: 'activity.upsert', seq: 2, t: 1, key: 'k', label_key: 'lk', pass_id: 1, status: 'running' },
  { type: 'block.open', seq: 3, t: 1, block_id: 'b', pass_id: 1, role: 'prose' },
  { type: 'block.delta', seq: 4, t: 1, block_id: 'b', delta: 'hi' },
  { type: 'block.commit', seq: 5, t: 1, block_id: 'b', text: 'hi there' },
  { type: 'seam.open', seq: 6, t: 1, pass_id: 2, label_key: 'pariprashna.pass.2' },
  { type: 'seam.set', seq: 7, t: 1, pass_id: 2, summary: 'Consulted dashas' },
  { type: 'citation.define', seq: 8, t: 1, index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 's' },
  { type: 'flag', seq: 9, t: 1, code: 'citation_gate_warn', level: 'warn' },
  { type: 'grade', seq: 10, t: 1, subject: 'citation_gate', grade: 'PASS' },
  { type: 'turn.commit', seq: 11, t: 1, turn_id: 'T', conversation_id: 'C', message_id: 'M', status: 'ok', assistant_chars: 42 },
  { type: 'turn.close', seq: 12, t: 1, turn_id: 'T', status: 'ok', ms: 5 },
  { type: 'error', seq: 13, t: 1, code: 'PLANNER_INVALID_PLAN', message: 'nope', retryable: false, phase: 'plan' },
]

describe('pariprashna protocol events', () => {
  it('round-trips every event type through serialize → SSE frame → decode', () => {
    for (const evt of ONE_OF_EACH) {
      const frame = serializeEvent(evt)
      expect(frame).toMatch(new RegExp(`^event: ${evt.type.replace('.', '\\.')}\\ndata: `))
      expect(frame.endsWith('\n\n')).toBe(true)
      const dataLine = frame.split('\n')[1].slice('data: '.length)
      const decoded = decodeEvent(dataLine)
      expect(decoded).toEqual(evt)
    }
  })

  it('covers all 14 event types in the discriminated union', () => {
    const types = new Set(ONE_OF_EACH.map((e) => e.type))
    expect(types.size).toBe(14)
    // Every fixture validates against the union.
    for (const evt of ONE_OF_EACH) {
      expect(PariprashnaEventSchema.safeParse(evt).success).toBe(true)
    }
  })

  it('rejects a malformed event at serialize time (fail-fast)', () => {
    // Missing required `pass_id` on activity.upsert — force through an unknown
    // cast (never `any`) to simulate a bad caller, and assert the guard throws.
    const bad = { type: 'activity.upsert', seq: 0, t: 0, key: 'k', label_key: 'lk', status: 'running' } as unknown as PariprashnaEvent
    expect(() => serializeEvent(bad)).toThrow()
  })

  it('decodeEvent returns null on garbage rather than throwing', () => {
    expect(decodeEvent('not json')).toBeNull()
    expect(decodeEvent('{"type":"nope"}')).toBeNull()
  })
})

describe('PariprashnaEmitter', () => {
  async function drain(fn: (em: PariprashnaEmitter) => void): Promise<string[]> {
    const chunks: string[] = []
    const decoder = new TextDecoder()
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        const em = new PariprashnaEmitter(controller)
        fn(em)
        em.close()
      },
    })
    const reader = stream.getReader()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      if (value) chunks.push(decoder.decode(value))
    }
    return chunks
  }

  it('emits an ordered, valid frame sequence with turn.open first and monotonic seq', async () => {
    const frames = await drain((em) => {
      em.turnOpen({ turn_id: 'T', conversation_id: 'C', chart_id: 'X', model_id: 'm', reading_depth: 'auto', length_tier: 'standard' })
      em.phase({ phase: 'plan', status: 'start' })
      em.blockOpen({ block_id: 'b', pass_id: 1, role: 'prose' })
      em.blockDelta({ block_id: 'b', delta: 'hi' })
      em.blockCommit({ block_id: 'b', text: 'hi' })
      em.turnClose({ turn_id: 'T', status: 'ok', ms: 1 })
    })
    const decoded = frames.map((f) => decodeEvent(f.split('\n')[1].slice('data: '.length)))
    expect(decoded.every((d) => d !== null)).toBe(true)
    expect(decoded[0]?.type).toBe('turn.open')
    expect(decoded.at(-1)?.type).toBe('turn.close')
    // seq strictly increments from 0.
    decoded.forEach((d, i) => expect(d?.seq).toBe(i))
  })
})
