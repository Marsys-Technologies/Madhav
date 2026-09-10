/**
 * receipt/hash.test.ts — lane G3-A (PPR-01).
 *
 * `computeReceiptHash` determinism + sensitivity: the same content hashes
 * identically regardless of key order (stable), and a real content change
 * changes the hash (sensitive) — both proven, not asserted by convention.
 */
import { describe, it, expect } from 'vitest'

import { computeReceiptHash } from '../hash'

describe('computeReceiptHash', () => {
  it('is stable across key-order permutations of the same content', () => {
    const a = { turn_id: 't1', chart_id: 'c1', facts: ['SIG.MSR.001', 'SIG.MSR.002'] }
    const b = { chart_id: 'c1', facts: ['SIG.MSR.001', 'SIG.MSR.002'], turn_id: 't1' }
    expect(computeReceiptHash(a)).toBe(computeReceiptHash(b))
  })

  it('is stable across repeated calls on an unchanged object', () => {
    const content = { turn_id: 't1', nested: { a: 1, b: [1, 2, 3] } }
    const h1 = computeReceiptHash(content)
    const h2 = computeReceiptHash(content)
    expect(h1).toBe(h2)
  })

  it('changes when a real content field changes (demonstrated, not assumed)', () => {
    const before = { turn_id: 't1', served: 3, floor_item_total: 6 }
    const after = { turn_id: 't1', served: 4, floor_item_total: 6 }
    expect(computeReceiptHash(before)).not.toBe(computeReceiptHash(after))
  })

  it('changes when an array element changes', () => {
    const before = { facts: ['SIG.MSR.001', 'SIG.MSR.002'] }
    const after = { facts: ['SIG.MSR.001', 'SIG.MSR.003'] }
    expect(computeReceiptHash(before)).not.toBe(computeReceiptHash(after))
  })

  it('produces a 64-char hex sha256 digest', () => {
    const h = computeReceiptHash({ x: 1 })
    expect(h).toMatch(/^[0-9a-f]{64}$/)
  })
})
