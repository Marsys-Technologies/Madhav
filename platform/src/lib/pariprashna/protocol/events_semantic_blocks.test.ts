/**
 * Lane P2-A (G2-A), protocol v2 — round-trip + emitter tests for the new
 * `block.commit` fields, the `prediction_card` event, and the
 * `turn.open.protocol_version` stamp. Kept as its own file rather than
 * folded into `events.test.ts` so its hardcoded "14 event types" fixture
 * count (`ONE_OF_EACH`) is left untouched.
 */
import { describe, it, expect } from 'vitest'

import {
  serializeEvent,
  decodeEvent,
  PariprashnaEventSchema,
  PARIPRASHNA_PROTOCOL_VERSION,
  type PariprashnaEvent,
} from './events'
import { PariprashnaEmitter } from './emitter'

describe('block.commit — additive v2 fields', () => {
  it('round-trips with kind/role/content/table/gap_text all present', () => {
    const evt: PariprashnaEvent = {
      type: 'block.commit',
      seq: 0,
      t: 1,
      block_id: 'b1',
      text: '| A | B |\n| --- | --- |\n| 1 | 2 |',
      kind: 'table',
      role: undefined,
      content: undefined,
      table: { headers: ['A', 'B'], rows: [['1', '2']] },
      gap_text: undefined,
    }
    const frame = serializeEvent(evt)
    const decoded = decodeEvent(frame.split('\n')[1].slice('data: '.length))
    expect(decoded).toEqual(evt)
  })

  it('a v1-shaped event (no additive fields at all) still validates — flag-OFF compatibility', () => {
    const evt = { type: 'block.commit', seq: 0, t: 1, block_id: 'b1', text: 'plain text' }
    expect(PariprashnaEventSchema.safeParse(evt).success).toBe(true)
  })

  it('rejects an invalid kind value (closed enum)', () => {
    const bad = { type: 'block.commit', seq: 0, t: 1, block_id: 'b1', text: 'x', kind: 'not_a_real_kind' }
    expect(PariprashnaEventSchema.safeParse(bad).success).toBe(false)
  })
})

describe('prediction_card event', () => {
  const candidate = {
    claim_text: 'A promotion is likely within two years.',
    domain: 'career',
    window_start: '2027-01-01',
    window_end: '2029-01-01',
    direction: 'positive',
    technique_refs: ['vimshottari_dasha'],
    grounding_fact_ids: ['SIG.MSR.001'],
    score: 0.85,
    horizon_text: 'within two years',
  }

  it('round-trips through serialize → SSE frame → decode', () => {
    const evt: PariprashnaEvent = {
      type: 'prediction_card',
      seq: 5,
      t: 1,
      conversation_id: 'conv-1',
      message_id: 'msg-1',
      part_id: 'part-1',
      candidate,
    }
    const frame = serializeEvent(evt)
    expect(frame).toMatch(/^event: prediction_card\ndata: /)
    const decoded = decodeEvent(frame.split('\n')[1].slice('data: '.length))
    expect(decoded).toEqual(evt)
  })

  it('validates against the discriminated union', () => {
    const evt = { type: 'prediction_card', seq: 0, t: 1, conversation_id: 'c', message_id: 'm', part_id: 'p', candidate }
    expect(PariprashnaEventSchema.safeParse(evt).success).toBe(true)
  })

  it('rejects a candidate missing a required field (fail-fast)', () => {
    const { score: _score, ...withoutScore } = candidate
    void _score
    const bad = { type: 'prediction_card', seq: 0, t: 1, conversation_id: 'c', message_id: 'm', part_id: 'p', candidate: withoutScore }
    expect(() => serializeEvent(bad as unknown as PariprashnaEvent)).toThrow()
  })
})

describe('turn.open — protocol_version', () => {
  // Deliberately NOT auto-stamped by the emitter (unlike `seq`/`t`) — see
  // `emitter.ts`'s `turnOpen` doc comment: the P0-C golden-stream
  // byte-equality harness caught an earlier version of this lane that DID
  // auto-stamp it, which put the field on every turn regardless of the
  // semantic-blocks flag and broke "flag OFF ⇒ byte-identical". The route
  // (`app/api/pariprashna/route.ts`) is the one call site that decides
  // whether to include it, gated on `isSemanticBlocksEnabled()`.
  it('the emitter passes an explicitly-supplied protocol_version through unchanged', async () => {
    const chunks: string[] = []
    const decoder = new TextDecoder()
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        const em = new PariprashnaEmitter(controller)
        em.turnOpen({
          turn_id: 'T',
          conversation_id: 'C',
          chart_id: 'X',
          model_id: 'm',
          reading_depth: 'auto',
          length_tier: 'standard',
          protocol_version: PARIPRASHNA_PROTOCOL_VERSION,
        })
        em.close()
      },
    })
    const reader = stream.getReader()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      if (value) chunks.push(decoder.decode(value))
    }
    const decoded = decodeEvent(chunks[0].split('\n')[1].slice('data: '.length))
    expect(decoded?.type).toBe('turn.open')
    expect(decoded && 'protocol_version' in decoded ? decoded.protocol_version : undefined).toBe(
      PARIPRASHNA_PROTOCOL_VERSION,
    )
  })

  it('the emitter omits protocol_version entirely when the caller does not supply one (flag-OFF shape)', async () => {
    const chunks: string[] = []
    const decoder = new TextDecoder()
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        const em = new PariprashnaEmitter(controller)
        em.turnOpen({ turn_id: 'T', conversation_id: 'C', chart_id: 'X', model_id: 'm', reading_depth: 'auto', length_tier: 'standard' })
        em.close()
      },
    })
    const reader = stream.getReader()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      if (value) chunks.push(decoder.decode(value))
    }
    // The raw SSE frame carries no `protocol_version` key at all — JSON.stringify
    // drops `undefined` values, so this is a genuine absence, not a null.
    expect(chunks[0]).not.toContain('protocol_version')
  })

  it('a v1-shaped turn.open (no protocol_version) still validates — old-decoder compatibility', () => {
    const evt = { type: 'turn.open', seq: 0, t: 1, turn_id: 'T', conversation_id: 'C', chart_id: 'X', model_id: 'm', reading_depth: 'auto', length_tier: 'standard' }
    expect(PariprashnaEventSchema.safeParse(evt).success).toBe(true)
  })
})
