/**
 * School Engine 7: Yogini Dasha
 * Foundation: Yogini Dasha system — 36-year repeating cycle of 8 Yoginis.
 * Each Yogini period colours all 5 domains with its planetary lord's signature.
 * Primary coverage: SIG.MSR.544–558 (15 signals, 2.6%).
 *
 * No default signal set and no embedded birth date or dasha: the engine analyses only the live
 * signals the caller passes in, and names the running Yogini only when ChartData.yoginiDasha
 * carries it. undefined or [] signals => honest not-available result (SS N-362/N-363;
 * CLAUDE.md §N.7). M9-B-S1 (2026-05-14).
 */

import type { SchoolAnalysis, SchoolResult, ChartData, Domain, SignalScore, YoginiState } from './types'
import { analyzeFromSignals, topSignalNames } from './engine_utils'

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

/** The running Yogini profile, only when the passed ChartData carries it. Never assumed. */
function findYogini(yoginiState?: YoginiState): YoginiProfile | undefined {
  if (!yoginiState) return undefined
  return YOGINI_CYCLE.find(y => y.yogini === yoginiState.yogini)
}

function buildVerdict(
  domain: Domain, score: number, top: SignalScore[], used: SignalScore[], state?: YoginiState,
): string {
  const level = score >= 4.0 ? 'active and favourable' : score >= 3.0 ? 'moderately active' : score >= 2.0 ? 'muted' : 'challenging'
  const base = `Yogini reads the period as ${level} for ${domain} from ${used.length} live signal(s) (weighted score ${score.toFixed(2)} / 5.0).`
  const yogini = findYogini(state)
  const periodPart = yogini && state
    ? ` Running Yogini (from the chart data): ${yogini.yogini} (${yogini.lord}), ${state.yearsElapsed.toFixed(2)} years elapsed, ${state.yearsRemaining.toFixed(2)} remaining; classical ${domain} modifier ${yogini.domainCharacter[domain].toFixed(1)}x; character: ${yogini.character}.`
    : ' The running Yogini is not available in the chart data, so no period character is asserted.'
  return `${base}${periodPart} Strongest: ${topSignalNames(top)}.`
}

export class YoginiEngine implements SchoolAnalysis {
  readonly school = 'yogini' as const
  readonly chartType = 'natal' as const

  async analyze(chartData: ChartData, domain: Domain, signals?: SignalScore[]): Promise<SchoolResult> {
    return analyzeFromSignals({
      school: this.school,
      domain,
      signals,
      verdict: (score, top, used) => buildVerdict(domain, score, top, used, chartData.yoginiDasha),
    })
  }
}

export const yogini_engine = new YoginiEngine()
