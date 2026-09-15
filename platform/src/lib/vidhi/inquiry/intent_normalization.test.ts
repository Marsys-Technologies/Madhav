import { describe, expect, it } from 'vitest'
import { normalizeInquiryScope } from './intent_normalization'

describe('inquiry scope normalization', () => {
  it('canonicalizes classifier aliases into one semantic scope', () => {
    const result = normalizeInquiryScope({
      intent: ' DOMAIN-ASSESSMENT ',
      domains: ['Money', 'WEALTH', ' finance '],
      width: 'BROAD',
      depth: 'Deep',
      horizon: 'far',
      intervention: 'None',
      entitlement: 'REFERENCE',
    })

    expect(result.scope).toEqual({
      intent: 'wealth_deepdive',
      domains: ['wealth'],
      width: 'panoramic',
      depth: 'deepdive',
      horizon: 'multi_year',
      intervention: false,
      entitlement: 'public_disclosed',
    })
    expect(result.receipt.normalization_version).toBe('inquiry-scope-normalization-v1')
    expect(result.receipt.applied_rules).toContain('intent:domain_assessment+wealth+deepdive->wealth_deepdive')
  })

  it('is stable across case, aliases, duplicates, and input order', () => {
    const first = normalizeInquiryScope({
      intent: 'domain_assessment', domains: ['job', 'career'], width: 'wide', depth: 'in-depth',
      horizon: 'near', intervention: 'NONE', entitlement: 'native',
    })
    const second = normalizeInquiryScope({
      intent: 'DOMAIN ASSESSMENT', domains: ['CAREER'], width: 'panoramic', depth: 'deepdive',
      horizon: 'present', intervention: false, entitlement: 'NATIVE',
    })

    expect(first.scope).toEqual(second.scope)
    expect(first.scope.intent).toBe('career_deepdive')
  })

  it('never broadens a restricted entitlement', () => {
    const result = normalizeInquiryScope({
      intent: 'chart_overview', domains: ['general'], width: 'standard', depth: 'standard',
      horizon: 'atemporal', intervention: false, entitlement: 'restricted',
    })
    expect(result.scope.entitlement).toBe('restricted')
  })
})
