import { describe, expect, it } from 'vitest'

import { classifyQuery } from '@/lib/pariprashna/safety/classifier'
import { CORPUS_FIXTURES, CORPUS_FIXTURE_SET_VERSION } from '../fixtures'
import { QUERY_CLASSES } from '../types'

describe('corpus fixtures', () => {
  it('covers all 12 query classes, each with at least one fixture', () => {
    const classesCovered = new Set(CORPUS_FIXTURES.map((f) => f.queryClass))
    for (const cls of QUERY_CLASSES) {
      expect(classesCovered.has(cls)).toBe(true)
    }
    expect(classesCovered.size).toBe(QUERY_CLASSES.length)
  })

  it('has exactly 60 fixtures (5 per class × 12 classes, the test plan §7 floor — v2, 2026-08-28)', () => {
    expect(CORPUS_FIXTURES).toHaveLength(60)
  })

  it('every query class has at least 5 fixtures (test plan §7 qualification floor)', () => {
    for (const cls of QUERY_CLASSES) {
      const count = CORPUS_FIXTURES.filter((f) => f.queryClass === cls).length
      expect(count, `query class '${cls}' has ${count} fixtures, floor is 5`).toBeGreaterThanOrEqual(5)
    }
  })

  it('every fixture is schema-valid: id, version, grounding note, non-empty query text', () => {
    for (const f of CORPUS_FIXTURES) {
      expect(f.fixtureId.length).toBeGreaterThan(0)
      expect(f.fixtureVersion).toBeGreaterThanOrEqual(1)
      expect(f.queryText.trim().length).toBeGreaterThan(0)
      expect(f.chartId.length).toBeGreaterThan(0)
      expect(f.groundingNote.trim().length).toBeGreaterThan(20)
      expect(['web', 'mcp', 'both']).toContain(f.expected.door)
      expect(typeof f.expected.runnable).toBe('boolean')
      if (!f.expected.runnable) {
        expect(f.expected.notRunnableReason?.length ?? 0).toBeGreaterThan(0)
      }
    }
  })

  it('fixture ids are unique', () => {
    const ids = CORPUS_FIXTURES.map((f) => f.fixtureId)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('CORPUS_FIXTURE_SET_VERSION is a positive integer (versioning discipline, CLAUDE.md §I B.8)', () => {
    expect(Number.isInteger(CORPUS_FIXTURE_SET_VERSION)).toBe(true)
    expect(CORPUS_FIXTURE_SET_VERSION).toBeGreaterThanOrEqual(1)
  })

  describe('sensitive fixtures — deliberately verified against the real safety classifier', () => {
    it('every sensitive-class fixture\'s recorded expectation matches what the classifier actually returns today', () => {
      const sensitiveFixtures = CORPUS_FIXTURES.filter((f) => f.queryClass === 'sensitive')
      expect(sensitiveFixtures.length).toBeGreaterThanOrEqual(5)
      for (const fixture of sensitiveFixtures) {
        const result = classifyQuery({ queryText: fixture.queryText })
        // The fixture's own recorded expectation must match what the classifier actually does —
        // this is the "checked against the classifier before being committed" proof, for every
        // sensitive fixture, not just the original.
        expect(
          result.classes,
          `fixture '${fixture.fixtureId}' classifier drift: recorded expectedSafetyClasses no longer matches classifyQuery()`,
        ).toEqual(fixture.expected.expectedSafetyClasses ?? [])
        expect(result.severity).toBe(fixture.expected.expectedSafetySeverity)
      }
    })

    it('at least one sensitive fixture still exercises the original HS-4 mortality-window path', () => {
      const fixture = CORPUS_FIXTURES.find((f) => f.fixtureId === 'sensitive-001-ayurdaya-longevity')
      expect(fixture).toBeDefined()
      const result = classifyQuery({ queryText: fixture!.queryText })
      expect(result.classes).toContain('hs4_mortality_window')
      expect(result.severity).toBe('review_required')
    })

    it('every non-sensitive-class fixture is confirmed clean — no accidental safety trigger', () => {
      const nonSensitive = CORPUS_FIXTURES.filter((f) => f.queryClass !== 'sensitive')
      expect(nonSensitive.length).toBe(CORPUS_FIXTURES.length - 5)
      for (const f of nonSensitive) {
        const result = classifyQuery({ queryText: f.queryText })
        expect(result.classes, `fixture '${f.fixtureId}' unexpectedly triggered safety detection`).toEqual([])
        expect(result.severity).toBe('none')
      }
    })
  })

  describe('cross-domain contradiction fixture — grounded in a real, already-documented finding', () => {
    it('cites SIG.MSR.413, the real UCN_v4_0 §IX.2 Contradiction 2 signal', () => {
      const fixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'cross_domain_contradiction')
      expect(fixture).toBeDefined()
      expect(fixture!.expected.expectedSignalRefs).toEqual(['SIG.MSR.413'])
      expect(fixture!.groundingNote).toContain('SIG.MSR.413')
    })
  })

  describe('door_parity fixture — honestly marked not runnable', () => {
    it('is not runnable, with a reason naming the G4-B dependency', () => {
      const fixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'door_parity')
      expect(fixture).toBeDefined()
      expect(fixture!.expected.runnable).toBe(false)
      expect(fixture!.expected.notRunnableReason).toContain('G4-B')
    })
  })
})
