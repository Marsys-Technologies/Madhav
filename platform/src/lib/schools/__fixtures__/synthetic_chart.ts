/**
 * CHART-GENERALITY GATE fixture (D28).
 *
 * A FICTIONAL, test-only chart: it does not describe any real person. No real birth or
 * chart data of any native may appear in this package (guarded by
 * tests/schools/no_native_data_guard.test.ts).
 *
 * Purpose: prove that the school engines read the live ChartData and live signals that are
 * passed in, never a hardcoded preset.
 *
 * Fixture facts (NOT a real chart):
 *   Ascendant: Cancer, Moon sign: Scorpio, Sun sign: Leo
 *   Saturn: debilitated in Aries (10H); Jupiter: Cancer (exalted) in 1H
 *   Yogini dasha: Mangala (fixture value)
 */
import type { ChartData } from '../types'

export const SYNTHETIC_CHART: ChartData = {
  chartId: 'synthetic-gate-fixture-d28',
  chartType: 'natal',
  ascendant: 'cancer',
  moonSign: 'scorpio',
  sunSign: 'leo',
  planets: [
    { planet: 'sun',     sign: 'leo',         house: 2,  degree: 14.2, isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'moon',    sign: 'scorpio',      house: 5,  degree: 8.7,  isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'mars',    sign: 'capricorn',    house: 7,  degree: 22.4, isRetrograde: false, isExalted: true,   isDebilitated: false },
    { planet: 'mercury', sign: 'virgo',        house: 3,  degree: 5.1,  isRetrograde: true,  isExalted: true,   isDebilitated: false },
    { planet: 'jupiter', sign: 'cancer',       house: 1,  degree: 18.9, isRetrograde: false, isExalted: true,   isDebilitated: false },
    { planet: 'venus',   sign: 'gemini',       house: 12, degree: 29.3, isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'saturn',  sign: 'aries',        house: 10, degree: 7.6,  isRetrograde: false, isExalted: false,  isDebilitated: true  },
    { planet: 'rahu',    sign: 'pisces',       house: 9,  degree: 14.1, isRetrograde: true,  isExalted: false,  isDebilitated: false },
    { planet: 'ketu',    sign: 'virgo',        house: 3,  degree: 14.1, isRetrograde: true,  isExalted: false,  isDebilitated: false },
  ],
  activeDasha: {
    mahadasha: 'venus',
    antardasha: 'saturn',
    pratyantardasha: 'jupiter',
    start: '2025-09-01',
    end: '2026-09-15',
  },
  yoginiDasha: {
    yogini: 'mangala',    // fixture value (fictional)
    lord: 'mars',
    yearsElapsed: 1.5,
    yearsRemaining: 2.5,
  },
  charaPadas: {
    atmakaraka: 'jupiter',
    amatyakaraka: 'mars',
    bhratrikaraka: 'mercury',
    matrikaraka: 'moon',
    putrakaraka: 'venus',
    gnatikaraka: 'saturn',
    darakaraka: 'sun',
  },
  kpSubLords: {
    ascendant: 'jupiter',
    moon: 'mars',
    sun: 'venus',
  },
  pendingFlags: [],
}

/**
 * Second FICTIONAL chart (test-only), deliberately different from SYNTHETIC_CHART in every
 * headline field, with pending flags set. Used to prove that scores depend on the signals
 * passed in, not on which chart is passed.
 */
export const SYNTHETIC_CHART_B: ChartData = {
  chartId: 'synthetic-gate-fixture-b',
  chartType: 'natal',
  ascendant: 'libra',
  moonSign: 'pisces',
  sunSign: 'taurus',
  planets: [
    { planet: 'sun',     sign: 'taurus',      house: 8,  degree: 3.3,  isRetrograde: false, isExalted: false, isDebilitated: false },
    { planet: 'moon',    sign: 'pisces',      house: 6,  degree: 16.0, isRetrograde: false, isExalted: false, isDebilitated: false },
    { planet: 'mars',    sign: 'leo',         house: 11, degree: 9.9,  isRetrograde: false, isExalted: false, isDebilitated: false },
    { planet: 'mercury', sign: 'aries',       house: 7,  degree: 25.5, isRetrograde: false, isExalted: false, isDebilitated: false },
    { planet: 'jupiter', sign: 'capricorn',   house: 4,  degree: 11.1, isRetrograde: false, isExalted: false, isDebilitated: true  },
    { planet: 'venus',   sign: 'virgo',       house: 12, degree: 20.2, isRetrograde: false, isExalted: false, isDebilitated: true  },
    { planet: 'saturn',  sign: 'libra',       house: 1,  degree: 1.7,  isRetrograde: true,  isExalted: true,  isDebilitated: false },
    { planet: 'rahu',    sign: 'gemini',      house: 9,  degree: 6.6,  isRetrograde: true,  isExalted: false, isDebilitated: false },
    { planet: 'ketu',    sign: 'sagittarius', house: 3,  degree: 6.6,  isRetrograde: true,  isExalted: false, isDebilitated: false },
  ],
  activeDasha: {
    mahadasha: 'mercury',
    antardasha: 'ketu',
    start: '2025-01-01',
    end: '2026-01-01',
  },
  yoginiDasha: {
    yogini: 'dhanya',
    lord: 'jupiter',
    yearsElapsed: 2.0,
    yearsRemaining: 1.0,
  },
  charaPadas: {
    atmakaraka: 'saturn',
    amatyakaraka: 'moon',
    bhratrikaraka: 'venus',
    matrikaraka: 'sun',
    putrakaraka: 'mercury',
    gnatikaraka: 'mars',
    darakaraka: 'jupiter',
  },
  kpSubLords: {
    ascendant: 'venus',
    moon: 'saturn',
    sun: 'moon',
  },
  pendingFlags: ['VARSHA_KUNDALI_PENDING', 'TRANSIT_DATA_PENDING'],
}
