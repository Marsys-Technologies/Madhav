import { describe, expect, it } from 'vitest'
import {
  canonicalNirmanaConductorRequestDigest,
  NIRMANA_CONDUCTOR_PRINCIPAL,
  NIRMANA_CONDUCTOR_SCOPE,
  NIRMANA_VERIFIER_PRINCIPAL,
} from '../conductor'

describe('Nirmana non-browser conductor contract', () => {
  it('keeps worker identities separate and the scope bounded to T0/F0/L0', () => {
    expect(NIRMANA_CONDUCTOR_PRINCIPAL).not.toEqual(NIRMANA_VERIFIER_PRINCIPAL)
    expect(NIRMANA_CONDUCTOR_SCOPE).toBe('T0,F0,L0')
    expect(NIRMANA_CONDUCTOR_PRINCIPAL).not.toContain('monitor')
    expect(NIRMANA_VERIFIER_PRINCIPAL).not.toContain('monitor')
  })

  it('creates a stable audit digest for the exact server request shape', () => {
    expect(canonicalNirmanaConductorRequestDigest({ command: 'evaluate' }))
      .toBe(canonicalNirmanaConductorRequestDigest({ command: 'evaluate' }))
    expect(canonicalNirmanaConductorRequestDigest({ command: 'evaluate' }))
      .not.toBe(canonicalNirmanaConductorRequestDigest({ command: 'verify_readiness' }))
  })
})
