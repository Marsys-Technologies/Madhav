/**
 * School Engine 6: BNN (Bhrigu Nandi Nadi)
 * Foundation: Bhrigu Nandi Nadi sequential transit analysis.
 * Trigger: Jupiter contacts a planet/node, then Saturn follows — sequential transit chains.
 * Primary coverage: SIG.MSR.515–538 (24 signals, 4.2%).
 * CF.M9.2 [TRANSIT_DATA_PENDING]: requires Swiss Ephemeris transit positions.
 *
 * No default signal set and no placeholder transit positions: the engine analyses only the
 * live signals the caller passes in. undefined or [] => honest not-available result
 * (SS N-362/N-363; CLAUDE.md §N.7). M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { analyzeFromSignals, topSignalNames } from './engine_utils'

const TRANSIT_DATA_PENDING = '[TRANSIT_DATA_PENDING]'

function buildVerdict(domain: Domain, score: number, top: SignalScore[], used: SignalScore[], pending: boolean): string {
  const flag = pending ? ` ${TRANSIT_DATA_PENDING}` : ''
  const level = score >= 3.5 ? 'active' : score >= 2.5 ? 'moderate' : 'dormant'
  return `BNN reads ${level} ${domain} transit chains from ${used.length} live signal(s) (weighted score ${score.toFixed(2)} / 5.0).${flag} BNN's operative mechanism is the sequential Jupiter-then-Saturn contact; exact transit positions are needed for timing precision. Strongest: ${topSignalNames(top)}.`
}

export class BNNEngine implements SchoolAnalysis {
  readonly school = 'bnn' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const pending = chartData.pendingFlags?.includes('TRANSIT_DATA_PENDING') ?? true
    return analyzeFromSignals({
      school: this.school,
      domain,
      signals,
      verdict: (score, top, used) => buildVerdict(domain, score, top, used, pending),
      pendingFlags: pending ? [TRANSIT_DATA_PENDING] : [],
    })
  }
}

export const bnn_engine = new BNNEngine()
