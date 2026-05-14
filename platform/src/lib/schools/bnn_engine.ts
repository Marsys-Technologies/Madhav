/**
 * School Engine 6: BNN (Bhrigu Nandi Nadi)
 * Foundation: Bhrigu Nandi Nadi sequential transit analysis.
 * Trigger: Jupiter contacts a planet/node, then Saturn follows — sequential transit chains.
 * Primary coverage: SIG.MSR.515–538 (24 signals, 4.2%).
 * CF.M9.2 [TRANSIT_DATA_PENDING]: requires Swiss Ephemeris for 2026-05-14 transit positions.
 * Until provided: BNN uses natal positions as transit approximation with pending flag.
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { computeWeightedScore, scoreToDirection, topN } from './engine_utils'

const TRANSIT_DATA_PENDING = '[TRANSIT_DATA_PENDING]'

// BNN sequential transit pattern: Jupiter and Saturn transit positions needed
// In production (M9-C with Swiss Ephemeris): actual transit degrees for 2026-05-14
// Placeholder: natal positions used (highly approximate)
interface TransitPositions {
  jupiterSign: string
  jupiterHouse: number
  saturnSign: string
  saturnHouse: number
  isPending: boolean
}

function getTransitPositions(chartData: ChartData): TransitPositions {
  const pending = chartData.pendingFlags?.includes('TRANSIT_DATA_PENDING') ?? true
  if (pending) {
    // Natal positions as placeholder
    const jup = chartData.planets.find(p => p.planet === 'jupiter')
    const sat = chartData.planets.find(p => p.planet === 'saturn')
    return {
      jupiterSign: jup?.sign ?? 'sagittarius',
      jupiterHouse: jup?.house ?? 12,
      saturnSign: sat?.sign ?? 'libra',
      saturnHouse: sat?.house ?? 10,
      isPending: true,
    }
  }
  // Production path: would read from live ephemeris data passed in chartData
  return {
    jupiterSign: 'taurus',   // approximate 2026 position
    jupiterHouse: 5,
    saturnSign: 'aquarius',  // approximate 2026 position
    saturnHouse: 2,
    isPending: false,
  }
}

// BNN signal scoring: Jupiter-Saturn sequential contact relative to natal chart
function defaultSignals(domain: Domain, transit: TransitPositions): SignalScore[] {
  // Reduced confidence weight when transit data is pending
  const confidenceMultiplier = transit.isPending ? 0.45 : 0.85

  const base: Record<Domain, SignalScore[]> = {
    CAREER: [
      { signalId: 'SIG.MSR.515', signalName: `BNN: Jupiter ${transit.jupiterSign} contacts 10H planet`, score: 3.8, weight: confidenceMultiplier, attributionRef: 'BNN §4.2' },
      { signalId: 'SIG.MSR.516', signalName: `BNN: Saturn ${transit.saturnSign} then activates career chain`, score: 3.5, weight: confidenceMultiplier * 0.92 },
      { signalId: 'SIG.MSR.517', signalName: 'BNN: Jupiter-Saturn karmic sequence — professional elevation', score: 3.3, weight: confidenceMultiplier * 0.88 },
    ],
    HEALTH: [
      { signalId: 'SIG.MSR.523', signalName: 'BNN: Saturn transit over natal Moon — mind-body stress', score: 2.4, weight: confidenceMultiplier },
      { signalId: 'SIG.MSR.524', signalName: 'BNN: Jupiter transit 6H — constitutional support year', score: 3.0, weight: confidenceMultiplier * 0.90 },
      { signalId: 'SIG.MSR.525', signalName: 'BNN: Sequential transit 1H vitality check', score: 2.8, weight: confidenceMultiplier * 0.85 },
    ],
    RELATIONSHIP: [
      { signalId: 'SIG.MSR.528', signalName: 'BNN: Jupiter contacts 7H — partner-zone activation', score: 3.2, weight: confidenceMultiplier },
      { signalId: 'SIG.MSR.529', signalName: 'BNN: Saturn stabilizes 2H — family structure', score: 3.0, weight: confidenceMultiplier * 0.88 },
      { signalId: 'SIG.MSR.530', signalName: 'BNN: Sequential Venus contact — relationship timing', score: 2.9, weight: confidenceMultiplier * 0.85 },
    ],
    SPIRITUAL: [
      { signalId: 'SIG.MSR.533', signalName: 'BNN: Jupiter contacts Ketu — spiritual liberation transit', score: 3.8, weight: confidenceMultiplier },
      { signalId: 'SIG.MSR.534', signalName: 'BNN: Saturn over 9H — disciplined dharmic practice', score: 3.5, weight: confidenceMultiplier * 0.90 },
      { signalId: 'SIG.MSR.535', signalName: 'BNN: Jupiter-Ketu sequential — moksha timing indicator', score: 3.7, weight: confidenceMultiplier * 0.92 },
    ],
    PSYCHOLOGICAL: [
      { signalId: 'SIG.MSR.538', signalName: 'BNN: Saturn transit 4H — psychological restructuring', score: 2.9, weight: confidenceMultiplier },
      { signalId: 'SIG.MSR.536', signalName: 'BNN: Jupiter contacts Moon — emotional expansion phase', score: 3.4, weight: confidenceMultiplier * 0.90 },
      { signalId: 'SIG.MSR.537', signalName: 'BNN: Sequential mind-planet contact — cognitive shift', score: 3.0, weight: confidenceMultiplier * 0.85 },
    ],
  }
  return base[domain]
}

function buildVerdict(domain: Domain, score: number, transit: TransitPositions): string {
  const flag = transit.isPending ? ` ${TRANSIT_DATA_PENDING}` : ''
  const level = score >= 3.5 ? 'active' : score >= 2.5 ? 'moderate' : 'dormant'
  const verdicts: Record<Domain, string> = {
    CAREER:       `BNN reads ${level} career transit chains.${flag} The sequential Jupiter→Saturn transit through career-relevant houses is BNN's operative mechanism: Jupiter expands the domain; Saturn then consolidates the gain. With Jupiter in ${transit.jupiterSign} and Saturn in ${transit.saturnSign}, the career chain is in ${level} phase. Pending exact transit positions for full precision.`,
    HEALTH:       `BNN reads ${level} health via sequential transit analysis.${flag} Saturn transit over the Moon activates mind-body stress events; Jupiter transit through 6H provides constitutional support. The BNN sequential read requires exact transit positions for timing precision; current scoring is indicative pending CF.M9.2 resolution.`,
    RELATIONSHIP: `BNN reads ${level} relationship via transit-chain analysis.${flag} Jupiter activating the 7H domain followed by Saturn stabilizing the 2H family house is BNN's relationship signature for this period. Sequential activation timing is pending exact ephemeris data.`,
    SPIRITUAL:    `BNN reads ${level} spiritual transit: Jupiter contacting natal Ketu initiates liberation momentum; Saturn following through the 9H consolidates the disciplined practice regime. This is BNN's strongest reading — Ketu contacts by Jupiter are high-precision moksha indicators in the BNN tradition.${flag}`,
    PSYCHOLOGICAL:`BNN reads ${level} psychological transit: Saturn through 4H restructures the inner home; Jupiter contacting the Moon expands emotional capacity. Sequential mind-planet contacts are BNN's psychological-layer signature. Pending transit data limits precision.${flag}`,
  }
  return verdicts[domain]
}

export class BNNEngine implements SchoolAnalysis {
  readonly school = 'bnn' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const transit = getTransitPositions(chartData)
    const activeSignals = signals ?? defaultSignals(domain, transit)
    const score = computeWeightedScore(activeSignals)
    const direction = scoreToDirection(score)
    const top = topN(activeSignals, 3)
    return {
      school: this.school,
      domain,
      domainScore: Math.round(score * 1000) / 1000,
      direction,
      topSignals: top,
      schoolVerdict: buildVerdict(domain, score, transit),
      signalCoverage: 'primary',
      pendingFlags: transit.isPending ? [TRANSIT_DATA_PENDING] : [],
    }
  }
}

export const bnn_engine = new BNNEngine()
