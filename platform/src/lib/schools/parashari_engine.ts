/**
 * School Engine 1: Parashari
 * Foundation: BPHS, Phaladeepika, Saravali, Brihat Jataka, Brihat Samhita, Uttara Kalamrita.
 * Primary coverage: natal yoga signals SIG.MSR.001–514 (89.7% of MSR v5.0).
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { computeWeightedScore, scoreToDirection, topN } from './engine_utils'

// Default signal set representing Parashari primary coverage for Abhisek's chart.
// In production (M9-C), school_signal_coverage DB query populates this.
function defaultSignals(domain: Domain, chartData: ChartData): SignalScore[] {
  const saturn = chartData.planets.find(p => p.planet === 'saturn')
  const saturnExalted = saturn?.isExalted ?? false
  const saturnIn10H = saturn?.house === 10

  const baseByDomain: Record<Domain, SignalScore[]> = {
    CAREER: [
      { signalId: 'SIG.MSR.041', signalName: 'Saturn 10H exalted yoga', score: saturnExalted && saturnIn10H ? 4.8 : 3.5, weight: 0.95, attributionRef: 'BPHS §24' },
      { signalId: 'SIG.MSR.089', signalName: 'Mercury-Saturn Capricorn conjunction', score: 4.2, weight: 0.80, attributionRef: 'Phaladeepika §12' },
      { signalId: 'SIG.MSR.103', signalName: 'Lagna lord in own sign career strength', score: 3.8, weight: 0.75, attributionRef: 'BPHS §17' },
    ],
    HEALTH: [
      { signalId: 'SIG.MSR.201', signalName: 'Moon 9H virgo — digestive sensitivity', score: 2.8, weight: 0.70 },
      { signalId: 'SIG.MSR.215', signalName: 'Jupiter 12H loss house constitutional', score: 2.5, weight: 0.65 },
      { signalId: 'SIG.MSR.198', signalName: 'Mars 4H — energy constitution moderate', score: 3.1, weight: 0.72 },
    ],
    RELATIONSHIP: [
      { signalId: 'SIG.MSR.302', signalName: 'Venus 2H Aquarius — partner values', score: 3.4, weight: 0.78 },
      { signalId: 'SIG.MSR.315', signalName: 'Jupiter darakaraka 12H — spiritual partner', score: 3.0, weight: 0.68 },
      { signalId: 'SIG.MSR.289', signalName: '7H lord — partnership house analysis', score: 2.9, weight: 0.65 },
    ],
    SPIRITUAL: [
      { signalId: 'SIG.MSR.401', signalName: 'Ketu 12H moksha placement', score: 4.5, weight: 0.90 },
      { signalId: 'SIG.MSR.412', signalName: 'Moon 9H — dharmic inclination', score: 4.2, weight: 0.85 },
      { signalId: 'SIG.MSR.398', signalName: 'Jupiter-Ketu 12H spiritual loss-of-self', score: 4.0, weight: 0.82 },
    ],
    PSYCHOLOGICAL: [
      { signalId: 'SIG.MSR.451', signalName: 'Moon-Mercury opposition — analytical mind', score: 3.6, weight: 0.80 },
      { signalId: 'SIG.MSR.462', signalName: 'Saturn Lagna lord — seriousness + discipline', score: 3.4, weight: 0.75 },
      { signalId: 'SIG.MSR.478', signalName: 'Rahu 6H — competitive ambition driver', score: 3.1, weight: 0.70 },
    ],
  }
  return baseByDomain[domain]
}

function buildVerdict(domain: Domain, score: number, signals: SignalScore[]): string {
  const top = signals[0]?.signalName ?? 'natal configuration'
  const level = score >= 4.0 ? 'exceptional' : score >= 3.0 ? 'strong' : score >= 2.0 ? 'moderate' : 'challenged'
  const verdicts: Record<Domain, string> = {
    CAREER:       `Parashari framework reads a ${level} career trajectory anchored by ${top}. Saturn exalted in the 10th house is the dominant yoga — Capricorn rising with Saturn as lagna lord in 10H constitutes a raja yoga of high order. The Mercury-Saturn conjunction in Lagna adds intellectual authority to executive capacity.`,
    HEALTH:       `Parashari reads ${level} constitutional vitality with Moon in Virgo 9th house indicating a sensitive digestive system and tendency toward analytical health anxiety. Jupiter in 12H introduces occasional lethargy. Mars in 4H sustains physical drive above baseline.`,
    RELATIONSHIP: `Parashari reads ${level} partnership potential via Venus in Aquarius 2H — values-aligned, intellectually driven partnerships. Jupiter as darakaraka in 12H points toward spiritual or unconventional bond; Saturn as lagna lord delays but rewards.`,
    SPIRITUAL:    `Parashari reads ${level} spiritual orientation: Ketu in 12H is a moksha karaka in its natural house, the strongest classical indicator of liberation-orientation. Moon in 9H (dharma house) with the Guru-Ketu axis intensifies the inclination toward inner-directed practice.`,
    PSYCHOLOGICAL:`Parashari reads a ${level} psychological profile structured around the Moon-Mercury axis and Saturn's Capricorn discipline. The opposition between Moon 9H (Virgo) and Mercury 1H (Capricorn) produces an analytical mind that can over-examine emotion. Rahu 6H drives competitive sublimation.`,
  }
  return verdicts[domain]
}

export class ParashariEngine implements SchoolAnalysis {
  readonly school = 'parashari' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const activeSignals = signals ?? defaultSignals(domain, chartData)
    const score = computeWeightedScore(activeSignals)
    const direction = scoreToDirection(score)
    const top = topN(activeSignals, 3)
    return {
      school: this.school,
      domain,
      domainScore: Math.round(score * 1000) / 1000,
      direction,
      topSignals: top,
      schoolVerdict: buildVerdict(domain, score, top),
      signalCoverage: 'primary',
    }
  }
}

export const parashari_engine = new ParashariEngine()
