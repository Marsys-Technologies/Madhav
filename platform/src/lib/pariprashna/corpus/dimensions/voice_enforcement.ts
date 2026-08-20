/**
 * pariprashna/corpus/dimensions/voice_enforcement.ts — lane P2-N (G3-F).
 *
 * G3-D (PPR-04, roadmap Gate 3) specifies the authoritative detector: "a
 * second-person-imperative detector on remedial-class blocks ('you should
 * wear' flags; 'the tradition prescribes' passes)". G3-D has not landed in
 * this worktree's base (dep: G2-A only, but not yet merged as of this
 * lane) — there is no production detector to reuse yet. This module is a
 * CORPUS-OWNED heuristic built from the roadmap's own concrete examples,
 * real and independently testable, but explicitly NOT the authoritative
 * G3-D detector. Residual: once G3-D lands, this scorer should be re-pointed
 * at G3-D's real detector output rather than its own regex, the same way
 * `register_leakage.ts` already reuses P2-E's counters instead of
 * re-deriving them.
 *
 * Scoped to `remedial`-class fixtures only (G3-D's own scope: "remedial-
 * class blocks") — any other class reports `not_yet_measurable` rather than
 * a score that would misrepresent what was actually checked.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const VOICE_ENFORCEMENT_DIMENSION = 'voice_enforcement' as const

/** "You should wear a red coral", "you must chant X" — the flagged shape. */
const IMPERATIVE_PATTERNS: RegExp[] = [
  /\byou (should|must|need to|ought to) (wear|chant|donate|fast|observe|perform|worship|recite|offer)\b/i,
  /\byou (should|must) (avoid|stop|start)\b/i,
]

export function scoreVoiceEnforcement(obs: TurnObservation): DimensionResult {
  const { fixture, proseText } = obs

  if (fixture.queryClass !== 'remedial') {
    return {
      dimension: VOICE_ENFORCEMENT_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'voice_enforcement scoring is scoped to remedial-class fixtures per G3-D (PPR-04)',
      findings: [],
    }
  }

  if (proseText === null) {
    return {
      dimension: VOICE_ENFORCEMENT_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no prose text was supplied for this observation',
      findings: [],
    }
  }

  const hits = IMPERATIVE_PATTERNS.filter((re) => re.test(proseText))
  if (hits.length === 0) {
    return { dimension: VOICE_ENFORCEMENT_DIMENSION, status: 'scored', score: 1, reason: null, findings: [] }
  }

  const findings = hits.map((re) => `second-person-imperative remedial phrasing matched (${re.source})`)
  const score = Math.max(0, 1 - hits.length / IMPERATIVE_PATTERNS.length)
  return { dimension: VOICE_ENFORCEMENT_DIMENSION, status: 'scored', score, reason: null, findings }
}
