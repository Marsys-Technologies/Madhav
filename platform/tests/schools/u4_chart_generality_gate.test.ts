/**
 * u4_chart_generality_gate.test.ts — CHART-GENERALITY GATE (D28)
 *
 * The integrity gate for school consensus. Proves the 7-school engines read the live
 * ChartData and the live signals passed in, and carry NO hardcoded preset or stored chart
 * (SS N-362: the former native-chart presets were removed; CLAUDE.md §N.7).
 *
 * GATE (rewritten for the no-defaults engines):
 *   1. With no live signals, two very different charts give the same honest result:
 *      every school not available (nothing chart-specific leaks out of the engines).
 *   2. With the same live signals, two different charts give the same per-school scores
 *      (scores depend on signals only, not on a stored chart).
 *   3. With different live signals, scores differ (the engines do read the signals).
 *
 * Also covers: live-signal routing, E2 authority weights, E3 magnitude, pending flags,
 * runner stays DB-free.
 */

import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { SYNTHETIC_CHART, SYNTHETIC_CHART_B } from '@/lib/schools/__fixtures__/synthetic_chart'
import { runFullTriangulation, runSchoolsForDomain } from '@/lib/schools/school_runner'
import { DOMAIN_AUTHORITY_WEIGHTS } from '@/lib/schools/chart_data_adapter'
import { ALL_DOMAINS, liveSignalsForAll } from './_support'

// ── D28 CHART-GENERALITY GATE ────────────────────────────────────────────────

describe('D28 CHART-GENERALITY GATE', () => {
  it('the two fictional fixtures differ in every headline field', () => {
    expect(SYNTHETIC_CHART.chartId).not.toBe(SYNTHETIC_CHART_B.chartId)
    expect(SYNTHETIC_CHART.ascendant).not.toBe(SYNTHETIC_CHART_B.ascendant)
    expect(SYNTHETIC_CHART.moonSign).not.toBe(SYNTHETIC_CHART_B.moonSign)
    expect(SYNTHETIC_CHART.sunSign).not.toBe(SYNTHETIC_CHART_B.sunSign)
  })

  it('no live signals: both charts give an identical all-not-available triangulation', async () => {
    const [a, b] = await Promise.all([runFullTriangulation(SYNTHETIC_CHART), runFullTriangulation(SYNTHETIC_CHART_B)])
    for (const set of [a, b]) {
      expect(set).toHaveLength(5)
      for (const r of set) {
        expect(r.convergence.convergenceLevel).toBe('NOT_AVAILABLE')
        expect(r.schoolResults.every(s => s.available === false)).toBe(true)
        expect(r.schoolResults.every(s => s.domainScore === null)).toBe(true)
      }
    }
  })

  it('same live signals on different charts: identical per-school scores (no stored-chart influence)', async () => {
    const live = { liveSignals: liveSignalsForAll(3.9) }
    const [a, b] = await Promise.all([runFullTriangulation(SYNTHETIC_CHART, live), runFullTriangulation(SYNTHETIC_CHART_B, live)])
    for (let i = 0; i < a.length; i++) {
      expect(a[i].convergence.perSchoolScores).toEqual(b[i].convergence.perSchoolScores)
      expect(a[i].convergence.meanDomainScore).toBe(b[i].convergence.meanDomainScore)
    }
  })

  it('different live signals: scores differ materially (engines read the signals)', async () => {
    const hi = await runFullTriangulation(SYNTHETIC_CHART, { liveSignals: liveSignalsForAll(4.6) })
    const lo = await runFullTriangulation(SYNTHETIC_CHART, { liveSignals: liveSignalsForAll(1.4) })
    for (let i = 0; i < hi.length; i++) {
      expect((hi[i].convergence.meanDomainScore as number) - (lo[i].convergence.meanDomainScore as number)).toBeGreaterThan(2)
    }
  })
})

// ── live signals routing ─────────────────────────────────────────────────────

describe('live signals routing', () => {
  it('runSchoolsForDomain passes liveSignals to each engine when provided', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', { liveSignals: liveSignalsForAll(4.5) })
    expect(result.schoolResults.length).toBe(7)
    expect(result.schoolResults.every(r => r.available === true)).toBe(true)
    for (const r of result.schoolResults) {
      expect(r.topSignals.every(t => t.signalId.startsWith('SIG.TEST.'))).toBe(true)
    }
  })
})

// ── E2: per-domain authority weighting ──────────────────────────────────────

describe('E2: domain authority weighting', () => {
  it('DOMAIN_AUTHORITY_WEIGHTS has 5 domains × 7 schools each summing to 1.0', () => {
    const schools = ['parashari', 'jaimini', 'kp', 'tajika', 'nadi', 'bnn', 'yogini'] as const
    for (const domain of ALL_DOMAINS) {
      const weights = DOMAIN_AUTHORITY_WEIGHTS[domain]
      const sum = schools.reduce((acc, s) => acc + (weights[s] ?? 0), 0)
      expect(Math.abs(sum - 1.0)).toBeLessThan(0.005)
    }
  })

  it('runSchoolsForDomain result carries weightedMeanScore when schools are available', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', { liveSignals: liveSignalsForAll(3.9) })
    expect(typeof result.weightedMeanScore).toBe('number')
    expect(result.weightedMeanScore).toBeCloseTo(3.9, 2)
  })

  it('weightedMeanScore is null (not zero) when no school is available', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER')
    expect(result.weightedMeanScore).toBeNull()
  })
})

// ── E3: direction + magnitude ────────────────────────────────────────────────

describe('E3: direction and magnitude in output', () => {
  it('convergence carries meanDomainScore + stdDomainScore', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'SPIRITUAL', { liveSignals: liveSignalsForAll(3.5) })
    expect(result.convergence.meanDomainScore).toBeGreaterThanOrEqual(0)
    expect(result.convergence.stdDomainScore).toBeGreaterThanOrEqual(0)
  })

  it('convergenceNarrative describes direction+magnitude', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', { liveSignals: liveSignalsForAll(4.5), includeNarratives: true })
    const narrative = result.convergence.convergenceNarrative ?? ''
    expect(/\d+\.\d+|strong|high|positive|exceptional|moderate|low/i.test(narrative)).toBe(true)
  })
})

// ── pending flags ────────────────────────────────────────────────────────────

describe('pending flag resolution', () => {
  it('synthetic fixture has no pending flags (clean baseline)', () => {
    expect(SYNTHETIC_CHART.pendingFlags).toEqual([])
  })

  it('tajika_engine produces non-pending result when the chart carries no pending flag', async () => {
    const chartWithYear = { ...SYNTHETIC_CHART, varshaKundaliYear: 2026 }
    const result = await runSchoolsForDomain(chartWithYear, 'CAREER', { liveSignals: liveSignalsForAll(3.5) })
    const tajika = result.schoolResults.find(r => r.school === 'tajika')
    expect(tajika).toBeDefined()
    expect(tajika?.pendingFlags?.includes('VARSHA_KUNDALI_PENDING')).toBeFalsy()
  })
})

// ── Anti-drift ───────────────────────────────────────────────────────────────

describe('Anti-drift: runner stays DB-free', () => {
  it('school_runner.ts does not import from db/client directly', () => {
    const src = fs.readFileSync(
      path.join(__dirname, '../../src/lib/schools/school_runner.ts'),
      'utf-8'
    )
    expect(src).not.toContain("from '../db/client'")
    expect(src).not.toContain("from '../../db/client'")
    expect(src).not.toContain('INSERT INTO')
    expect(src).not.toContain('UPDATE school_')
  })

  it('SYNTHETIC_CHART.chartId is not a real chart_id', () => {
    expect(SYNTHETIC_CHART.chartId).toMatch(/^synthetic-/)
    expect(SYNTHETIC_CHART_B.chartId).toMatch(/^synthetic-/)
  })
})
