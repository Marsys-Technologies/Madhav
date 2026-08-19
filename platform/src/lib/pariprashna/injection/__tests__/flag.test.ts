/**
 * Lane G1-G — the flag ships OFF, and that is asserted rather than assumed.
 *
 * The P1 pre-authorization note's whole premise is that merging a lane cannot
 * alter production behaviour. A default that silently flipped to `true` in a
 * future edit would void that premise for every control in this directory at
 * once, so it gets its own detector (§N.8).
 */
import { describe, it, expect } from 'vitest'

import { DEFAULT_FLAGS } from '@/lib/config/feature_flags'
import { INJECTION_CONTAINMENT_FLAG } from '../flag'

describe('PARIPRASHNA_INJECTION_CONTAINMENT', () => {
  it('is declared in DEFAULT_FLAGS', () => {
    expect(Object.keys(DEFAULT_FLAGS)).toContain(INJECTION_CONTAINMENT_FLAG)
  })

  it('defaults to FALSE — the lane ships dark', () => {
    expect(DEFAULT_FLAGS[INJECTION_CONTAINMENT_FLAG]).toBe(false)
  })

  it('is a DIFFERENT flag from the safety gate — the two must arm independently', () => {
    // They share the pre-wire pass but arm different pattern classes. Collapsing
    // them into one flag is what `mortalityRulesEnabled` exists to prevent.
    expect(INJECTION_CONTAINMENT_FLAG).not.toBe('PARIPRASHNA_SAFETY_GATE_ENABLED')
  })
})
