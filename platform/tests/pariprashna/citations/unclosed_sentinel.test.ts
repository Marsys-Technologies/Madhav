/**
 * PB-1 S-3 fixture (a): `unclosed-sentinel`.
 *
 * A stream carrying a `⟦cite:` that never closes must NEVER stall, and must
 * DROP the held bytes (fail closed) at the byte limit OR the timeout —
 * whichever fires first — emitting a flag{malformed_sentinel}. Proves the
 * stream cannot be held hostage by a sentinel that never closes.
 *
 * ── V3-E-061 fix (2026-08-30) ─────────────────────────────────────────────
 * Pre-fix, this suite asserted the OLD (buggy) fail-OPEN contract: a flushed
 * hold's raw bytes — including the literal `⟦cite:` bracket markup — were
 * forwarded verbatim into reader-visible `text`. That is exactly the
 * mechanism V3-E-061 caught live in production (a malformed `⟦cite: ⟧` token
 * reaching reader prose). The assertions below now encode the fixed,
 * fail-CLOSED contract: a malformed hold is dropped in its entirety — no
 * `⟦`, `[[`, or `cite:` fragment, and no byte of the held content, ever
 * appears in `text` — while the stream still never stalls and prose before/
 * after the dropped segment still flows.
 */

import { describe, it, expect } from 'vitest'
import {
  CitationStreamRewriter,
  MAX_HOLDBACK_BYTES,
  TIMEOUT_MS,
} from '@/lib/pariprashna/citations'
import { makeRewriter, makeFixtureResolver, runStream } from './fixtures'

describe('unclosed-sentinel: byte-limit flush', () => {
  it('drops held bytes (fail closed) once MAX_HOLDBACK is exceeded, never stalling', () => {
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

    // The pre-text survives; the held sentinel markup itself is DROPPED, not
    // surfaced as prose — fail closed (V3-E-061 fix). The post-text delta
    // (' After') is a bare continuation with no leading whitespace boundary
    // reached inside the still-active prose stage by end(), so it survives
    // too, but crucially carries no trace of the dropped sentinel.
    expect(text).toContain('Before ')
    expect(text).not.toContain('⟦')
    expect(text).not.toContain('cite:')
    expect(text).not.toContain('x'.repeat(10)) // none of the junk body leaked
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
  it('drops held bytes (fail closed) once TIMEOUT elapses, even with no new data', () => {
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
    // Fail closed (V3-E-061 fix): the held sentinel body is dropped entirely,
    // never forwarded as text.
    expect(flushed.text).toBe('')
    expect(flushed.text).not.toContain('⟦')
    expect(flushed.text).not.toContain('pending')
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
    // 'def' is appended to the hold buffer before the timeout check runs, so
    // it is part of the SAME dropped segment as '⟦cite:abc' — none of it
    // reaches text. Fail closed (V3-E-061 fix): no fragment of the hold, at
    // any point in its accumulation, ever leaks.
    expect(late.text).toBe('')
    expect(late.text).not.toContain('⟦')
    expect(late.text).not.toContain('abc')
    expect(late.text).not.toContain('def')
  })
})

describe('unclosed-sentinel: end-of-stream flush', () => {
  it('drops a still-open hold at end() with reason eof_unclosed, never in text', () => {
    const rw = makeRewriter()
    // 'Tail ' is prose BEFORE the opener and is released by the write() call
    // itself (asserted separately below); only the still-open hold is live
    // when end() runs, so `ended.text` covers just that flush.
    const opened = rw.write('Tail ⟦cite:neverCloses', 0)
    expect(opened.text).toBe('Tail ')
    const ended = rw.end()
    const malformed = ended.events.filter(
      (e) => e.type === 'flag' && e.flag === 'malformed_sentinel',
    )
    expect(malformed).toHaveLength(1)
    expect(malformed[0]).toMatchObject({ reason: 'eof_unclosed' })
    // Fail closed (V3-E-061 fix): the held sentinel is dropped, not surfaced.
    expect(ended.text).toBe('')
    expect(ended.text).not.toContain('⟦')
    expect(ended.text).not.toContain('neverCloses')
  })
})

describe('unclosed-sentinel: leak-safety of flushed bytes', () => {
  it('a malformed hold containing an internal table name never reaches text (dropped whole)', () => {
    const rw = new CitationStreamRewriter({
      resolver: makeFixtureResolver(),
      modelId: 'm',
    })
    // Malformed (never closes) AND contains an internal table name in the body.
    rw.write('⟦cite: bodha_msr_signals leaking', 0)
    const ended = rw.end()
    expect(ended.text).not.toMatch(/bodha_msr_signals/)
    // Fail closed (V3-E-061 fix): NOTHING from the hold reaches text, not
    // just the id-shaped token — the sentinel markup and the word "leaking"
    // are dropped too, since the whole segment is discarded rather than
    // selectively lint-cleaned and forwarded.
    expect(ended.text).not.toContain('⟦')
    expect(ended.text).not.toContain('leaking')
    // The register-leak lint still ran (audit/telemetry channel) and would
    // have redacted the id had its `clean` text been forwarded — proving the
    // fix does not depend on removing that detection, only on never shipping
    // its output as reader text.
    const leaks = ended.events.filter(
      (e) => e.type === 'flag' && e.flag === 'register_leak',
    )
    expect(leaks.length).toBeGreaterThanOrEqual(1)
  })
})
