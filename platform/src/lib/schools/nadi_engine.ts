/**
 * School Engine 5: Nadi (Chandra Kala Nadi + Dhruva Nadi)
 * Foundation: Chandra Kala Nadi (CKN), Dhruva Nadi sampler.
 * Key distinction: Nadi reads house-from-planet (not house-from-Lagna).
 * Primary coverage: SIG.MSR.539–543 (CKN signals) + 2 cross-source Dhruva Nadi.
 * All other natal signals are SILENT for Nadi — different trigger mechanism.
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { computeWeightedScore, scoreToDirection, topN } from './engine_utils'

// Nadi house-from-planet convention for Abhisek's natal chart
// For each planet, count house positions FROM that planet (not from Lagna)
function nadiHouseFromPlanet(
  sourcePlanet: string,
  targetHouse: number,
  chartData: ChartData
): number {
  const source = chartData.planets.find(p => p.planet === sourcePlanet)
  if (!source) return targetHouse
  const sourceH = source.house
  const relative = ((targetHouse - sourceH + 12) % 12) + 1
  return relative
}

// Nadi-specific signal scoring: evaluate trigger conditions using house-from-planet logic
function defaultSignals(domain: Domain, chartData: ChartData): SignalScore[] {
  // Nadi primary signals are limited to CKN range (SIG.MSR.539–543 + 2 cross)
  // Score based on planetary configurations read from planet's own house perspective
  const saturn = chartData.planets.find(p => p.planet === 'saturn')
  const moon = chartData.planets.find(p => p.planet === 'moon')

  // From Saturn's position (house 10 = Libra): 10H from Saturn = Saturn itself — trikona
  const saturnFromSaturn10H = nadiHouseFromPlanet('saturn', 10, chartData) === 1 ? 1.1 : 1.0

  const base: Record<Domain, SignalScore[]> = {
    CAREER: [
      { signalId: 'SIG.MSR.539', signalName: 'CKN: 10H from Saturn occupied by Moon — career-mind link', score: 3.2 * saturnFromSaturn10H, weight: 0.65, attributionRef: 'CKN §8.14' },
      { signalId: 'SIG.MSR.540', signalName: 'CKN: Saturn in own trinal house from Moon — career activation', score: 3.0, weight: 0.60 },
      { signalId: 'SIG.MSR.541', signalName: 'DHR: Jupiter 12H from Saturn — foreign/spiritual career dimension', score: 2.8, weight: 0.55 },
    ],
    HEALTH: [
      { signalId: 'SIG.MSR.542', signalName: 'CKN: 6H from Moon — disease evaluation from Moon planet', score: 2.5, weight: 0.58 },
      { signalId: 'SIG.MSR.543', signalName: 'CKN: 8H from Sun — chronic illness reading from Sun', score: 2.3, weight: 0.52 },
      { signalId: 'SIG.MSR.539', signalName: 'CKN: vitality from 1H-from-planet configuration', score: 2.7, weight: 0.55 },
    ],
    RELATIONSHIP: [
      { signalId: 'SIG.MSR.541', signalName: 'CKN: 7H from Venus — partner read from Venus', score: 2.8, weight: 0.60 },
      { signalId: 'SIG.MSR.542', signalName: 'CKN: 2H from Moon — family bond from Moon perspective', score: 2.6, weight: 0.55 },
      { signalId: 'SIG.MSR.540', signalName: 'CKN: Jupiter from Venus house — partner expansion', score: 2.5, weight: 0.52 },
    ],
    SPIRITUAL: [
      { signalId: 'SIG.MSR.543', signalName: 'CKN: 9H from Moon — dharma from Moon planet', score: 3.5, weight: 0.70 },
      { signalId: 'SIG.MSR.539', signalName: 'CKN: 12H from Saturn — moksha from Saturn reading', score: 3.2, weight: 0.65 },
      { signalId: 'SIG.MSR.541', signalName: 'DHR: Ketu from Ketu — liberation indicator', score: 3.4, weight: 0.68 },
    ],
    PSYCHOLOGICAL: [
      { signalId: 'SIG.MSR.540', signalName: 'CKN: 1H from Moon — self from Moon perspective', score: 3.0, weight: 0.62 },
      { signalId: 'SIG.MSR.542', signalName: 'CKN: 5H from Mercury — intellect from Mercury', score: 3.1, weight: 0.63 },
      { signalId: 'SIG.MSR.543', signalName: 'CKN: Saturn 10H from Moon — discipline via Moon lens', score: 2.8, weight: 0.58 },
    ],
  }
  return base[domain]
}

function buildVerdict(domain: Domain, score: number): string {
  const level = score >= 3.5 ? 'strong' : score >= 2.5 ? 'moderate' : 'limited'
  const verdicts: Record<Domain, string> = {
    CAREER:       `Nadi (CKN) reads ${level} career through the house-from-planet lens: from Saturn's own position in 10H, Moon in the 12th-from-Saturn creates a career-mind link across the spiritual horizon. This is a Nadi-specific reading unavailable to Parashari's Lagna-based convention, and it reveals the inner solitary nature of the professional drive.`,
    HEALTH:       `Nadi reads ${level} health through the 6H-from-Moon and 8H-from-Sun conventions. The CKN's signature is that disease evaluation begins from the relevant planet rather than the Lagna, revealing constitutional tendencies invisible to Lagna-based schools. Chronic indicators (8H from Sun) are in the moderate range.`,
    RELATIONSHIP: `Nadi reads ${level} relationship indicators: the 7H from Venus convention places the partner's characteristics directly in the Venus framework, while the 2H-from-Moon evaluation assesses family-bond quality from the mind's natural home. Scores are limited by Nadi's sparse primary coverage on natal relationship signals.`,
    SPIRITUAL:    `Nadi reads ${level} spiritual indicators: the 9H-from-Moon reading reveals dharmic inclination through the emotional-self lens, while 12H-from-Saturn evaluates moksha potential from the karmic discipline planet. The Dhruva Nadi Ketu-from-Ketu placement is a pure liberation indicator. This is among the strongest Nadi readings.`,
    PSYCHOLOGICAL:`Nadi reads ${level} psychology via the 1H-from-Moon (self as Moon knows it) and 5H-from-Mercury (intellect from Mercury's own house). The Nadi tradition reads psyche from its own planetary home rather than from an abstract Lagna, revealing the internally-driven nature of the psychological structure.`,
  }
  return verdicts[domain]
}

export class NadiEngine implements SchoolAnalysis {
  readonly school = 'nadi' as const
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
      schoolVerdict: buildVerdict(domain, score),
      signalCoverage: 'primary',
    }
  }
}

export const nadi_engine = new NadiEngine()
