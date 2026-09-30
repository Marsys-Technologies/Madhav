import { describe, it, expect } from 'vitest'
import { errorFromThroughput } from '../throughputError'

/**
 * Packet B1 — R-2 (review B1_rereview_20260926T190244Z.md, "THE BIG ONE").
 *
 * The direct, mutation-proof unit test for the fix: `errorFromThroughput` must
 * surface `tp.last_error` when `tp.state === 'error'`, and must NOT pass a stale
 * `last_error` through for any other state (measured live: exactly one production
 * row, bg_transit_engine, is state='lit' with a stale never-cleared last_error —
 * an unconditional pass-through would have flipped it to a false 'error').
 *
 * Mutation-checked: reverting to `return null` (the pre-fix behaviour) fails
 * `surfaces last_error when state is error`. Reverting to an unconditional
 * `return tp?.last_error ?? null` (the pass-through that was tried and rejected)
 * fails `does not surface a stale last_error when state is not error`.
 */
describe('errorFromThroughput (Packet B1, R-2)', () => {
  it('surfaces last_error when state is error — this IS the fix', () => {
    expect(errorFromThroughput({
      state: 'error', last_built_at: '2026-08-21T02:36:53Z', rows_written: 112270,
      last_error: 'BLOCKED: upstream dependency(ies) mi_gunanaka did not complete in this run; skipped to avoid building on incomplete data',
    })).toBe('BLOCKED: upstream dependency(ies) mi_gunanaka did not complete in this run; skipped to avoid building on incomplete data')
  })

  it('does not surface a stale last_error when state is not error (the bg_transit_engine regression this gate prevents)', () => {
    expect(errorFromThroughput({
      state: 'lit', last_built_at: '2026-01-01T00:00:00Z', rows_written: 500,
      last_error: 'ForeignKeyViolation: update or delete on table "bg_transit_rules" violates foreign key constraint',
    })).toBeNull()
  })

  it('returns null when last_error is itself null even though state is error', () => {
    expect(errorFromThroughput({ state: 'error', last_built_at: null, rows_written: null, last_error: null })).toBeNull()
  })

  it('returns null for dormant/stale/building states regardless of last_error content', () => {
    for (const state of ['dormant', 'stale', 'building', 'incomplete']) {
      expect(errorFromThroughput({ state, last_built_at: null, rows_written: 0, last_error: 'some text' })).toBeNull()
    }
  })

  it('returns null when tp itself is undefined (no throughput row at all)', () => {
    expect(errorFromThroughput(undefined)).toBeNull()
  })
})
