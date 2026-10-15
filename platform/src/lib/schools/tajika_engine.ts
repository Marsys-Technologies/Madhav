/**
 * School Engine 3: Tajika
 * Foundation: Prashna Marga, Hora Sara, Tajika Neelakanthi (procurement pending).
 * Operates on Varsha Kundali (annual solar return chart), NOT the natal chart.
 * Primary coverage: SIG.MSR.559–573 (15 signals; solar_return_scope:true).
 * CF.M9.1 [VARSHA_KUNDALI_PENDING]: the Varsha Kundali requires Swiss Ephemeris.
 *
 * No default signal set: the engine analyses only the live signals the caller passes in.
 * undefined or [] => honest not-available result (SS N-362/N-363; CLAUDE.md §N.7).
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { analyzeFromSignals, topSignalNames } from './engine_utils'

const VARSHA_KUNDALI_PENDING = '[VARSHA_KUNDALI_PENDING]'

function buildVerdict(domain: Domain, score: number, top: SignalScore[], used: SignalScore[], pending: boolean): string {
  const flag = pending ? ` ${VARSHA_KUNDALI_PENDING}` : ''
  const level = score >= 3.5 ? 'favorable' : score >= 2.5 ? 'moderate' : 'muted'
  return `Tajika reads ${level} annual ${domain} prospects from ${used.length} live signal(s) (weighted score ${score.toFixed(2)} / 5.0).${flag} Strongest: ${topSignalNames(top)}.`
}

export class TajikaEngine implements SchoolAnalysis {
  readonly school = 'tajika' as const
  // Tajika operates on Varsha Kundali, not natal
  readonly chartType = 'varsha_kundali' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const pending = chartData.pendingFlags?.includes('VARSHA_KUNDALI_PENDING') ?? true
    return analyzeFromSignals({
      school: this.school,
      domain,
      signals,
      verdict: (score, top, used) => buildVerdict(domain, score, top, used, pending),
      pendingFlags: pending ? [VARSHA_KUNDALI_PENDING] : [],
    })
  }
}

export const tajika_engine = new TajikaEngine()
