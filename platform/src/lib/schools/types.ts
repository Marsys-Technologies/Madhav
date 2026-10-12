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
  kpSubLordsFrame?: string             // 'KP frame (Krishnamurti ayanamsha)' whenever kpSubLords is set (SS N-342)
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

/**
 * Why a school could not be analysed (SS N-362/N-363; CLAUDE.md §N.7: an honest null beats an
 * invented judgment).
 *  - no_live_signals: the caller supplied no live signals for the school (undefined OR []).
 *  - zero_signal_weight: signals were supplied but their total weight is 0, so no weighted
 *    score can be formed.
 */
export type UnavailableReason = 'no_live_signals' | 'zero_signal_weight'

/**
 * The three states of the signals argument, kept explicit so an empty array is never
 * confused with a missing key:
 *  - not_supplied:   undefined/null (the caller passed nothing for this school)
 *  - supplied_empty: [] (the caller passed an empty list)
 *  - supplied:       a non-empty list (analyse it)
 */
export type SignalSupply = 'not_supplied' | 'supplied_empty' | 'supplied'

export interface SchoolResult {
  school: SchoolName
  domain: Domain
  /** 0.0–5.0 weighted aggregate; null when the school is not available. */
  domainScore: number | null
  /** null when the school is not available (no judgment is made). */
  direction: Direction | null
  topSignals: SignalScore[]       // top 3 by score×weight
  schoolVerdict: string           // 1–3 sentence acharya-grade prose
  signalCoverage: CoverageType
  pendingFlags?: string[]         // propagated from engine (e.g. [TRANSIT_DATA_PENDING])
  /**
   * Additive (SS N-362/N-363). false = the engine did NOT analyse this domain (no live
   * signals); consumers must skip it and must not count it as agreement or in "n of 7".
   * Absent or true = analysed from the signals that were passed in.
   */
  available?: boolean
  unavailableReason?: UnavailableReason
  /** How the signals argument looked when the engine was called. */
  signalSupply?: SignalSupply
}

export interface SchoolAnalysis {
  school: SchoolName
  chartType: 'natal' | 'varsha_kundali'
  analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult>
}

export interface ConvergenceScore {
  domain: Domain
  schoolsAgreeing: number
  /** Denominator of schoolsAgreeing: available schools, minus Tajika when [VARSHA_KUNDALI_PENDING]. */
  schoolsTotal: number
  /** Schools evaluated (normally 7), available or not. */
  schoolsEvaluated: number
  /** Schools that were analysed from live signals (evaluated minus unavailable). */
  schoolsAvailable: number
  /** Schools skipped because they had no live signals (never counted as agreement). */
  schoolsUnavailable: SchoolName[]
  /** 'NOT_AVAILABLE' when no school could be analysed: no convergence is claimed. */
  convergenceLevel: ConvergenceLevel | 'NOT_AVAILABLE'
  meanDomainScore: number | null
  stdDomainScore: number | null
  direction: Direction | 'mixed' | 'not_available'
  /** Available schools only (unavailable schools have no entry, not a zero). */
  perSchoolScores: Partial<Record<SchoolName, number>>
  convergenceNarrative?: string
}

export interface MultiSchoolResult {
  chartId: string
  runDate: string                 // ISO date
  domain: Domain
  schoolResults: SchoolResult[]
  convergence: ConvergenceScore
  // E2/E3 extensions (U4 2026-06-22): authority-weighted consensus
  weightedMeanScore?: number | null
  perSchoolWeighted?: Partial<Record<SchoolName, number>>
  weightedSchoolsAgreeing?: number
}
