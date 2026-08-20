import { describe, expect, it } from 'vitest'

import { baseObservation } from '../../__tests__/test_helpers'
import type { CorpusFixture, TurnObservation } from '../../types'
import type { CorpusRunReport } from '../../report_schema'
import { CORPUS_FIXTURE_SET_VERSION } from '../../fixtures'
import { CORPUS_SCORING_HARNESS_VERSION } from '../../dimensions'
import { evaluateQualification, qualifyModelForWorkClass } from '../gate'
import { QUALIFICATION_BARS } from '../bars'

const TARGET = { kind: 'mocked_pipeline' as const, description: 'gate test double' }

/**
 * `baseObservation`'s default receipt (test_helpers.ts) has `coverage`
 * `empty:1, dark:1` (2 gaps expected) but only 1 entry in `honest_gaps.gaps`
 * — a deliberate mismatch in the shared helper that `honest_gaps_disclosure`
 * correctly scores at 0.5, below every work class's 0.75 floor. A "should
 * pass" fixture for THIS test file needs a receipt that is actually
 * internally consistent on that field, so failures here are attributable to
 * the thing each test is actually exercising, not to an incidental gap in
 * the shared mock. `dark: 0` makes the expected/actual gap counts agree
 * (1 == 1) without touching any other dimension's inputs.
 */
function passingReceiptOverrides(fixture: CorpusFixture) {
  const base = baseObservation({ fixture }).receipt!
  return { ...base, coverage: { ...base.coverage, dark: 0 } }
}

describe('qualifyModelForWorkClass — pass path', () => {
  it('marks a model qualified for `sensitive` when its receipt correctly enforces the HS-4 hard stop', async () => {
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> =>
      baseObservation({
        fixture,
        receipt: {
          ...passingReceiptOverrides(fixture),
          safety_decision: {
            status: 'measured',
            decision_id: 'dec-hs4',
            enforced: true,
            severity: 'review_required',
            action: 'seal_pending_signoff',
            classes_detected: ['hs4_mortality_window'],
            review_id: 'review-1',
            audit_written: true,
            unavailable_reason: null,
          },
        },
      })

    const result = await qualifyModelForWorkClass({
      modelId: 'test-model-pass',
      workClass: 'sensitive',
      runTurn,
      target: TARGET,
    })

    expect(result.status).toBe('qualified')
    expect(result.qualified).toBe(true)
    const safetyCheck = result.dimensionChecks.find((c) => c.dimension === 'safety_compliance')!
    expect(safetyCheck.meanScore).toBe(1)
    expect(safetyCheck.passed).toBe(true)
  })

  it('marks a model qualified for `factual` when the receipt cleanly resolves its own citations', async () => {
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> =>
      baseObservation({ fixture, receipt: passingReceiptOverrides(fixture) })

    const result = await qualifyModelForWorkClass({
      modelId: 'test-model-pass',
      workClass: 'factual',
      runTurn,
      target: TARGET,
    })

    expect(result.status).toBe('qualified')
    expect(result.qualified).toBe(true)
    expect(result.fixturesRun).toBe(1)
  })
})

describe('qualifyModelForWorkClass — fail path', () => {
  it('marks a model NOT qualified for `sensitive` when the receipt does not enforce the hard stop (baseReceipt default)', async () => {
    // baseReceipt()'s default safety_decision is enforced:false/action:'proceed' — a
    // real, undoctored failure to enforce the sensitive fixture's HS-4 expectation.
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> => baseObservation({ fixture })

    const result = await qualifyModelForWorkClass({
      modelId: 'test-model-fail',
      workClass: 'sensitive',
      runTurn,
      target: TARGET,
    })

    expect(result.status).toBe('not_qualified')
    expect(result.qualified).toBe(false)
    const safetyCheck = result.dimensionChecks.find((c) => c.dimension === 'safety_compliance')!
    expect(safetyCheck.meanScore).toBeLessThan(1)
    expect(safetyCheck.passed).toBe(false)
  })

  it('marks a model NOT qualified for `interpretive` when derivation_chains cite unresolved facts', async () => {
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> => {
      const base = baseObservation({ fixture })
      return {
        ...base,
        receipt: {
          ...base.receipt!,
          derivation_chains: [{ block_id: 'blk-bad', pass_id: 1, role: 'prose', fact_refs: ['SIG.NOT.REAL'] }],
        },
      }
    }

    const result = await qualifyModelForWorkClass({
      modelId: 'test-model-fail',
      workClass: 'interpretive',
      runTurn,
      target: TARGET,
    })

    expect(result.status).toBe('not_qualified')
    expect(result.qualified).toBe(false)
    const derivationCheck = result.dimensionChecks.find((c) => c.dimension === 'derivation_integrity')!
    expect(derivationCheck.meanScore).toBe(0)
    expect(derivationCheck.passed).toBe(false)
  })

  it('discriminates correctly: the same runTurn logic passes one work class and fails another', async () => {
    // A receipt that is fine for `factual` but explicitly fails the sensitive bar
    // (no HS-4 enforcement) — proves the gate is scoped per work class, not global.
    const runTurn = async (fixture: CorpusFixture): Promise<TurnObservation> =>
      baseObservation({ fixture, receipt: passingReceiptOverrides(fixture) })

    const factualResult = await qualifyModelForWorkClass({
      modelId: 'test-model-mixed',
      workClass: 'factual',
      runTurn,
      target: TARGET,
    })
    const sensitiveResult = await qualifyModelForWorkClass({
      modelId: 'test-model-mixed',
      workClass: 'sensitive',
      runTurn,
      target: TARGET,
    })

    expect(factualResult.qualified).toBe(true)
    expect(sensitiveResult.qualified).toBe(false)
  })
})

describe('evaluateQualification — unmeasurable dimensions never silently pass (§N.8)', () => {
  function emptyReport(overrides: Partial<CorpusRunReport['summary']['mean_score_by_dimension']> = {}): CorpusRunReport {
    return {
      report_schema_version: 1,
      corpus_fixture_set_version: CORPUS_FIXTURE_SET_VERSION,
      scoring_harness_version: CORPUS_SCORING_HARNESS_VERSION,
      generated_at: '2026-08-20T00:00:00.000Z',
      target: TARGET,
      fixture_results: [],
      summary: {
        fixtures_total: 2,
        fixtures_run: 2,
        fixtures_skipped: 0,
        mean_score_by_dimension: {
          derivation_integrity: null,
          b11_coverage: null,
          citation_precision: null,
          citation_recall: null,
          calibration_language_honesty: null,
          safety_compliance: null,
          register_leakage: null,
          honest_gaps_disclosure: null,
          voice_enforcement: null,
          cross_domain_contradiction_surfaced: null,
          falsifier_quality: null,
          typed_confidence_honesty: null,
          reader_comprehension: null,
          ...overrides,
        },
      },
    }
  }

  it('never marks a model qualified when every required dimension for the work class is null', () => {
    const result = evaluateQualification({
      modelId: 'ghost-model',
      workClass: 'interpretive',
      report: emptyReport(),
    })

    expect(result.qualified).toBe(false)
    expect(result.status).toBe('not_yet_measurable')
    // Every check the bar declares is present, and none is silently marked passed.
    for (const check of result.dimensionChecks) {
      expect(check.passed).toBeNull()
    }
  })

  it('still requires ALL measured dimensions to pass even when some remain null (partial data is not a free pass)', () => {
    // derivation_integrity scores perfectly but safety_compliance (required at 0.9
    // general floor) is deliberately left failing — a real mixed result, not a
    // synthetic all-or-nothing case.
    const result = evaluateQualification({
      modelId: 'partial-model',
      workClass: 'factual',
      report: emptyReport({ derivation_integrity: 1, safety_compliance: 0.5 }),
    })

    expect(result.qualified).toBe(false)
    expect(result.status).toBe('not_qualified')
    const derivationCheck = result.dimensionChecks.find((c) => c.dimension === 'derivation_integrity')!
    expect(derivationCheck.passed).toBe(true)
    const safetyCheck = result.dimensionChecks.find((c) => c.dimension === 'safety_compliance')!
    expect(safetyCheck.passed).toBe(false)
    // b11_coverage/citation_precision (also required for `factual`) are still null and still excluded, not defaulted to true.
    const b11Check = result.dimensionChecks.find((c) => c.dimension === 'b11_coverage')!
    expect(b11Check.passed).toBeNull()
    expect(result.unmeasuredDimensions).toContain('b11_coverage')
  })

  it('reports falsifier_quality and typed_confidence_honesty as unmeasured (still §N.8 stubs), never as a pass, even though the bar declares them in scope', () => {
    const interpretiveBar = QUALIFICATION_BARS.interpretive
    expect(interpretiveBar.requiredDimensions.some((r) => r.dimension === 'falsifier_quality')).toBe(true)

    const result = evaluateQualification({
      modelId: 'stub-dimension-model',
      workClass: 'interpretive',
      // Everything else passes, only the stub dimensions are (honestly) null.
      report: emptyReport({
        derivation_integrity: 1,
        calibration_language_honesty: 1,
        safety_compliance: 1,
        register_leakage: 1,
        honest_gaps_disclosure: 1,
        b11_coverage: 1,
        citation_precision: 1,
        citation_recall: 1,
        cross_domain_contradiction_surfaced: 1,
        voice_enforcement: 1,
        // falsifier_quality stays null — the honest stub state.
      }),
    })

    expect(result.qualified).toBe(true) // measured dimensions all pass
    expect(result.status).toBe('qualified')
    expect(result.unmeasuredDimensions).toContain('falsifier_quality')
    const falsifierCheck = result.dimensionChecks.find((c) => c.dimension === 'falsifier_quality')!
    expect(falsifierCheck.passed).toBeNull()
    expect(falsifierCheck.meanScore).toBeNull()
  })

  it('never qualifies a work class with zero fixtures run, regardless of scores', () => {
    const zeroRunReport = emptyReport({ derivation_integrity: 1, safety_compliance: 1 })
    const result = evaluateQualification({
      modelId: 'no-run-model',
      workClass: 'factual',
      report: { ...zeroRunReport, summary: { ...zeroRunReport.summary, fixtures_run: 0 } },
    })
    expect(result.qualified).toBe(false)
    expect(result.status).toBe('not_yet_measurable')
  })
})
