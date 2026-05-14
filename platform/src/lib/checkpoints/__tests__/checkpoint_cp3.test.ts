/**
 * CP.3 checkpoint integration tests (AC.CP3.11)
 *
 * Verifies that checkpoint_4_5, checkpoint_5_5, checkpoint_8_5 each call
 * getEffectiveModel('marsys', '<checkpoint_X_X>', 'primary') — the CP.3 migration.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('fs', () => ({
  default: {
    readFileSync: vi.fn(() => 'Query: {{query}}\nPlan: {{query_plan_json}}\nAlternatives: {{discarded_alternatives}}\nClass: {{query_class}}\nAssets: {{bundle_assets}}\nSignals: {{signals_preview}}\nValidators: {{validator_results_json}}\nSynthesis: {{synthesized_text}}'),
  },
}))
vi.mock('@/lib/telemetry/index', () => ({
  telemetry: { recordMetric: vi.fn(), recordLatency: vi.fn(), recordError: vi.fn() },
}))

const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters', () => ({ runAdapter: (...args: unknown[]) => mockRunAdapter(...args) }))

const mockGetFlag = vi.fn()
vi.mock('@/lib/config/index', () => ({ getFlag: (...args: unknown[]) => mockGetFlag(...args) }))

const mockGetEffectiveModel = vi.fn().mockResolvedValue('resolved-model-id')
vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: (...args: unknown[]) => mockGetEffectiveModel(...args),
}))

import { runCheckpoint4_5 } from '../checkpoint_4_5'
import { runCheckpoint5_5 } from '../checkpoint_5_5'
import { runCheckpoint8_5 } from '../checkpoint_8_5'
import type { Checkpoint45Input, Checkpoint55Input, Checkpoint85Input, StructuredPrediction } from '../types'

function makeInput45(): Checkpoint45Input {
  return {
    query: 'Test query',
    query_plan: {
      query_plan_id: 'plan-001',
      query_text: 'Test query',
      query_class: 'factual',
      domains: [],
      total_token_budget: 1000,
      is_multi_domain: false,
    } as unknown as import('@/lib/router/types').QueryPlan,
  }
}

function makeInput55(): Checkpoint55Input {
  return {
    query: 'Test query',
    query_plan: {
      query_plan_id: 'plan-001',
      query_text: 'Test query',
      query_class: 'factual',
      domains: [],
      total_token_budget: 1000,
      is_multi_domain: false,
    } as unknown as import('@/lib/router/types').QueryPlan,
    bundle: {
      bundle_id: 'bundle-001',
      query_plan_reference: 'plan-001',
      manifest_fingerprint: 'fp',
      mandatory_context: [],
      total_tokens: 0,
      bundle_hash: 'hash',
      schema_version: '1.0',
    },
    tool_results: [],
  }
}

function makeInput85(): Checkpoint85Input {
  return {
    synthesized_text: 'This is a test synthesis.',
    query_class: 'factual',
    validator_results: [],
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetFlag.mockImplementation((flag: string) => {
    if (flag === 'CHECKPOINT_4_5_ENABLED') return true
    if (flag === 'CHECKPOINT_5_5_ENABLED') return true
    if (flag === 'CHECKPOINT_8_5_ENABLED') return true
    if (flag === 'PREDICTION_EXTRACT_ENABLED') return false
    return false
  })
  mockGetEffectiveModel.mockResolvedValue('resolved-model-id')
  mockRunAdapter.mockResolvedValue({
    finalText: JSON.stringify({ verdict: 'pass', confidence: 0.9, reasoning: 'ok' }),
    usage: { inputTokens: 0, outputTokens: 0 },
    finishReason: 'stop',
    intermediate: [],
  })
})

// ─── checkpoint_4_5 ───────────────────────────────────────────────────────────

describe('checkpoint_4_5 CP.3 integration', () => {
  it('calls getEffectiveModel with marsys + checkpoint_4_5 + primary', async () => {
    await runCheckpoint4_5(makeInput45())
    expect(mockGetEffectiveModel).toHaveBeenCalledWith('marsys', 'checkpoint_4_5', 'primary')
  })

  it('passes resolved model ID to runAdapter', async () => {
    mockGetEffectiveModel.mockResolvedValue('gemini-flash-lite-test')
    await runCheckpoint4_5(makeInput45())
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('gemini-flash-lite-test')
  })

  it('skips getEffectiveModel when checkpoint is disabled', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag !== 'CHECKPOINT_4_5_ENABLED')
    await runCheckpoint4_5(makeInput45())
    expect(mockGetEffectiveModel).not.toHaveBeenCalled()
  })

  it('uses DB override when flag is on (propagated through mock)', async () => {
    mockGetEffectiveModel.mockResolvedValue('db-override-model-4-5')
    await runCheckpoint4_5(makeInput45())
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('db-override-model-4-5')
  })

  it('passes resolved model to runAdapter call', async () => {
    mockGetEffectiveModel.mockResolvedValue('resolved-checkpoint-4-5')
    await runCheckpoint4_5(makeInput45())
    const callArg = mockRunAdapter.mock.calls[0]?.[0]
    expect(callArg).toBeDefined()
  })
})

// ─── checkpoint_5_5 ───────────────────────────────────────────────────────────

describe('checkpoint_5_5 CP.3 integration', () => {
  it('calls getEffectiveModel with marsys + checkpoint_5_5 + primary', async () => {
    await runCheckpoint5_5(makeInput55())
    expect(mockGetEffectiveModel).toHaveBeenCalledWith('marsys', 'checkpoint_5_5', 'primary')
  })

  it('passes resolved model ID to runAdapter', async () => {
    mockGetEffectiveModel.mockResolvedValue('gemini-flash-lite-test-5-5')
    await runCheckpoint5_5(makeInput55())
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('gemini-flash-lite-test-5-5')
  })

  it('skips getEffectiveModel when checkpoint_5_5 is disabled', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag !== 'CHECKPOINT_5_5_ENABLED')
    await runCheckpoint5_5(makeInput55())
    expect(mockGetEffectiveModel).not.toHaveBeenCalled()
  })

  it('uses DB override when flag is on (propagated through mock)', async () => {
    mockGetEffectiveModel.mockResolvedValue('db-override-model-5-5')
    await runCheckpoint5_5(makeInput55())
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('db-override-model-5-5')
  })

  it('passes resolved model to runAdapter call', async () => {
    await runCheckpoint5_5(makeInput55())
    const callArg = mockRunAdapter.mock.calls[0]?.[0]
    expect(callArg).toBeDefined()
  })
})

// ─── checkpoint_8_5 ───────────────────────────────────────────────────────────

describe('checkpoint_8_5 CP.3 integration', () => {
  it('calls getEffectiveModel with marsys + checkpoint_8_5 + primary', async () => {
    await runCheckpoint8_5(makeInput85())
    expect(mockGetEffectiveModel).toHaveBeenCalledWith('marsys', 'checkpoint_8_5', 'primary')
  })

  it('passes resolved model ID to runAdapter', async () => {
    mockGetEffectiveModel.mockResolvedValue('gemini-flash-lite-test-8-5')
    await runCheckpoint8_5(makeInput85())
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('gemini-flash-lite-test-8-5')
  })

  it('skips getEffectiveModel when checkpoint_8_5 is disabled', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag !== 'CHECKPOINT_8_5_ENABLED')
    await runCheckpoint8_5(makeInput85())
    expect(mockGetEffectiveModel).not.toHaveBeenCalled()
  })

  it('uses DB override when flag is on (propagated through mock)', async () => {
    mockGetEffectiveModel.mockResolvedValue('db-override-model-8-5')
    await runCheckpoint8_5(makeInput85())
    const callArg = mockRunAdapter.mock.calls[0][0] as { modelOverride: { modelId: string } }
    expect(callArg.modelOverride.modelId).toBe('db-override-model-8-5')
  })

  it('passes resolved model to runAdapter call', async () => {
    await runCheckpoint8_5(makeInput85())
    const callArg = mockRunAdapter.mock.calls[0]?.[0]
    expect(callArg).toBeDefined()
  })
})
