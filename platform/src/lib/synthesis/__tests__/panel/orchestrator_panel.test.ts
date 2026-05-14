/**
 * Stream E — Panel Orchestrator + Strategy Switch tests
 * schema_version: 1.0
 *
 * Covers:
 *   - createOrchestrator() flag/opt-in matrix
 *   - Audit event shape consistency across both strategies
 *   - Panel payload presence/absence in audit event
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

// ── Model resolver ─────────────────────────────────────────────────────────────
vi.mock('@/lib/models/resolver', () => ({
  resolveModel: vi.fn((id: string) => ({ id, provider: 'anthropic' })),
  isReasoningModel: vi.fn(() => false),
  resolveWorkerModel: vi.fn((id: string) => id ?? 'claude-haiku-4-5'),
  supportsStreaming: vi.fn(() => true),
  googleProviderOptions: vi.fn(() => null),
  deepseekProviderOptions: vi.fn(() => undefined),
}))

// ── AI SDK ─────────────────────────────────────────────────────────────────────
const mockStreamText = vi.fn()
vi.mock('ai', () => ({
  streamText: (...args: unknown[]) => mockStreamText(...args),
  stepCountIs: vi.fn((n: number) => ({ type: 'stepCount', value: n })),
  smoothStream: vi.fn(() => (stream: unknown) => stream),
  tool: vi.fn((config: unknown) => config),
  generateText: vi.fn().mockResolvedValue({ text: '' }),
}))

// ── Models registry ────────────────────────────────────────────────────────────
vi.mock('@/lib/models/registry', () => ({
  supports: vi.fn().mockReturnValue(true),
  getReasoningMode: vi.fn(() => 'none'),
  MODELS: [],
  DEFAULT_STACK_ID: 'anthropic',
  DEFAULT_MODEL_ID: 'claude-sonnet-4-6',
  STACK_ROUTING: {},
  getModelMeta: vi.fn((id: string) => ({
    id,
    label: 'Test',
    provider: 'anthropic',
    speedTier: 'fast',
    maxOutputTokens: 64000,
    capabilities: ['tool-use', 'prompt-caching'],
    costPer1MInput: 3.0,
    costPer1MOutput: 15.0,
  })),
}))

// ── Retrieval / cache ──────────────────────────────────────────────────────────
vi.mock('@/lib/retrieve/index', () => ({ getTool: vi.fn() }))
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

// ── Telemetry ─────────────────────────────────────────────────────────────────
vi.mock('@/lib/telemetry/index', () => ({
  telemetry: {
    recordMetric: vi.fn(),
    recordLatency: vi.fn(),
    recordCost: vi.fn(),
    recordError: vi.fn(),
  },
}))

// ── Prompts ───────────────────────────────────────────────────────────────────
vi.mock('@/lib/prompts/index', () => ({
  getDefaultRegistry: vi.fn(() => ({
    get: vi.fn(() => ({
      version: '1.0',
      system: 'You are a Jyotish analyst.',
      style_suffixes: {},
    })),
  })),
}))
vi.mock('@/lib/prompts/types', () => ({
  renderTemplate: vi.fn((_t: unknown, vars: Record<string, string>) =>
    `Rendered: ${vars.bundle_summary ?? 'test'}`
  ),
}))

// ── Checkpoints ───────────────────────────────────────────────────────────────
vi.mock('@/lib/checkpoints/checkpoint_4_5', () => ({
  runCheckpoint4_5: vi.fn().mockResolvedValue({
    checkpoint_id: 'checkpoint_4_5',
    verdict: 'pass',
    confidence: 1,
    reasoning: 'skipped',
    latency_ms: 0,
    skipped: true,
  }),
}))
vi.mock('@/lib/checkpoints/checkpoint_5_5', () => ({
  runCheckpoint5_5: vi.fn().mockResolvedValue({
    checkpoint_id: 'checkpoint_5_5',
    verdict: 'pass',
    confidence: 1,
    reasoning: 'skipped',
    latency_ms: 0,
    skipped: true,
  }),
}))
vi.mock('@/lib/checkpoints/checkpoint_8_5', () => ({
  runCheckpoint8_5: vi.fn().mockResolvedValue({
    checkpoint_id: 'checkpoint_8_5',
    verdict: 'pass',
    confidence: 1,
    reasoning: 'skipped',
    latency_ms: 0,
    skipped: true,
  }),
}))

// ── Panel sub-modules ─────────────────────────────────────────────────────────
vi.mock('@/lib/synthesis/panel/member_runner', () => ({
  runPanelMembers: vi.fn().mockResolvedValue({
    member_outputs: [
      {
        member_index: 0,
        model_id: 'claude-sonnet-4-6',
        provider_family: 'anthropic',
        status: 'success',
        answer: 'Panel answer 1',
        latency_ms: 100,
      },
      {
        member_index: 1,
        model_id: 'gpt-4.1',
        provider_family: 'openai',
        status: 'success',
        answer: 'Panel answer 2',
        latency_ms: 150,
      },
      {
        member_index: 2,
        model_id: 'gemini-2.5-pro',
        provider_family: 'google',
        status: 'success',
        answer: 'Panel answer 3',
        latency_ms: 120,
      },
    ],
  }),
}))

vi.mock('@/lib/synthesis/panel/adjudicator', () => ({
  adjudicate: vi.fn().mockResolvedValue({
    final_answer: 'Synthesized answer',
    divergence_summary: {
      has_divergence: false,
      divergence_count: 0,
      summary_text: '',
    },
    member_alignment: {
      member_1: 'aligned',
      member_2: 'aligned',
      member_3: 'aligned',
    },
    adjudicator_model_id: 'deepseek-chat',
    latency_ms: 200,
  }),
}))

vi.mock('@/lib/synthesis/panel/divergence_detector', () => ({
  classifyDivergence: vi.fn().mockReturnValue({
    has_divergence: false,
    instances: [],
    member_alignment_summary: {},
  }),
}))

vi.mock('@/lib/synthesis/panel/default_slate', () => ({
  DEFAULT_PANEL_SLATE: [
    {
      provider_family: 'anthropic',
      model_id: 'claude-sonnet-4-6',
      prompt_variant_tag: 'panel_member_v1',
    },
    {
      provider_family: 'openai',
      model_id: 'gpt-4.1',
      prompt_variant_tag: 'panel_member_v1',
    },
    {
      provider_family: 'google',
      model_id: 'gemini-2.5-pro',
      prompt_variant_tag: 'panel_member_v1',
    },
  ],
  selectAdjudicator: vi.fn().mockReturnValue({
    provider_family: 'deepseek',
    model_id: 'deepseek-chat',
  }),
}))

// ── Feature flags ─────────────────────────────────────────────────────────────
const mockGetFlag = vi.fn()
vi.mock('@/lib/config/index', () => ({
  getFlag: (...args: unknown[]) => mockGetFlag(...args),
}))

// ── Imports under test ────────────────────────────────────────────────────────
import { createOrchestrator } from '../../orchestrator'
import { SingleModelOrchestrator } from '../../single_model_strategy'
import { PanelModeOrchestrator } from '../../panel_strategy'
import type { SynthesisRequest } from '../../types'

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeMockStreamResult() {
  return {
    toUIMessageStreamResponse: vi.fn(),
    consumeStream: vi.fn(),
    textStream: {},
    text: Promise.resolve('synthesized response text'),
  }
}

function makeSynthesisRequest(overrides: Partial<SynthesisRequest> = {}): SynthesisRequest {
  return {
    query: 'What does Mars in the 1st house indicate?',
    query_plan: {
      query_plan_id: 'plan-panel-001',
      query_text: 'What does Mars in the 1st house indicate?',
      query_class: 'interpretive',
      domains: ['personality'],
      forward_looking: false,
      audience_tier: 'super_admin',
      tools_authorized: [],
      history_mode: 'synthesized',
      panel_mode: true,
      expected_output_shape: 'three_interpretation',
      manifest_fingerprint: 'fp-panel',
      schema_version: '1.0',
    },
    bundle: {
      bundle_id: 'bundle-panel-001',
      query_plan_reference: 'plan-panel-001',
      manifest_fingerprint: 'fp-panel',
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
      bundle_hash: 'sha256:bundle-panel',
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

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks()
  mockGetFlag.mockReturnValue(false)
})

// ── Strategy switch: flag matrix ───────────────────────────────────────────────

describe('createOrchestrator — strategy switch', () => {
  it('returns SingleModelOrchestrator when PANEL_MODE_ENABLED=false (no request arg)', () => {
    mockGetFlag.mockReturnValue(false)
    const orch = createOrchestrator()
    expect(orch).toBeInstanceOf(SingleModelOrchestrator)
  })

  it('returns SingleModelOrchestrator when PANEL_MODE_ENABLED=false AND panel_opt_in=true (flag wins)', () => {
    mockGetFlag.mockReturnValue(false)
    const orch = createOrchestrator({ panel_opt_in: true })
    expect(orch).toBeInstanceOf(SingleModelOrchestrator)
  })

  it('returns SingleModelOrchestrator when PANEL_MODE_ENABLED=true AND panel_opt_in=false (opt-in required)', () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'PANEL_MODE_ENABLED')
    const orch = createOrchestrator({ panel_opt_in: false })
    expect(orch).toBeInstanceOf(SingleModelOrchestrator)
  })

  it('returns PanelModeOrchestrator when PANEL_MODE_ENABLED=true AND panel_opt_in=true', () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'PANEL_MODE_ENABLED')
    const orch = createOrchestrator({ panel_opt_in: true })
    expect(orch).toBeInstanceOf(PanelModeOrchestrator)
  })

  it('returns SingleModelOrchestrator when called with no request arg regardless of flags', () => {
    mockGetFlag.mockReturnValue(true)
    const orch = createOrchestrator()
    // No panel_opt_in → undefined → not === true → SingleModel
    expect(orch).toBeInstanceOf(SingleModelOrchestrator)
  })

  it('returns SingleModelOrchestrator when panel_opt_in is undefined', () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'PANEL_MODE_ENABLED')
    const orch = createOrchestrator({ panel_opt_in: undefined })
    expect(orch).toBeInstanceOf(SingleModelOrchestrator)
  })
})

// ── Audit event shape: single-model path ──────────────────────────────────────

describe('single-model path — audit event shape', () => {
  it('emits synthesis_complete event_type', async () => {
    mockGetFlag.mockReturnValue(false)
    const onAuditEvent = vi.fn()

    let capturedOnFinish: ((args: {
      finishReason: string
      usage?: { inputTokens?: number; outputTokens?: number }
      text?: string
    }) => void) | undefined

    mockStreamText.mockImplementation((args: { onFinish?: (e: unknown) => void }) => {
      capturedOnFinish = args.onFinish as typeof capturedOnFinish
      return makeMockStreamResult()
    })

    const orch = createOrchestrator({ panel_opt_in: false })
    await orch.synthesize(makeSynthesisRequest({ onAuditEvent }))

    await capturedOnFinish?.({
      finishReason: 'stop',
      usage: { inputTokens: 50, outputTokens: 20 },
      text: 'single-model answer',
    })

    expect(onAuditEvent).toHaveBeenCalledOnce()
    const event = onAuditEvent.mock.calls[0][0]
    expect(event.event_type).toBe('synthesis_complete')
  })

  it('panel payload is ABSENT from single-model audit event', async () => {
    mockGetFlag.mockReturnValue(false)
    const onAuditEvent = vi.fn()

    let capturedOnFinish: ((args: {
      finishReason: string
      usage?: { inputTokens?: number; outputTokens?: number }
      text?: string
    }) => void) | undefined

    mockStreamText.mockImplementation((args: { onFinish?: (e: unknown) => void }) => {
      capturedOnFinish = args.onFinish as typeof capturedOnFinish
      return makeMockStreamResult()
    })

    const orch = createOrchestrator({ panel_opt_in: false })
    await orch.synthesize(makeSynthesisRequest({ onAuditEvent }))
    await capturedOnFinish?.({ finishReason: 'stop', text: 'answer' })

    const event = onAuditEvent.mock.calls[0][0]
    expect(event.panel).toBeUndefined()
  })
})

// ── Audit event shape: panel path ─────────────────────────────────────────────

describe('panel path — audit event shape', () => {
  beforeEach(() => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'PANEL_MODE_ENABLED')
  })

  it('emits synthesis_complete event_type', async () => {
    const onAuditEvent = vi.fn()

    let capturedOnFinish: ((args: {
      finishReason: string
      usage?: { inputTokens?: number; outputTokens?: number }
      text?: string
    }) => void) | undefined

    mockStreamText.mockImplementation((args: { onFinish?: (e: unknown) => void }) => {
      capturedOnFinish = args.onFinish as typeof capturedOnFinish
      return makeMockStreamResult()
    })

    const orch = createOrchestrator({ panel_opt_in: true })
    await orch.synthesize(makeSynthesisRequest({ onAuditEvent }))
    await capturedOnFinish?.({ finishReason: 'stop', text: 'Synthesized answer' })

    expect(onAuditEvent).toHaveBeenCalledOnce()
    const event = onAuditEvent.mock.calls[0][0]
    expect(event.event_type).toBe('synthesis_complete')
  })

  it('panel payload EXISTS in panel audit event', async () => {
    const onAuditEvent = vi.fn()

    let capturedOnFinish: ((args: {
      finishReason: string
      usage?: { inputTokens?: number; outputTokens?: number }
      text?: string
    }) => void) | undefined

    mockStreamText.mockImplementation((args: { onFinish?: (e: unknown) => void }) => {
      capturedOnFinish = args.onFinish as typeof capturedOnFinish
      return makeMockStreamResult()
    })

    const orch = createOrchestrator({ panel_opt_in: true })
    await orch.synthesize(makeSynthesisRequest({ onAuditEvent }))
    await capturedOnFinish?.({ finishReason: 'stop', text: 'Synthesized answer' })

    const event = onAuditEvent.mock.calls[0][0]
    expect(event.panel).toBeDefined()
    expect(event.panel.adjudicator_model_id).toBe('deepseek-chat')
    expect(event.panel.panel_slate).toEqual([
      'claude-sonnet-4-6',
      'gpt-4.1',
      'gemini-2.5-pro',
    ])
  })

  it('synthesizer_model_id reflects panel:adjudicator pattern', async () => {
    let capturedOnFinish: ((args: {
      finishReason: string
      usage?: { inputTokens?: number; outputTokens?: number }
      text?: string
    }) => void) | undefined

    const onAuditEvent = vi.fn()
    mockStreamText.mockImplementation((args: { onFinish?: (e: unknown) => void }) => {
      capturedOnFinish = args.onFinish as typeof capturedOnFinish
      return makeMockStreamResult()
    })

    const orch = createOrchestrator({ panel_opt_in: true })
    const { metadata } = await orch.synthesize(makeSynthesisRequest({ onAuditEvent }))
    await capturedOnFinish?.({ finishReason: 'stop', text: 'Synthesized answer' })

    expect(metadata.synthesizer_model_id).toBe('panel:deepseek-chat')

    const event = onAuditEvent.mock.calls[0][0]
    expect(event.synthesizer_model_id).toBe('panel:deepseek-chat')
  })
})
