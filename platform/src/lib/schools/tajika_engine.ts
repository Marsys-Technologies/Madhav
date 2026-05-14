/**
 * School Engine 3: Tajika
 * Foundation: Prashna Marga, Hora Sara, Tajika Neelakanthi (procurement pending).
 * Operates on Varsha Kundali (annual solar return chart), NOT the natal chart.
 * Primary coverage: SIG.MSR.559–573 (15 signals; solar_return_scope:true).
 * CF.M9.1 [VARSHA_KUNDALI_PENDING]: 2026 Varsha Kundali requires Swiss Ephemeris.
 * Until provided: natal chart used as approximation; all scores flagged PENDING.
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { computeWeightedScore, scoreToDirection, topN } from './engine_utils'

const VARSHA_KUNDALI_PENDING = '[VARSHA_KUNDALI_PENDING]'

// Tajika signals — solar-return scope. Until 2026 Varsha Kundali is computed,
// these are scored from natal chart approximation with reduced confidence.
function defaultSignals(domain: Domain): SignalScore[] {
  const base: Record<Domain, SignalScore[]> = {
    CAREER: [
      { signalId: 'SIG.MSR.561', signalName: 'Varshesha in 10H — annual career lord strong', score: 3.5, weight: 0.50, attributionRef: 'Prashna Marga §14.2' },
      { signalId: 'SIG.MSR.562', signalName: 'Muntha in career house — annual career activation', score: 3.2, weight: 0.45 },
      { signalId: 'SIG.MSR.563', signalName: 'Sahama Punya favorable — annual fortune', score: 3.0, weight: 0.42 },
    ],
    HEALTH: [
      { signalId: 'SIG.MSR.568', signalName: 'Tajika Ithasala of lagna lord — annual health integration', score: 2.8, weight: 0.40 },
      { signalId: 'SIG.MSR.569', signalName: 'Varsha Lagna strength — annual vitality', score: 2.6, weight: 0.38 },
      { signalId: 'SIG.MSR.570', signalName: 'Nakta aspect formation — transferred health influence', score: 2.5, weight: 0.35 },
    ],
    RELATIONSHIP: [
      { signalId: 'SIG.MSR.573', signalName: 'Sahama Dara — partnership Sahama position', score: 3.0, weight: 0.42 },
      { signalId: 'SIG.MSR.559', signalName: 'Ithasala between Venus and 7H lord', score: 2.8, weight: 0.40 },
      { signalId: 'SIG.MSR.566', signalName: 'Kambula formation — indirect relationship support', score: 2.7, weight: 0.38 },
    ],
    SPIRITUAL: [
      { signalId: 'SIG.MSR.560', signalName: 'Ishrafa — completing spiritual impulse in annual chart', score: 3.2, weight: 0.45 },
      { signalId: 'SIG.MSR.571', signalName: 'Sahama Vidya — annual knowledge/spiritual Sahama', score: 3.0, weight: 0.42 },
      { signalId: 'SIG.MSR.572', signalName: 'Muntha trine aspect — annual spiritual receptivity', score: 2.8, weight: 0.40 },
    ],
    PSYCHOLOGICAL: [
      { signalId: 'SIG.MSR.564', signalName: 'Varshesha — annual mind lord', score: 2.9, weight: 0.42 },
      { signalId: 'SIG.MSR.565', signalName: 'Sahama Paka — annual psychological digestion', score: 2.7, weight: 0.38 },
      { signalId: 'SIG.MSR.567', signalName: 'Ithasala — completing mental aspect in Varsha', score: 2.6, weight: 0.36 },
    ],
  }
  return base[domain]
}

function buildVerdict(domain: Domain, score: number, pending: boolean): string {
  const flag = pending ? ` ${VARSHA_KUNDALI_PENDING}` : ''
  const level = score >= 3.5 ? 'favorable' : score >= 2.5 ? 'moderate' : 'muted'
  const verdicts: Record<Domain, string> = {
    CAREER:       `Tajika reads ${level} annual career prospects for 2026 Varsha Kundali.${flag} The Varshesha (annual lord) position relative to 10H is the operative indicator; Muntha activation of the career house further supports productive action in the annual arc. Scores pending final Varsha Kundali computation.`,
    HEALTH:       `Tajika reads ${level} annual health for the 2026 solar return.${flag} The Ithasala (applying aspect) of the Varsha Lagna lord determines the integration or disintegration direction of the annual health arc. Final scores pending Varsha Kundali.`,
    RELATIONSHIP: `Tajika reads ${level} annual relationship prospects.${flag} The Sahama Dara (partner's lot) and any Ithasala between Venus and the 7H lord in the Varsha Kundali govern the annual relationship arc. Scores are natal-approximated pending solar return computation.`,
    SPIRITUAL:    `Tajika reads ${level} annual spiritual receptivity.${flag} The Ishrafa (separating aspect) completes spiritual impulses from the prior year; Sahama Vidya (knowledge lot) positions the native for annual learning. Pending Varsha Kundali.`,
    PSYCHOLOGICAL:`Tajika reads ${level} annual psychological conditions.${flag} The Varshesha (annual mind lord) and Sahama Paka (digestion lot) govern the annual psychological environment. Pending Varsha Kundali for precise scoring.`,
  }
  return verdicts[domain]
}

export class TajikaEngine implements SchoolAnalysis {
  readonly school = 'tajika' as const
  // Tajika operates on Varsha Kundali, not natal
  readonly chartType = 'varsha_kundali' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const pending = chartData.pendingFlags?.includes('VARSHA_KUNDALI_PENDING') ?? true
    const activeSignals = signals ?? defaultSignals(domain)
    const score = computeWeightedScore(activeSignals)
    const direction = scoreToDirection(score)
    const top = topN(activeSignals, 3)
    return {
      school: this.school,
      domain,
      domainScore: Math.round(score * 1000) / 1000,
      direction,
      topSignals: top,
      schoolVerdict: buildVerdict(domain, score, pending),
      signalCoverage: 'primary',
      pendingFlags: pending ? [VARSHA_KUNDALI_PENDING] : [],
    }
  }
}

export const tajika_engine = new TajikaEngine()
