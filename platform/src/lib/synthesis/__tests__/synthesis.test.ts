import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock server-only so the import guard doesn't fail in test environment
vi.mock('server-only', () => ({}))

// Mock the model resolver — we don't want real LLM calls
vi.mock('@/lib/models/resolver', () => ({
  resolveModel: vi.fn(() => ({ id: 'claude-haiku-4-5', provider: 'anthropic' })),
  isReasoningModel: vi.fn(() => false),
  resolveWorkerModel: vi.fn((id: string) => id ?? 'claude-haiku-4-5'),
  supportsStreaming: vi.fn(() => true),
  googleProviderOptions: vi.fn(() => null),
  deepseekProviderOptions: vi.fn(() => null),
}))

// Mock streamText at the ai module level — must be before any imports
const mockStreamText = vi.fn()
vi.mock('ai', () => ({
  streamText: (...args: unknown[]) => mockStreamText(...args),
  stepCountIs: vi.fn((n: number) => ({ type: 'stepCount', value: n })),
  smoothStream: vi.fn(() => (stream: unknown) => stream),
  tool: vi.fn((config: unknown) => config),
}))

// Mock the registry/supports for models
vi.mock('@/lib/models/registry', () => ({
  supports: vi.fn(),
  MODELS: [],
  getModelMeta: vi.fn((id: string) => ({
    id,
    label: 'Test Model',
    provider: 'anthropic',
    speedTier: 'fast',
    maxOutputTokens: 64000,
    capabilities: ['tool-use', 'prompt-caching'],
  })),
  getReasoningMode: vi.fn(() => 'none'),
}))

// Mock retrieval tools
vi.mock('@/lib/retrieve/index', () => ({
  getTool: vi.fn((name: string) => ({
    name,
    version: '1.0',
    retrieve: vi.fn().mockResolvedValue({ results: [], tool_name: name }),
  })),
}))

// Mock validators — runAll is called in onFinish (BUG-2); must be mocked
// so the audit test doesn't wait on real validator logic.
vi.mock('@/lib/validators/index', () => ({
  runAll: vi.fn().mockResolvedValue([]),
}))

// Mock cache
vi.mock('@/lib/cache/index', () => ({
  executeWithCache: vi.fn().mockResolvedValue({
    tool_bundle_id: 'test-bundle',
    tool_name: 'msr_sql',
    tool_version: '1.0',
    invocation_params: {},
    results: [],
    served_from_cache: false,
    latency_ms: 10,
    result_hash: 'sha256:abc',
    schema_version: '1.0' as const,
  }),
  RequestScopedToolCache: vi.fn().mockImplementation(() => ({
    get: vi.fn(),
    put: vi.fn(),
    getPromise: vi.fn().mockReturnValue(undefined),
    generateKey: vi.fn().mockReturnValue('test-key'),
    clear: vi.fn(),
    size: vi.fn().mockReturnValue(0),
  })),
  createToolCache: vi.fn(),
}))

import { SingleModelOrchestrator } from '../single_model_strategy'
import type { SynthesisRequest } from '../types'
import { supports } from '@/lib/models/registry'

const mockSupports = vi.mocked(supports)

// ── Shared fixture ────────────────────────────────────────────────────────────

function makeRequest(overrides: Partial<SynthesisRequest> = {}): SynthesisRequest {
  return {
    query: 'What does my chart say about career?',
    query_plan: {
      query_plan_id: 'plan-uuid-001',
      query_text: 'What does my chart say about career?',
      query_class: 'interpretive',
      domains: ['career'],
      forward_looking: false,
      audience_tier: 'super_admin',
      tools_authorized: ['msr_sql', 'pattern_register'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'three_interpretation',
      manifest_fingerprint: 'fp-test-abc123',
      schema_version: '1.0',
    },
    bundle: {
      bundle_id: 'bundle-uuid-001',
      query_plan_reference: 'plan-uuid-001',
      manifest_fingerprint: 'fp-test-abc123',
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
      bundle_hash: 'sha256:bundle-hash-xyz',
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
    text: Promise.resolve('test response'),
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks()
  // Default: model supports both capabilities
  mockSupports.mockImplementation((_id: string, cap: string) =>
    cap === 'tool-use' || cap === 'prompt-caching'
  )
})

describe('SingleModelOrchestrator — system prompt', () => {
  it('calls streamText with a rendered system prompt as the first message', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest()
    await orchestrator.synthesize(request)

    expect(mockStreamText).toHaveBeenCalledOnce()
    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const firstMessage = callArgs.messages[0]

    expect(firstMessage.role).toBe('system')
    // The rendered prompt includes key placeholder substitutions
    expect(firstMessage.content).toContain('the native')
    expect(firstMessage.content).toContain('FORENSIC (floor)')
  })

  it('includes the user query as the last message', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest()
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const lastMessage = callArgs.messages[callArgs.messages.length - 1]

    expect(lastMessage.role).toBe('user')
    expect(lastMessage.content).toBe(request.query)
  })

  it('includes conversation history messages between system and user', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest({
      conversation_history: [
        { role: 'user', content: 'Previous question' },
        { role: 'assistant', content: 'Previous answer' },
      ],
    })
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    // system + 2 history + current user = 4
    expect(callArgs.messages).toHaveLength(4)
    expect(callArgs.messages[1].content).toBe('Previous question')
    expect(callArgs.messages[2].content).toBe('Previous answer')
  })
})

describe('SingleModelOrchestrator — tool-use', () => {
  it('provides non-empty tools when model supports tool-use', async () => {
    mockSupports.mockImplementation((_id: string, cap: string) =>
      cap === 'tool-use' || cap === 'prompt-caching'
    )
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeRequest())

    const callArgs = mockStreamText.mock.calls[0][0] as { tools?: Record<string, unknown> }
    expect(callArgs.tools).toBeDefined()
    expect(Object.keys(callArgs.tools ?? {})).toContain('msr_sql')
    expect(Object.keys(callArgs.tools ?? {})).toContain('pattern_register')
  })

  it('passes undefined tools when model does not support tool-use', async () => {
    mockSupports.mockImplementation((_id: string, cap: string) =>
      cap === 'prompt-caching' // tool-use NOT supported
    )
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeRequest())

    const callArgs = mockStreamText.mock.calls[0][0] as { tools?: Record<string, unknown> }
    expect(callArgs.tools).toBeUndefined()
  })

  it('adds Anthropic cache-control header when model supports prompt-caching', async () => {
    mockSupports.mockImplementation((_id: string, cap: string) =>
      cap === 'tool-use' || cap === 'prompt-caching'
    )
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeRequest())

    const callArgs = mockStreamText.mock.calls[0][0] as {
      messages: Array<{ role: string; providerOptions?: { anthropic?: { cacheControl?: unknown } } }>
    }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.providerOptions?.anthropic?.cacheControl).toEqual({ type: 'ephemeral' })
  })

  it('omits cache-control header when model does not support prompt-caching', async () => {
    mockSupports.mockImplementation((_id: string, cap: string) =>
      cap === 'tool-use' // prompt-caching NOT supported
    )
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    await orchestrator.synthesize(makeRequest())

    const callArgs = mockStreamText.mock.calls[0][0] as {
      messages: Array<{ role: string; providerOptions?: unknown }>
    }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.providerOptions).toBeUndefined()
  })
})

describe('SingleModelOrchestrator — metadata', () => {
  it('returns metadata with correct fields', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest()
    const { metadata } = await orchestrator.synthesize(request)

    // synthesis_prompt_version comes from the template version
    expect(metadata.synthesis_prompt_version).toBeTruthy()
    expect(typeof metadata.synthesis_prompt_version).toBe('string')

    expect(metadata.synthesizer_model_id).toBe('claude-haiku-4-5')
    expect(metadata.bundle_hash).toBe('sha256:bundle-hash-xyz')

    // started_at should be a valid ISO date
    expect(() => new Date(metadata.started_at)).not.toThrow()
    expect(new Date(metadata.started_at).toISOString()).toBe(metadata.started_at)
  })

  it('returns the streamText result object', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const { result } = await orchestrator.synthesize(makeRequest())

    expect(result).toBe(mockResult)
  })
})

describe('SingleModelOrchestrator — FUB-1: chart_context', () => {
  it('uses real chart_context values in the system prompt when provided', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest({
      chart_context: {
        name: 'Abhisek Mohanty',
        birth_date: '1984-02-05',
        birth_time: '10:43',
        birth_place: 'Bhubaneswar, Odisha, India',
      },
    })
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.content).toContain('1984-02-05')
    expect(systemMsg.content).toContain('10:43')
    expect(systemMsg.content).toContain('Bhubaneswar')
  })

  it('falls back to placeholder strings when chart_context is omitted', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest() // no chart_context
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.content).toContain('<birth date unavailable>')
    expect(systemMsg.content).not.toContain('1984-02-05')
  })
})

describe('SingleModelOrchestrator — FUB-2: chart context block injection', () => {
  it('appends CHART_CONTEXT_BLOCK to system prompt when vector_search results + floor entries exist', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest({
      tool_results: [
        {
          tool_bundle_id: 'vs-bundle-001',
          tool_name: 'vector_search',
          tool_version: '1.1.0',
          invocation_params: {},
          results: [
            {
              content: 'Sun is in Capricorn in the 10th house.',
              source_canonical_id: 'FORENSIC',
              source_version: '8.0',
              confidence: 0.95,
              signal_id: 'chunk:rag_001',
            },
          ],
          served_from_cache: false,
          latency_ms: 10,
          result_hash: 'sha256:vs-hash',
          schema_version: '1.0' as const,
        },
      ],
    })
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.role).toBe('system')
    expect(systemMsg.content).toContain('CHART_CONTEXT_BLOCK')
    expect(systemMsg.content).toContain('Sun is in Capricorn')
    expect(systemMsg.content).toContain('[chunk:chunk:rag_001]')
  })

  it('does not inject CHART_CONTEXT_BLOCK when no vector_search results are present', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest({ tool_results: [] })
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.content).not.toContain('<CHART_CONTEXT_BLOCK')
  })
})

describe('SingleModelOrchestrator — FUB-3: tool_results injection', () => {
  it('appends PRE_FETCHED_TOOL_RESULTS to system prompt from non-vector_search tool results', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest({
      tool_results: [
        {
          tool_bundle_id: 'msr-bundle-001',
          tool_name: 'msr_sql',
          tool_version: '1.0.0',
          invocation_params: {},
          results: [
            {
              content: 'SIG.MSR.042 — Strong 10th lord in kendra.',
              source_canonical_id: 'MSR',
              source_version: '3.0',
              confidence: 0.87,
              signal_id: 'SIG.MSR.042',
            },
          ],
          served_from_cache: false,
          latency_ms: 5,
          result_hash: 'sha256:msr-hash',
          schema_version: '1.0' as const,
        },
      ],
    })
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.content).toContain('PRE_FETCHED_TOOL_RESULTS')
    expect(systemMsg.content).toContain('SIG.MSR.042')
    expect(systemMsg.content).toContain('[signal:SIG.MSR.042]')
  })

  it('does not inject PRE_FETCHED_TOOL_RESULTS when tool_results is empty', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest({ tool_results: [] })
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const systemMsg = callArgs.messages[0]
    expect(systemMsg.content).not.toContain('<PRE_FETCHED_TOOL_RESULTS>')
  })

  it('user message remains the last message when tool_results are present', async () => {
    const mockResult = makeMockStreamResult()
    mockStreamText.mockReturnValue(mockResult)

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest({
      tool_results: [
        {
          tool_bundle_id: 'msr-bundle-002',
          tool_name: 'msr_sql',
          tool_version: '1.0.0',
          invocation_params: {},
          results: [{ content: 'Some signal.', source_canonical_id: 'MSR', source_version: '3.0', confidence: 0.8 }],
          served_from_cache: false,
          latency_ms: 5,
          result_hash: 'sha256:msr2',
          schema_version: '1.0' as const,
        },
      ],
    })
    await orchestrator.synthesize(request)

    const callArgs = mockStreamText.mock.calls[0][0] as { messages: Array<{ role: string; content: string }> }
    const lastMsg = callArgs.messages[callArgs.messages.length - 1]
    expect(lastMsg.role).toBe('user')
    expect(lastMsg.content).toBe(request.query)
  })
})

describe('SingleModelOrchestrator — audit event', () => {
  it('logs an audit event to console.log on stream finish', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    // Capture and invoke the onFinish callback
    let capturedOnFinish: ((args: { finishReason: string; usage: { inputTokens: number; outputTokens: number } }) => Promise<void> | void) | undefined

    mockStreamText.mockImplementation((args: { onFinish?: (e: { finishReason: string; usage: { inputTokens: number; outputTokens: number } }) => Promise<void> | void }) => {
      capturedOnFinish = args.onFinish
      return makeMockStreamResult()
    })

    const orchestrator = new SingleModelOrchestrator()
    const request = makeRequest()
    await orchestrator.synthesize(request)

    // Simulate the stream finishing — await so async validators complete
    await capturedOnFinish?.({ finishReason: 'stop', usage: { inputTokens: 100, outputTokens: 50 } })

    // Verify audit event was logged
    const auditCall = consoleSpy.mock.calls.find(call =>
      typeof call[0] === 'string' && call[0].includes('[synthesis] audit event:')
    )
    expect(auditCall).toBeDefined()

    const auditJson = JSON.parse((auditCall![1] as string))
    expect(auditJson.event_type).toBe('synthesis_complete')
    expect(auditJson.query_plan_id).toBe('plan-uuid-001')
    expect(auditJson.bundle_id).toBe('bundle-uuid-001')
    expect(auditJson.finish_reason).toBe('stop')
    expect(auditJson.synthesizer_model_id).toBe('claude-haiku-4-5')
    expect(auditJson.validator_votes).toEqual({})
    expect(auditJson.started_at).toBeTruthy()
    expect(auditJson.finished_at).toBeTruthy()

    consoleSpy.mockRestore()
  })
})
