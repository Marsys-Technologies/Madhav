/**
 * Lane P2-A (G2-A) — the live-wire → reducer seam for the new block.commit
 * fields and the `prediction_card` event.
 *
 * `reading_parts_semantic_blocks.test.ts` proves the SERVER emits the right
 * `block.commit` shape. This file proves the CLIENT adapter reads it
 * correctly — in particular that a flag-OFF stream (no `kind`/`role`/etc on
 * the event) still degrades to the exact pre-lane `kind: 'paragraph'`
 * behavior, so this lane cannot regress a deployed v1 stream.
 */
import { describe, it, expect } from 'vitest'
import { makeS1LiveAdapter } from '../s1LiveAdapter'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'

function env(seq: number) {
  return { seq, t: 1000 + seq }
}

describe('s1LiveAdapter — block.commit', () => {
  it('flag-OFF shape (no kind/role/table/gap_text/content on the wire event) maps to kind: paragraph, exactly as before this lane', () => {
    const adapter = makeS1LiveAdapter('turn-1', 'question text', Date.now())
    const ev: PariprashnaEvent = { type: 'block.commit', ...env(0), block_id: 'b1', text: 'hello there' }
    const [wire] = adapter.map(ev)
    expect(wire).toMatchObject({ type: 'block.commit', blockId: 'b1', kind: 'paragraph', html: 'hello there' })
    expect((wire as { role?: string }).role).toBeUndefined()
    expect((wire as { table?: unknown }).table).toBeUndefined()
  })

  it('carries a real kind/role/table when the server sent them', () => {
    const adapter = makeS1LiveAdapter('turn-1', 'question text', Date.now())
    const ev: PariprashnaEvent = {
      type: 'block.commit',
      ...env(1),
      block_id: 'b2',
      text: '| A | B |\n| --- | --- |\n| 1 | 2 |',
      kind: 'table',
      table: { headers: ['A', 'B'], rows: [['1', '2']] },
    }
    const [wire] = adapter.map(ev)
    expect(wire).toMatchObject({
      type: 'block.commit',
      blockId: 'b2',
      kind: 'table',
      table: { headers: ['A', 'B'], rows: [['1', '2']] },
    })
  })

  it('prefers `content` over `text` for the reader-facing html when both are present', () => {
    const adapter = makeS1LiveAdapter('turn-1', 'question text', Date.now())
    const ev: PariprashnaEvent = {
      type: 'block.commit',
      ...env(2),
      block_id: 'b3',
      text: '> raw quoted line',
      kind: 'verse',
      content: 'raw quoted line',
    }
    const [wire] = adapter.map(ev)
    expect((wire as { html?: string }).html).toBe('raw quoted line')
  })
})

describe('s1LiveAdapter — prediction_card', () => {
  it('maps a prediction_card event to a WireEvent carrying the part id + candidate', () => {
    const adapter = makeS1LiveAdapter('turn-1', 'question text', Date.now())
    const ev: PariprashnaEvent = {
      type: 'prediction_card',
      ...env(3),
      conversation_id: 'conv-1',
      message_id: 'msg-1',
      part_id: 'part-1',
      candidate: {
        claim_text: 'A promotion is likely within two years.',
        domain: 'career',
        window_start: '2027-01-01',
        window_end: '2029-01-01',
        direction: 'positive',
        technique_refs: ['vimshottari_dasha'],
        grounding_fact_ids: ['SIG.MSR.001'],
        score: 0.85,
        horizon_text: 'within two years',
      },
    }
    const [wire] = adapter.map(ev)
    if (ev.type !== 'prediction_card') throw new Error('unreachable — fixture literal')
    expect(wire).toEqual({
      type: 'prediction_card',
      turnId: 'turn-1',
      partId: 'part-1',
      conversationId: 'conv-1',
      candidate: ev.candidate,
      eventId: 'turn-1-3',
    })
  })
})
