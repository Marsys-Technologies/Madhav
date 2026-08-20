import { describe, expect, it } from 'vitest'

import type { ModelQualificationResult } from '../gate'
import {
  buildQualificationRegistry,
  getQualificationRecord,
  isQualified,
  qualifiedModelIds,
} from '../registry'

function fakeResult(overrides: Partial<ModelQualificationResult> = {}): ModelQualificationResult {
  return {
    modelId: 'model-a',
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

describe('buildQualificationRegistry / getQualificationRecord', () => {
  it('looks up a record by (modelId, workClass)', () => {
    const registry = buildQualificationRegistry([
      fakeResult({ modelId: 'model-a', workClass: 'factual', qualified: true }),
      fakeResult({ modelId: 'model-a', workClass: 'sensitive', qualified: false, status: 'not_qualified' }),
    ])

    expect(getQualificationRecord(registry, 'model-a', 'factual')?.qualified).toBe(true)
    expect(getQualificationRecord(registry, 'model-a', 'sensitive')?.qualified).toBe(false)
    expect(getQualificationRecord(registry, 'model-a', 'predictive')).toBeUndefined()
    expect(getQualificationRecord(registry, 'model-b', 'factual')).toBeUndefined()
  })

  it('the most recently supplied result for a (modelId, workClass) pair wins', () => {
    const registry = buildQualificationRegistry([
      fakeResult({ modelId: 'model-a', workClass: 'factual', qualified: false, status: 'not_qualified' }),
      fakeResult({ modelId: 'model-a', workClass: 'factual', qualified: true, status: 'qualified' }),
    ])
    expect(getQualificationRecord(registry, 'model-a', 'factual')?.qualified).toBe(true)
  })
})

describe('isQualified', () => {
  it('is false for a model/work-class pair that was never evaluated (never silently true)', () => {
    const registry = buildQualificationRegistry([])
    expect(isQualified(registry, 'never-evaluated', 'factual')).toBe(false)
  })

  it('is false for a model explicitly evaluated as not_qualified — same boolean as never-evaluated, by design', () => {
    const registry = buildQualificationRegistry([
      fakeResult({ modelId: 'model-a', workClass: 'sensitive', qualified: false, status: 'not_qualified' }),
    ])
    expect(isQualified(registry, 'model-a', 'sensitive')).toBe(false)
  })

  it('is true only for a real qualified: true record', () => {
    const registry = buildQualificationRegistry([
      fakeResult({ modelId: 'model-a', workClass: 'interpretive', qualified: true, status: 'qualified' }),
    ])
    expect(isQualified(registry, 'model-a', 'interpretive')).toBe(true)
  })
})

describe('qualifiedModelIds', () => {
  it('lists only the qualified models for a work class', () => {
    const registry = buildQualificationRegistry([
      fakeResult({ modelId: 'model-a', workClass: 'factual', qualified: true, status: 'qualified' }),
      fakeResult({ modelId: 'model-b', workClass: 'factual', qualified: false, status: 'not_qualified' }),
      fakeResult({ modelId: 'model-c', workClass: 'factual', qualified: true, status: 'qualified' }),
      fakeResult({ modelId: 'model-a', workClass: 'sensitive', qualified: true, status: 'qualified' }),
    ])
    expect([...qualifiedModelIds(registry, 'factual')].sort()).toEqual(['model-a', 'model-c'])
    expect(qualifiedModelIds(registry, 'sensitive')).toEqual(['model-a'])
    expect(qualifiedModelIds(registry, 'predictive')).toEqual([])
  })
})
