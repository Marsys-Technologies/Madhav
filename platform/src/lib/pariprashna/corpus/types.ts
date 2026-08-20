/**
 * pariprashna/corpus/types.ts — lane P2-N (roadmap id G3-F, "the quality
 * corpus"). PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md line 106.
 *
 * Shared vocabulary for the corpus: the 12 query classes, the fixture shape,
 * the per-turn observation a scoring dimension reads, and the dimension
 * result shape every scorer returns.
 *
 * SCAFFOLDING LANE, explicitly (roadmap's own framing): "P2-N (corpus) and
 * P2-O (qualification) are authored in parallel from the start and run
 * last." This module and its siblings build the fixture set and the scoring
 * harness so a real corpus run is possible once G3-B/C/D land and a deployed
 * route exists to run against — it does not itself claim such a run
 * happened (see `runner.ts`'s docblock).
 *
 * §N.8 discipline threads through every type here: `DimensionResult.status`
 * is `'scored'` only when a real detector produced the number: any dimension
 * (or per-observation input) lacking a real source returns
 * `'not_yet_measurable'` with a `reason`, never a fabricated passing score.
 */

// ---------------------------------------------------------------------------
// The 12 query classes (roadmap line 106, verbatim list).
// ---------------------------------------------------------------------------

export const QUERY_CLASSES = [
  'factual',
  'interpretive_whole_chart',
  'timing',
  'cross_domain_contradiction',
  'remedial',
  'sensitive',
  'ambiguous_clarification',
  'incomplete_evidence',
  'returning_conversation_drift',
  'disagreement',
  'prediction_capture_outcome',
  'door_parity',
] as const

export type QueryClass = (typeof QUERY_CLASSES)[number]

// ---------------------------------------------------------------------------
// The 13 scored dimensions (roadmap line 106's "incl." list, expanded to a
// closed set of 13 — see dimensions/index.ts's own docblock for the mapping
// from the roadmap's named examples to this closed enum, and for which of
// the 5 not named verbatim were added and why).
// ---------------------------------------------------------------------------

export const DIMENSION_IDS = [
  'derivation_integrity',
  'b11_coverage',
  'citation_precision',
  'citation_recall',
  'calibration_language_honesty',
  'safety_compliance',
  'register_leakage',
  'honest_gaps_disclosure',
  'voice_enforcement',
  'cross_domain_contradiction_surfaced',
  'falsifier_quality',
  'typed_confidence_honesty',
  'reader_comprehension',
] as const

export type DimensionId = (typeof DIMENSION_IDS)[number]

// ---------------------------------------------------------------------------
// Fixtures.
// ---------------------------------------------------------------------------

/**
 * `chart_id` a fixture is grounded against. The canonical native's chart
 * (CLAUDE.md §B) for anything that cites real chart content; a clearly
 * labeled synthetic id for anything that must not touch canonical chart
 * data during test authoring (see fixtures.ts per-fixture grounding notes).
 */
export const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

export interface CorpusFixtureExpectations {
  /**
   * Ground truth for `citation_recall`: the `SIG.*` refs a correct answer to
   * this query should cite. Omitted (undefined) for fixtures where no single
   * correct citation set can be pre-declared honestly — `citation_recall`
   * reports `not_yet_measurable` for those, rather than inventing a target.
   */
  expectedSignalRefs?: readonly string[]
  /** Ground truth for `b11_coverage` / `cross_domain_contradiction_surfaced`. */
  expectedDomains?: readonly string[]
  /**
   * Ground truth for `safety_compliance`, verified against the REAL
   * `classifyQuery` detector at fixture-authoring time (see fixtures.ts's
   * per-fixture grounding note) — never asserted from the query text alone.
   */
  expectedSafetyClasses?: readonly string[]
  expectedSafetySeverity?: 'none' | 'advisory' | 'review_required' | 'hard_stop'
  /** Which door(s) this fixture is meant to exercise. */
  door: 'web' | 'mcp' | 'both'
  /**
   * Whether this fixture can be run end-to-end against a real target TODAY.
   * `false` with `notRunnableReason` set is the honest state for anything
   * gated on a lane that has not landed in this worktree's base (G3-B/C/D,
   * G4-B) — see fixtures.ts's `door_parity` fixture for the concrete case
   * the roadmap itself calls out.
   */
  runnable: boolean
  notRunnableReason?: string
}

export interface CorpusFixture {
  fixtureId: string
  /** Bumped whenever this fixture's query text or expectations change. */
  fixtureVersion: number
  queryClass: QueryClass
  queryText: string
  chartId: string
  /**
   * How this fixture is grounded — a citable source (UCN section, MSR
   * signal, classifier detection run, roadmap line) rather than an assertion
   * of astrological judgment. Required on every fixture (B.3 derivation-
   * ledger discipline extended to fixture authoring).
   */
  groundingNote: string
  expected: CorpusFixtureExpectations
  /** Prior conversation turns this fixture assumes exist (drift/history classes only). */
  priorTurns?: readonly { role: 'user' | 'assistant'; text: string }[]
}

// ---------------------------------------------------------------------------
// TurnObservation — what a scoring dimension reads. Every field is a REAL
// artifact from elsewhere in the codebase (G3-A's receipt, P2-E's turn
// metrics), never re-derived here. A field being `null` is the honest
// "this run didn't produce that artifact" state, not an error.
// ---------------------------------------------------------------------------

import type { AcharyaReadingReceipt } from '@/lib/pariprashna/receipt/schema'
import type { TurnMetricsSnapshot } from '@/lib/pariprashna/observability/turn_metrics'

export interface TurnObservation {
  fixture: CorpusFixture
  /** The G3-A receipt assembled for this turn, or null if none was produced. */
  receipt: AcharyaReadingReceipt | null
  /** `TurnMetricsCollector.snapshot()` for this turn, or null if not captured. */
  turnMetrics: TurnMetricsSnapshot | null
  /** The reader-visible prose actually served this turn, or null if not captured. */
  proseText: string | null
}

// ---------------------------------------------------------------------------
// DimensionResult — every scorer's return shape.
// ---------------------------------------------------------------------------

export type DimensionResultStatus = 'scored' | 'not_yet_measurable'

export interface DimensionResult {
  dimension: DimensionId
  status: DimensionResultStatus
  /** 0..1. Always null when status is `not_yet_measurable` (§N.8: null, not green). */
  score: number | null
  /** Populated iff status is `not_yet_measurable` — the one place a "why" lives. */
  reason: string | null
  /** Human-readable flags a report renders alongside the score. Always present. */
  findings: readonly string[]
}

export type DimensionScorer = (obs: TurnObservation) => DimensionResult
