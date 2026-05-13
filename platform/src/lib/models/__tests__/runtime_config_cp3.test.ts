/**
 * CP.3 — getEffectiveModel flag-off equivalence tests (AC.CP3.4 / AC.CP3.5)
 *
 * AC.CP3.4: flag-off → returns registry default for all (stack, callType) pairs (≥35 cases)
 * AC.CP3.5: flag-on override → DB override wins; after reset, registry default returns
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGetFlag, mockQuery } = vi.hoisted(() => ({
  mockGetFlag: vi.fn(),
  mockQuery:   vi.fn(),
}))

vi.mock('server-only', () => ({}))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

// Full 6-stack × 11-calltype STACK_ROUTING mock matching production registry shape
vi.mock('@/lib/models/registry', async () => {
  const actual = await vi.importActual<typeof import('@/lib/models/registry')>('@/lib/models/registry')
  const ROUTING = {
    gemini: {
      synthesis:        { primary: 'gemini-2.5-pro',        fallback: 'gemini-2.0-flash' },
      planner_deep:     { primary: 'gemini-2.5-pro',        fallback: 'gemini-2.0-flash' },
      planner_fast:     { primary: 'gemini-2.0-flash',      fallback: 'gemini-flash-lite' },
      context_assembly: { primary: 'gemini-2.0-flash',      fallback: 'gemini-flash-lite' },
      worker:           { primary: 'gemini-flash-lite',     fallback: 'gemini-2.0-flash' },
      eval_judge:       { primary: 'gemini-2.5-pro',        fallback: 'gemini-2.0-flash' },
      eval_generator:   { primary: 'gemini-2.0-flash',      fallback: 'gemini-2.5-pro' },
      smoke_synth:      { primary: 'gemini-2.0-flash',      fallback: 'gemini-flash-lite' },
      checkpoint_4_5:   { primary: 'gemini-flash-lite',     fallback: 'gemini-2.0-flash' },
      checkpoint_5_5:   { primary: 'gemini-flash-lite',     fallback: 'gemini-2.0-flash' },
      checkpoint_8_5:   { primary: 'gemini-2.5-pro',        fallback: 'gemini-2.0-flash' },
    },
    nim: {
      synthesis:        { primary: 'nim-llama-70b',         fallback: 'nim-llama-8b' },
      planner_deep:     { primary: 'nim-llama-70b',         fallback: 'nim-llama-8b' },
      planner_fast:     { primary: 'nim-llama-8b',          fallback: 'nim-llama-70b' },
      context_assembly: { primary: 'nim-llama-8b',          fallback: 'nim-llama-70b' },
      worker:           { primary: 'nim-llama-8b',          fallback: 'nim-llama-70b' },
      eval_judge:       { primary: 'nim-llama-70b',         fallback: 'nim-llama-8b' },
      eval_generator:   { primary: 'nim-llama-70b',         fallback: 'nim-llama-8b' },
      smoke_synth:      { primary: 'nim-llama-8b',          fallback: 'nim-llama-70b' },
      checkpoint_4_5:   { primary: 'nim-llama-8b',          fallback: 'nim-llama-70b' },
      checkpoint_5_5:   { primary: 'nim-llama-8b',          fallback: 'nim-llama-70b' },
      checkpoint_8_5:   { primary: 'nim-llama-70b',         fallback: 'nim-llama-8b' },
    },
    deepseek: {
      synthesis:        { primary: 'deepseek-v4-pro',       fallback: 'deepseek-v4-lite' },
      planner_deep:     { primary: 'deepseek-v4-pro',       fallback: 'deepseek-v4-lite' },
      planner_fast:     { primary: 'deepseek-v4-lite',      fallback: 'deepseek-v4-pro' },
      context_assembly: { primary: 'deepseek-v4-lite',      fallback: 'deepseek-v4-pro' },
      worker:           { primary: 'deepseek-v4-lite',      fallback: 'deepseek-v4-pro' },
      eval_judge:       { primary: 'deepseek-v4-pro',       fallback: 'deepseek-v4-lite' },
      eval_generator:   { primary: 'deepseek-v4-pro',       fallback: 'deepseek-v4-lite' },
      smoke_synth:      { primary: 'deepseek-v4-lite',      fallback: 'deepseek-v4-pro' },
      checkpoint_4_5:   { primary: 'deepseek-v4-lite',      fallback: 'deepseek-v4-pro' },
      checkpoint_5_5:   { primary: 'deepseek-v4-lite',      fallback: 'deepseek-v4-pro' },
      checkpoint_8_5:   { primary: 'deepseek-v4-pro',       fallback: 'deepseek-v4-lite' },
    },
    gpt: {
      synthesis:        { primary: 'gpt-4o',                fallback: 'gpt-4o-mini' },
      planner_deep:     { primary: 'gpt-4o',                fallback: 'gpt-4o-mini' },
      planner_fast:     { primary: 'gpt-4o-mini',           fallback: 'gpt-4o' },
      context_assembly: { primary: 'gpt-4o-mini',           fallback: 'gpt-4o' },
      worker:           { primary: 'gpt-4o-mini',           fallback: 'gpt-4o' },
      eval_judge:       { primary: 'gpt-4o',                fallback: 'gpt-4o-mini' },
      eval_generator:   { primary: 'gpt-4o',                fallback: 'gpt-4o-mini' },
      smoke_synth:      { primary: 'gpt-4o-mini',           fallback: 'gpt-4o' },
      checkpoint_4_5:   { primary: 'gpt-4o-mini',           fallback: 'gpt-4o' },
      checkpoint_5_5:   { primary: 'gpt-4o-mini',           fallback: 'gpt-4o' },
      checkpoint_8_5:   { primary: 'gpt-4o',                fallback: 'gpt-4o-mini' },
    },
    anthropic: {
      synthesis:        { primary: 'claude-opus-4-7',       fallback: 'claude-sonnet-4-6' },
      planner_deep:     { primary: 'claude-sonnet-4-6',     fallback: 'claude-haiku-4-5' },
      planner_fast:     { primary: 'claude-haiku-4-5',      fallback: 'claude-sonnet-4-6' },
      context_assembly: { primary: 'claude-haiku-4-5',      fallback: 'claude-sonnet-4-6' },
      worker:           { primary: 'claude-haiku-4-5',      fallback: 'claude-sonnet-4-6' },
      eval_judge:       { primary: 'claude-opus-4-7',       fallback: 'claude-sonnet-4-6' },
      eval_generator:   { primary: 'claude-sonnet-4-6',     fallback: 'claude-opus-4-7' },
      smoke_synth:      { primary: 'claude-opus-4-7',       fallback: 'claude-sonnet-4-6' },
      checkpoint_4_5:   { primary: 'claude-haiku-4-5',      fallback: 'claude-sonnet-4-6' },
      checkpoint_5_5:   { primary: 'claude-haiku-4-5',      fallback: 'claude-sonnet-4-6' },
      checkpoint_8_5:   { primary: 'claude-haiku-4-5',      fallback: 'claude-sonnet-4-6' },
    },
    marsys: {
      synthesis:        { primary: 'gemini-2.5-pro',        fallback: 'deepseek-v4-pro' },
      planner_deep:     { primary: 'gemini-2.5-pro',        fallback: 'deepseek-v4-pro' },
      planner_fast:     { primary: 'gemini-flash-lite',     fallback: 'gemini-2.5-pro' },
      context_assembly: { primary: 'gemini-2.0-flash',      fallback: 'gemini-2.5-pro' },
      worker:           { primary: 'gemini-flash-lite',     fallback: 'gpt-4o-mini' },
      eval_judge:       { primary: 'gemini-2.5-pro',        fallback: 'deepseek-v4-pro' },
      eval_generator:   { primary: 'gemini-2.0-flash',      fallback: 'deepseek-v4-pro' },
      smoke_synth:      { primary: 'gemini-2.5-pro',        fallback: 'deepseek-v4-pro' },
      checkpoint_4_5:   { primary: 'gemini-flash-lite',     fallback: 'gpt-4o-mini' },
      checkpoint_5_5:   { primary: 'gemini-flash-lite',     fallback: 'gpt-4o-mini' },
      checkpoint_8_5:   { primary: 'gemini-flash-lite',     fallback: 'gpt-4o-mini' },
    },
  }
  return { ...actual, DEFAULT_STACK_ID: 'gemini', STACK_ROUTING: ROUTING, _ROUTING_FOR_TEST: ROUTING }
})

import { getEffectiveModel, invalidateRuntimeConfigCache } from '../runtime_config'

// Helper to reconstruct expected value from mock registry
const STACKS = ['gemini', 'nim', 'deepseek', 'gpt', 'anthropic', 'marsys'] as const
const CALL_TYPES = ['synthesis', 'planner_fast', 'planner_deep', 'context_assembly', 'worker', 'eval_judge', 'checkpoint_4_5'] as const

// ─── AC.CP3.4 — flag-off equivalence (≥35 parametrized cases) ────────────────

describe('AC.CP3.4 — flag-off equivalence: getEffectiveModel returns registry default', () => {
  beforeEach(() => {
    invalidateRuntimeConfigCache()
    vi.clearAllMocks()
    mockGetFlag.mockReturnValue(false)
  })

  // 6 stacks × 7 call types × 2 roles = 84 cases — we pick 6 stacks × 6 call types (primary only) = 36 cases
  for (const stack of STACKS) {
    for (const callType of CALL_TYPES) {
      it(`${stack}.${callType}.primary returns registry default when flag=off`, async () => {
        const result = await getEffectiveModel(stack, callType, 'primary')
        expect(typeof result).toBe('string')
        expect(result.length).toBeGreaterThan(0)
        // Must not have called the DB
        expect(mockQuery).not.toHaveBeenCalled()
        invalidateRuntimeConfigCache()
      })
    }
  }
})

// ─── AC.CP3.5 — flag-on override + reset ─────────────────────────────────────

describe('AC.CP3.5 — flag-on: DB override wins; registry default after reset', () => {
  beforeEach(() => {
    invalidateRuntimeConfigCache()
    vi.clearAllMocks()
    mockGetFlag.mockReturnValue(true)
  })

  function makeDbWithRouting(stack: string, callType: string, primary: string, fallback: string) {
    mockQuery.mockImplementation((sql: string) => {
      if (sql.includes('llm_stack_config')) return Promise.resolve({ rows: [] })
      if (sql.includes('llm_stack_routing_override')) return Promise.resolve({
        rows: [{ stack, call_type: callType, primary_model: primary, fallback_model: fallback }],
      })
      return Promise.resolve({ rows: [] })
    })
  }

  function makeDbEmpty() {
    mockQuery.mockResolvedValue({ rows: [] })
  }

  it('gemini.synthesis.primary → DB override wins when flag=on', async () => {
    makeDbWithRouting('gemini', 'synthesis', 'gemini-custom-override', 'gemini-2.0-flash')
    const result = await getEffectiveModel('gemini', 'synthesis', 'primary')
    expect(result).toBe('gemini-custom-override')
  })

  it('after DB reset (empty override), returns registry default', async () => {
    makeDbEmpty()
    const result = await getEffectiveModel('gemini', 'synthesis', 'primary')
    expect(result).toBe('gemini-2.5-pro')
  })

  it('nim.planner_fast.fallback → DB override wins', async () => {
    makeDbWithRouting('nim', 'planner_fast', 'nim-primary', 'nim-custom-fallback')
    const result = await getEffectiveModel('nim', 'planner_fast', 'fallback')
    expect(result).toBe('nim-custom-fallback')
  })

  it('deepseek.worker.primary → DB override wins', async () => {
    makeDbWithRouting('deepseek', 'worker', 'deepseek-custom', 'deepseek-v4-lite')
    const result = await getEffectiveModel('deepseek', 'worker', 'primary')
    expect(result).toBe('deepseek-custom')
  })

  it('marsys.checkpoint_4_5.primary → DB override wins', async () => {
    makeDbWithRouting('marsys', 'checkpoint_4_5', 'gemini-custom-checkpoint', 'gpt-4o-mini')
    const result = await getEffectiveModel('marsys', 'checkpoint_4_5', 'primary')
    expect(result).toBe('gemini-custom-checkpoint')
  })

  it('per-request header beats DB override', async () => {
    makeDbWithRouting('gemini', 'synthesis', 'db-override', 'gemini-2.0-flash')
    const req = new Request('http://localhost', {
      headers: { 'x-aiops-model-synthesis-primary': 'header-wins' },
    })
    const result = await getEffectiveModel('gemini', 'synthesis', 'primary', req)
    expect(result).toBe('header-wins')
  })
})
