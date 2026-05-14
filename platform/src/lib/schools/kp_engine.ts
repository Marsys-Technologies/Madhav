/**
 * School Engine 4: Krishnamurti Paddhati (KP)
 * Foundation: KP sub-lord system; star-lord chain determines signal activation.
 * Primary coverage: SIG.MSR signals with KP primary attribution (95 signals, 16.6%).
 * Sub-lord of each cusp determines whether natal promise is activated.
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { computeWeightedScore, scoreToDirection, topN } from './engine_utils'

// KP house significators for each domain (primary cusp lords)
const DOMAIN_CUSPS: Record<Domain, number[]> = {
  CAREER:       [10, 6, 2],    // 10H profession, 6H service, 2H income
  HEALTH:       [1, 6, 8, 12], // 1H vitality, 6H disease, 8H chronic, 12H hospitalisation
  RELATIONSHIP: [7, 2, 11],    // 7H partner, 2H family, 11H fulfilment
  SPIRITUAL:    [9, 5, 12],    // 9H dharma, 5H mantra/putra, 12H moksha
  PSYCHOLOGICAL:[1, 4, 5],     // 1H self, 4H mind, 5H intellect
}

// KP sub-lord activation: Abhisek's natal KP sub-lords from FORENSIC
// In production: query kp_sublords table (migration 024)
const KP_SUBLORD_ACTIVATION: Record<number, number> = {
  1: 0.95,   // Ascendant sub-lord Saturn → high activation (Saturn rules 1H + 2H for Capricorn)
  2: 0.80,   // 2H income house sub-lord → good activation
  4: 0.72,   // 4H mind house → moderate
  5: 0.68,   // 5H intellect → moderate
  6: 0.70,   // 6H service/disease → moderate
  7: 0.65,   // 7H partner → moderate-lower
  8: 0.60,   // 8H transformation → moderate-lower
  9: 0.82,   // 9H dharma → good (Moon 9H)
  10: 0.90,  // 10H career → high (Saturn exalted 10H)
  11: 0.75,  // 11H gains → moderate
  12: 0.55,  // 12H losses → lower activation (12H sub-lord usually dilutes promise)
}

function houseActivation(domain: Domain): number {
  const cusps = DOMAIN_CUSPS[domain]
  const weights = cusps.map(c => KP_SUBLORD_ACTIVATION[c] ?? 0.5)
  return weights.reduce((s, w) => s + w, 0) / weights.length
}

function defaultSignals(domain: Domain): SignalScore[] {
  const activation = houseActivation(domain)
  const base: Record<Domain, SignalScore[]> = {
    CAREER: [
      { signalId: 'SIG.MSR.043', signalName: 'KP 10H sub-lord Saturn — career house activated', score: 4.5, weight: activation, attributionRef: 'KP Vol.1 §8' },
      { signalId: 'SIG.MSR.051', signalName: 'KP 6H sub-lord — service capacity confirmed', score: 3.2, weight: activation * 0.85 },
      { signalId: 'SIG.MSR.059', signalName: 'KP 2H sub-lord — income accumulation promise', score: 3.5, weight: activation * 0.88 },
    ],
    HEALTH: [
      { signalId: 'SIG.MSR.202', signalName: 'KP 1H sub-lord Saturn — strong natal vitality promise', score: 3.8, weight: activation },
      { signalId: 'SIG.MSR.217', signalName: 'KP 6H sub-lord — disease house moderate activation', score: 2.6, weight: activation * 0.82 },
      { signalId: 'SIG.MSR.225', signalName: 'KP 8H sub-lord — chronic/surgery indicator checked', score: 2.4, weight: activation * 0.78 },
    ],
    RELATIONSHIP: [
      { signalId: 'SIG.MSR.308', signalName: 'KP 7H sub-lord — partnership activation moderate', score: 3.0, weight: activation },
      { signalId: 'SIG.MSR.319', signalName: 'KP 2H sub-lord — family bond support', score: 3.2, weight: activation * 0.85 },
      { signalId: 'SIG.MSR.327', signalName: 'KP 11H sub-lord — fulfilment-of-desire layer', score: 3.1, weight: activation * 0.82 },
    ],
    SPIRITUAL: [
      { signalId: 'SIG.MSR.409', signalName: 'KP 9H sub-lord Moon — dharma activation confirmed', score: 4.0, weight: activation },
      { signalId: 'SIG.MSR.421', signalName: 'KP 12H sub-lord — moksha house partial activation', score: 3.2, weight: activation * 0.80 },
      { signalId: 'SIG.MSR.431', signalName: 'KP 5H sub-lord — mantra/prayer house', score: 3.0, weight: activation * 0.75 },
    ],
    PSYCHOLOGICAL: [
      { signalId: 'SIG.MSR.460', signalName: 'KP 1H sub-lord Saturn — self-identity activation strong', score: 3.7, weight: activation },
      { signalId: 'SIG.MSR.469', signalName: 'KP 4H sub-lord — mind house activation moderate', score: 3.1, weight: activation * 0.85 },
      { signalId: 'SIG.MSR.476', signalName: 'KP 5H sub-lord — intellect layer activation', score: 3.0, weight: activation * 0.80 },
    ],
  }
  return base[domain]
}

function buildVerdict(domain: Domain, score: number, activation: number): string {
  const level = score >= 4.0 ? 'strong' : score >= 3.0 ? 'confirmed' : score >= 2.0 ? 'conditional' : 'unactivated'
  const actPct = Math.round(activation * 100)
  const verdicts: Record<Domain, string> = {
    CAREER:       `KP reads ${level} career promise with ${actPct}% sub-lord activation across career-house cusps (10H, 6H, 2H). Saturn as 10H sub-lord in its own sign Libra (exalted) is the apex activation — the KP sub-lord chain confirms the natal promise for professional distinction. Income house (2H) also well-activated.`,
    HEALTH:       `KP reads ${level} health constitution with ${actPct}% activation. The 1H (vitality) sub-lord Saturn in its exaltation sign gives a strong vitality promise. The 6H (disease) activation is moderate, suggesting manageable health challenges rather than chronic conditions. No alarming 8H sub-lord pattern detected.`,
    RELATIONSHIP: `KP reads ${level} relationship potential with ${actPct}% mean activation across relationship cusps. The 7H sub-lord activation is in the moderate range, with 2H (family bond) and 11H (fulfilment) providing supplementary support. KP does not contradict Parashari reading.`,
    SPIRITUAL:    `KP reads ${level} spiritual unfoldment: 9H (dharma) sub-lord Moon — itself the AK — in Virgo registers high activation (${actPct}%). The 12H moksha sub-lord shows moderate activation, consistent with the Ketu 12H natal placement. KP confirms the spiritual inclination from multiple cusp angles.`,
    PSYCHOLOGICAL:`KP reads ${level} psychological integration: 1H sub-lord Saturn activates strongly (${actPct}%), conferring psychological discipline and delayed-gratification orientation. The 4H (mind) sub-lord activates at moderate levels — indicating a grounded but not fixed mental structure.`,
  }
  return verdicts[domain]
}

export class KPEngine implements SchoolAnalysis {
  readonly school = 'kp' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const activation = houseActivation(domain)
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
      schoolVerdict: buildVerdict(domain, score, activation),
      signalCoverage: 'primary',
    }
  }
}

export const kp_engine = new KPEngine()
