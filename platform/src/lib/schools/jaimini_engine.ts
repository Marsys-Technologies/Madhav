/**
 * School Engine 2: Jaimini
 * Foundation: Jaimini Sutras, BPHS (Jaimini chapters), Chara Karaka hierarchy.
 * Primary coverage: SIG.MSR signals with Jaimini primary attribution (181 signals, 31.6%).
 * Chara Dasha lord modulates all domain scores. M9-B-S1 (2026-05-14).
 *
 * No default signal set: the engine analyses only the live signals the caller passes in.
 * undefined or [] => honest not-available result (SS N-362/N-363; CLAUDE.md §N.7).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { analyzeFromSignals, topSignalNames } from './engine_utils'

// Classical relative weight of each Chara Karaka ROLE (chart-independent: which planet
// holds a role is read from ChartData.charaPadas, never assumed here).
const CHARA_HIERARCHY: Record<string, number> = {
  atmakaraka:    1.0,
  amatyakaraka:  0.85,
  bhratrikaraka: 0.70,
  matrikaraka:   0.60,
  putrakaraka:   0.55,
  gnatikaraka:   0.50,
  darakaraka:    0.45,
}

// Domain → primary Chara Karaka relevance
const DOMAIN_KARAKA: Record<Domain, string[]> = {
  CAREER:       ['amatyakaraka', 'atmakaraka'],
  HEALTH:       ['atmakaraka', 'matrikaraka'],
  RELATIONSHIP: ['darakaraka', 'atmakaraka'],
  SPIRITUAL:    ['atmakaraka', 'gnatikaraka'],
  PSYCHOLOGICAL:['atmakaraka', 'bhratrikaraka'],
}

function karakaWeight(domain: Domain): number {
  let weight = 0.6 // baseline
  for (const karaka of DOMAIN_KARAKA[domain]) {
    weight = Math.max(weight, CHARA_HIERARCHY[karaka] ?? 0.5)
  }
  return weight
}

function buildVerdict(
  domain: Domain, score: number, top: SignalScore[], used: SignalScore[], charaPadas: Record<string, string> | undefined,
): string {
  const level = score >= 4.0 ? 'exceptional' : score >= 3.0 ? 'strong' : score >= 2.0 ? 'moderate' : 'challenged'
  const roles = DOMAIN_KARAKA[domain]
    .map(r => (charaPadas?.[r] ? `${r} ${charaPadas[r]}` : null))
    .filter((x): x is string => x !== null)
  const karakaPart = roles.length > 0 ? ` Relevant Chara Karakas (from the chart data): ${roles.join(', ')}.` : ''
  return `Jaimini reads ${level} ${domain} promise from ${used.length} live signal(s) (weighted score ${score.toFixed(2)} / 5.0).${karakaPart} Strongest: ${topSignalNames(top)}.`
}

export class JaiminiEngine implements SchoolAnalysis {
  readonly school = 'jaimini' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const kWeight = karakaWeight(domain)
    return analyzeFromSignals({
      school: this.school,
      domain,
      signals,
      prepare: live => live.map(s => ({ ...s, weight: s.weight * kWeight })),
      verdict: (score, top, used) => buildVerdict(domain, score, top, used, chartData.charaPadas),
    })
  }
}

export const jaimini_engine = new JaiminiEngine()
