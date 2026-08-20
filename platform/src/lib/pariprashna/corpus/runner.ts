/**
 * pariprashna/corpus/runner.ts — the corpus runner (lane P2-N, roadmap id
 * G3-F).
 *
 * SCAFFOLDING, explicitly: this function executes the 12-fixture corpus
 * against whatever `runTurn` the caller supplies and emits a versioned
 * report. It does NOT itself talk to the deployed route, a database, or an
 * LLM provider — the roadmap's own framing for this lane says the corpus is
 * "authored... run last" (dependencies G3-B/C/D not yet merged into this
 * worktree's base, and several dimensions need a live receipt this lane has
 * no route to produce). Supplying a `runTurn` that calls the real deployed
 * route (once G3-B/C/D land) turns this into a genuine corpus run with zero
 * changes to this file — that is the point of taking `runTurn` as an
 * injected function rather than hardcoding a fetch call here. Every test in
 * `__tests__/runner.test.ts` supplies a `runTurn` built from realistic
 * fixture data (the same convention `receipt/__tests__/assemble.test.ts`
 * already uses for the receipt assembler this runner builds on) — proving
 * the AGGREGATION logic is correct, not asserting a live run happened.
 */

import type { CorpusFixture, TurnObservation } from './types'
import { CORPUS_FIXTURE_SET_VERSION, CORPUS_FIXTURES } from './fixtures'
import { CORPUS_SCORING_HARNESS_VERSION, scoreAllDimensions } from './dimensions'
import { DIMENSION_IDS } from './types'
import {
  CORPUS_REPORT_SCHEMA_VERSION,
  type CorpusRunReport,
  type CorpusTarget,
  type FixtureRunResult,
} from './report_schema'

export type TurnRunner = (fixture: CorpusFixture) => Promise<TurnObservation>

export interface RunCorpusArgs {
  /** Defaults to the full `CORPUS_FIXTURES` set; pass a subset for a targeted run. */
  fixtures?: readonly CorpusFixture[]
  /** Produces the observation for one fixture — a live route call or a test double. */
  runTurn: TurnRunner
  target: CorpusTarget
  /** Injectable for deterministic tests; defaults to `new Date()`. */
  now?: Date
}

export async function runCorpus(args: RunCorpusArgs): Promise<CorpusRunReport> {
  const fixtures = args.fixtures ?? CORPUS_FIXTURES
  const now = args.now ?? new Date()

  const fixtureResults: FixtureRunResult[] = []
  const dimensionScoreSums = new Map<string, { sum: number; count: number }>()

  for (const fixture of fixtures) {
    if (!fixture.expected.runnable) {
      fixtureResults.push({
        fixture_id: fixture.fixtureId,
        fixture_version: fixture.fixtureVersion,
        query_class: fixture.queryClass,
        ran: false,
        skipped_reason: fixture.expected.notRunnableReason ?? 'fixture marked not runnable',
        dimension_results: [],
      })
      continue
    }

    const obs = await args.runTurn(fixture)
    const results = scoreAllDimensions(obs)

    for (const r of results) {
      if (r.status !== 'scored' || r.score === null) continue
      const entry = dimensionScoreSums.get(r.dimension) ?? { sum: 0, count: 0 }
      entry.sum += r.score
      entry.count += 1
      dimensionScoreSums.set(r.dimension, entry)
    }

    fixtureResults.push({
      fixture_id: fixture.fixtureId,
      fixture_version: fixture.fixtureVersion,
      query_class: fixture.queryClass,
      ran: true,
      skipped_reason: null,
      // Report shape (report_schema.ts, zod-inferred) wants a mutable `findings`
      // array; `DimensionResult.findings` is `readonly` at the scorer boundary
      // (types.ts) so a scorer can never claim to mutate a caller's array. Copy
      // at the one point that crosses from "internal result" to "report row".
      dimension_results: results.map((r) => ({ ...r, findings: [...r.findings] })),
    })
  }

  const meanScoreByDimension = Object.fromEntries(
    DIMENSION_IDS.map((dim) => {
      const entry = dimensionScoreSums.get(dim)
      return [dim, entry && entry.count > 0 ? entry.sum / entry.count : null]
    }),
  ) as Record<(typeof DIMENSION_IDS)[number], number | null>

  const fixturesRun = fixtureResults.filter((f) => f.ran).length

  return {
    report_schema_version: CORPUS_REPORT_SCHEMA_VERSION,
    corpus_fixture_set_version: CORPUS_FIXTURE_SET_VERSION,
    scoring_harness_version: CORPUS_SCORING_HARNESS_VERSION,
    generated_at: now.toISOString(),
    target: args.target,
    fixture_results: fixtureResults,
    summary: {
      fixtures_total: fixtures.length,
      fixtures_run: fixturesRun,
      fixtures_skipped: fixtures.length - fixturesRun,
      mean_score_by_dimension: meanScoreByDimension,
    },
  }
}
