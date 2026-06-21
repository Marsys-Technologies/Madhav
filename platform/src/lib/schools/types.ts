/**
 * M9 Multi-School Triangulation — core types.
 * All 7 Jyotish schools implement SchoolAnalysis; convergence aggregation uses ConvergenceScore.
 * M9-B-S1 (2026-05-14).
 */

export type SchoolName =
  | 'parashari'
  | 'jaimini'
  | 'tajika'
  | 'kp'
  | 'nadi'
  | 'bnn'
  | 'yogini'

export type Domain =
  | 'CAREER'
  | 'HEALTH'
  | 'RELATIONSHIP'
  | 'SPIRITUAL'
  | 'PSYCHOLOGICAL'

export type CoverageType = 'primary' | 'secondary' | 'silent'

export type Direction = 'positive' | 'negative' | 'neutral'

export type ConvergenceLevel = 'HIGH' | 'MEDIUM' | 'LOW'

export interface PlanetPosition {
  planet: string       // 'sun' | 'moon' | 'mars' | 'mercury' | 'jupiter' | 'venus' | 'saturn' | 'rahu' | 'ketu'
  sign: string         // 'capricorn' | 'virgo' | ...
  house: number        // 1–12
  degree: number       // 0.0–29.99
  isRetrograde: boolean
  isExalted: boolean
  isDebilitated: boolean
}

export interface DashaState {
  mahadasha: string
  antardasha: string
  pratyantardasha?: string
  start: string        // ISO date
  end: string
}

export interface YoginiState {
  yogini: string       // 'mangala' | 'pingala' | 'dhanya' | 'bhramari' | 'bhadrika' | 'ulka' | 'siddha' | 'sankata'
  lord: string         // planetary lord of the Yogini
  yearsElapsed: number
  yearsRemaining: number
}

export interface ChartData {
  chartId: string
  chartType: 'natal' | 'varsha_kundali'
  ascendant: string
  moonSign: string
  sunSign: string
  planets: PlanetPosition[]
  activeDasha: DashaState
  yoginiDasha?: YoginiState
  charaPadas?: Record<string, string>  // {atmakaraka: 'moon', amatyakaraka: 'saturn', ...}
  kpSubLords?: Record<string, string>  // {ascendant: 'saturn', moon: 'venus', ...}
  varshaKundaliYear?: number
  pendingFlags?: string[]              // ['VARSHA_KUNDALI_PENDING', 'TRANSIT_DATA_PENDING']
}

export interface SignalScore {
  signalId: string
  signalName: string
  score: number        // 0.0–5.0 per signal
  weight: number       // 0.0–1.0 coverage/confidence weight
  attributionRef?: string
}

export interface SchoolResult {
  school: SchoolName
  domain: Domain
  domainScore: number             // 0.0–5.0 weighted aggregate
  direction: Direction
  topSignals: SignalScore[]       // top 3 by score×weight
  schoolVerdict: string           // 1–3 sentence acharya-grade prose
  signalCoverage: CoverageType
  pendingFlags?: string[]         // propagated from engine (e.g. [TRANSIT_DATA_PENDING])
}

export interface SchoolAnalysis {
  school: SchoolName
  chartType: 'natal' | 'varsha_kundali'
  analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult>
}

export interface ConvergenceScore {
  domain: Domain
  schoolsAgreeing: number
  schoolsTotal: number            // normally 7; 6 if Tajika [VARSHA_KUNDALI_PENDING]
  convergenceLevel: ConvergenceLevel
  meanDomainScore: number
  stdDomainScore: number
  direction: Direction | 'mixed'
  perSchoolScores: Record<SchoolName, number>
  convergenceNarrative?: string
}

export interface MultiSchoolResult {
  chartId: string
  runDate: string                 // ISO date
  domain: Domain
  schoolResults: SchoolResult[]
  convergence: ConvergenceScore
  // E2/E3 extensions (U4 2026-06-22): authority-weighted consensus
  weightedMeanScore?: number
  perSchoolWeighted?: Partial<Record<SchoolName, number>>
  weightedSchoolsAgreeing?: number
}

// Abhisek Mohanty's natal chart — canonical L1 data (FORENSIC v8.0; chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)
export const ABHISEK_CHART: ChartData = {
  chartId: 'abhisek_primary',
  chartType: 'natal',
  ascendant: 'capricorn',
  moonSign: 'virgo',
  sunSign: 'capricorn',
  planets: [
    { planet: 'sun',     sign: 'capricorn', house: 1,  degree: 21.5, isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'moon',    sign: 'virgo',     house: 9,  degree: 27.0, isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'mars',    sign: 'aries',     house: 4,  degree: 12.3, isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'mercury', sign: 'capricorn', house: 1,  degree: 27.9, isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'jupiter', sign: 'sagittarius', house: 12, degree: 8.2, isRetrograde: false, isExalted: false, isDebilitated: false },
    { planet: 'venus',   sign: 'aquarius',  house: 2,  degree: 14.6, isRetrograde: false, isExalted: false,  isDebilitated: false },
    { planet: 'saturn',  sign: 'libra',     house: 10, degree: 19.1, isRetrograde: false, isExalted: true,   isDebilitated: false },
    { planet: 'rahu',    sign: 'gemini',    house: 6,  degree: 22.0, isRetrograde: true,  isExalted: false,  isDebilitated: false },
    { planet: 'ketu',    sign: 'sagittarius', house: 12, degree: 22.0, isRetrograde: true, isExalted: false,  isDebilitated: false },
  ],
  activeDasha: {
    mahadasha: 'moon',
    antardasha: 'moon',
    start: '2026-01-01',
    end: '2026-07-31',
  },
  yoginiDasha: {
    yogini: 'bhramari',
    lord: 'mars',
    yearsElapsed: 0.27,
    yearsRemaining: 3.73,
  },
  charaPadas: {
    atmakaraka: 'moon',
    amatyakaraka: 'saturn',
    bhratrikaraka: 'mercury',
    matrikaraka: 'mars',
    putrakaraka: 'sun',
    gnatikaraka: 'venus',
    darakaraka: 'jupiter',
  },
  kpSubLords: {
    ascendant: 'saturn',
    moon: 'venus',
    sun: 'saturn',
  },
  pendingFlags: ['VARSHA_KUNDALI_PENDING', 'TRANSIT_DATA_PENDING'],
}
