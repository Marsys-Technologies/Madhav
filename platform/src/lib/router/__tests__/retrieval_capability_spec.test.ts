import { describe, it, expect } from 'vitest'
import {
  DOMAIN_VARGA_MAP,
  getDomainVargas,
  RETRIEVAL_CAPABILITY_SPEC,
  getCapability,
} from '../retrieval_capability_spec'

describe('VARGA-ETL-FULL-S1 D18: DOMAIN_VARGA_MAP', () => {
  it('career_dharma mandatory contains both D10 and D9', () => {
    const entry = DOMAIN_VARGA_MAP.career_dharma
    expect(entry).toBeDefined()
    expect(entry.mandatory).toContain('D10')
    expect(entry.mandatory).toContain('D9')
  })

  it('moksha resolves to D20 mandatory with D9 + D60 secondary', () => {
    const entry = DOMAIN_VARGA_MAP.moksha
    expect(entry.mandatory).toEqual(['D20'])
    expect(entry.secondary).toContain('D9')
    expect(entry.secondary).toContain('D60')
  })

  it('vehicles_comforts resolves to D16 mandatory + D9 secondary', () => {
    const entry = DOMAIN_VARGA_MAP.vehicles_comforts
    expect(entry.mandatory).toEqual(['D16'])
    expect(entry.secondary).toEqual(['D9'])
  })

  it('partner aliases marriage to D9', () => {
    expect(DOMAIN_VARGA_MAP.partner.mandatory).toContain('D9')
  })

  it('health_longevity is D30 mandatory', () => {
    expect(DOMAIN_VARGA_MAP.health_longevity.mandatory).toContain('D30')
  })

  it('past_karma is D60 mandatory with D45 + D9 secondary', () => {
    const entry = DOMAIN_VARGA_MAP.past_karma
    expect(entry.mandatory).toEqual(['D60'])
    expect(entry.secondary).toContain('D45')
    expect(entry.secondary).toContain('D9')
  })

  it('auspiciousness is D40 mandatory', () => {
    expect(DOMAIN_VARGA_MAP.auspiciousness.mandatory).toEqual(['D40'])
  })

  it('purity is D45 mandatory', () => {
    expect(DOMAIN_VARGA_MAP.purity.mandatory).toEqual(['D45'])
  })

  it('getDomainVargas returns undefined for unknown domains', () => {
    expect(getDomainVargas('not_a_real_domain')).toBeUndefined()
  })

  it('cross_varga_dignity_query is registered in the capability spec', () => {
    const cap = getCapability('cross_varga_dignity_query')
    expect(cap).toBeDefined()
    expect(RETRIEVAL_CAPABILITY_SPEC.length).toBeGreaterThanOrEqual(18)
  })
})
