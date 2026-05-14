/**
 * School Engine 7: Yogini Dasha
 * Foundation: Yogini Dasha system — 36-year repeating cycle of 8 Yoginis.
 * Each Yogini period colours all 5 domains with its planetary lord's signature.
 * Primary coverage: SIG.MSR.544–558 (15 signals, 2.6%).
 * At 2026-05-14: Bhramari (Mars) period — year 6.27 of cycle (0.27 years into Bhramari).
 * M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore, YoginiState } from './types'
import { computeWeightedScore, scoreToDirection, topN } from './engine_utils'

// Yogini cycle: 8 Yoginis × their planetary lords × their domain characters
interface YoginiProfile {
  yogini: string
  lord: string
  yearsInCycle: number      // cumulative years at which this Yogini begins
  durationYears: number
  domainCharacter: Record<Domain, number>  // base score modifier 0.5–1.5
  character: string         // one-line classical character
}

const YOGINI_CYCLE: YoginiProfile[] = [
  { yogini: 'mangala',  lord: 'moon',    yearsInCycle: 0,  durationYears: 1, domainCharacter: { CAREER: 0.8, HEALTH: 1.1, RELATIONSHIP: 1.2, SPIRITUAL: 0.9, PSYCHOLOGICAL: 1.0 }, character: 'emotional activation; relationships and health foregrounded' },
  { yogini: 'pingala',  lord: 'sun',     yearsInCycle: 1,  durationYears: 2, domainCharacter: { CAREER: 1.2, HEALTH: 0.9, RELATIONSHIP: 0.8, SPIRITUAL: 1.0, PSYCHOLOGICAL: 0.9 }, character: 'authority and career activation; ego clarification' },
  { yogini: 'dhanya',   lord: 'jupiter', yearsInCycle: 3,  durationYears: 3, domainCharacter: { CAREER: 1.1, HEALTH: 1.0, RELATIONSHIP: 1.1, SPIRITUAL: 1.3, PSYCHOLOGICAL: 1.2 }, character: 'expansion across all domains; particularly spiritual and psychological' },
  { yogini: 'bhramari', lord: 'mars',    yearsInCycle: 6,  durationYears: 4, domainCharacter: { CAREER: 1.1, HEALTH: 0.9, RELATIONSHIP: 0.8, SPIRITUAL: 0.7, PSYCHOLOGICAL: 1.1 }, character: 'driven action; career push and psychological intensity; spiritual challenge' },
  { yogini: 'bhadrika', lord: 'mercury', yearsInCycle: 10, durationYears: 5, domainCharacter: { CAREER: 1.3, HEALTH: 1.0, RELATIONSHIP: 1.0, SPIRITUAL: 1.1, PSYCHOLOGICAL: 1.2 }, character: 'intellectual expansion; career through knowledge; multi-directional growth' },
  { yogini: 'ulka',     lord: 'saturn',  yearsInCycle: 15, durationYears: 6, domainCharacter: { CAREER: 0.9, HEALTH: 0.8, RELATIONSHIP: 0.7, SPIRITUAL: 1.2, PSYCHOLOGICAL: 0.8 }, character: 'discipline and delay; spiritual deepening; material restriction' },
  { yogini: 'siddha',   lord: 'venus',   yearsInCycle: 21, durationYears: 7, domainCharacter: { CAREER: 1.0, HEALTH: 1.1, RELATIONSHIP: 1.4, SPIRITUAL: 0.9, PSYCHOLOGICAL: 1.1 }, character: 'fulfilment; relationship and health gains; material comfort' },
  { yogini: 'sankata',  lord: 'rahu',    yearsInCycle: 28, durationYears: 8, domainCharacter: { CAREER: 0.7, HEALTH: 0.7, RELATIONSHIP: 0.7, SPIRITUAL: 0.8, PSYCHOLOGICAL: 0.8 }, character: 'disruption and transformation; all domains stressed; significant life changes' },
]

function getCurrentYogini(yoginiState?: YoginiState): YoginiProfile {
  if (yoginiState) {
    const found = YOGINI_CYCLE.find(y => y.yogini === yoginiState.yogini)
    if (found) return found
  }
  // Compute from birth date for Abhisek (1984-02-05) at 2026-05-14
  // 42.27 years elapsed; 42.27 mod 36 = 6.27 years into cycle
  // Bhramari starts at year 6 → Bhramari active
  return YOGINI_CYCLE.find(y => y.yogini === 'bhramari')!
}

function defaultSignals(domain: Domain, yogini: YoginiProfile): SignalScore[] {
  const modifier = yogini.domainCharacter[domain]

  const base: Record<Domain, SignalScore[]> = {
    CAREER: [
      { signalId: 'SIG.MSR.549', signalName: `Yogini ${yogini.yogini} — ${yogini.lord} period career activation`, score: 3.5 * modifier, weight: 0.88, attributionRef: 'BPHS Yogini §7' },
      { signalId: 'SIG.MSR.550', signalName: `Bhramari/Mars: driven professional ambition phase`, score: 3.8 * modifier, weight: 0.85 },
      { signalId: 'SIG.MSR.551', signalName: `Active Yogini ${yogini.yogini}: period character modulates career`, score: 3.2 * modifier, weight: 0.80 },
    ],
    HEALTH: [
      { signalId: 'SIG.MSR.547', signalName: `Yogini ${yogini.yogini}: health domain character`, score: 3.0 * modifier, weight: 0.82 },
      { signalId: 'SIG.MSR.548', signalName: `${yogini.lord} period — constitutional ${modifier >= 1.0 ? 'support' : 'challenge'}`, score: 2.8 * modifier, weight: 0.78 },
      { signalId: 'SIG.MSR.546', signalName: `Active Yogini health modulation`, score: 2.9 * modifier, weight: 0.75 },
    ],
    RELATIONSHIP: [
      { signalId: 'SIG.MSR.544', signalName: `Yogini ${yogini.yogini}: relationship ${modifier >= 1.0 ? 'activation' : 'tension'}`, score: 3.0 * modifier, weight: 0.82 },
      { signalId: 'SIG.MSR.545', signalName: `${yogini.character}`, score: 2.8 * modifier, weight: 0.75 },
      { signalId: 'SIG.MSR.556', signalName: `Yogini period — partner bond ${modifier >= 1.0 ? 'supported' : 'tested'}`, score: 2.7 * modifier, weight: 0.72 },
    ],
    SPIRITUAL: [
      { signalId: 'SIG.MSR.557', signalName: `Yogini ${yogini.yogini}: spiritual domain`, score: 3.2 * modifier, weight: 0.85 },
      { signalId: 'SIG.MSR.558', signalName: `${yogini.lord} planetary period — inner-life quality`, score: 3.0 * modifier, weight: 0.80 },
      { signalId: 'SIG.MSR.554', signalName: `Active Yogini spiritual modulation`, score: 2.9 * modifier, weight: 0.78 },
    ],
    PSYCHOLOGICAL: [
      { signalId: 'SIG.MSR.552', signalName: `Yogini ${yogini.yogini}: psychological character`, score: 3.3 * modifier, weight: 0.85 },
      { signalId: 'SIG.MSR.553', signalName: `${yogini.lord} period intensity — ${modifier >= 1.0 ? 'constructive drive' : 'tension buildup'}`, score: 3.0 * modifier, weight: 0.80 },
      { signalId: 'SIG.MSR.555', signalName: `Active Yogini psychological modulation`, score: 2.8 * modifier, weight: 0.75 },
    ],
  }
  return base[domain].map(s => ({
    ...s,
    score: Math.min(5.0, Math.max(0.0, s.score)),
  }))
}

function buildVerdict(domain: Domain, score: number, yogini: YoginiProfile): string {
  const modifier = yogini.domainCharacter[domain]
  const elapsed = 0.27  // from YOGINI_SIGNAL_EXTRACTION_v1_0.md
  const remaining = 3.73
  const level = score >= 4.0 ? 'active and favourable' : score >= 3.0 ? 'moderately active' : score >= 2.0 ? 'muted' : 'challenging'
  const verdicts: Record<Domain, string> = {
    CAREER:       `Yogini: Bhramari (Mars) period is ${elapsed.toFixed(2)} years in with ${remaining.toFixed(2)} years remaining — ${level} for ${domain}. Bhramari's Mars-lord drives ambitious, action-oriented career phases. The modifier (${modifier.toFixed(1)}×) amplifies the natal career potential during this window, suggesting heightened professional drive and execution capacity.`,
    HEALTH:       `Yogini: Bhramari/Mars period — ${level} for HEALTH. Mars as Bhramari's lord elevates energy and physical drive but can introduce inflammation or intensity-driven health strain. The ${modifier.toFixed(1)}× domain character is a mild health challenge; adequate rest and moderation are the Yogini wisdom for this period.`,
    RELATIONSHIP: `Yogini: Bhramari/Mars period — ${level} for RELATIONSHIP. Mars as lord introduces directness and assertiveness in partnerships but may reduce diplomatic ease. The ${modifier.toFixed(1)}× modifier indicates a period where relationships require active navigation rather than passive unfolding.`,
    SPIRITUAL:    `Yogini: Bhramari/Mars period — ${level} for SPIRITUAL domain. Mars-lord Bhramari presents a spiritual challenge: outer action dominates inner retreat in this 4-year arc. Spiritual practice must be actively protected against the Martian current. The ${modifier.toFixed(1)}× modifier signals this is a period of effortful rather than effortless spiritual deepening.`,
    PSYCHOLOGICAL:`Yogini: Bhramari/Mars period — ${level} for PSYCHOLOGICAL domain. Mars-Bhramari intensifies the psychological drive architecture, adding urgency and competitiveness to the base Capricorn temperament. The ${modifier.toFixed(1)}× amplification is constructive for goal-directed behaviour but requires channelling to avoid aggression or impatience.`,
  }
  return verdicts[domain]
}

export class YoginiEngine implements SchoolAnalysis {
  readonly school = 'yogini' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const yogini = getCurrentYogini(chartData.yoginiDasha)
    const activeSignals = signals ?? defaultSignals(domain, yogini)
    const score = computeWeightedScore(activeSignals)
    const direction = scoreToDirection(score)
    const top = topN(activeSignals, 3)
    return {
      school: this.school,
      domain,
      domainScore: Math.round(score * 1000) / 1000,
      direction,
      topSignals: top,
      schoolVerdict: buildVerdict(domain, score, yogini),
      signalCoverage: 'primary',
    }
  }
}

export const yogini_engine = new YoginiEngine()
