/**
 * rank_vocabulary.test.ts — EL-59/EL-20 ONE rank vocabulary
 * ============================================================================
 * Named regression this guards: Venus served as a bare `weakest_rank_in_chart: 5`
 * in one tool with no basis/population, and "weakest of 7 by shadbala" prose in
 * another, with no shared vocabulary connecting the two. Every rank produced by
 * this module must carry rank + population_size + rank_basis together.
 */

import { describe, it, expect } from 'vitest'
import { buildRankStatement, rankGrahasByShadbala } from '../rank_vocabulary'

describe('buildRankStatement', () => {
  it('always carries rank + population_size + rank_basis + rank_statement together', () => {
    const stmt = buildRankStatement(5, 7, 'shadbala among 7 classical planets', 'Venus')
    expect(stmt.rank).toBe(5)
    expect(stmt.population_size).toBe(7)
    expect(stmt.rank_basis).toBe('shadbala among 7 classical planets')
    expect(stmt.rank_statement).toMatch(/Venus/)
    expect(stmt.rank_statement).toMatch(/shadbala among 7 classical planets/)
  })

  it('names the weakest position explicitly when rank === population_size', () => {
    const stmt = buildRankStatement(7, 7, 'shadbala among 7 classical planets', 'Venus')
    expect(stmt.rank_statement).toMatch(/weakest/i)
    expect(stmt.rank_statement).toMatch(/rank 7 of 7/)
  })

  it('names the strongest position explicitly when rank === 1', () => {
    const stmt = buildRankStatement(1, 7, 'shadbala among 7 classical planets', 'Jupiter')
    expect(stmt.rank_statement).toMatch(/strongest/i)
  })
})

describe('rankGrahasByShadbala — the Venus regression, closed', () => {
  const grahas = [
    { graha: 'SU', shadbala_total: 3.2 },
    { graha: 'MO', shadbala_total: 4.1 },
    { graha: 'MA', shadbala_total: 2.8 },
    { graha: 'ME', shadbala_total: 3.9 },
    { graha: 'JU', shadbala_total: 4.5 },
    { graha: 'VE', shadbala_total: 1.9 }, // weakest by design
    { graha: 'SA', shadbala_total: 2.5 },
    { graha: 'RA', shadbala_total: 9.9 }, // excluded from classical_7
    { graha: 'KE', shadbala_total: 9.9 }, // excluded from classical_7
  ]

  it('ranks Venus rank 7 of 7 (weakest) among the classical 7 — same shape "weakest of 7" prose would cite', () => {
    const ranked = rankGrahasByShadbala(grahas, 'classical_7')
    expect(ranked).toHaveLength(7)
    const venus = ranked.find(r => r.graha === 'VE')!
    expect(venus.rank).toBe(7)
    expect(venus.population_size).toBe(7)
    expect(venus.rank_basis).toMatch(/shadbala among 7 classical planets/)
    expect(venus.rank_statement).toMatch(/weakest/i)
    // The bare-integer regression: rank is never served without population_size + rank_basis
    // attached to it in the SAME object.
    expect(venus).toHaveProperty('population_size')
    expect(venus).toHaveProperty('rank_basis')
  })

  it('excludes Rahu/Ketu from the classical_7 population (no classical shadbala)', () => {
    const ranked = rankGrahasByShadbala(grahas, 'classical_7')
    expect(ranked.find(r => r.graha === 'RA')).toBeUndefined()
    expect(ranked.find(r => r.graha === 'KE')).toBeUndefined()
  })

  it('all_9 population includes Rahu/Ketu and states population_size=9', () => {
    const ranked = rankGrahasByShadbala(grahas, 'all_9')
    expect(ranked).toHaveLength(9)
    expect(ranked.every(r => r.population_size === 9)).toBe(true)
  })

  it('deterministic tie-break: equal shadbala resolves by canonical graha order, stable across runs', () => {
    const tied = [
      { graha: 'MA', shadbala_total: 3.0 },
      { graha: 'SU', shadbala_total: 3.0 },
    ]
    const r1 = rankGrahasByShadbala(tied, 'classical_7')
    const r2 = rankGrahasByShadbala(tied, 'classical_7')
    expect(r1.map(r => r.graha)).toEqual(r2.map(r => r.graha))
    // SU precedes MA in canonical order (SU,MO,MA,...)
    expect(r1[0]!.graha).toBe('SU')
  })

  it('rank 1 is assigned to the strongest shadbala', () => {
    const ranked = rankGrahasByShadbala(grahas, 'classical_7')
    expect(ranked[0]!.graha).toBe('JU')
    expect(ranked[0]!.rank).toBe(1)
  })
})
