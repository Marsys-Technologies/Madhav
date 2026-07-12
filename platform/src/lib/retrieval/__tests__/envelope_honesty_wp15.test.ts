/**
 * envelope_honesty_wp15.test.ts — WP-1.5 receipt-honesty contract (LCA-18).
 *
 * Proves the program-wide envelope contract that every W1 serving lane conforms to:
 *   - buildHonestPagination NEVER emits the audit's canonical lie (a `false`/undeclared
 *     trim at a full page, or a null cursor while more rows remain);
 *   - `more_available` is computed, never guessed, and agrees with (served, limit, total);
 *   - when more_available is true, next_cursor is a WORKING, round-trippable cursor;
 *   - buildRetrievalEnvelope always emits `more_available` (never a silent absent field).
 */
import { describe, it, expect } from 'vitest'
import {
  buildHonestPagination,
  encodeCursor,
  decodeCursor,
  buildRetrievalEnvelope,
} from '@/lib/retrieval/envelope'

describe('WP-1.5 buildHonestPagination — trim always declared', () => {
  it('a full page with more rows beyond it declares the trim + a working cursor', () => {
    // The audit lie: 200 served of 7014 with truncated:false + null cursor.
    const p = buildHonestPagination({ served: 200, limit: 200, offset: 0, total: 7014 })
    expect(p.more_available).toBe(true)
    expect(p.total).toBe(7014)
    expect(p.next_cursor).not.toBeNull()
    // cursor is working: it decodes to the next offset.
    expect(decodeCursor(p.next_cursor)).toBe(200)
  })

  it('the last (partial) page honestly reports no more available and null cursor', () => {
    const p = buildHonestPagination({ served: 14, limit: 200, offset: 0, total: 14 })
    expect(p.more_available).toBe(false)
    expect(p.next_cursor).toBeNull()
  })

  it('an exact-boundary page (served+offset == total) is the last page', () => {
    const p = buildHonestPagination({ served: 50, limit: 50, offset: 6950, total: 7000 })
    expect(p.more_available).toBe(false)
    expect(p.next_cursor).toBeNull()
  })

  it('a mid-stream full page advances the cursor from the current offset', () => {
    const p = buildHonestPagination({ served: 50, limit: 50, offset: 100, total: 7000 })
    expect(p.more_available).toBe(true)
    expect(decodeCursor(p.next_cursor)).toBe(150)
  })

  it('total:null (uncomputable) — a full page is presumptively not the last', () => {
    // orientation serving 10 of ~13.3k with total:null must NOT read as "no more".
    const p = buildHonestPagination({ served: 10, limit: 10, offset: 0, total: null })
    expect(p.more_available).toBe(true)
    expect(p.next_cursor).not.toBeNull()
  })

  it('total:null with an under-full page is honestly the last page', () => {
    const p = buildHonestPagination({ served: 3, limit: 10, offset: 0, total: null })
    expect(p.more_available).toBe(false)
    expect(p.next_cursor).toBeNull()
  })

  it('INVARIANT: more_available === true implies a non-null working cursor (fuzz)', () => {
    for (let served = 0; served <= 60; served += 7) {
      for (const limit of [10, 50, 200]) {
        for (const total of [null, 0, 14, served, served + 1, 7014]) {
          for (const offset of [0, 100]) {
            const p = buildHonestPagination({ served, limit, offset, total })
            if (p.more_available) {
              expect(p.next_cursor, `served=${served} limit=${limit} total=${total} offset=${offset}`).not.toBeNull()
              expect(decodeCursor(p.next_cursor)).toBe(offset + served)
            } else {
              expect(p.next_cursor).toBeNull()
            }
          }
        }
      }
    }
  })
})

describe('WP-1.5 cursor round-trip', () => {
  it('encode → decode is identity for the offset', () => {
    for (const n of [0, 1, 200, 13364, 585710]) {
      expect(decodeCursor(encodeCursor(n))).toBe(n)
    }
  })
  it('decode of malformed / null input is null (never throws)', () => {
    expect(decodeCursor(null)).toBeNull()
    expect(decodeCursor(undefined)).toBeNull()
    expect(decodeCursor('not-base64-$$$')).toBeNull()
    expect(decodeCursor(Buffer.from('{"nope":1}', 'utf8').toString('base64'))).toBeNull()
  })
})

describe('WP-1.5 buildRetrievalEnvelope — more_available always present', () => {
  it('legacy envelope emits more_available (never a silent absent field)', () => {
    const env = buildRetrievalEnvelope({
      tool: 't', content: {},
      pagination: buildHonestPagination({ served: 200, limit: 200, offset: 0, total: 7014 }),
    })
    expect(env.pagination.more_available).toBe(true)
    expect(env.pagination.next_cursor).not.toBeNull()
  })

  it('derives more_available when caller passes only total+limit (no explicit flag)', () => {
    const env = buildRetrievalEnvelope({
      tool: 't', content: {},
      pagination: { offset: 0, limit: 200, total: 7014 },
    })
    expect(env.pagination.more_available).toBe(true)
  })

  it('a fully-served page derives more_available:false', () => {
    const env = buildRetrievalEnvelope({
      tool: 't', content: {},
      pagination: { offset: 0, limit: 200, total: 12 },
    })
    expect(env.pagination.more_available).toBe(false)
  })
})
