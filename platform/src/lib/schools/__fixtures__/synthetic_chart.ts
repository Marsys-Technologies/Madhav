/**
 * CHART-GENERALITY GATE fixture (D28).
 *
 * A deliberately DIFFERENT chart than any preset chart the engines ship with.
 * Purpose: prove that the school engines read live ChartData, not hardcoded presets.
 * If runFullTriangulation(SYNTHETIC_CHART) == runFullTriangulation(<the preset chart>), the
 * engines are still reading defaultSignals (presets). That would be a GATE FAILURE.
 *
 * Fixture facts (NOT a real chart, test-only; it describes no native):
 *   Ascendant: Cancer
 *   Moon sign: Scorpio
 *   Sun sign: Leo
 *   Saturn: debilitated in Aries
 *   Jupiter: Cancer (exalted) in 1H
 *   No Saturn exaltation in 10H, so a Saturn-exaltation career yoga is absent.
 *   Yogini dasha: Mangala
 *
 * The canonical native chart's facts live in the chart_facts table (CLAUDE.md section B), never here.
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
    yogini: 'mangala',    // lord = Mars
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
