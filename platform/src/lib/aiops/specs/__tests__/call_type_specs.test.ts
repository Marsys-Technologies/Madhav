import { describe, it, expect } from 'vitest'
import { filterCatalogForCallType, CALL_TYPE_SPECS } from '../call_type_specs'
import type { CatalogEntry } from '@/lib/aiops/catalog/types'

// ─── factory ──────────────────────────────────────────────────────────────────

function entry(overrides: Partial<CatalogEntry> = {}): CatalogEntry {
  return {
    model_id:           'model-default',
    provider:           'google',
    label:              'Default Model',
    context_window:     200_000,
    param_count:        70,
    capabilities:       [],
    role:               null,
    cost_input_per_1m:  1.0,
    cost_output_per_1m: 2.0,
    metadata_pending:   false,
    is_registry_entry:  true,
    ...overrides,
  }
}

// ─── mandatory filters ────────────────────────────────────────────────────────

describe('filterCatalogForCallType — mandatory: minInputTokens', () => {
  it('synthesis: excludes models with context_window < 1M', () => {
    const models = [
      entry({ model_id: 'big',   context_window: 1_000_000 }),
      entry({ model_id: 'small', context_window:   800_000 }),
    ]
    const result = filterCatalogForCallType(models, 'synthesis')
    expect(result.map(m => m.model_id)).toEqual(['big'])
  })

  it('synthesis: includes model with exactly 1M context', () => {
    const models = [entry({ model_id: 'exact', context_window: 1_000_000 })]
    const result = filterCatalogForCallType(models, 'synthesis')
    expect(result).toHaveLength(1)
  })

  it('eval_judge: excludes models with context_window < 200K', () => {
    const models = [
      entry({ model_id: 'ok',  context_window: 200_000 }),
      entry({ model_id: 'too-small', context_window: 100_000 }),
    ]
    const result = filterCatalogForCallType(models, 'eval_judge')
    expect(result.map(m => m.model_id)).toEqual(['ok'])
  })

  it('smoke_synth: requires ≥1M context same as synthesis', () => {
    const models = [
      entry({ model_id: 'pass', context_window: 2_000_000 }),
      entry({ model_id: 'fail', context_window: 999_999 }),
    ]
    const result = filterCatalogForCallType(models, 'smoke_synth')
    expect(result.map(m => m.model_id)).toEqual(['pass'])
  })
})

describe('filterCatalogForCallType — mandatory: capabilities', () => {
  it('planner_deep: excludes models without tool-use capability', () => {
    const models = [
      entry({ model_id: 'no-tools',   capabilities: [] }),
      entry({ model_id: 'has-tools',  capabilities: ['tool-use'] }),
    ]
    const result = filterCatalogForCallType(models, 'planner_deep')
    expect(result.map(m => m.model_id)).toEqual(['has-tools'])
  })

  it('planner_fast: excludes models without tool-use capability', () => {
    const models = [
      entry({ model_id: 'no-tools',  capabilities: [] }),
      entry({ model_id: 'has-tools', capabilities: ['tool-use', 'prompt-caching'] }),
    ]
    const result = filterCatalogForCallType(models, 'planner_fast')
    expect(result.map(m => m.model_id)).toEqual(['has-tools'])
  })
})

describe('filterCatalogForCallType — mandatory: roleIn', () => {
  it('synthesis: excludes model with role=planner (not in roleIn)', () => {
    const ctx = 1_000_000
    const models = [
      entry({ model_id: 'synth',    role: 'synthesis', context_window: ctx }),
      entry({ model_id: 'both',     role: 'both',      context_window: ctx }),
      entry({ model_id: 'planner',  role: 'planner',   context_window: ctx }),
      entry({ model_id: 'null-role', role: null,        context_window: ctx }),
    ]
    const result = filterCatalogForCallType(models, 'synthesis')
    const ids = result.map(m => m.model_id)
    expect(ids).toContain('synth')
    expect(ids).toContain('both')
    expect(ids).toContain('null-role')  // null role is not excluded
    expect(ids).not.toContain('planner')
  })
})

// ─── preferred sort ───────────────────────────────────────────────────────────

describe('filterCatalogForCallType — preferred sort', () => {
  it('worker: sorts by cost_asc (cheapest first)', () => {
    const models = [
      entry({ model_id: 'cheap',     cost_input_per_1m: 0.5 }),
      entry({ model_id: 'expensive', cost_input_per_1m: 5.0 }),
      entry({ model_id: 'mid',       cost_input_per_1m: 2.0 }),
    ]
    const result = filterCatalogForCallType(models, 'worker')
    expect(result.map(m => m.model_id)).toEqual(['cheap', 'mid', 'expensive'])
  })

  it('synthesis: sorts by params_desc (highest param count first)', () => {
    const models1M = [
      entry({ model_id: 'small',  param_count:  7,  context_window: 1_000_000 }),
      entry({ model_id: 'large',  param_count: 70,  context_window: 1_000_000 }),
      entry({ model_id: 'medium', param_count: 13,  context_window: 1_000_000 }),
    ]
    const result = filterCatalogForCallType(models1M, 'synthesis')
    expect(result[0].model_id).toBe('large')
    expect(result[2].model_id).toBe('small')
  })

  it('returns empty array when no models pass mandatory filter', () => {
    const models = [
      entry({ model_id: 'tiny', context_window: 4_096 }),
    ]
    const result = filterCatalogForCallType(models, 'synthesis')
    expect(result).toHaveLength(0)
  })

  it('CALL_TYPE_SPECS covers all 11 CallTypes', () => {
    const expectedTypes = [
      'synthesis', 'context_assembly', 'planner_deep', 'planner_fast', 'worker',
      'eval_judge', 'eval_generator', 'smoke_synth', 'checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5',
    ]
    for (const ct of expectedTypes) {
      expect(CALL_TYPE_SPECS).toHaveProperty(ct)
    }
  })
})
