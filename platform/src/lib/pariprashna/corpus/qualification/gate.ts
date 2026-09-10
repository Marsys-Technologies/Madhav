/**
 * pariprashna/corpus/qualification/gate.ts — lane P2-O (G3-G, PPR-32).
 *
 * The qualification gate. Runs G3-F's existing `runCorpus` (unmodified,
 * imported from `../runner`) against the fixture subset for one work class,
 * then evaluates the resulting `CorpusRunReport.summary.mean_score_by_dimension`
 * against `bars.ts`'s per-work-class bar.
 *
 * §N.8 discipline, concretely: `evaluateQualification` never treats a
 * `null` mean (a dimension with zero `scored` results in this run) as a
 * passing score. Every `DimensionRequirement` from the bar is evaluated
 * three ways —
 *
 *   1. mean is a number → checked against the threshold, contributes to
 *      qualification pass/fail.
 *   2. mean is `null` (nothing scored) → excluded from pass/fail entirely
 *      and reported in `unmeasured_dimensions`, never silently counted as
 *      passing NOR silently required to block qualification on a dimension
 *      this corpus run had no way to measure.
 *
 * If EVERY required dimension for a work class comes back `null` (nothing
 * measurable at all — e.g. an empty/degenerate report), qualification
 * cannot be a meaningful "pass": `status` is `not_yet_measurable` and
 * `qualified` is `false`, never `true` by default. A model is never
 * qualified by the absence of evidence.
 */

import type { CorpusTarget, CorpusRunReport } from '../report_schema'
import { runCorpus, type TurnRunner } from '../runner'
import { getFixturesForWorkClass, type WorkClass } from './work_classes'
import { QUALIFICATION_BARS } from './bars'
import type { DimensionId } from '../types'

export const QUALIFICATION_GATE_VERSION = 1 as const

export interface DimensionCheckResult {
  dimension: DimensionId
  threshold: number
  /** `null` iff this dimension produced zero `scored` results in this run. */
  meanScore: number | null
  /** `null` when `meanScore` is `null` — an unmeasured dimension has no pass/fail verdict. */
  passed: boolean | null
  rationale: string
}

export type QualificationStatus = 'qualified' | 'not_qualified' | 'not_yet_measurable'

export interface ModelQualificationResult {
  modelId: string
  workClass: WorkClass
  status: QualificationStatus
  qualified: boolean
  dimensionChecks: readonly DimensionCheckResult[]
  /** Dimensions the bar declares in scope but which produced no scored result this run — see gate.ts docblock. */
  unmeasuredDimensions: readonly DimensionId[]
  fixturesRun: number
  fixturesTotal: number
  evaluatedAt: string
  provenance: {
    qualificationGateVersion: number
    reportSchemaVersion: number
    corpusFixtureSetVersion: number
    scoringHarnessVersion: number
    target: CorpusTarget
  }
}

/**
 * Evaluates an already-produced `CorpusRunReport` (scoped to one work
 * class's fixtures — see `qualifyModelForWorkClass` below, which is the
 * usual entry point) against that work class's bar. Exposed separately so a
 * caller that already has a report (e.g. a persisted historical run) can
 * re-evaluate it without re-running the corpus.
 */
export function evaluateQualification(args: {
  modelId: string
  workClass: WorkClass
  report: CorpusRunReport
}): ModelQualificationResult {
  const { modelId, workClass, report } = args
  const bar = QUALIFICATION_BARS[workClass]
  const means = report.summary.mean_score_by_dimension

  const dimensionChecks: DimensionCheckResult[] = bar.requiredDimensions.map((req) => {
    const mean = means[req.dimension] ?? null
    return {
      dimension: req.dimension,
      threshold: req.threshold,
      meanScore: mean,
      passed: mean === null ? null : mean >= req.threshold,
      rationale: req.rationale,
    }
  })

  const unmeasuredDimensions = dimensionChecks.filter((c) => c.passed === null).map((c) => c.dimension)
  const measuredChecks = dimensionChecks.filter((c): c is DimensionCheckResult & { passed: boolean } => c.passed !== null)

  const enoughFixturesRan = report.summary.fixtures_run >= bar.minFixturesRun

  let status: QualificationStatus
  let qualified: boolean

  if (!enoughFixturesRan || measuredChecks.length === 0) {
    // Never a pass by default: no evidence means no qualification, full stop.
    status = 'not_yet_measurable'
    qualified = false
  } else if (measuredChecks.every((c) => c.passed)) {
    status = 'qualified'
    qualified = true
  } else {
    status = 'not_qualified'
    qualified = false
  }

  return {
    modelId,
    workClass,
    status,
    qualified,
    dimensionChecks,
    unmeasuredDimensions,
    fixturesRun: report.summary.fixtures_run,
    fixturesTotal: report.summary.fixtures_total,
    evaluatedAt: report.generated_at,
    provenance: {
      qualificationGateVersion: QUALIFICATION_GATE_VERSION,
      reportSchemaVersion: report.report_schema_version,
      corpusFixtureSetVersion: report.corpus_fixture_set_version,
      scoringHarnessVersion: report.scoring_harness_version,
      target: report.target,
    },
  }
}

/**
 * The usual entry point: runs G3-F's `runCorpus` scoped to `workClass`'s
 * fixture subset, then evaluates the result. `runTurn` is the same
 * injectable seam `runner.ts` already defines — pass one that calls a real
 * deployed route bound to a specific model to get a genuine qualification
 * run, or a test double for a mocked/constructed run (see this lane's own
 * tests, and `runner.ts`'s own docblock for why this seam exists).
 */
export async function qualifyModelForWorkClass(args: {
  modelId: string
  workClass: WorkClass
  runTurn: TurnRunner
  target: CorpusTarget
  now?: Date
}): Promise<ModelQualificationResult> {
  const fixtures = getFixturesForWorkClass(args.workClass)
  const report = await runCorpus({
    fixtures,
    runTurn: args.runTurn,
    target: args.target,
    now: args.now,
  })
  return evaluateQualification({ modelId: args.modelId, workClass: args.workClass, report })
}
