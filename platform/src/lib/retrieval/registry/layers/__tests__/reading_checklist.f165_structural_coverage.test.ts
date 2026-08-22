/**
 * reading_checklist.f165_structural_coverage.test.ts — F-165 (PARIŚEṢA-V4) regression.
 *
 * THE DEFECT: F-57 fixed VOCABULARY correctness (`SHASTRA_MAP['general'].signal_domain ===
 * 'general'`, and `'general'` IS a member of `CANONICAL_DOMAINS`), so `domain_resolution.
 * is_exact`/`is_canonical` correctly read true for it and neither F-57 flag fires. But
 * `bodha_msr_signals` carries ZERO rows tagged 'general' on the canonical chart
 * (482012f1-710e-4a25-994a-93821f5871aa — live-verified 2026-08-22), and `bodha_mechanisms.
 * domains_affected_array` covers only 1 of the 13 canonical domains ('wealth', 5 rows) — so
 * `afflictions_empty` read as a genuine all-clear when it was actually structural
 * non-coverage. Vocabulary-exactness and population are two different axes; conflating them
 * is the defect (CLAUDE.md §N.6).
 *
 * `fetchDomainStructuralCoverage` closes this: a REAL live count against both source tables,
 * every call — never a hardcoded list of known-empty domains (§N.7 item 3 / §N.8, which a
 * hardcoded list would itself violate).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

import { fetchDomainStructuralCoverage } from '../reading_checklist'
import { CANONICAL_DOMAINS } from '@/lib/domain_vocabulary'
import { SHASTRA_MAP } from '../register_d9_judgment'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'

beforeEach(() => {
  queryMock.mockReset()
})

describe('F-165 — fetchDomainStructuralCoverage: population, not vocabulary', () => {
  it("a zero-coverage domain (both tables empty, e.g. 'general' live on 482012f1) is flagged structurally_unpopulated", async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 0, mech_count: 0, mech_domain_coverage: 1 }] })
    const result = await fetchDomainStructuralCoverage(CHART, AYA, SHASTRA_MAP['general']!.signal_domain)
    expect(result.available).toBe(true)
    expect(result.msr_signals).toBe(0)
    expect(result.mechanisms).toBe(0)
    expect(result.structurally_unpopulated).toBe(true)
    expect(result.mechanisms_domain_coverage).toBe(1)
    expect(result.total_canonical_domains).toBe(CANONICAL_DOMAINS.length)
  })

  it('the can-read-false half: a domain populated in bodha_msr_signals (any valence) is NOT structurally_unpopulated even with zero mechanisms rows — proves the two cases are distinguished', async () => {
    // Mirrors a domain like 'career' (15198 msr rows, 0 mechanisms rows live) — populated in
    // one store is enough to disprove "never populated"; afflictions_empty may still fire
    // separately (malefic-only subset), but NOT alongside domain_structurally_unpopulated.
    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 15198, mech_count: 0, mech_domain_coverage: 1 }] })
    const result = await fetchDomainStructuralCoverage(CHART, AYA, 'career')
    expect(result.structurally_unpopulated).toBe(false)
    expect(result.msr_signals).toBe(15198)
    expect(result.mechanisms).toBe(0)
  })

  it('a domain populated ONLY in mechanisms (msr=0, mech>0) is also NOT structurally_unpopulated — both must be zero', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 0, mech_count: 5, mech_domain_coverage: 1 }] })
    const result = await fetchDomainStructuralCoverage(CHART, AYA, 'wealth')
    expect(result.structurally_unpopulated).toBe(false)
  })

  it('reports mechanisms_domain_coverage against the full 13-domain vocabulary regardless of the queried domain (always-present disclosure, §N.8)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 100, mech_count: 0, mech_domain_coverage: 1 }] })
    const result = await fetchDomainStructuralCoverage(CHART, AYA, 'health')
    expect(result.available).toBe(true)
    expect(result.mechanisms_domain_coverage).toBe(1)
    expect(result.total_canonical_domains).toBe(13)
  })

  it('a query failure degrades to available:false (honest "could not measure"), never a fabricated zero or a fabricated populated claim', async () => {
    queryMock.mockRejectedValueOnce(new Error('connection reset'))
    const result = await fetchDomainStructuralCoverage(CHART, AYA, 'general')
    expect(result.available).toBe(false)
    expect(result.structurally_unpopulated).toBe(false)
    expect(result.msr_signals).toBe(0)
    expect(result.mechanisms).toBe(0)
  })

  it('queries bodha_msr_signals AND bodha_mechanisms scoped to chart_id/ayanamsha_id/domain — never a hardcoded domain list', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ msr_count: 0, mech_count: 0, mech_domain_coverage: 1 }] })
    await fetchDomainStructuralCoverage(CHART, AYA, 'general')
    expect(queryMock).toHaveBeenCalledTimes(1)
    const [sql, params] = queryMock.mock.calls[0]!
    expect(sql).toContain('bodha_msr_signals')
    expect(sql).toContain('bodha_mechanisms')
    expect(sql).not.toMatch(/'general'|'travel'|'residence'/) // no domain literal baked into the SQL text
    expect(params).toEqual([CHART, AYA, 'general'])
  })
})

describe('F-165 — the flag code is registered in the closed envelope vocabulary', () => {
  it('domain_structurally_unpopulated is emittable', async () => {
    const { judgmentFlag } = await import('../../../envelope')
    const flag = judgmentFlag('domain_structurally_unpopulated', 'detail')
    expect(flag).toEqual({ code: 'domain_structurally_unpopulated', detail: 'detail' })
  })
})
