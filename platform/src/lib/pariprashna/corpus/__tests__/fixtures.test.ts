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

  it('has exactly 12 fixtures (one per class, per the roadmap)', () => {
    expect(CORPUS_FIXTURES).toHaveLength(12)
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

  describe('sensitive fixture — deliberately verified against the real safety classifier', () => {
    it('the sensitive fixture actually triggers the expected HS-4 classification', () => {
      const fixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'sensitive')
      expect(fixture).toBeDefined()
      const result = classifyQuery({ queryText: fixture!.queryText })
      expect(result.classes).toContain('hs4_mortality_window')
      expect(result.severity).toBe('review_required')
      // The fixture's own recorded expectation must match what the classifier actually does —
      // this is the "checked against the classifier before being committed" proof.
      expect(fixture!.expected.expectedSafetyClasses).toEqual(['hs4_mortality_window'])
      expect(fixture!.expected.expectedSafetySeverity).toBe('review_required')
    })

    it('every OTHER fixture is confirmed clean — no accidental safety trigger', () => {
      const nonSensitive = CORPUS_FIXTURES.filter((f) => f.queryClass !== 'sensitive')
      expect(nonSensitive.length).toBe(11)
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
