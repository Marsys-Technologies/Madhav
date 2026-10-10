/**
 * School Engine 5: Nadi (Chandra Kala Nadi + Dhruva Nadi)
 * Foundation: Chandra Kala Nadi (CKN), Dhruva Nadi sampler.
 * Key distinction: Nadi reads house-from-planet (not house-from-Lagna).
 * Primary coverage: SIG.MSR.539–543 (CKN signals) + 2 cross-source Dhruva Nadi.
 * All other natal signals are SILENT for Nadi — different trigger mechanism.
 *
 * No default signal set: the engine analyses only the live signals the caller passes in.
 * undefined or [] => honest not-available result (SS N-362/N-363; CLAUDE.md §N.7).
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { analyzeFromSignals, topSignalNames } from './engine_utils'

function buildVerdict(domain: Domain, score: number, top: SignalScore[], used: SignalScore[]): string {
  const level = score >= 3.5 ? 'strong' : score >= 2.5 ? 'moderate' : 'limited'
  return `Nadi (CKN) reads ${level} ${domain} through the house-from-planet lens from ${used.length} live signal(s) (weighted score ${score.toFixed(2)} / 5.0). Nadi reads each planet's own house reckoning rather than Lagna-based convention, and its primary coverage is sparse. Strongest: ${topSignalNames(top)}.`
}

export class NadiEngine implements SchoolAnalysis {
  readonly school = 'nadi' as const
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

export const nadi_engine = new NadiEngine()
