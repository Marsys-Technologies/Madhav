/**
 * P2-close item 3 — the live-adapter half of the receipt wire event. Pins
 * that a real `receipt.define` PariprashnaEvent maps to a `receipt.define`
 * WireEvent carrying the receipt through unchanged, following the same
 * template `s1LiveAdapter.reading_depth.test.ts` already established for the
 * sibling late-arriving wire event.
 */

import { describe, it, expect } from 'vitest'

import { makeS1LiveAdapter } from './s1LiveAdapter'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'

describe('s1LiveAdapter — receipt.define', () => {
  it('maps a real receipt.define event to a receipt.define WireEvent carrying the receipt through', () => {
    const adapter = makeS1LiveAdapter('t1', 'q', Date.now())
    const receipt = { turn_id: 't1', receipt_hash: 'abc', interpretation_sets: { status: 'measured', sets: [] } }
    const ev: PariprashnaEvent = {
      type: 'receipt.define',
      seq: 12,
      t: 1,
      turn_id: 't1',
      receipt,
    }
    expect(adapter.map(ev)).toEqual([
      { type: 'receipt.define', turnId: 't1', receipt, eventId: 't1-12' },
    ])
  })
})
