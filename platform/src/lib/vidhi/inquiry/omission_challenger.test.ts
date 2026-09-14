import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { challengeInquirySelection } from './omission_challenger'

describe('independent omission challenger', () => {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-14T00:00:00.000Z')

  it('finds both rule-required and graph-required omissions independently', () => {
    const result = challengeInquirySelection({
      snapshot,
      question: 'Give me a complete wealth outlook',
      scope: {
        intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive',
        horizon: 'multi_year', intervention: false, entitlement: 'native',
      },
      selected_scu_ids: ['scu.finance.prosperity_assessment'],
    })

    expect(result.findings.some((finding) => finding.rule_id === 'OMIT-INHIBITOR')).toBe(true)
    expect(result.findings.some((finding) => finding.source === 'graph'
      && finding.missing_scu_id === 'scu.bodha.mechanism.network')).toBe(true)
    expect(result.challenge_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
  })

  it('is deterministic and emits no finding for already selected targets', () => {
    const selected = snapshot.scus.map((scu) => scu.scu_id)
    const scope = {
      intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive',
      horizon: 'multi_year', intervention: false, entitlement: 'native',
    } as const
    const first = challengeInquirySelection({
      snapshot,
      question: 'complete wealth outlook',
      scope,
      selected_scu_ids: selected,
    })
    const second = challengeInquirySelection({
      snapshot,
      question: 'complete wealth outlook',
      scope,
      selected_scu_ids: [...selected].reverse(),
    })

    expect(first.findings).toEqual([])
    expect(second.challenge_hash).toBe(first.challenge_hash)
  })
})
