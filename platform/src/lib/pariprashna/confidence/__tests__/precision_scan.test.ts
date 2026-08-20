/**
 * confidence/__tests__/precision_scan.test.ts — T-8 precision scan (lane
 * G3-C, PPR-03).
 */
import { describe, it, expect } from 'vitest'

import { scanPrecision, countDecimalPlaces, PRECISION_BANDS } from '../precision_scan'

describe('scanPrecision — T-8: a quantity must not be served with more precision than its sample supports', () => {
  it('flags "73.4% confident" from a sample of 3 as overstated and demotes to the integer-percent band', () => {
    const result = scanPrecision({ value: 0.734, servedDecimalPlaces: 1, sampleSize: 3 })
    expect(result.overstated).toBe(true)
    expect(result.max_supported_decimal_places).toBe(0)
    expect(result.demoted_value).toBe(1) // 0.734 rounded to 0 decimal places
    expect(result.band_label).toBe('insufficient_sample')
  })

  it('does NOT flag an integer-percent value from a small-but-nonzero sample (5-29) — 0 decimal places is exactly what that band supports', () => {
    const result = scanPrecision({ value: 0.73, servedDecimalPlaces: 0, sampleSize: 10 })
    expect(result.overstated).toBe(false)
    expect(result.band_label).toBe('integer_percent_only')
  })

  it('flags one-decimal precision as overstated at n=10 (only 0 decimal places supported)', () => {
    const result = scanPrecision({ value: 0.73, servedDecimalPlaces: 1, sampleSize: 10 })
    expect(result.overstated).toBe(true)
  })

  it('permits one decimal place at n=30 (the placeholder band boundary) and flags two decimal places at the same n', () => {
    const ok = scanPrecision({ value: 0.734, servedDecimalPlaces: 1, sampleSize: 30 })
    expect(ok.overstated).toBe(false)
    const over = scanPrecision({ value: 0.7341, servedDecimalPlaces: 4, sampleSize: 30 })
    expect(over.overstated).toBe(true)
    expect(over.max_supported_decimal_places).toBe(1)
  })

  it('permits two decimal places once n>=100', () => {
    const result = scanPrecision({ value: 0.7342, servedDecimalPlaces: 2, sampleSize: 150 })
    expect(result.overstated).toBe(false)
    expect(result.band_label).toBe('two_decimal_supported')
  })

  it('a null sample size is treated as the coarsest band (never assumes a sample it cannot see)', () => {
    const result = scanPrecision({ value: 0.734, servedDecimalPlaces: 1, sampleSize: null })
    expect(result.overstated).toBe(true)
    expect(result.max_supported_decimal_places).toBe(0)
    expect(result.sample_size).toBeNull()
  })

  it('discloses that the precision bands are a placeholder convention, not a sourced threshold', () => {
    const result = scanPrecision({ value: 0.5, servedDecimalPlaces: 0, sampleSize: 100 })
    expect(result.bands_are_placeholder).toBe(true)
  })

  it('PRECISION_BANDS is ordered ascending by minSampleSize (structural sanity)', () => {
    for (let i = 1; i < PRECISION_BANDS.length; i++) {
      expect(PRECISION_BANDS[i].minSampleSize).toBeGreaterThan(PRECISION_BANDS[i - 1].minSampleSize)
    }
  })
})

describe('countDecimalPlaces', () => {
  it('counts real decimal places', () => {
    expect(countDecimalPlaces(0.734)).toBe(3)
    expect(countDecimalPlaces(0.5)).toBe(1)
    expect(countDecimalPlaces(73)).toBe(0)
    expect(countDecimalPlaces(0)).toBe(0)
  })

  it('handles scientific notation for very small numbers without throwing', () => {
    expect(countDecimalPlaces(1e-7)).toBeGreaterThan(0)
  })

  it('is defensive on non-finite input', () => {
    expect(countDecimalPlaces(NaN)).toBe(0)
    expect(countDecimalPlaces(Infinity)).toBe(0)
  })
})
