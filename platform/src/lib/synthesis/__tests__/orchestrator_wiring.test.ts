/**
 * Stream D — Orchestrator wiring tests
 *
 * Verifies that checkpoint hooks are correctly integrated into
 * SingleModelOrchestrator and that flag-OFF path is byte-identical to Phase 3.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/models/resolver', () => ({
  resolveModel: vi.fn(() => ({ id: 'claude-haiku-4-5', provider: 'anthropic' })),
  isReasoningModel: vi.fn(() => false),
  resolveWorkerModel: vi.fn((id: string) => id ?? 'claude-haiku-4-5'),
  supportsStreaming: vi.fn(() => true),
  googleProviderOptions: vi.fn(() => null),
  deepseekProviderOptions: vi.fn(() => null),
}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({
  streamText: (...args: unknown[]) => mockStreamText(...args),
  generateText: vi.fn().mockResolvedValue({ text: '[]' }),
  stepCountIs: vi.fn((n: number) => ({ type: 'stepCount', value: n })),
  smoothStream: vi.fn(() => (stream: unknown) => stream),
  tool: vi.fn((config: unknown) => config),
}))

vi.mock('@/lib/models/registry', () => ({
  supports: vi.fn().mockReturnValue(true),
  MODELS: [],
  getModelMeta: vi.fn((id: string) => ({
    id,
    label: 'Test',
    provider: 'anthropic',
    speedTier: 'fast',
    maxOutputTokens: 64000,
    capabilities: ['tool-use', 'prompt-caching'],
  })),
  getReasoningMode: vi.fn(() => 'none'),
}))

vi.mock('@/lib/retrieve/index', () => ({
  getTool: vi.fn(),
}))

vi.mock('@/lib/cache/index', () => ({
  executeWithCache: vi.fn().mockResolvedValue({
    tool_bundle_id: 'tb-test',
    tool_name: 'msr_sql',
    tool_version: '1.0',
    invocation_params: {},
    results: [],
    served_from_cache: false,
    latency_ms: 10,
    result_hash: 'sha256:abc',
    schema_version: '1.0',
  }),
}))

vi.mock('@/lib/telemetry/index', () => ({
  telemetry: {
    recordMetric: vi.fn(),
    recordLatency: vi.fn(),
    recordCost: vi.fn(),
    recordError: vi.fn(),
  },
}))

vi.mock('@/lib/prompts/index', () => ({
  getDefaultRegistry: vi.fn(() => ({
    get: vi.fn(() => ({
      version: '1.0',
      system: 'You are a Jyotish analyst. Query: {{query_text}}. Bundle: {{bundle_summary}}. Tools: {{tools_available}}.',
      style_suffixes: {},
    })),
  })),
}))

vi.mock('@/lib/prompts/types', () => ({
  renderTemplate: vi.fn((_template: unknown, vars: Record<string, string>) => {
    return `Rendered prompt for: ${vars.bundle_summary ?? 'test'}`
  }),
}))

// ── Checkpoint mocks ──────────────────────────────────────────────────────────

const mockRunCheckpoint4_5 = vi.fn()
const mockRunCheckpoint5_5 = vi.fn()
const mockRunCheckpoint8_5 = vi.fn()

vi.mock('@/lib/checkpoints/checkpoint_4_5', () => ({
  runCheckpoint4_5: (...args: unknown[]) => mockRunCheckpoint4_5(...args),
}))
vi.mock('@/lib/checkpoints/checkpoint_5_5', () => ({
  runCheckpoint5_5: (...args: unknown[]) => mockRunCheckpoint5_5(...args),
}))
vi.mock('@/lib/checkpoints/checkpoint_8_5', () => ({
  runCheckpoint8_5: (...args: unknown[]) => mockRunCheckpoint8_5(...args),
}))

const mockGetFlag = vi.fn()
vi.mock('@/lib/config/index', () => ({ getFlag: (...args: unknown[]) => mockGetFlag(...args) }))

import { SingleModelOrchestrator } from '../single_model_strategy'
import { CheckpointHaltError } from '../../checkpoints/types'
import type { SynthesisRequest } from '../types'

function makePassResult(id: string) {
  return {
    checkpoint_id: id,
    verdict: 'pass' as const,
    confidence: 0.95,
    reasoning: 'ok',
    latency_ms: 100,
    skipped: false,
  }
}

function makeSkippedResult(id: string) {
  return {
    checkpoint_id: id,
    verdict: 'pass' as const,
    confidence: 1,
    reasoning: 'checkpoint disabled (flag OFF)',
    latency_ms: 0,
    skipped: true,
  }
}

function makeSynthesisRequest(overrides: Partial<SynthesisRequest> = {}): SynthesisRequest {
  return {
    query: 'What does Mars in the 1st house indicate?',
    query_plan: {
      query_plan_id: 'plan-wiring-001',
      query_text: 'What does Mars in the 1st house indicate?',
      query_class: 'interpretive',
      domains: ['personality'],
      forward_looking: false,
      audience_tier: 'super_admin',
      tools_authorized: ['msr_sql'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'three_interpretation',
      manifest_fingerprint: 'fp-wiring',
      schema_version: '1.0',
    },
    bundle: {
      bundle_id: 'bundle-wiring-001',
      query_plan_reference: 'plan-wiring-001',
      manifest_fingerprint: 'fp-wiring',
      mandatory_context: [
        {
          canonical_id: 'FORENSIC',
          version: '8.0',
          content_hash: 'sha256:aaa',
          token_count: 1000,
          role: 'floor',
          source: 'rule_composer',
        },
      ],
      total_tokens: 1000,
      bundle_hash: 'sha256:bundle-wiring',
      schema_version: '1.0',
    },
    tool_results: [],
    conversation_history: [],
    selected_model_id: 'claude-haiku-4-5',
    style: 'acharya',
    audience_tier: 'super_admin',
    cache: {
      get: vi.fn(),
      put: vi.fn(),
      getPromise: vi.fn().mockReturnValue(undefined),
      generateKey: vi.fn().mockReturnValue('test-key'),
      clear: vi.fn(),
      size: vi.fn().mockReturnValue(0),
    } as unknown as import('@/lib/cache/index').RequestScopedToolCache,
    ...overrides,
  }
}

function makeMockStreamResult() {
  return {
    toUIMessageStreamResponse: vi.fn(),
    consumeStream: vi.fn(),
    textStream: {},
    text: Promise.resolve('synthesized response text'),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  // All flags OFF by default (Phase 3 baseline)
  mockGetFlag.mockReturnValue(false)
  mockRunCheckpoint4_5.mockResolvedValue(makeSkippedResult('checkpoint_4_5'))
  mockRunCheckpoint5_5.mockResolvedValue(makeSkippedResult('checkpoint_5_5'))
  mockRunCheckpoint8_5.mockResolvedValue(makeSkippedResult('checkpoint_8_5'))
})

// ── Flag-OFF: byte-identical path ─────────────────────────────────────────────

describe('orchestrator — all flags OFF', () => {
  it('calls streamText exactly once when all checkpoint flags are OFF', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeSynthesisRequest())

    expect(mockStreamText).toHaveBeenCalledOnce()
  })

  it('checkpoint runners are NOT called when flags are OFF', async () => {
    mockStreamText.mockReturnValue(makeMockStreamResult())

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeSynthesisRequest())

    expect(mockRunCheckpoint4_5).not.toHaveBeenCalled()
    expect(mockRunCheckpoint5_5).not.toHaveBeenCalled()
  })

  it('returns result and metadata as in Phase 3 baseline', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const { result, metadata } = await orchestrator.synthesize(makeSynthesisRequest())

    expect(result).toBe(mockResult)
    expect(metadata.synthesizer_model_id).toBe('claude-haiku-4-5')
    expect(metadata.bundle_hash).toBe('sha256:bundle-wiring')
  })
})

// ── Flag-ON: checkpoint 4.5 ───────────────────────────────────────────────────

describe('orchestrator — checkpoint 4.5 enabled', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_4_5_ENABLED')
    mockRunCheckpoint4_5.mockResolvedValue(makePassResult('checkpoint_4_5'))
  })

  it('calls runCheckpoint4_5 exactly once', async () => {
    mockStreamText.mockReturnValue(makeMockStreamResult())

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeSynthesisRequest())

    expect(mockRunCheckpoint4_5).toHaveBeenCalledOnce()
  })

  it('passes query and query_plan to checkpoint 4.5', async () => {
    mockStreamText.mockReturnValue(makeMockStreamResult())
    const request = makeSynthesisRequest()

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(request)

    const callArgs = mockRunCheckpoint4_5.mock.calls[0][0]
    expect(callArgs.query).toBe(request.query)
    expect(callArgs.query_plan.query_plan_id).toBe(request.query_plan.query_plan_id)
  })
})

// ── Flag-ON: checkpoint 5.5 ───────────────────────────────────────────────────

describe('orchestrator — checkpoint 5.5 enabled', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_5_5_ENABLED')
    mockRunCheckpoint5_5.mockResolvedValue(makePassResult('checkpoint_5_5'))
  })

  it('calls runCheckpoint5_5 exactly once', async () => {
    mockStreamText.mockReturnValue(makeMockStreamResult())

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeSynthesisRequest())

    expect(mockRunCheckpoint5_5).toHaveBeenCalledOnce()
  })

  it('passes bundle and tool_results to checkpoint 5.5', async () => {
    mockStreamText.mockReturnValue(makeMockStreamResult())
    const request = makeSynthesisRequest()

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(request)

    const callArgs = mockRunCheckpoint5_5.mock.calls[0][0]
    expect(callArgs.bundle.bundle_id).toBe(request.bundle.bundle_id)
    expect(callArgs.tool_results).toBe(request.tool_results)
  })
})

// ── Halt on 4.5 short-circuits 5.5 and synthesis ─────────────────────────────

describe('orchestrator — halt on checkpoint 4.5 short-circuits 5.5 and synthesis', () => {
  it('throws CheckpointHaltError and does not call streamText', async () => {
    const haltResult = { ...makePassResult('checkpoint_4_5'), verdict: 'halt' as const }
    const haltError = new CheckpointHaltError('checkpoint_4_5', haltResult)

    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_4_5_ENABLED' || flag === 'CHECKPOINT_4_5_FAIL_HARD'
    )
    mockRunCheckpoint4_5.mockRejectedValue(haltError)

    const orchestrator = new SingleModelOrchestrator()
    await expect(orchestrator.synthesize(makeSynthesisRequest())).rejects.toThrow(CheckpointHaltError)

    expect(mockStreamText).not.toHaveBeenCalled()
    expect(mockRunCheckpoint5_5).not.toHaveBeenCalled()
  })
})

// ── Halt on 5.5 short-circuits synthesis ─────────────────────────────────────

describe('orchestrator — halt on checkpoint 5.5 short-circuits synthesis', () => {
  it('throws CheckpointHaltError and does not call streamText', async () => {
    const haltResult = { ...makePassResult('checkpoint_5_5'), verdict: 'halt' as const }
    const haltError = new CheckpointHaltError('checkpoint_5_5', haltResult)

    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_4_5_ENABLED' ||
      flag === 'CHECKPOINT_5_5_ENABLED' ||
      flag === 'CHECKPOINT_5_5_FAIL_HARD'
    )
    mockRunCheckpoint4_5.mockResolvedValue(makePassResult('checkpoint_4_5'))
    mockRunCheckpoint5_5.mockRejectedValue(haltError)

    const orchestrator = new SingleModelOrchestrator()
    await expect(orchestrator.synthesize(makeSynthesisRequest())).rejects.toThrow(CheckpointHaltError)

    expect(mockStreamText).not.toHaveBeenCalled()
  })
})

// ── Multi-checkpoint warn: all logged ────────────────────────────────────────

describe('orchestrator — multiple warns from 4.5 and 5.5', () => {
  it('proceeds to synthesis when both 4.5 and 5.5 warn (no halt)', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_4_5_ENABLED' || flag === 'CHECKPOINT_5_5_ENABLED'
    )
    mockRunCheckpoint4_5.mockResolvedValue({ ...makePassResult('checkpoint_4_5'), verdict: 'warn' as const })
    mockRunCheckpoint5_5.mockResolvedValue({ ...makePassResult('checkpoint_5_5'), verdict: 'warn' as const })
    mockStreamText.mockReturnValue(makeMockStreamResult())

    const orchestrator = new SingleModelOrchestrator()
    const { result } = await orchestrator.synthesize(makeSynthesisRequest())

    expect(result).toBeDefined()
    expect(mockStreamText).toHaveBeenCalledOnce()
  })
})

// ── onAuditEvent callback ─────────────────────────────────────────────────────

describe('orchestrator — onAuditEvent callback', () => {
  it('invokes onAuditEvent with audit event when provided', async () => {
    const onAuditEvent = vi.fn()
    let capturedOnFinish: ((args: { finishReason: string; usage?: { inputTokens?: number; outputTokens?: number }; text?: string }) => void) | undefined

    mockStreamText.mockImplementation((args: { onFinish?: (e: unknown) => void }) => {
      capturedOnFinish = args.onFinish as typeof capturedOnFinish
      return makeMockStreamResult()
    })

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeSynthesisRequest({ onAuditEvent }))

    await capturedOnFinish?.({ finishReason: 'stop', usage: { inputTokens: 100, outputTokens: 50 }, text: 'response' })

    expect(onAuditEvent).toHaveBeenCalledOnce()
    const event = onAuditEvent.mock.calls[0][0]
    expect(event.event_type).toBe('synthesis_complete')
    expect(event.finish_reason).toBe('stop')
  })
})
