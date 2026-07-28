/**
 * SAMĪKṢĀ transition-matrix unit tests (pure, no DB) — PB-3 lane L-1.
 *
 * Proves the ONE legal-transition matrix rejects illegal moves and admits legal ones. This is
 * a real check, not a self-agreeing mock: it enumerates EVERY (from × to) pair over the 9-state
 * enum and asserts the matrix's verdict matches the explicitly-listed legal set — so a typo
 * that silently widened or narrowed LEGAL_TRANSITIONS would fail here.
 */

import { describe, it, expect } from 'vitest'
import {
  LIFECYCLE_STATES,
  LEGAL_TRANSITIONS,
  type LifecycleState,
} from '../schema'
import { isLegalTransition, assertLegalTransition, isTerminal, IllegalTransitionError } from '../transitions'

describe('SAMĪKṢĀ lifecycle transition matrix', () => {
  it('enumerates exactly 9 lifecycle states (brief names 9 tokens under an "8-state" label)', () => {
    expect(LIFECYCLE_STATES).toHaveLength(9)
    expect(new Set(LIFECYCLE_STATES).size).toBe(9)
  })

  it('every (from × to) pair matches the explicitly-listed legal set', () => {
    for (const from of LIFECYCLE_STATES) {
      for (const to of LIFECYCLE_STATES) {
        const legal = LEGAL_TRANSITIONS[from].includes(to)
        expect(isLegalTransition(from, to)).toBe(legal)
      }
    }
  })

  it('admits the core progression detected→confirmed→open→window_closed→outcome_recorded', () => {
    const chain: LifecycleState[] = ['detected', 'confirmed', 'open', 'window_closed', 'outcome_recorded']
    for (let i = 0; i < chain.length - 1; i++) {
      expect(isLegalTransition(chain[i], chain[i + 1])).toBe(true)
    }
  })

  it('admits the documented exit + aging transitions', () => {
    expect(isLegalTransition('detected', 'dismissed')).toBe(true)
    expect(isLegalTransition('detected', 'lapsed_unconfirmed')).toBe(true)
    expect(isLegalTransition('window_closed', 'unverifiable')).toBe(true)
    expect(isLegalTransition('window_closed', 'lapsed')).toBe(true)
  })

  it('REJECTS illegal jumps (the acceptance instrument)', () => {
    // The task's own example: detected → outcome_recorded is illegal.
    expect(isLegalTransition('detected', 'outcome_recorded')).toBe(false)
    expect(isLegalTransition('detected', 'open')).toBe(false)
    expect(isLegalTransition('open', 'outcome_recorded')).toBe(false) // must close the window first
    expect(isLegalTransition('window_closed', 'confirmed')).toBe(false) // no going back
    expect(isLegalTransition('confirmed', 'confirmed')).toBe(false) // self-loop is not legal
  })

  it('assertLegalTransition throws IllegalTransitionError on an illegal move', () => {
    expect(() => assertLegalTransition('detected', 'outcome_recorded')).toThrow(IllegalTransitionError)
    // ...and does NOT throw on a legal one.
    expect(() => assertLegalTransition('detected', 'confirmed')).not.toThrow()
  })

  it('all five exit states are terminal (no outbound transitions)', () => {
    for (const t of ['outcome_recorded', 'dismissed', 'lapsed', 'unverifiable', 'lapsed_unconfirmed'] as const) {
      expect(isTerminal(t)).toBe(true)
      expect(() => assertLegalTransition(t, 'confirmed')).toThrow(IllegalTransitionError)
    }
  })
})
