/**
 * School Engine 4: Krishnamurti Paddhati (KP)
 * Foundation: KP sub-lord system; star-lord chain determines signal activation.
 * Primary coverage: SIG.MSR signals with KP primary attribution (95 signals, 16.6%).
 * Sub-lord of each cusp determines whether natal promise is activated.
 *
 * No default signal set and no per-chart sub-lord constants: the engine analyses only the
 * live signals the caller passes in. undefined or [] => honest not-available result
 * (SS N-362/N-363; CLAUDE.md §N.7). M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { analyzeFromSignals, topSignalNames } from './engine_utils'

// KP house significators for each domain (classical primary cusps; chart-independent)
const DOMAIN_CUSPS: Record<Domain, number[]> = {
  CAREER:       [10, 6, 2],    // 10H profession, 6H service, 2H income
  HEALTH:       [1, 6, 8, 12], // 1H vitality, 6H disease, 8H chronic, 12H hospitalisation
  RELATIONSHIP: [7, 2, 11],    // 7H partner, 2H family, 11H fulfilment
  SPIRITUAL:    [9, 5, 12],    // 9H dharma, 5H mantra/putra, 12H moksha
  PSYCHOLOGICAL:[1, 4, 5],     // 1H self, 4H mind, 5H intellect
}

function buildVerdict(domain: Domain, score: number, top: SignalScore[], used: SignalScore[]): string {
  const level = score >= 4.0 ? 'strong' : score >= 3.0 ? 'confirmed' : score >= 2.0 ? 'conditional' : 'unactivated'
  const cusps = DOMAIN_CUSPS[domain].map(c => `${c}H`).join(', ')
  return `KP reads ${level} ${domain} promise from ${used.length} live signal(s) (weighted score ${score.toFixed(2)} / 5.0) over the domain cusps (${cusps}). Strongest: ${topSignalNames(top)}.`
}

export class KPEngine implements SchoolAnalysis {
  readonly school = 'kp' as const
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

export const kp_engine = new KPEngine()
