/**
 * lane P2-E (PPR-33/GAP-14) — `ReadingPartsAssembler`'s `onBlockCommitLagMs`
 * hook. Proves two things a lag measured from OUTSIDE this class could not:
 * (1) it fires exactly once per real commit, including the INTERNAL commit
 * `ensureBlock` triggers on a prose↔thinking role switch; (2) every
 * pre-existing caller (positional construction with fewer args) is
 * byte-for-byte unchanged — the callback defaults to a no-op.
 */
import { describe, it, expect } from 'vitest'

import { ReadingPartsAssembler } from './reading_parts'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

function fakeEmitter(): PariprashnaEmitter {
  return {
    flag: () => {},
    blockOpen: () => {},
    blockDelta: () => {},
    blockCommit: () => {},
  } as unknown as PariprashnaEmitter
}

describe('ReadingPartsAssembler onBlockCommitLagMs', () => {
  it('fires once with a real, non-negative lag on an explicit commitBlock()', () => {
    const lags: number[] = []
    const a = new ReadingPartsAssembler(fakeEmitter(), 1, false, [], (ms) => lags.push(ms))
    a.appendProse(a.ensureBlock('prose'), 'hello')
    a.commitBlock()
    expect(lags.length).toBe(1)
    expect(lags[0]).toBeGreaterThanOrEqual(0)
  })

  it('fires on the INTERNAL commit ensureBlock triggers on a role switch — the case an outside-observer would miss', () => {
    const lags: number[] = []
    const a = new ReadingPartsAssembler(fakeEmitter(), 1, false, [], (ms) => lags.push(ms))
    a.appendProse(a.ensureBlock('prose'), 'prose text')
    a.appendThinking(a.ensureBlock('thinking'), 'thinking text') // ensureBlock() commits the prose block HERE
    a.commitBlock() // commits the thinking block
    expect(lags.length).toBe(2)
  })

  it('never fires for a turn with no block ever opened', () => {
    const lags: number[] = []
    const a = new ReadingPartsAssembler(fakeEmitter(), 1, false, [], (ms) => lags.push(ms))
    a.commitBlock() // no-op: nothing was ever opened
    expect(lags.length).toBe(0)
  })

  it('defaults to a no-op — every pre-existing 4-arg (or fewer) call site is unaffected', () => {
    const a = new ReadingPartsAssembler(fakeEmitter(), 1, false, [])
    expect(() => {
      a.appendProse(a.ensureBlock('prose'), 'hello')
      a.commitBlock()
    }).not.toThrow()
  })
})
