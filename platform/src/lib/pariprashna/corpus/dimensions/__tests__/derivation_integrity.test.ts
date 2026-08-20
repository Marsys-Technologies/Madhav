import { describe, expect, it } from 'vitest'

import { baseObservation, baseReceipt } from '../../__tests__/test_helpers'
import { scoreDerivationIntegrity } from '../derivation_integrity'

describe('scoreDerivationIntegrity', () => {
  it('scores 1.0 when every derivation_chains ref resolves in facts_consumed', () => {
    const result = scoreDerivationIntegrity(baseObservation())
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
    expect(result.findings).toEqual([])
  })

  it('flags and lowers score when a block cites a ref absent from facts_consumed', () => {
    const receipt = baseReceipt({
      derivation_chains: [
        { block_id: 'blk-1-1', pass_id: 1, role: 'prose', fact_refs: ['SIG.MSR.413'] },
        { block_id: 'blk-1-2', pass_id: 1, role: 'prose', fact_refs: ['SIG.MSR.999'] }, // not in facts_consumed
      ],
    })
    const result = scoreDerivationIntegrity(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(0.5)
    expect(result.findings.some((f) => f.includes('SIG.MSR.999'))).toBe(true)
  })

  it('flags the silent-empty defect: facts_consumed populated but no block cites anything', () => {
    const receipt = baseReceipt({ derivation_chains: [] })
    const result = scoreDerivationIntegrity(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(0)
    expect(result.findings.length).toBeGreaterThan(0)
  })

  it('returns not_yet_measurable when no receipt was supplied', () => {
    const result = scoreDerivationIntegrity(baseObservation({ receipt: null }))
    expect(result.status).toBe('not_yet_measurable')
    expect(result.score).toBeNull()
    expect(result.reason).toBeTruthy()
  })
})
