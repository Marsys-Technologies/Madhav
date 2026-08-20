/**
 * pariprashna/corpus/dimensions/cross_domain_contradiction_surfaced.ts —
 * lane P2-N (G3-F).
 *
 * Roadmap Gate 3 evidence line: "a planted-contradiction fixture surfaced,
 * not smoothed". The authoritative future signal is G3-B's structured
 * `interpretation_sets` output (rules-in-tension metadata) — not merged in
 * this worktree's base. This module is a CORPUS-OWNED heuristic pending
 * G3-B, combining two real, checkable signals:
 *
 *   1. `receipt.cross_domain` (G3-A, merged) — did the plan actually
 *      authorize multiple domains for this turn (a contradiction spanning
 *      one domain alone is not cross-domain).
 *   2. A tension-acknowledging lexicon scanned over the turn's own served
 *      prose — does the text actually name the tension ("simultaneously",
 *      "at the same time", "both ... and", "tension") rather than silently
 *      picking one side.
 *
 * Scoped to `cross_domain_contradiction`-class fixtures only. Residual: once
 * G3-B lands, prefer checking its `rules_in_tension` structured flag over
 * this lexicon scan, the same upgrade path `voice_enforcement.ts` names for
 * G3-D.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const CROSS_DOMAIN_CONTRADICTION_SURFACED_DIMENSION = 'cross_domain_contradiction_surfaced' as const

const TENSION_LEXICON: RegExp[] = [
  /\bsimultaneously\b/i,
  /\bat the same time\b/i,
  /\btension\b/i,
  /\bboth\b.{0,40}\band\b/i,
  /\bnot (merely|just)\b.{0,40}\bbut also\b/i,
  /\bparadox\b/i,
]

export function scoreCrossDomainContradictionSurfaced(obs: TurnObservation): DimensionResult {
  const { fixture, receipt, proseText } = obs

  if (fixture.queryClass !== 'cross_domain_contradiction') {
    return {
      dimension: CROSS_DOMAIN_CONTRADICTION_SURFACED_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'scoring is scoped to cross_domain_contradiction-class fixtures',
      findings: [],
    }
  }

  if (!receipt || proseText === null) {
    return {
      dimension: CROSS_DOMAIN_CONTRADICTION_SURFACED_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'requires both a receipt and prose text for this observation',
      findings: [],
    }
  }

  const findings: string[] = []
  let domainComponent = 0
  if (receipt.cross_domain.status === 'measured' && (receipt.cross_domain.domains?.length ?? 0) >= 2) {
    domainComponent = 1
  } else {
    findings.push('receipt.cross_domain does not show 2+ authorized domains for a cross-domain-contradiction query')
  }

  const tensionHit = TENSION_LEXICON.some((re) => re.test(proseText))
  if (!tensionHit) {
    findings.push('no tension-acknowledging language found in served prose — possible smoothing, not surfacing')
  }

  const score = (domainComponent + (tensionHit ? 1 : 0)) / 2
  return { dimension: CROSS_DOMAIN_CONTRADICTION_SURFACED_DIMENSION, status: 'scored', score, reason: null, findings }
}
