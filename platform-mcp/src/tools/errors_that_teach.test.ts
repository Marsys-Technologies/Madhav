/**
 * errors_that_teach.test.ts — D-2 Lane V-3, CR-7 CLASS (ledger row 24).
 */
import { describe, it, expect } from 'vitest'
import {
  buildTeachingError, reconcileVocabulary,
  YOGA_CATALOG_DOMAINS, YOGA_DOMAIN_SYNONYMS,
} from './errors_that_teach.js'

describe('buildTeachingError', () => {
  it('carries a concrete corrected_call', () => {
    const e = buildTeachingError('ref_yogas_get', 'domain=wealth returns 0 rows',
      { domain: 'dhana' }, 'Retry with domain="dhana".', { domain: YOGA_CATALOG_DOMAINS })
    expect(e.ok).toBe(false)
    expect(e.corrected_call).toEqual({ tool: 'ref_yogas_get', params: { domain: 'dhana' } })
    expect(e.vocabulary?.domain).toContain('dhana')
  })
  it('emits null corrected_call when no fix is derivable', () => {
    const e = buildTeachingError('t', 'bad', null, 'hint')
    expect(e.corrected_call).toBeNull()
  })
})

describe('reconcileVocabulary — ref_yogas_get domain trap (§B.5)', () => {
  it('maps wealth → dhana via synonyms', () => {
    const r = reconcileVocabulary('wealth', YOGA_CATALOG_DOMAINS, YOGA_DOMAIN_SYNONYMS)
    expect(r.matched).toBe(false)
    expect(r.stored_value).toBe('dhana')
  })
  it('accepts an exact stored term', () => {
    const r = reconcileVocabulary('dhana', YOGA_CATALOG_DOMAINS, YOGA_DOMAIN_SYNONYMS)
    expect(r.matched).toBe(true)
    expect(r.stored_value).toBe('dhana')
  })
  it('maps career → raja', () => {
    expect(reconcileVocabulary('career', YOGA_CATALOG_DOMAINS, YOGA_DOMAIN_SYNONYMS).stored_value).toBe('raja')
  })
  it('token-affinity routes "raj yoga" toward raja', () => {
    const r = reconcileVocabulary('raj', YOGA_CATALOG_DOMAINS)
    expect(r.suggestions).toContain('raja')
  })
  it('returns suggestions even for an unmappable value', () => {
    const r = reconcileVocabulary('zzz_nonsense', YOGA_CATALOG_DOMAINS)
    expect(r.matched).toBe(false)
    expect(Array.isArray(r.suggestions)).toBe(true)
  })
})
