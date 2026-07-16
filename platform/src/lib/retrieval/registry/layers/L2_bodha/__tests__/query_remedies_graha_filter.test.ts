/**
 * CR-42/R-19/R-20 fix (D-1.6 S-1) — regression test, Gate Ś item 1.
 *
 * "Saturn remedy query returns only-Saturn or explicit rejection (never Jupiter)."
 *
 * Before this fix, the `graha`/`target_graha` filter on the L2 Bodha remedy surface
 * (bodha_rm_resonances / bodha_rm_remedy_prescriptions) was an exact-match `graha = $`
 * predicate with NO case normalization, while the DB stores capitalized full names
 * ("Saturn", "Venus", ...). A caller passing lowercase "saturn" (the natural form an
 * LLM caller reaches for, and the literal Gate Ś wording) silently got ZERO rows back
 * instead of Saturn's rows — the filter never "fell through" to serve a different
 * planet's rows outright, but it DID silently fail to honor the filter it claimed to
 * apply. This test pins: (1) graha:'saturn' (lowercase) returns ONLY Saturn-target
 * rows; (2) it NEVER returns a Jupiter row; (3) the SQL actually issued uses
 * LOWER(x) = LOWER($) case-insensitive matching, not a case-sensitive exact match.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryRemediesCapability } from '../query_remedies'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// Simulates the real bodha_rm_resonances/bodha_rm_remedy_prescriptions tables: a
// case-insensitive `LOWER(graha) = LOWER($n)` WHERE clause only matches Saturn rows
// when called with graha:'saturn'; a case-SENSITIVE query (the pre-fix behavior)
// would match nothing at all (not literally "serve Jupiter" — but would silently
// return zero Saturn rows, which is the failure mode this test guards against
// alongside the never-serve-Jupiter assertion).
function routeRemedyQueries(requestedGraha: string) {
  const allResonances = [
    { resonance_id: 'r-sat-1', graha: 'Saturn', resonance_score: 0.8 },
    { resonance_id: 'r-ven-1', graha: 'Venus', resonance_score: 0.7 },
    { resonance_id: 'r-jup-1', graha: 'Jupiter', resonance_score: 0.6 },
  ]
  const allPrescriptions = [
    { prescription_id: 'p-sat-1', target_graha: 'Saturn', tradition: 'mantra' },
    { prescription_id: 'p-ven-1', target_graha: 'Venus', tradition: 'mantra' },
    { prescription_id: 'p-jup-1', target_graha: 'Jupiter', tradition: 'mantra' },
  ]
  return (sql: string, params: unknown[]) => {
    const s = String(sql)
    // Only match rows whose graha/target_graha case-insensitively equals the
    // requested filter — mirrors the FIXED SQL's LOWER(x) = LOWER($) semantics.
    const wanted = requestedGraha.toLowerCase()
    if (s.includes('FROM bodha_rm_resonances')) {
      const rows = params.includes(requestedGraha)
        ? allResonances.filter(r => r.graha.toLowerCase() === wanted)
        : allResonances
      return Promise.resolve({ rows })
    }
    if (s.includes('FROM bodha_rm_remedy_prescriptions')) {
      const rows = params.includes(requestedGraha)
        ? allPrescriptions.filter(r => r.target_graha.toLowerCase() === wanted)
        : allPrescriptions
      return Promise.resolve({ rows })
    }
    return Promise.resolve({ rows: [] })
  }
}

describe('query_remedies (L2 Bodha) — graha filter case-insensitivity (CR-42/CR-10, Gate Ś item 1)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('graha:"saturn" (lowercase) returns ONLY Saturn-target rows and NEVER a Jupiter row', async () => {
    queryMock.mockImplementation(routeRemedyQueries('saturn'))

    const result = await queryRemediesCapability.handler(
      { chart_id: CHART_ID, graha: 'saturn' },
      undefined,
    ) as {
      content: {
        resonances: Array<{ graha: unknown }>
        prescriptions: Array<{ target_graha: unknown }>
      }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)

    const resonanceGrahas = result.content.resonances.map(r => String(r.graha))
    const prescriptionGrahas = result.content.prescriptions.map(p => String(p.target_graha))

    // Only Saturn — never empty due to a silent case-mismatch, and never any other graha.
    expect(resonanceGrahas.length).toBeGreaterThan(0)
    expect(resonanceGrahas.every(g => g === 'Saturn')).toBe(true)
    expect(resonanceGrahas).not.toContain('Jupiter')
    expect(resonanceGrahas).not.toContain('Venus')

    expect(prescriptionGrahas.length).toBeGreaterThan(0)
    expect(prescriptionGrahas.every(g => g === 'Saturn')).toBe(true)
    expect(prescriptionGrahas).not.toContain('Jupiter')
    expect(prescriptionGrahas).not.toContain('Venus')
  })

  it('graha:"SATURN" (uppercase) and graha:"Saturn" (canonical case) also return only Saturn rows', async () => {
    for (const variant of ['SATURN', 'Saturn', 'SaTuRn']) {
      queryMock.mockReset()
      queryMock.mockImplementation(routeRemedyQueries(variant))
      const result = await queryRemediesCapability.handler(
        { chart_id: CHART_ID, graha: variant },
        undefined,
      ) as { content: { resonances: Array<{ graha: unknown }> }; is_error: boolean }

      expect(result.is_error).toBe(false)
      const grahas = result.content.resonances.map(r => String(r.graha))
      expect(grahas.every(g => g === 'Saturn')).toBe(true)
      expect(grahas).not.toContain('Jupiter')
    }
  })

  it('the resonance-side SQL uses LOWER(graha) = LOWER($n) case-insensitive matching, not an exact-match predicate', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    await queryRemediesCapability.handler({ chart_id: CHART_ID, graha: 'saturn' }, undefined)

    const resonanceCall = queryMock.mock.calls.find(
      call => typeof call[0] === 'string' && (call[0] as string).includes('FROM bodha_rm_resonances'),
    )
    expect(resonanceCall).toBeDefined()
    const [sql] = resonanceCall as [string, unknown[]]
    expect(sql).toMatch(/LOWER\(graha\)\s*=\s*LOWER\(\$/i)
    expect(sql).not.toMatch(/\bgraha\s*=\s*\$\d/) // guards against reverting to the old exact-match form
  })

  it('the prescription-side SQL uses LOWER(target_graha) = LOWER($n) case-insensitive matching', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    await queryRemediesCapability.handler({ chart_id: CHART_ID, graha: 'saturn' }, undefined)

    const prescriptionCall = queryMock.mock.calls.find(
      call => typeof call[0] === 'string' && (call[0] as string).includes('FROM bodha_rm_remedy_prescriptions'),
    )
    expect(prescriptionCall).toBeDefined()
    const [sql] = prescriptionCall as [string, unknown[]]
    expect(sql).toMatch(/LOWER\(target_graha\)\s*=\s*LOWER\(\$/i)
    expect(sql).not.toMatch(/\btarget_graha\s*=\s*\$\d/)
  })
})
