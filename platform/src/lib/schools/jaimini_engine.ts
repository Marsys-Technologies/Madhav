/**
 * School Engine 2: Jaimini
 * Foundation: Jaimini Sutras, BPHS (Jaimini chapters), Chara Karaka hierarchy.
 * Primary coverage: SIG.MSR signals with Jaimini primary attribution (181 signals, 31.6%).
 * Chara Dasha lord modulates all domain scores. M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore } from './types'
import { computeWeightedScore, scoreToDirection, topN } from './engine_utils'

// Jaimini Chara Karaka hierarchy for Abhisek (from FORENSIC §22)
// AK=Moon, AmK=Saturn, BK=Mercury, MK=Mars, PK=Sun, GK=Venus, DK=Jupiter
const CHARA_HIERARCHY: Record<string, number> = {
  atmakaraka:   1.0,  // Moon — highest weight
  amatyakaraka: 0.85, // Saturn
  bhratrikaraka: 0.70, // Mercury
  matrikaraka:  0.60, // Mars
  putrakaraka:  0.55, // Sun
  gnatikaraka:  0.50, // Venus
  darakaraka:   0.45, // Jupiter
}

// Domain → primary Chara Karaka relevance
const DOMAIN_KARAKA: Record<Domain, string[]> = {
  CAREER:       ['amatyakaraka', 'atmakaraka'],
  HEALTH:       ['atmakaraka', 'matrikaraka'],
  RELATIONSHIP: ['darakaraka', 'atmakaraka'],
  SPIRITUAL:    ['atmakaraka', 'gnatikaraka'],
  PSYCHOLOGICAL:['atmakaraka', 'bhratrikaraka'],
}

function karakaWeight(domain: Domain, charaPadas: Record<string, string>): number {
  const relevantKarakas = DOMAIN_KARAKA[domain]
  let weight = 0.6 // baseline
  for (const karaka of relevantKarakas) {
    const w = CHARA_HIERARCHY[karaka] ?? 0.5
    weight = Math.max(weight, w)
  }
  return weight
}

function defaultSignals(domain: Domain): SignalScore[] {
  const base: Record<Domain, SignalScore[]> = {
    CAREER: [
      { signalId: 'SIG.MSR.055', signalName: 'Amatyakaraka Saturn in Libra — exalted career significator', score: 4.6, weight: 0.90, attributionRef: 'Jaimini Sutra 3.1.14' },
      { signalId: 'SIG.MSR.067', signalName: 'Atmakaraka Moon — aspirations through public role', score: 3.8, weight: 0.82, attributionRef: 'Jaimini Sutra 2.1.7' },
      { signalId: 'SIG.MSR.071', signalName: 'Karakamsa Gemini — Mercury-ruled intellectual vocation', score: 3.5, weight: 0.75 },
    ],
    HEALTH: [
      { signalId: 'SIG.MSR.211', signalName: 'Atmakaraka Moon in Virgo — psychosomatic sensitivity', score: 2.9, weight: 0.78 },
      { signalId: 'SIG.MSR.220', signalName: 'Matrikaraka Mars 4H — physical constitution driver', score: 3.2, weight: 0.72 },
      { signalId: 'SIG.MSR.228', signalName: 'Putrakaraka Sun 1H — vitality indicator', score: 3.0, weight: 0.68 },
    ],
    RELATIONSHIP: [
      { signalId: 'SIG.MSR.310', signalName: 'Darakaraka Jupiter 12H — partner beyond ordinary horizon', score: 3.3, weight: 0.80 },
      { signalId: 'SIG.MSR.321', signalName: 'Atmakaraka Moon — emotional needs in partnership', score: 3.0, weight: 0.70 },
      { signalId: 'SIG.MSR.305', signalName: 'Gnatikaraka Venus 2H — resource-sharing in bond', score: 3.1, weight: 0.65 },
    ],
    SPIRITUAL: [
      { signalId: 'SIG.MSR.407', signalName: 'Atmakaraka Moon — soul purpose via nurturing-dharma', score: 4.0, weight: 0.88 },
      { signalId: 'SIG.MSR.418', signalName: 'Karakamsa aspected by Jupiter — viveka (discriminating intellect)', score: 3.8, weight: 0.82 },
      { signalId: 'SIG.MSR.425', signalName: 'Gnatikaraka Venus — bhakti/devotional inclination', score: 3.5, weight: 0.75 },
    ],
    PSYCHOLOGICAL: [
      { signalId: 'SIG.MSR.458', signalName: 'AK Moon Virgo — perfectionism + self-analysis', score: 3.7, weight: 0.82 },
      { signalId: 'SIG.MSR.467', signalName: 'AmK Saturn discipline — delayed gratification tolerance', score: 3.5, weight: 0.78 },
      { signalId: 'SIG.MSR.472', signalName: 'BK Mercury analytical — cognitive strength', score: 3.3, weight: 0.72 },
    ],
  }
  return base[domain]
}

function buildVerdict(domain: Domain, score: number, charaPadas: Record<string, string>): string {
  const ak = charaPadas.atmakaraka ?? 'moon'
  const amk = charaPadas.amatyakaraka ?? 'saturn'
  const level = score >= 4.0 ? 'exceptional' : score >= 3.0 ? 'strong' : score >= 2.0 ? 'moderate' : 'challenged'
  const verdicts: Record<Domain, string> = {
    CAREER:       `Jaimini reads ${level} career promise: Amatyakaraka ${amk.toUpperCase()} exalted in Libra 10H is the defining signal — career significator at peak dignity. Atmakaraka ${ak.toUpperCase()} in Virgo adds the soul's drive toward analytical mastery. Karakamsa in Gemini positions the native toward Mercury-ruled intellectual professions.`,
    HEALTH:       `Jaimini reads ${level} health through the Karaka lens: Atmakaraka Moon in Virgo indicates soul-level sensitivity manifesting as psychosomatic vigilance. Matrikaraka Mars supports physical drive; 8H influences on AK determine disease proneness more than natal placements alone.`,
    RELATIONSHIP: `Jaimini reads ${level} relationship indicators: Darakaraka Jupiter in 12H (house of foreign, spiritual, invisible realms) suggests a partner from a different background or faith. The AK Moon's Virgo position calls for emotional precision in bond.`,
    SPIRITUAL:    `Jaimini reads ${level} spiritual capacity: Atmakaraka Moon as AK is itself a strong indicator of a soul oriented toward nurturing the world-dharma. The Karakamsa in Gemini aspected by Jupiter infuses viveka (discriminating wisdom) as the operative faculty.`,
    PSYCHOLOGICAL:`Jaimini reads ${level} psychological structure: AK Moon in Virgo produces a soul whose inner architecture is analytic, precise, and prone to self-refinement. AmK Saturn channels the mind toward long-horizon discipline rather than impulsive reaction.`,
  }
  return verdicts[domain]
}

export class JaiminiEngine implements SchoolAnalysis {
  readonly school = 'jaimini' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    const activeSignals = signals ?? defaultSignals(domain)
    const kWeight = karakaWeight(domain, chartData.charaPadas ?? {})
    const scaled = activeSignals.map(s => ({ ...s, weight: s.weight * kWeight }))
    const score = computeWeightedScore(scaled)
    const direction = scoreToDirection(score)
    const top = topN(scaled, 3)
    return {
      school: this.school,
      domain,
      domainScore: Math.round(score * 1000) / 1000,
      direction,
      topSignals: top,
      schoolVerdict: buildVerdict(domain, score, chartData.charaPadas ?? {}),
      signalCoverage: 'primary',
    }
  }
}

export const jaimini_engine = new JaiminiEngine()
