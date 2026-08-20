/**
 * pariprashna/corpus/qualification/work_classes.ts — lane P2-O (roadmap id
 * G3-G, PPR-32). PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md line 107:
 * "Per-work-class eval suites (factual/interpretive/predictive/sensitive); a
 * model serves a class only after passing".
 *
 * This module is the FIRST piece the roadmap line demands and the one most
 * likely to be done carelessly: mapping G3-F's 12 query classes onto the 4
 * named work classes. Two mappings are near-tautological (`factual` →
 * `factual`, `sensitive` → `sensitive`); the rest require real judgment, and
 * two of the 12 do not fit any of the 4 work classes at all and are
 * EXCLUDED with a stated reason rather than forced into a class they don't
 * belong to (the same "honest null beats an invented judgment" discipline
 * CLAUDE.md §N.7 item 6 states for narration, applied here to classification).
 *
 * ── The mapping, and why ────────────────────────────────────────────────
 *
 * factual → factual
 *   `factual-001-moon-nakshatra-lagna`: a pinpointed lookup against FORENSIC
 *   birth anchors. The obvious case.
 *
 * interpretive → interpretive_whole_chart, cross_domain_contradiction,
 *                 remedial, incomplete_evidence, returning_conversation_drift,
 *                 disagreement
 *   - `interpretive_whole_chart` is the class the work-class is named after —
 *     obvious.
 *   - `cross_domain_contradiction` requires synthesizing signals across
 *     domains (CLAUDE.md B.11 Whole-Chart-Read) into one coherent answer —
 *     that synthesis IS interpretation, not a fact lookup or a forecast.
 *   - `remedial` measures are classically PRESCRIBED FROM an interpretive
 *     reading (Saturn's affliction pattern → the remedy that addresses it);
 *     the remedy is downstream of interpretation, not a fourth independent
 *     capability, and nothing in the roadmap's 4-class list names "remedial"
 *     as its own class.
 *   - `incomplete_evidence` (the D-60 fixture) is an interpretive question
 *     (what a divisional chart indicates about karma) that happens to stress
 *     honest-gap disclosure under interpretation — the honesty requirement
 *     doesn't change what capability is being exercised.
 *   - `returning_conversation_drift` and `disagreement` are both interpretive
 *     content (career-authority claims, Mercury's convergence) wrapped in a
 *     conversational-dynamics test (reconciling history / holding a position
 *     under pushback). The capability under test is still "synthesize and
 *     defend an interpretation", not a distinct work class.
 *
 * predictive → timing, prediction_capture_outcome
 *   - `timing` is explicitly about what a dasha sub-period MEANS for future
 *     events — CLAUDE.md §A's own mission statement names "time-indexed,
 *     probabilistic, calibrated predictions" as the product; this fixture is
 *     that capability exercised directly.
 *   - `prediction_capture_outcome` is given verbatim in this lane's own brief
 *     as the obvious predictive-class mapping (a prior prediction, an
 *     outcome-recording request).
 *
 * sensitive → sensitive
 *   `sensitive-001-ayurdaya-longevity`: VERIFIED against the real
 *   `classifyQuery()` detector (fixtures.ts's own groundingNote) as an actual
 *   HS-4 mortality-window trigger. The obvious case, and the only fixture in
 *   the set that exercises the hard-stop safety path at all.
 *
 * EXCLUDED (fits none of the 4 work classes) →
 *   - `ambiguous_clarification` ("Will I be successful?"): the class under
 *     test is the ABSENCE of resolvable scope — a correct answer asks a
 *     clarifying question rather than answering as any of factual /
 *     interpretive / predictive / sensitive. A model cannot be "qualified to
 *     serve ambiguous queries" as a work class the way it can be qualified
 *     to serve factual lookups — the fixture tests a conversational
 *     reflex (does the model resolve scope before answering), not a
 *     content capability. Forcing it into `interpretive` (the closest
 *     tempting bucket) would let a model's clarification-reflex score leak
 *     into its interpretive-content qualification, which is exactly the
 *     kind of category error this mapping exists to prevent.
 *   - `door_parity` (Lagna-sign, both doors): tests infrastructure PARITY
 *     between the web and MCP doors, not a content capability at all —
 *     and per its own fixture (`expected.runnable: false`, gated on G4-B),
 *     it cannot even produce a receipt to score today. A work-class
 *     qualification bar over a fixture that cannot run would be
 *     `not_yet_measurable` in exactly the sense §N.8 says must never be
 *     silently treated as a pass — simpler and more honest to exclude it
 *     from work-class scope entirely and let it stay G4-D's concern
 *     (the roadmap's own "Parity contract" lane).
 *
 * A model is not evaluated against, and cannot be "qualified" or
 * "disqualified" for, either excluded class — `getFixturesForWorkClass`
 * simply never returns them, and `WORK_CLASSES` (the 4-member enum this
 * module exports) has no 5th/6th member for them to hide in.
 */

import { CORPUS_FIXTURES } from '../fixtures'
import type { CorpusFixture, QueryClass } from '../types'

export const WORK_CLASSES = ['factual', 'interpretive', 'predictive', 'sensitive'] as const
export type WorkClass = (typeof WORK_CLASSES)[number]

export interface QueryClassMapping {
  queryClass: QueryClass
  /** `null` means this query class is deliberately excluded from work-class scope — see this module's docblock. */
  workClass: WorkClass | null
  reason: string
}

export const QUERY_CLASS_WORK_CLASS_MAP: readonly QueryClassMapping[] = [
  {
    queryClass: 'factual',
    workClass: 'factual',
    reason: 'A pinpointed factual lookup against FORENSIC birth anchors — the direct case.',
  },
  {
    queryClass: 'interpretive_whole_chart',
    workClass: 'interpretive',
    reason: 'The class the work-class is named after — requires B.11 Whole-Chart-Read synthesis.',
  },
  {
    queryClass: 'timing',
    workClass: 'predictive',
    reason:
      'Asks what a dasha sub-period MEANS for future events — the time-indexed prediction capability ' +
      'named in CLAUDE.md §A.',
  },
  {
    queryClass: 'cross_domain_contradiction',
    workClass: 'interpretive',
    reason:
      'Synthesizing signals across domains into one coherent answer is interpretation, not a lookup ' +
      'or a forecast; exercises B.11 cross-domain routing directly.',
  },
  {
    queryClass: 'remedial',
    workClass: 'interpretive',
    reason:
      'Remedial measures are classically prescribed FROM an interpretive reading (the affliction ' +
      'pattern determines the remedy) — downstream of interpretation, not a 5th independent capability, ' +
      'and not named as its own class by the roadmap.',
  },
  {
    queryClass: 'sensitive',
    workClass: 'sensitive',
    reason:
      'VERIFIED HS-4 mortality-window trigger against the real classifyQuery() detector — the direct case.',
  },
  {
    queryClass: 'ambiguous_clarification',
    workClass: null,
    reason:
      'Tests the ABSENCE of resolvable scope (a correct answer clarifies rather than answers as any ' +
      'content class). A conversational reflex, not a content capability a model is "qualified" for.',
  },
  {
    queryClass: 'incomplete_evidence',
    workClass: 'interpretive',
    reason:
      'An interpretive question (what D-60 indicates) that stresses honest-gap disclosure under ' +
      'interpretation — the honesty requirement does not change the underlying capability being tested.',
  },
  {
    queryClass: 'returning_conversation_drift',
    workClass: 'interpretive',
    reason:
      'Interpretive content (career-authority claims) wrapped in a conversational-continuity test — ' +
      'the capability under test is synthesizing/reconciling an interpretation, not a distinct class.',
  },
  {
    queryClass: 'disagreement',
    workClass: 'interpretive',
    reason:
      'Defending an already-grounded interpretive claim under reader pushback — still interpretive ' +
      'content, not a distinct work class.',
  },
  {
    queryClass: 'prediction_capture_outcome',
    workClass: 'predictive',
    reason: 'A prior prediction referenced plus an outcome-recording request — the direct predictive case.',
  },
  {
    queryClass: 'door_parity',
    workClass: null,
    reason:
      'Tests web/MCP infrastructure parity, not a content capability, and (per its own fixture) cannot ' +
      'even produce a scoreable receipt in this base (gated on G4-B) — excluded rather than forced into ' +
      'a class it does not fit.',
  },
]

const MAP_BY_QUERY_CLASS: ReadonlyMap<QueryClass, QueryClassMapping> = new Map(
  QUERY_CLASS_WORK_CLASS_MAP.map((m) => [m.queryClass, m]),
)

export function getWorkClassForQueryClass(queryClass: QueryClass): WorkClass | null {
  const mapping = MAP_BY_QUERY_CLASS.get(queryClass)
  if (!mapping) {
    throw new Error(`no work-class mapping declared for query class "${queryClass}" — mapping is out of date`)
  }
  return mapping.workClass
}

/** The fixtures (from G3-F's fixed 12) belonging to one work class. Never includes an excluded query class. */
export function getFixturesForWorkClass(workClass: WorkClass): readonly CorpusFixture[] {
  return CORPUS_FIXTURES.filter((f) => getWorkClassForQueryClass(f.queryClass) === workClass)
}
