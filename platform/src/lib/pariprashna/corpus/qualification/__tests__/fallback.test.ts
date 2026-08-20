import { describe, expect, it } from 'vitest'

import { getModelMeta } from '@/lib/models/registry'
import type { ModelQualificationResult } from '../gate'
import { buildQualificationRegistry } from '../registry'
import { selectModelForWorkClass } from '../fallback'

function fakeResult(overrides: Partial<ModelQualificationResult>): ModelQualificationResult {
  return {
    modelId: 'model',
    workClass: 'factual',
    status: 'qualified',
    qualified: true,
    dimensionChecks: [],
    unmeasuredDimensions: [],
    fixturesRun: 1,
    fixturesTotal: 1,
    evaluatedAt: '2026-08-20T00:00:00.000Z',
    provenance: {
      qualificationGateVersion: 1,
      reportSchemaVersion: 1,
      corpusFixtureSetVersion: 1,
      scoringHarnessVersion: 1,
      target: { kind: 'mocked_pipeline', description: 'test' },
    },
    ...overrides,
  }
}

// Two real premium-tier synthesis models from the live registry, chosen so
// the tier-matching logic is exercised against real registry data rather
// than a synthetic tier system re-invented for this test.
const PREMIUM_A = 'claude-opus-4-7'
const PREMIUM_B = 'gemini-2.5-pro'

describe('selectModelForWorkClass', () => {
  it('returns the requested model unchanged, not degraded, when it is qualified', () => {
    const registry = buildQualificationRegistry([
      fakeResult({ modelId: PREMIUM_A, workClass: 'interpretive', qualified: true, status: 'qualified' }),
    ])

    const result = selectModelForWorkClass({ requestedModelId: PREMIUM_A, workClass: 'interpretive', registry })

    expect(result.selectedModelId).toBe(PREMIUM_A)
    expect(result.outcome).toBe('requested_model_qualified')
    expect(result.degraded).toBe(false)
    expect(result.flag).toBeNull()
  })

  it('substitutes a same-tier qualified model when the requested model is not qualified — never silently', () => {
    expect(getModelMeta(PREMIUM_A)?.tier).toBe('premium')
    expect(getModelMeta(PREMIUM_B)?.tier).toBe('premium')

    const registry = buildQualificationRegistry([
      fakeResult({ modelId: PREMIUM_A, workClass: 'sensitive', qualified: false, status: 'not_qualified' }),
      fakeResult({ modelId: PREMIUM_B, workClass: 'sensitive', qualified: true, status: 'qualified' }),
    ])

    const result = selectModelForWorkClass({ requestedModelId: PREMIUM_A, workClass: 'sensitive', registry })

    expect(result.selectedModelId).toBe(PREMIUM_B)
    expect(result.requestedModelId).toBe(PREMIUM_A)
    expect(result.outcome).toBe('substituted_same_tier')
    expect(result.degraded).toBe(true)
    // Never silent — the substitution is always visible on the result.
    expect(result.flag).not.toBeNull()
    expect(result.flag).toContain('sensitive')
    expect(result.provenance.selectedModelQualified).toBe(true)
    expect(result.provenance.requestedModelQualified).toBe(false)
    expect(result.provenance.selectedModelTier).toBe('premium')
  })

  it('degrades VISIBLY (flag + provenance) rather than silently proceeding when no same-tier substitute exists', () => {
    // Registry has evaluations for both premium models but NEITHER is qualified —
    // no substitute exists anywhere in the tier.
    const registry = buildQualificationRegistry([
      fakeResult({ modelId: PREMIUM_A, workClass: 'predictive', qualified: false, status: 'not_qualified' }),
      fakeResult({ modelId: PREMIUM_B, workClass: 'predictive', qualified: false, status: 'not_qualified' }),
    ])

    const result = selectModelForWorkClass({ requestedModelId: PREMIUM_A, workClass: 'predictive', registry })

    expect(result.selectedModelId).toBe(PREMIUM_A) // proceeds with the request — but flagged
    expect(result.outcome).toBe('degraded_unqualified')
    expect(result.degraded).toBe(true)
    expect(result.flag).not.toBeNull()
    expect(result.flag).toContain('unqualified_model_serving_work_class')
    expect(result.provenance.selectedModelQualified).toBe(false)
  })

  it('degrades VISIBLY with an empty registry too (nothing evaluated yet is not "everyone passes")', () => {
    const registry = buildQualificationRegistry([])

    const result = selectModelForWorkClass({ requestedModelId: PREMIUM_A, workClass: 'factual', registry })

    expect(result.degraded).toBe(true)
    expect(result.outcome).toBe('degraded_unqualified')
    expect(result.flag).not.toBeNull()
  })

  it('never crosses tiers when substituting: a worker-tier request never gets silently upgraded to a premium substitute', () => {
    const workerModel = 'gpt-4o-mini' // tier: worker
    expect(getModelMeta(workerModel)?.tier).toBe('worker')

    const registry = buildQualificationRegistry([
      fakeResult({ modelId: workerModel, workClass: 'factual', qualified: false, status: 'not_qualified' }),
      // A premium model IS qualified, but it must never be offered as a substitute for a worker-tier request.
      fakeResult({ modelId: PREMIUM_A, workClass: 'factual', qualified: true, status: 'qualified' }),
    ])

    const result = selectModelForWorkClass({ requestedModelId: workerModel, workClass: 'factual', registry })

    expect(result.selectedModelId).not.toBe(PREMIUM_A)
    expect(result.outcome).toBe('degraded_unqualified')
    expect(result.provenance.requestedModelTier).toBe('worker')
  })

  it('degrades VISIBLY for an unknown model id rather than guessing a tier', () => {
    const registry = buildQualificationRegistry([])

    const result = selectModelForWorkClass({
      requestedModelId: 'not-a-real-registered-model-id',
      workClass: 'factual',
      registry,
    })

    expect(result.outcome).toBe('degraded_unknown_model')
    expect(result.degraded).toBe(true)
    expect(result.flag).not.toBeNull()
    expect(result.provenance.requestedModelTier).toBeNull()
  })
})
