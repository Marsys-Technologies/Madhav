/**
 * PB-1 S-3 fixture (a): `unclosed-sentinel`.
 *
 * A stream carrying a `⟦cite:` that never closes must NEVER stall, and must
 * flush the held bytes as plain text at the byte limit OR the timeout — whichever
 * fires first — emitting a flag{malformed_sentinel}. Proves the stream cannot be
 * held hostage by a sentinel that never closes.
 */

import { describe, it, expect } from 'vitest'
import {
  CitationStreamRewriter,
  MAX_HOLDBACK_BYTES,
  TIMEOUT_MS,
} from '@/lib/pariprashna/citations'
import { makeRewriter, makeFixtureResolver, runStream } from './fixtures'

describe('unclosed-sentinel: byte-limit flush', () => {
  it('flushes held bytes as text once MAX_HOLDBACK is exceeded, never stalling', () => {
    const rw = makeRewriter()
    // One opener, then a long junk run with no closer. Same clock so timeout
    // cannot fire — isolates the byte-limit path.
    const junk = 'x'.repeat(MAX_HOLDBACK_BYTES + 20)
    const { text, events } = runStream(rw, ['Before ', '⟦cite:', junk, ' After'], {
      perDeltaMs: 0,
    })

    const malformed = events.filter(
      (e) => e.type === 'flag' && e.flag === 'malformed_sentinel',
    )
    expect(malformed).toHaveLength(1)
    expect(malformed[0]).toMatchObject({ reason: 'byte_limit' })

    // The held sentinel text is surfaced as prose, not swallowed. Both the
    // pre-text and the post-text survive; nothing is lost.
    expect(text).toContain('Before ')
    expect(text).toContain('⟦cite:')
    expect(text).toContain('After')
    expect(rw.isHolding()).toBe(false)
  })

  it('never holds more than MAX_HOLDBACK bytes before flushing', () => {
    const rw = makeRewriter()
    // Feed one byte at a time; assert the rewriter is not still holding after
    // the ceiling is crossed.
    let heldPastLimit = false
    const opener = '⟦cite:'
    rw.write(opener, 0)
    for (let i = 0; i < MAX_HOLDBACK_BYTES + 10; i++) {
      rw.write('x', 0)
      if (i > MAX_HOLDBACK_BYTES && rw.isHolding()) heldPastLimit = true
    }
    expect(heldPastLimit).toBe(false)
  })
})

describe('unclosed-sentinel: timeout flush', () => {
  it('flushes held bytes as text once TIMEOUT elapses, even with no new data', () => {
    const rw = makeRewriter()
    // Small hold, well under the byte limit, but the clock advances past TIMEOUT.
    const first = rw.write('Prefix ', 0) // trailing space → released immediately
    expect(first.text).toBe('Prefix ')
    const opened = rw.write('⟦cite:pending', 10) // enters hold at t=10 (benign body)
    expect(opened.text).toBe('') // nothing emitted while holding
    expect(rw.isHolding()).toBe(true)

    // No further deltas arrive; a timer tick past the deadline must flush.
    const flushed = rw.checkTimeout(10 + TIMEOUT_MS + 1)
    const malformed = flushed.events.filter(
      (e) => e.type === 'flag' && e.flag === 'malformed_sentinel',
    )
    expect(malformed).toHaveLength(1)
    expect(malformed[0]).toMatchObject({ reason: 'timeout' })
    expect(flushed.text).toContain('⟦cite:pending')
    expect(rw.isHolding()).toBe(false)
  })

  it('timeout is checked on the next write too (slow trickle cannot keep a stall alive)', () => {
    const rw = makeRewriter()
    rw.write('⟦cite:abc', 0)
    expect(rw.isHolding()).toBe(true)
    // A late delta arriving past the deadline triggers the flush on write().
    const late = rw.write('def', TIMEOUT_MS + 5)
    const malformed = late.events.filter(
      (e) => e.type === 'flag' && e.flag === 'malformed_sentinel',
    )
    expect(malformed.length).toBeGreaterThanOrEqual(1)
    expect(rw.isHolding()).toBe(false)
  })
})

describe('unclosed-sentinel: end-of-stream flush', () => {
  it('flushes a still-open hold at end() with reason eof_unclosed', () => {
    const rw = makeRewriter()
    rw.write('Tail ⟦cite:neverCloses', 0)
    const ended = rw.end()
    const malformed = ended.events.filter(
      (e) => e.type === 'flag' && e.flag === 'malformed_sentinel',
    )
    expect(malformed).toHaveLength(1)
    expect(malformed[0]).toMatchObject({ reason: 'eof_unclosed' })
    expect(ended.text).toContain('⟦cite:neverCloses')
  })
})

describe('unclosed-sentinel: leak-safety of flushed bytes', () => {
  it('lint still runs on flushed malformed bytes — an id inside never leaks', () => {
    const rw = new CitationStreamRewriter({
      resolver: makeFixtureResolver(),
      modelId: 'm',
    })
    // Malformed (never closes) AND contains an internal table name in the body.
    rw.write('⟦cite: bodha_msr_signals leaking', 0)
    const ended = rw.end()
    expect(ended.text).not.toMatch(/bodha_msr_signals/)
    // and a register_leak flag was raised for the redaction.
    const leaks = ended.events.filter(
      (e) => e.type === 'flag' && e.flag === 'register_leak',
    )
    expect(leaks.length).toBeGreaterThanOrEqual(1)
  })
})
