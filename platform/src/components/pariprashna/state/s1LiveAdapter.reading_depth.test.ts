/**
 * Lane P2-C (PPR-09/16) — the live-adapter half of the honest depth-received
 * disclosure. `reading_depth_received` is the ONE `grade` subject the adapter
 * now maps to a reducer-driving event; every other subject keeps the
 * pre-existing drop-to-`[]` behavior documented in the adapter's header.
 */

import { describe, it, expect } from 'vitest'

import { makeS1LiveAdapter } from './s1LiveAdapter'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'

describe('s1LiveAdapter — grade → reading_depth.received', () => {
  it('maps a reading_depth_received grade to a reading_depth.received WireEvent', () => {
    const adapter = makeS1LiveAdapter('t1', 'q', Date.now())
    const ev: PariprashnaEvent = {
      type: 'grade',
      seq: 3,
      t: 1,
      subject: 'reading_depth_received',
      grade: 'standard',
      detail: 'scope_tuple: intent=career width=standard depth=standard',
    }
    expect(adapter.map(ev)).toEqual([{ type: 'reading_depth.received', turnId: 't1', depth: 'standard', eventId: 't1-3' }])
  })

  it('still drops every other grade subject (e.g. query_class) — not a reducer-state driver', () => {
    const adapter = makeS1LiveAdapter('t1', 'q', Date.now())
    const ev: PariprashnaEvent = { type: 'grade', seq: 4, t: 1, subject: 'query_class', grade: 'timing', detail: '1 planned tools' }
    expect(adapter.map(ev)).toEqual([])
  })
})
