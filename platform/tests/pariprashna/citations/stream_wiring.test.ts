/**
 * G2-B "Citations at first paint" (PPR-08, FD-2/FD-6) — `TurnCitationStream`.
 *
 * Proves the three load-bearing claims of the live wiring, independent of the
 * route/adapter: (1) a sentinel arriving DURING streaming resolves to a
 * `citation.define` wire event and a reader marker BEFORE the stream ends —
 * not just at final commit; (2) the hallucination counter fires for a
 * sentinel with no matching source; (3) `resolvedCitations` is the turn's own
 * resolution ledger, in wire order, deduplicated by ref — the thing
 * persistence should read instead of re-scanning text.
 */

import { describe, it, expect } from 'vitest'
import { TurnCitationStream, type UnstampedCitationWireEvent } from '@/lib/pariprashna/citations/stream_wiring'
import { makeFixtureResolver } from './fixtures'

function makeStream(collected: UnstampedCitationWireEvent[]): TurnCitationStream {
  return new TurnCitationStream({
    resolver: makeFixtureResolver(),
    modelId: 'test-model',
    onWireEvent: (e) => collected.push(e),
    now: () => 0,
  })
}

describe('TurnCitationStream', () => {
  it('resolves a sentinel mid-stream: marker text + citation.define BEFORE end()', () => {
    const events: UnstampedCitationWireEvent[] = []
    const s = makeStream(events)

    const out1 = s.write('Mercury shows strength here ')
    expect(out1).toContain('Mercury shows strength here')
    // No citation.define yet — no sentinel has arrived.
    expect(events.some((e) => e.type === 'citation.define')).toBe(false)

    const out2 = s.write('⟦cite: SIG.MSR.413⟧')
    expect(out2).toBe('[1]')
    const defines = events.filter((e): e is Extract<UnstampedCitationWireEvent, { type: 'citation.define' }> =>
      e.type === 'citation.define',
    )
    expect(defines).toHaveLength(1)
    expect(defines[0].index).toBe(1)
    expect(defines[0].signal_id).toBe('SIG.MSR.413')
    expect(defines[0].grade).toBe('primary')
    expect(defines[0].reader_label).toBe('Mercury eight-system convergence')

    // Proves this happened DURING streaming, not only at the end: end() adds
    // no further text and no further citation.define for the same ref.
    const finalChunk = s.end()
    expect(finalChunk).toBe('')
    expect(events.filter((e) => e.type === 'citation.define')).toHaveLength(1)
  })

  it('an unresolvable ref increments the hallucination counter and grades unverified', () => {
    const events: UnstampedCitationWireEvent[] = []
    const s = makeStream(events)
    s.write('A claim citing ⟦cite: SIG.MSR.GHOST999⟧.')
    s.end()

    expect(s.hallucinationCount).toBe(1)
    const define = events.find((e) => e.type === 'citation.define')
    expect(define && define.type === 'citation.define' && define.grade).toBe('unverified')
  })

  it('resolvedCitations is the turn resolution ledger, in wire order, deduplicated by ref', () => {
    const events: UnstampedCitationWireEvent[] = []
    const s = makeStream(events)
    s.write('First ⟦cite: SIG.MSR.413⟧, then ⟦cite: SIG.MSR.042⟧, then again ⟦cite: SIG.MSR.413⟧.')
    s.end()

    expect(s.resolvedCitations.map((c) => c.signal_id)).toEqual(['SIG.MSR.413', 'SIG.MSR.042'])
    expect(s.resolvedCitations.map((c) => c.index)).toEqual([1, 2])
    expect(s.resolvedCitations[0].grade).toBe('primary')
    expect(s.resolvedCitations[1].grade).toBe('supporting')
  })

  it('a sentinel split across two write() calls still resolves (hold-back works live)', () => {
    const events: UnstampedCitationWireEvent[] = []
    const s = makeStream(events)
    const part1 = s.write('Grounded in this ⟦cite: SIG.MSR')
    const part2 = s.write('.413⟧ finding.')
    // "finding." has no trailing whitespace yet, so the rewriter's own
    // trailing-partial-word holdback (stageProse, rewriter.ts) keeps it back
    // until end() — this is proven separately: the citation.define + marker
    // both landed DURING this write() call, before any flush.
    const tail = s.end()

    expect(part1).toBe('Grounded in this ')
    expect(part2).toBe('[1] ')
    expect(tail).toBe('finding.')
    expect(events.filter((e) => e.type === 'citation.define')).toHaveLength(1)
  })

  it('a held sentinel flushes as plain text once the hold-back timeout elapses (tick)', () => {
    const events: UnstampedCitationWireEvent[] = []
    let clock = 0
    const s = new TurnCitationStream({
      resolver: makeFixtureResolver(),
      modelId: 'test-model',
      onWireEvent: (e) => events.push(e),
      now: () => clock,
    })
    s.write('Unclosed sentinel: ⟦cite: SIG.MSR.413')
    expect(s.tick()).toBe('') // well within the 400ms budget — still holding
    clock = 500
    const flushed = s.tick()
    expect(flushed).toContain('cite')
    expect(events.some((e) => e.type === 'flag' && e.code === 'malformed_sentinel')).toBe(true)
    // No citation.define fired — the sentinel never closed.
    expect(events.some((e) => e.type === 'citation.define')).toBe(false)
  })

  it('end() is idempotent — a second call after the first produces nothing new', () => {
    const events: UnstampedCitationWireEvent[] = []
    const s = makeStream(events)
    s.write('plain prose, no citation')
    const first = s.end()
    const eventsAfterFirst = events.length
    const second = s.end()
    expect(second).toBe('')
    expect(events).toHaveLength(eventsAfterFirst)
    void first
  })
})
