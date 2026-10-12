/**
 * School Engine 1: Parashari
 * Foundation: BPHS, Phaladeepika, Saravali, Brihat Jataka, Brihat Samhita, Uttara Kalamrita.
 * Primary coverage: natal yoga signals SIG.MSR.001–514 (89.7% of MSR v5.0).
 *
 * No default signal set: the engine analyses only the live signals the caller passes in.
 * undefined or [] => honest not-available result (SS N-362/N-363; CLAUDE.md §N.7).
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { analyzeFromSignals, topSignalNames } from './engine_utils'

function buildVerdict(domain: Domain, score: number, top: SignalScore[], used: SignalScore[]): string {
  const level = score >= 4.0 ? 'exceptional' : score >= 3.0 ? 'strong' : score >= 2.0 ? 'moderate' : 'challenged'
  const strongest = topSignalNames(top)
  return `Parashari framework reads a ${level} ${domain} picture from ${used.length} live signal(s) (weighted score ${score.toFixed(2)} / 5.0). Strongest: ${strongest}.`
}

export class ParashariEngine implements SchoolAnalysis {
  readonly school = 'parashari' as const
  readonly chartType = 'natal' as const

  async analyze(_chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    return analyzeFromSignals({
      school: this.school,
      domain,
      signals,
      verdict: (score, top, used) => buildVerdict(domain, score, top, used),
    })
  }
}

export const parashari_engine = new ParashariEngine()
