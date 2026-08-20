import { describe, expect, it } from 'vitest'

import { CORPUS_FIXTURES, CORPUS_FIXTURE_SET_VERSION } from '../fixtures'
import { CORPUS_SCORING_HARNESS_VERSION } from '../dimensions'
import { runCorpus } from '../runner'
import { CorpusRunReportSchema } from '../report_schema'
import { baseObservation } from './test_helpers'
import type { CorpusFixture, TurnObservation } from '../types'

describe('runCorpus', () => {
  it('skips the not-runnable fixture (door_parity) and runs the other 11, producing a schema-valid report', async () => {
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> => baseObservation({ fixture })

    const report = await runCorpus({
      runTurn,
      target: { kind: 'mocked_pipeline', description: 'in-memory fixture mock' },
      now: new Date('2026-08-20T12:00:00.000Z'),
    })

    expect(CorpusRunReportSchema.parse(report)).toBeTruthy()
    expect(report.report_schema_version).toBe(1)
    expect(report.corpus_fixture_set_version).toBe(CORPUS_FIXTURE_SET_VERSION)
    expect(report.scoring_harness_version).toBe(CORPUS_SCORING_HARNESS_VERSION)
    expect(report.summary.fixtures_total).toBe(12)
    expect(report.summary.fixtures_run).toBe(11)
    expect(report.summary.fixtures_skipped).toBe(1)

    const doorParityResult = report.fixture_results.find((f) => f.query_class === 'door_parity')
    expect(doorParityResult?.ran).toBe(false)
    expect(doorParityResult?.skipped_reason).toContain('G4-B')
    expect(doorParityResult?.dimension_results).toEqual([])
  })

  it('aggregates mean_score_by_dimension correctly across fixtures that were actually run', async () => {
    // Every fixture gets an observation whose receipt cites exactly its own
    // facts, so derivation_integrity should be 1.0 for every RUN fixture.
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> => baseObservation({ fixture })

    const report = await runCorpus({
      fixtures: CORPUS_FIXTURES.filter((f) => f.expected.runnable),
      runTurn,
      target: { kind: 'mocked_pipeline', description: 'in-memory fixture mock' },
    })

    expect(report.summary.fixtures_run).toBe(11)
    expect(report.summary.mean_score_by_dimension.derivation_integrity).toBe(1)
    // Unscored stub dimensions never contribute a numeric mean.
    expect(report.summary.mean_score_by_dimension.falsifier_quality).toBeNull()
    expect(report.summary.mean_score_by_dimension.typed_confidence_honesty).toBeNull()
    expect(report.summary.mean_score_by_dimension.reader_comprehension).toBeNull()
  })

  it('respects an injected fixtures subset', async () => {
    const onlyFactual = CORPUS_FIXTURES.filter((f) => f.queryClass === 'factual')
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> => baseObservation({ fixture })

    const report = await runCorpus({
      fixtures: onlyFactual,
      runTurn,
      target: { kind: 'mocked_pipeline', description: 'single-fixture run' },
    })

    expect(report.summary.fixtures_total).toBe(1)
    expect(report.fixture_results).toHaveLength(1)
  })
})
