/**
 * SS N-362/N-363: for EVERY school engine the signals argument has three explicit states.
 *   undefined  -> not supplied  -> honest not-available (reason no_live_signals)
 *   []         -> supplied empty -> the same honest not-available (never a computed zero score,
 *                                   never a silent default)
 *   non-empty  -> analysed from those signals only
 * Also covers the runner and the convergence consumers (unavailable schools are skipped, never
 * counted as agreement or in "n of 7", and the narrative says how many were available).
 */
import { describe, it, expect } from 'vitest'
import { parashari_engine } from '@/lib/schools/parashari_engine'
import { jaimini_engine } from '@/lib/schools/jaimini_engine'
import { tajika_engine } from '@/lib/schools/tajika_engine'
import { kp_engine } from '@/lib/schools/kp_engine'
import { nadi_engine } from '@/lib/schools/nadi_engine'
import { bnn_engine } from '@/lib/schools/bnn_engine'
import { yogini_engine } from '@/lib/schools/yogini_engine'
import { SYNTHETIC_CHART, SYNTHETIC_CHART_B } from '@/lib/schools/__fixtures__/synthetic_chart'
import { runSchoolsForDomain, runFullTriangulation } from '@/lib/schools/school_runner'
import { classifySignalSupply } from '@/lib/schools/engine_utils'
import type { SchoolAnalysis, SchoolName } from '@/lib/schools/types'
import { ALL_DOMAINS, ALL_SCHOOLS, liveSignals, liveSignalsForAll } from './_support'

const ENGINES: SchoolAnalysis[] = [
  parashari_engine, jaimini_engine, tajika_engine, kp_engine, nadi_engine, bnn_engine, yogini_engine,
]

describe('classifySignalSupply', () => {
  it('distinguishes the three states', () => {
    expect(classifySignalSupply(undefined)).toBe('not_supplied')
    expect(classifySignalSupply(null)).toBe('not_supplied')
    expect(classifySignalSupply([])).toBe('supplied_empty')
    expect(classifySignalSupply(liveSignals(3, 1))).toBe('supplied')
  })
})

describe.each(ENGINES.map(e => [e.school, e] as const))('engine %s: three signal states', (_name, engine) => {
  for (const domain of ALL_DOMAINS) {
    it(`${domain}: undefined => not available`, async () => {
      const r = await engine.analyze(SYNTHETIC_CHART, domain)
      expect(r.school).toBe(engine.school)
      expect(r.domain).toBe(domain)
      expect(r.available).toBe(false)
      expect(r.unavailableReason).toBe('no_live_signals')
      expect(r.signalSupply).toBe('not_supplied')
      expect(r.domainScore).toBeNull()
      expect(r.direction).toBeNull()
      expect(r.topSignals).toEqual([])
      expect(r.signalCoverage).toBe('silent')
      expect(r.schoolVerdict).toContain('not available')
    })

    it(`${domain}: [] => not available (not a zero score, not a default)`, async () => {
      const r = await engine.analyze(SYNTHETIC_CHART, domain, [])
      expect(r.available).toBe(false)
      expect(r.unavailableReason).toBe('no_live_signals')
      expect(r.signalSupply).toBe('supplied_empty')
      expect(r.domainScore).toBeNull()
      expect(r.direction).toBeNull()
      expect(r.topSignals).toEqual([])
    })

    it(`${domain}: non-empty => analysed from the passed signals only`, async () => {
      const sigs = liveSignals(4.2)
      const r = await engine.analyze(SYNTHETIC_CHART, domain, sigs)
      expect(r.available).toBe(true)
      expect(r.signalSupply).toBe('supplied')
      expect(r.unavailableReason).toBeUndefined()
      expect(r.domainScore).not.toBeNull()
      expect(r.topSignals.length).toBeGreaterThan(0)
      for (const t of r.topSignals) {
        expect(sigs.map(s => s.signalId)).toContain(t.signalId)
      }
    })
  }

  it('score tracks the passed signals (no hidden preset): high > low', async () => {
    const hi = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(4.6))
    const lo = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(1.2))
    expect(hi.domainScore as number).toBeGreaterThan(lo.domainScore as number)
  })

  it('same signals on two different fictional charts give the same score', async () => {
    const a = await engine.analyze(SYNTHETIC_CHART, 'HEALTH', liveSignals(3.7))
    const b = await engine.analyze(SYNTHETIC_CHART_B, 'HEALTH', liveSignals(3.7))
    expect(a.domainScore).toBe(b.domainScore)
    expect(a.direction).toBe(b.direction)
  })

  it('supplied signals with zero total weight => not available (reason zero_signal_weight)', async () => {
    const r = await engine.analyze(SYNTHETIC_CHART, 'CAREER', [
      { signalId: 'SIG.TEST.Z', signalName: 'zero weight', score: 4, weight: 0 },
    ])
    expect(r.available).toBe(false)
    expect(r.unavailableReason).toBe('zero_signal_weight')
    expect(r.domainScore).toBeNull()
  })

  it('verdict carries no stored-chart facts', async () => {
    const r = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(3.5))
    for (const banned of ['Capricorn', 'exalted in Libra', 'Bhramari', 'Karakamsa in Gemini', 'FORENSIC']) {
      expect(r.schoolVerdict).not.toContain(banned)
    }
  })
})

describe('school_runner: three states per school and convergence consumers', () => {
  it('no liveSignals at all => every school not available; convergence NOT_AVAILABLE; no 7/7', async () => {
    const res = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER')
    expect(res.schoolResults).toHaveLength(7)
    expect(res.schoolResults.every(r => r.available === false)).toBe(true)
    const c = res.convergence
    expect(c.convergenceLevel).toBe('NOT_AVAILABLE')
    expect(c.schoolsAgreeing).toBe(0)
    expect(c.schoolsTotal).toBe(0)
    expect(c.schoolsAvailable).toBe(0)
    expect(c.schoolsEvaluated).toBe(7)
    expect(c.schoolsUnavailable.sort()).toEqual([...ALL_SCHOOLS].sort())
    expect(c.meanDomainScore).toBeNull()
    expect(c.stdDomainScore).toBeNull()
    expect(c.direction).toBe('not_available')
    expect(c.perSchoolScores).toEqual({})
    expect(res.weightedMeanScore).toBeNull()
    expect(res.weightedSchoolsAgreeing).toBe(0)
    expect(res.perSchoolWeighted).toEqual({})
    expect(c.convergenceNarrative).toContain('0 of 7 schools available')
    expect(c.convergenceNarrative).toContain('not available')
  })

  it('liveSignals with every school = [] reads exactly like all-undefined', async () => {
    const empties = Object.fromEntries(ALL_SCHOOLS.map(s => [s, []])) as Record<SchoolName, never[]>
    const a = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', { liveSignals: empties })
    const b = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER')
    expect(a.schoolResults.every(r => r.available === false && r.signalSupply === 'supplied_empty')).toBe(true)
    expect(b.schoolResults.every(r => r.available === false && r.signalSupply === 'not_supplied')).toBe(true)
    expect(a.convergence.convergenceLevel).toBe('NOT_AVAILABLE')
    expect(a.convergence.schoolsTotal).toBe(b.convergence.schoolsTotal)
    expect(a.weightedMeanScore).toBeNull()
  })

  it('mixed: 3 schools with signals, 1 with [], 3 absent => 3 of 7 available, unavailable ones not counted', async () => {
    const res = await runSchoolsForDomain(SYNTHETIC_CHART_B, 'CAREER', {
      liveSignals: {
        parashari: liveSignals(4.4),
        kp: liveSignals(4.0),
        jaimini: liveSignals(4.2),
        nadi: [],
      },
    })
    const c = res.convergence
    expect(c.schoolsEvaluated).toBe(7)
    expect(c.schoolsAvailable).toBe(3)
    expect(c.schoolsTotal).toBe(3)
    expect(c.schoolsAgreeing).toBe(3)
    expect([...c.schoolsUnavailable].sort()).toEqual(['bnn', 'nadi', 'tajika', 'yogini'])
    expect(Object.keys(c.perSchoolScores).sort()).toEqual(['jaimini', 'kp', 'parashari'])
    expect(c.convergenceLevel).toBe('LOW') // 3 agreeing is < 4; an honest small-n level, not 3/7 "agreement"
    expect(c.convergenceNarrative).toContain('3 of 7 schools available')
    expect(c.convergenceNarrative).toContain('3/3 counted schools')
    expect(c.convergenceNarrative).toContain('bnn')
    expect(Object.keys(res.perSchoolWeighted ?? {}).sort()).toEqual(['jaimini', 'kp', 'parashari'])
    expect(res.weightedSchoolsAgreeing).toBe(3)
  })

  it('weighted mean is renormalised over available schools (one school => its own score)', async () => {
    const res = await runSchoolsForDomain(SYNTHETIC_CHART, 'HEALTH', { liveSignals: { kp: liveSignals(4.0) } })
    expect(res.weightedMeanScore).toBeCloseTo(4.0, 2)
    expect(res.convergence.meanDomainScore).toBeCloseTo(4.0, 2)
  })

  it('all 7 with signals => 7 of 7 available, nothing unavailable', async () => {
    const res = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', { liveSignals: liveSignalsForAll(4.5) })
    expect(res.convergence.schoolsAvailable).toBe(7)
    expect(res.convergence.schoolsUnavailable).toEqual([])
    expect(res.convergence.convergenceNarrative).toContain('7 of 7 schools available')
  })

  it('runFullTriangulation without signals: five domains, all NOT_AVAILABLE', async () => {
    const all = await runFullTriangulation(SYNTHETIC_CHART)
    expect(all).toHaveLength(5)
    for (const r of all) expect(r.convergence.convergenceLevel).toBe('NOT_AVAILABLE')
  })
})
