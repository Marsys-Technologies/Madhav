/**
 * envelope_cursor_fingerprint_w3.test.ts — W3 "One Envelope" cursor filter/sort fingerprints
 * (RETRIEVAL_PLANE_ELEVATION_PLAN §R-2 item 4 / master brief §E).
 *
 * Proves the core contract at the envelope-utility level (no DB):
 *   - computeFilterFingerprint is deterministic and key-order-independent.
 *   - a cursor minted with a fingerprint, replayed under the SAME fingerprint, resolves to
 *     its own offset with no mismatch.
 *   - the SAME cursor replayed against a DIFFERENT fingerprint resolves to offset 0 with
 *     mismatch:true — never the stale offset.
 *   - a cursor minted with NO fingerprint (the pre-W3 / filterless shape) round-trips exactly
 *     as before — no regression for existing offset-only consumers.
 *   - buildHonestPagination's emitted next_cursor carries the fingerprint end-to-end.
 */
import { describe, it, expect } from 'vitest'
import {
  buildHonestPagination,
  encodeCursor,
  decodeCursor,
  decodeCursorFull,
  computeFilterFingerprint,
  checkCursorFingerprint,
  CURSOR_FILTER_MISMATCH_FLAG,
} from '@/lib/retrieval/envelope'

describe('W3 computeFilterFingerprint — deterministic, key-order-independent', () => {
  it('is deterministic for the same logical filter set', () => {
    const a = computeFilterFingerprint({ domain: 'career', min_salience: 0.5 })
    const b = computeFilterFingerprint({ domain: 'career', min_salience: 0.5 })
    expect(a).toBe(b)
  })

  it('is independent of object-key insertion order', () => {
    const a = computeFilterFingerprint({ domain: 'career', min_salience: 0.5, top_k: 50 })
    const b = computeFilterFingerprint({ top_k: 50, domain: 'career', min_salience: 0.5 })
    const c = computeFilterFingerprint({ min_salience: 0.5, top_k: 50, domain: 'career' })
    expect(a).toBe(b)
    expect(b).toBe(c)
  })

  it('treats undefined-valued keys the same as omitted keys', () => {
    const a = computeFilterFingerprint({ domain: 'career', source_subsystem: undefined })
    const b = computeFilterFingerprint({ domain: 'career' })
    expect(a).toBe(b)
  })

  it('differs when a filter value actually differs', () => {
    const a = computeFilterFingerprint({ domain: 'career' })
    const b = computeFilterFingerprint({ domain: 'wealth' })
    expect(a).not.toBe(b)
  })

  it('differs when the filter set has a genuinely different shape (nested/array values)', () => {
    const a = computeFilterFingerprint({ domain: 'career', tags: ['a', 'b'] })
    const b = computeFilterFingerprint({ domain: 'career', tags: ['b', 'a'] })
    // array ORDER is semantically significant (unlike object key order) — must differ.
    expect(a).not.toBe(b)
  })

  it('the empty filter set (a genuinely filterless capability) is stable', () => {
    const a = computeFilterFingerprint({})
    const b = computeFilterFingerprint({})
    expect(a).toBe(b)
  })
})

describe('W3 cursor round-trip — with and without a fingerprint', () => {
  it('encodeCursor/decodeCursor offset round-trip is unaffected by adding a fingerprint param', () => {
    const fp = computeFilterFingerprint({ domain: 'career' })
    for (const n of [0, 1, 42, 9999]) {
      expect(decodeCursor(encodeCursor(n, fp))).toBe(n)
      expect(decodeCursor(encodeCursor(n))).toBe(n) // no-fingerprint case, unchanged
    }
  })

  it('decodeCursorFull recovers both offset and fingerprint', () => {
    const fp = computeFilterFingerprint({ domain: 'career' })
    const cursor = encodeCursor(50, fp)
    const decoded = decodeCursorFull(cursor)
    expect(decoded).not.toBeNull()
    expect(decoded?.offset).toBe(50)
    expect(decoded?.filterFingerprint).toBe(fp)
  })

  it('decodeCursorFull reports filterFingerprint:null for a fingerprint-less (legacy) cursor', () => {
    const cursor = encodeCursor(50) // pre-W3 shape: no fp
    const decoded = decodeCursorFull(cursor)
    expect(decoded?.offset).toBe(50)
    expect(decoded?.filterFingerprint).toBeNull()
  })

  it('decodeCursorFull is malformed-input safe, same discipline as decodeCursor', () => {
    expect(decodeCursorFull(null)).toBeNull()
    expect(decodeCursorFull(undefined)).toBeNull()
    expect(decodeCursorFull('not-base64-$$$')).toBeNull()
    expect(decodeCursorFull(Buffer.from('{"nope":1}', 'utf8').toString('base64'))).toBeNull()
  })
})

describe('W3 checkCursorFingerprint — the replay-safety contract', () => {
  it('no cursor at all → offset 0, no mismatch, noFingerprint true (first call)', () => {
    const fp = computeFilterFingerprint({ domain: 'career' })
    const check = checkCursorFingerprint(undefined, fp)
    expect(check).toEqual({ offset: 0, mismatch: false, noFingerprint: true })
  })

  it('SAME filters replayed: cursor resolves to its own offset, no mismatch', () => {
    const fp = computeFilterFingerprint({ domain: 'career' })
    const cursor = encodeCursor(50, fp)
    const check = checkCursorFingerprint(cursor, fp) // replaying under the SAME fingerprint
    expect(check.mismatch).toBe(false)
    expect(check.offset).toBe(50)
  })

  it('DIFFERENT filters replayed with the old cursor: mismatch fires, offset resets to 0 — never the stale offset', () => {
    const mintedUnder = computeFilterFingerprint({ domain: 'career' })
    const cursor = encodeCursor(50, mintedUnder) // page 2 of the "career" family
    const replayedUnder = computeFilterFingerprint({ domain: 'wealth' }) // a DIFFERENT facet value
    const check = checkCursorFingerprint(cursor, replayedUnder)
    expect(check.mismatch).toBe(true)
    // The critical assertion: offset must NOT be the stale 50 — that would silently splice
    // into the "wealth" family at an arbitrary offset and look like a valid continuation.
    expect(check.offset).toBe(0)
  })

  it('a legacy (fingerprint-less) cursor never reports a mismatch — honest "not applicable"', () => {
    const cursor = encodeCursor(50) // no fp embedded (pre-W3 cursor, or filterless capability)
    const fp = computeFilterFingerprint({ domain: 'career' })
    const check = checkCursorFingerprint(cursor, fp)
    expect(check.mismatch).toBe(false)
    expect(check.noFingerprint).toBe(true)
    expect(check.offset).toBe(50) // still honors the offset — no regression for filterless callers
  })

  it('a cursor for a genuinely filterless capability (offset-only, both ends use {}) round-trips with no mismatch', () => {
    const fp = computeFilterFingerprint({})
    const cursor = encodeCursor(20, fp)
    const check = checkCursorFingerprint(cursor, fp)
    expect(check.mismatch).toBe(false)
    expect(check.offset).toBe(20)
  })

  it('the reserved flag literal is exactly "cursor_filter_mismatch"', () => {
    expect(CURSOR_FILTER_MISMATCH_FLAG).toBe('cursor_filter_mismatch')
  })
})

describe('W3 buildHonestPagination — filterFingerprint is embedded in the emitted cursor', () => {
  it('when filterFingerprint is supplied, the next_cursor carries it end-to-end', () => {
    const fp = computeFilterFingerprint({ domain: 'career', min_salience: 0.5 })
    const p = buildHonestPagination({ served: 50, limit: 50, offset: 0, total: 200, filterFingerprint: fp })
    expect(p.next_cursor).not.toBeNull()
    const decoded = decodeCursorFull(p.next_cursor)
    expect(decoded?.offset).toBe(50)
    expect(decoded?.filterFingerprint).toBe(fp)
    // Backward-compat: decodeCursor (offset-only) still works unchanged.
    expect(decodeCursor(p.next_cursor)).toBe(50)
  })

  it('omitting filterFingerprint produces the exact pre-W3 cursor shape (no regression)', () => {
    const p = buildHonestPagination({ served: 50, limit: 50, offset: 0, total: 200 })
    expect(p.next_cursor).not.toBeNull()
    expect(decodeCursor(p.next_cursor)).toBe(50)
    expect(decodeCursorFull(p.next_cursor)?.filterFingerprint).toBeNull()
  })

  it('a full round trip: mint via buildHonestPagination, replay under the same filters → no mismatch, correct next offset', () => {
    const fp = computeFilterFingerprint({ entity_class: 'planet' })
    const page1 = buildHonestPagination({ served: 100, limit: 100, offset: 0, total: 250, filterFingerprint: fp })
    const check = checkCursorFingerprint(page1.next_cursor, fp)
    expect(check.mismatch).toBe(false)
    expect(check.offset).toBe(100)

    const page2 = buildHonestPagination({ served: 100, limit: 100, offset: check.offset, total: 250, filterFingerprint: fp })
    const check2 = checkCursorFingerprint(page2.next_cursor, fp)
    expect(check2.mismatch).toBe(false)
    expect(check2.offset).toBe(200)
  })

  it('a full round trip: mint under one filter, replay under a different filter → mismatch, not the wrong page', () => {
    const fpA = computeFilterFingerprint({ entity_class: 'planet' })
    const fpB = computeFilterFingerprint({ entity_class: 'sign' })
    const page1 = buildHonestPagination({ served: 100, limit: 100, offset: 0, total: 250, filterFingerprint: fpA })
    const check = checkCursorFingerprint(page1.next_cursor, fpB)
    expect(check.mismatch).toBe(true)
    expect(check.offset).toBe(0)
  })
})
