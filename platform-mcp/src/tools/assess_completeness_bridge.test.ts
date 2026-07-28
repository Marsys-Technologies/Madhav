/**
 * assess_completeness_bridge.test.ts — PARIŚODHANA B2 (Reachability Triangle, T1-1).
 * ================================================================================
 * VERIFY (do NOT rebuild) the shipped assess_* → dossier bridge. The "named bridge that
 * no document owns" — assess_wealth/assess_career folding the dossier's 100%-accounted
 * completeness block into their response — landed in PRs #782 (Elevation α) and #797/#799
 * (SATYA-ŚEṢA W7). This test locks it so a later refactor cannot silently regress it.
 *
 * Pure: runDossier is a no-I/O function over the precompiled wealth/career slices for the
 * two canonical charts — no DB, no network (see registry_bridge.ts's own note).
 *
 * §N.6 (Serving Density Principle): the completeness block layers coverage by state
 * (served / empty_for_this_chart / not_computed_globally / …) and never flattens the
 * territory into one undifferentiated count — asserted below.
 */
import { describe, it, expect } from 'vitest'
import { assembleDomainCompleteness, attachDomainCompleteness } from './registry_bridge.js'

const CANON = '482012f1-710e-4a25-994a-93821f5871aa'

describe('assess_* domain-completeness bridge (verify, not rebuild)', () => {
  it.each([['wealth'], ['career']])(
    'assembleDomainCompleteness(%j) reaches 100%%-accounted, synthesis_gate OPEN',
    (domain) => {
      const c = assembleDomainCompleteness(domain, CANON)
      expect(c).not.toBeNull()
      expect(c!['fully_accounted']).toBe(true)
      expect(c!['synthesis_gate']).toBe('OPEN')
      expect(c!['pct']).toBe(100)
      expect(Array.isArray(c!['coverage_map'])).toBe(true)
      expect((c!['coverage_map'] as unknown[]).length).toBeGreaterThan(0)
      // §N.6: coverage is layered by state, never flattened to a single number.
      const byState = c!['coverage_by_state'] as Record<string, number>
      expect(byState).toBeDefined()
      expect(Object.keys(byState)).toEqual(
        expect.arrayContaining([
          'served',
          'empty_for_this_chart',
          'not_computed_globally',
          'superseded_by_aggregate',
          'excluded_by_named_rule',
        ]),
      )
    },
  )

  it('attachDomainCompleteness mutates a response in place with the domain_completeness block', () => {
    const response: Record<string, unknown> = { verdict: 'stub' }
    attachDomainCompleteness(response, 'wealth', CANON)
    expect(response['domain_completeness']).toBeDefined()
    const c = response['domain_completeness'] as Record<string, unknown>
    expect(c['domain']).toBe('wealth')
    expect(c['fully_accounted']).toBe(true)
  })

  it('returns null for a domain with no precompiled slice (honest no-op, never a fabricated block)', () => {
    expect(assembleDomainCompleteness('wealth', 'no-such-chart-0000-0000-000000000000')).toBeNull()
  })
})
