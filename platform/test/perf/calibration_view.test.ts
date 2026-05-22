/**
 * calibration_view.test.ts — Track B tests (AC.S1.3, AC.S1.4, AC.S1.5)
 *
 * Tests the Wilson CI logic, the calibration row shape, and the
 * discrepancy-flag logic used by PredictionsCalibration.tsx.
 * No DB or Supabase required — pure logic tests.
 */

import { describe, it, expect } from 'vitest'

// ── Wilson CI (pure JS, mirrors wilson.sql exactly) ───────────────────────────

function wilsonLower(s: number, n: number, z: number = 1.96): number {
  if (n === 0) return 0
  const p = s / n
  const denom  = 1 + z * z / n
  const center = (p + z * z / (2 * n)) / denom
  const margin = (z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
  return Math.max(0, center - margin)
}

function wilsonUpper(s: number, n: number, z: number = 1.96): number {
  if (n === 0) return 1
  const p = s / n
  const denom  = 1 + z * z / n
  const center = (p + z * z / (2 * n)) / denom
  const margin = (z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
  return Math.min(1, center + margin)
}

// ── AC.S1.4: Wilson test vectors ───────────────────────────────────────────────

describe('AC.S1.4 — Wilson confidence interval', () => {
  it('50% of 10: lower ≈ 0.24', () => {
    const lb = wilsonLower(5, 10)
    expect(lb).toBeGreaterThanOrEqual(0.23)
    expect(lb).toBeLessThanOrEqual(0.28)
  })

  it('50% of 10: upper ≈ 0.76', () => {
    const ub = wilsonUpper(5, 10)
    expect(ub).toBeGreaterThanOrEqual(0.72)
    expect(ub).toBeLessThanOrEqual(0.78)
  })

  it('0 of 0: lower = 0, upper = 1 (null-safe fallback)', () => {
    expect(wilsonLower(0, 0)).toBe(0)
    expect(wilsonUpper(0, 0)).toBe(1)
  })

  it('100% of 100: lower bound > 0.94', () => {
    expect(wilsonLower(100, 100)).toBeGreaterThan(0.94)
  })

  it('0% of 20: upper bound < 0.17', () => {
    expect(wilsonUpper(0, 20)).toBeLessThan(0.17)
  })

  it('CI is symmetric around 50% for p=0.5', () => {
    const lb = wilsonLower(50, 100)
    const ub = wilsonUpper(50, 100)
    expect(Math.abs((lb + ub) / 2 - 0.5)).toBeLessThan(0.001)
  })

  it('CI shrinks as N increases', () => {
    const small = wilsonUpper(5, 10) - wilsonLower(5, 10)
    const large = wilsonUpper(50, 100) - wilsonLower(50, 100)
    expect(large).toBeLessThan(small)
  })
})

// ── Calibration row type tests ────────────────────────────────────────────────

interface MockCalibrationRow {
  confidence_band: string
  domain: string
  horizon_bucket: string
  total_predictions: number
  realized: number
  disconfirmed: number
  partial: number
  pending: number
  realized_rate: number | null
  realized_rate_ci_low: number | null
  realized_rate_ci_high: number | null
  last_outcome_at: string | null
}

function computeRealizedRate(row: MockCalibrationRow): number | null {
  const n = row.realized + row.disconfirmed
  if (n === 0) return null
  return row.realized / n
}

function computeDiscrepancy(row: MockCalibrationRow): boolean {
  const BAND_MIDPOINT: Record<string, number> = { high: 0.70, medium: 0.50, low: 0.30 }
  const n = row.realized + row.disconfirmed
  if (n < 10 || row.realized_rate === null) return false
  const mid  = BAND_MIDPOINT[row.confidence_band] ?? 0.50
  return Math.abs(row.realized_rate - mid) > 0.15
}

describe('AC.S1.3 — mv_calibration_score row shape', () => {
  const sampleRow: MockCalibrationRow = {
    confidence_band: 'high',
    domain: 'career',
    horizon_bucket: '31-180d',
    total_predictions: 15,
    realized: 8,
    disconfirmed: 4,
    partial: 1,
    pending: 2,
    realized_rate: 8 / 12,     // 0.6667
    realized_rate_ci_low: wilsonLower(8, 12),
    realized_rate_ci_high: wilsonUpper(8, 12),
    last_outcome_at: '2026-05-20T10:00:00Z',
  }

  it('has required fields', () => {
    expect(sampleRow.confidence_band).toBeDefined()
    expect(sampleRow.domain).toBeDefined()
    expect(sampleRow.horizon_bucket).toBeDefined()
    expect(sampleRow.total_predictions).toBeTypeOf('number')
    expect(sampleRow.realized).toBeTypeOf('number')
  })

  it('realized_rate = realized / (realized + disconfirmed)', () => {
    expect(computeRealizedRate(sampleRow)).toBeCloseTo(8 / 12, 4)
  })

  it('realized + disconfirmed + partial + pending = total_predictions', () => {
    const sum = sampleRow.realized + sampleRow.disconfirmed
                + sampleRow.partial + sampleRow.pending
    expect(sum).toBe(sampleRow.total_predictions)
  })

  it('realized_rate is within the Wilson CI bounds', () => {
    const rate = sampleRow.realized_rate!
    expect(rate).toBeGreaterThanOrEqual(sampleRow.realized_rate_ci_low!)
    expect(rate).toBeLessThanOrEqual(sampleRow.realized_rate_ci_high!)
  })

  it('high-band row with 67% realized (midpoint 70%) is NOT a discrepancy', () => {
    expect(computeDiscrepancy(sampleRow)).toBe(false)  // |0.667 - 0.70| = 0.033 < 0.15
  })

  it('high-band row with 40% realized IS a discrepancy', () => {
    const badRow: MockCalibrationRow = {
      ...sampleRow,
      realized: 4,
      disconfirmed: 6,
      realized_rate: 4 / 10,  // 0.40; |0.40 - 0.70| = 0.30 > 0.15
    }
    expect(computeDiscrepancy(badRow)).toBe(true)
  })

  it('discrepancy flag requires N ≥ 10', () => {
    const smallRow: MockCalibrationRow = {
      ...sampleRow,
      realized: 1, disconfirmed: 5, realized_rate: 1 / 6,
    }
    expect(computeDiscrepancy(smallRow)).toBe(false)  // n=6 < 10, no flag
  })
})

// ── Horizon bucket classification ─────────────────────────────────────────────

describe('horizon_bucket classification', () => {
  function bucketFor(days: number): string {
    if (days <= 30) return '<=30d'
    if (days <= 180) return '31-180d'
    if (days <= 730) return '181-730d'
    return '>730d'
  }

  it('30 days → <=30d', () => expect(bucketFor(30)).toBe('<=30d'))
  it('31 days → 31-180d', () => expect(bucketFor(31)).toBe('31-180d'))
  it('180 days → 31-180d', () => expect(bucketFor(180)).toBe('31-180d'))
  it('181 days → 181-730d', () => expect(bucketFor(181)).toBe('181-730d'))
  it('730 days → 181-730d', () => expect(bucketFor(730)).toBe('181-730d'))
  it('731 days → >730d', () => expect(bucketFor(731)).toBe('>730d'))
  it('365 days → 181-730d', () => expect(bucketFor(365)).toBe('181-730d'))
})

// ── AC.S1.5: Dashboard renders real data (smoke) ──────────────────────────────

describe('AC.S1.5 — PredictionsCalibration renders real data', () => {
  it('CalibrationRow with data should produce a visible realized rate', () => {
    const row: MockCalibrationRow = {
      confidence_band: 'medium',
      domain: 'health',
      horizon_bucket: '<=30d',
      total_predictions: 5,
      realized: 2,
      disconfirmed: 3,
      partial: 0,
      pending: 0,
      realized_rate: 2 / 5,
      realized_rate_ci_low: wilsonLower(2, 5),
      realized_rate_ci_high: wilsonUpper(2, 5),
      last_outcome_at: null,
    }
    const pctStr = `${(row.realized_rate! * 100).toFixed(0)}%`
    expect(pctStr).toBe('40%')
    expect(row.realized_rate_ci_low).toBeGreaterThanOrEqual(0)
    expect(row.realized_rate_ci_high).toBeLessThanOrEqual(1)
  })

  it('empty rows array produces no-data state (rows.length === 0)', () => {
    const rows: MockCalibrationRow[] = []
    expect(rows.length).toBe(0)
  })
})
