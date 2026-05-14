/**
 * §3.7 — Runtime equivalence tests (≥35 parametrized cases).
 *
 * Verifies that legacy_runAdapter.ts (flag-off path) correctly maps every
 * QueryRequest field to the underlying streamText call, that output is
 * normalised into a valid ModelInteraction, and that runAdapter /
 * streamAdapterRaw dispatch to the legacy path when ADAPTERS_ENABLED=false.
 */
import { describe, test, expect, vi, beforeEach } from 'vitest'
import type { QueryRequest } from '../../types'

vi.mock('server-only', () => ({}))

// ── AI SDK mocks ──────────────────────────────────────────────────────────────

const mockStreamText = vi.fn()
const mockStepCountIs = vi.fn((n: number) => `__stepCountIs_${n}`)
const mockSmoothStream = vi.fn(() => '__smoothStream__')

vi.mock('ai', () => ({
  streamText: (...args: unknown[]) => mockStreamText(...args),
  stepCountIs: (n: number) => mockStepCountIs(n),
  smoothStream: () => mockSmoothStream(),
  jsonSchema: (s: unknown) => ({ __jsonSchema: s }),
}))

vi.mock('@ai-sdk/anthropic', () => ({ anthropic: vi.fn((id: string) => `ant:${id}`) }))
vi.mock('@ai-sdk/deepseek', () => ({ deepseek: vi.fn((id: string) => `ds:${id}`) }))
vi.mock('@ai-sdk/google', () => ({ google: vi.fn((id: string) => `g:${id}`) }))
vi.mock('@ai-sdk/openai', () => ({
  openai: vi.fn((id: string) => `oai:${id}`),
  createOpenAI: vi.fn(() => ({ chat: vi.fn((id: string) => `nim:${id}`) })),
}))

// ── Config mock ───────────────────────────────────────────────────────────────

const mockGetFlag = vi.fn()
vi.mock('@/lib/config/index', () => ({
  getFlag: (key: string) => mockGetFlag(key),
}))

// ── Resolver mocks ────────────────────────────────────────────────────────────

const mockResolveModel = vi.fn()
const mockDeepseekOpts = vi.fn()
const mockGoogleOpts = vi.fn()

vi.mock('@/lib/models/resolver', () => ({
  resolveModel: (id: string) => mockResolveModel(id),
  deepseekProviderOptions: (...args: unknown[]) => mockDeepseekOpts(...args),
  googleProviderOptions: (...args: unknown[]) => mockGoogleOpts(...args),
}))

// ── Registry mocks ────────────────────────────────────────────────────────────

type FakeMeta = {
  id: string
  provider: string
  hint: string
  maxOutputTokens: number
  costPer1MInput: number
  costPer1MOutput: number
}

const DEFAULT_META: FakeMeta = {
  id: 'test-model',
  provider: 'anthropic',
  hint: 'test',
  maxOutputTokens: 8192,
  costPer1MInput: 1,
  costPer1MOutput: 2,
}

const mockGetModelMeta = vi.fn()

vi.mock('@/lib/models/registry', () => ({
  getModelMeta: (...args: unknown[]) => mockGetModelMeta(...args),
  DEFAULT_STACK_ID: 'gemini',
  DEFAULT_MODEL_ID: 'gemini-2.5-flash-lite',
  STACK_ROUTING: {
    gemini: {
      worker: { primary: 'gemini-flash' },
      synthesis: { primary: 'gemini-pro' },
      planner: { primary: 'gemini-flash' },
    },
  },
}))

// ── Stream mock for the new-path adapter dispatcher ──────────────────────────

const mockStreamAdapter = vi.fn()
vi.mock('../../stream_adapter', () => ({
  streamAdapter: (...args: unknown[]) => mockStreamAdapter(...args),
}))

// Collect-interaction is bundled inside run_adapter; mock stream_adapter is enough.

// ── Helpers ───────────────────────────────────────────────────────────────────

async function* emptyGen() {}

function fakeStream(parts: Array<Record<string, unknown>> = []) {
  async function* gen() { for (const p of parts) yield p }
  return { fullStream: gen() }
}

const BASE_REQ: QueryRequest = {
  callType: 'worker',
  modelOverride: { modelId: 'test-model' },
  systemPrompt: 'sys',
  messages: [{ role: 'user', content: 'q' }],
}

// ── Imports after mocks ───────────────────────────────────────────────────────

import { runAdapterLegacy, streamAdapterRawLegacy } from '../../legacy_runAdapter'
import { runAdapter } from '../../run_adapter'
import { streamAdapterRaw } from '../../raw'

// ─────────────────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks()
  mockGetFlag.mockReturnValue(false)
  mockGetModelMeta.mockReturnValue(DEFAULT_META)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  mockResolveModel.mockImplementation((id: any) => `resolved:${id}`)
  mockDeepseekOpts.mockReturnValue(undefined)
  mockGoogleOpts.mockReturnValue(undefined)
  mockStreamText.mockImplementation(() => fakeStream())
})

// ─────────────────────────────────────────────────────────────────────────────
// Block A — runAdapterLegacy: QueryRequest fields → streamText call args
// Each test.each entry is one test. Total for this block: 7 + 9 = 16 tests.
// ─────────────────────────────────────────────────────────────────────────────

describe('runAdapterLegacy — field → streamText arg mapping', () => {
  test.each([
    ['systemPrompt', { systemPrompt: 'custom system' }, 'system', 'custom system'],
    ['maxOutputTokens', { maxOutputTokens: 512 }, 'maxOutputTokens', 512],
    ['temperature-zero', { temperature: 0 }, 'temperature', 0],
    ['temperature-0.7', { temperature: 0.7 }, 'temperature', 0.7],
    ['toolChoice-required', { toolChoice: 'required' }, 'toolChoice', 'required'],
    ['toolChoice-none', { toolChoice: 'none' }, 'toolChoice', 'none'],
    ['toolChoice-auto', { toolChoice: 'auto' }, 'toolChoice', 'auto'],
  ] as Array<[string, Partial<QueryRequest>, string, unknown]>)(
    'passes %s → streamText.%s', async (_, extra, field, expected) => {
      await runAdapterLegacy({ ...BASE_REQ, ...extra })
      const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
      expect(called[field]).toEqual(expected)
    },
  )

  test('passes messages array through unchanged', async () => {
    const msgs = [{ role: 'user' as const, content: 'hello' }, { role: 'assistant' as const, content: 'hi' }]
    await runAdapterLegacy({ ...BASE_REQ, messages: msgs })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.messages).toEqual(msgs)
  })

  test('passes model from resolveModel()', async () => {
    await runAdapterLegacy(BASE_REQ)
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.model).toBe('resolved:test-model')
  })

  test('sets maxRetries:0 when disableSdkRetry=true', async () => {
    await runAdapterLegacy({ ...BASE_REQ, disableSdkRetry: true })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.maxRetries).toBe(0)
  })

  test('omits maxRetries when disableSdkRetry is not set', async () => {
    await runAdapterLegacy(BASE_REQ)
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.maxRetries).toBeUndefined()
  })

  test('sets experimental_transform when smoothStream=true', async () => {
    await runAdapterLegacy({ ...BASE_REQ, smoothStream: true })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.experimental_transform).toBe('__smoothStream__')
  })

  test('omits experimental_transform when smoothStream not set', async () => {
    await runAdapterLegacy(BASE_REQ)
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.experimental_transform).toBeUndefined()
  })

  test('sets stopWhen via stepCountIs when multiStep is set', async () => {
    await runAdapterLegacy({ ...BASE_REQ, multiStep: { maxSteps: 5 } })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.stopWhen).toBe('__stepCountIs_5')
  })

  test('omits stopWhen when multiStep is not set', async () => {
    await runAdapterLegacy(BASE_REQ)
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.stopWhen).toBeUndefined()
  })

  test('passes rawOnFinish as onFinish', async () => {
    const cb = vi.fn()
    await runAdapterLegacy({ ...BASE_REQ, rawOnFinish: cb })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.onFinish).toBe(cb)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Block B — finishReason normalization (5 parametrized cases)
// ─────────────────────────────────────────────────────────────────────────────

describe('runAdapterLegacy — finishReason normalization', () => {
  test.each([
    ['stop', 'stop'],
    ['length', 'length'],
    ['tool-calls', 'tool_calls'],
    ['content-filter', 'content_filter'],
    ['error', 'error'],
  ] as Array<[string, string]>)(
    'SDK reason "%s" → ModelInteraction "%s"', async (sdkReason, expected) => {
      mockStreamText.mockImplementation(() =>
        fakeStream([
          { type: 'finish', finishReason: sdkReason, totalUsage: { inputTokens: 5, outputTokens: 3 } },
        ]),
      )
      const result = await runAdapterLegacy(BASE_REQ)
      expect(result.finishReason).toBe(expected)
    },
  )
})

// ─────────────────────────────────────────────────────────────────────────────
// Block C — tool definition conversion (3 tests)
// ─────────────────────────────────────────────────────────────────────────────

describe('runAdapterLegacy — tool conversion', () => {
  test('empty tools array → tools: undefined in streamText call', async () => {
    await runAdapterLegacy({ ...BASE_REQ, tools: [] })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.tools).toBeUndefined()
  })

  test('single tool → keyed by name with jsonSchema-wrapped parameters', async () => {
    await runAdapterLegacy({
      ...BASE_REQ,
      tools: [{ name: 'submit_plan', description: 'submit the plan', parameters: { type: 'object' } }],
    })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    const tools = called.tools as Record<string, { description: string; parameters: unknown }>
    expect(tools.submit_plan.description).toBe('submit the plan')
    expect(tools.submit_plan.parameters).toMatchObject({ __jsonSchema: expect.anything() })
  })

  test('two tools → both keys present in the tools map', async () => {
    await runAdapterLegacy({
      ...BASE_REQ,
      tools: [
        { name: 'tool_a', description: 'a', parameters: {} },
        { name: 'tool_b', description: 'b', parameters: {} },
      ],
    })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(Object.keys(called.tools as object)).toEqual(['tool_a', 'tool_b'])
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Block D — stream event collection into ModelInteraction (6 tests)
// ─────────────────────────────────────────────────────────────────────────────

describe('runAdapterLegacy — stream event collection', () => {
  test('text-delta events concatenate into finalText', async () => {
    mockStreamText.mockImplementation(() =>
      fakeStream([{ type: 'text-delta', text: 'hello' }, { type: 'text-delta', text: ' world' }]),
    )
    const result = await runAdapterLegacy(BASE_REQ)
    expect(result.finalText).toBe('hello world')
  })

  test('empty stream → finalText is undefined', async () => {
    const result = await runAdapterLegacy(BASE_REQ)
    expect(result.finalText).toBeUndefined()
  })

  test('tool-call event → intermediate entry with correct payload shape', async () => {
    mockStreamText.mockImplementation(() =>
      fakeStream([
        { type: 'tool-call', toolName: 'submit_plan', input: { k: 'v' }, toolCallId: 'tc1' },
      ]),
    )
    const result = await runAdapterLegacy(BASE_REQ)
    expect(result.intermediate).toHaveLength(1)
    const evt = result.intermediate[0]
    expect(evt.type).toBe('tool_call')
    const payload = evt.payload as { name: string; args: unknown; callId: string }
    expect(payload.name).toBe('submit_plan')
    expect(payload.args).toEqual({ k: 'v' })
    expect(payload.callId).toBe('tc1')
  })

  test('finish event → usage populated from totalUsage', async () => {
    mockStreamText.mockImplementation(() =>
      fakeStream([
        { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 100, outputTokens: 50 } },
      ]),
    )
    const result = await runAdapterLegacy(BASE_REQ)
    expect(result.usage.inputTokens).toBe(100)
    expect(result.usage.outputTokens).toBe(50)
  })

  test('no finish event → usage defaults to zeros', async () => {
    const result = await runAdapterLegacy(BASE_REQ)
    expect(result.usage.inputTokens).toBe(0)
    expect(result.usage.outputTokens).toBe(0)
  })

  test('result carries correct modelId and provider from meta', async () => {
    const result = await runAdapterLegacy(BASE_REQ)
    expect(result.modelId).toBe('test-model')
    expect(result.provider).toBe('anthropic')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Block E — streamAdapterRawLegacy: QueryRequest fields → streamText args
// 5 parametrized + 5 individual = 10 tests
// ─────────────────────────────────────────────────────────────────────────────

describe('streamAdapterRawLegacy — field → streamText arg mapping', () => {
  test.each([
    ['systemPrompt', { systemPrompt: 'raw sys' }, 'system', 'raw sys'],
    ['maxOutputTokens', { maxOutputTokens: 256 }, 'maxOutputTokens', 256],
    ['temperature', { temperature: 0.5 }, 'temperature', 0.5],
    ['toolChoice-required', { toolChoice: 'required' }, 'toolChoice', 'required'],
    ['toolChoice-none', { toolChoice: 'none' }, 'toolChoice', 'none'],
  ] as Array<[string, Partial<QueryRequest>, string, unknown]>)(
    'passes %s → streamText.%s', (_, extra, field, expected) => {
      mockStreamText.mockReturnValue({ fullStream: emptyGen() })
      streamAdapterRawLegacy({ ...BASE_REQ, ...extra })
      const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
      expect(called[field]).toEqual(expected)
    },
  )

  test('sets maxRetries:0 when disableSdkRetry=true', () => {
    mockStreamText.mockReturnValue({ fullStream: emptyGen() })
    streamAdapterRawLegacy({ ...BASE_REQ, disableSdkRetry: true })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.maxRetries).toBe(0)
  })

  test('omits maxRetries when disableSdkRetry is not set', () => {
    mockStreamText.mockReturnValue({ fullStream: emptyGen() })
    streamAdapterRawLegacy(BASE_REQ)
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.maxRetries).toBeUndefined()
  })

  test('sets experimental_transform when smoothStream=true', () => {
    mockStreamText.mockReturnValue({ fullStream: emptyGen() })
    streamAdapterRawLegacy({ ...BASE_REQ, smoothStream: true })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.experimental_transform).toBe('__smoothStream__')
  })

  test('passes rawOnFinish as onFinish', () => {
    const cb = vi.fn()
    mockStreamText.mockReturnValue({ fullStream: emptyGen() })
    streamAdapterRawLegacy({ ...BASE_REQ, rawOnFinish: cb })
    const called = mockStreamText.mock.calls[0][0] as Record<string, unknown>
    expect(called.onFinish).toBe(cb)
  })

  test('returns the streamText result and meta', () => {
    const fakeResult = { fullStream: emptyGen(), __tag: 'fake' }
    mockStreamText.mockReturnValue(fakeResult)
    const { result, meta } = streamAdapterRawLegacy(BASE_REQ)
    expect(result).toBe(fakeResult)
    expect((meta as FakeMeta).id).toBe('test-model')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Block F — runAdapter flag dispatch (3 tests)
// ─────────────────────────────────────────────────────────────────────────────

describe('runAdapter — ADAPTERS_ENABLED flag dispatch', () => {
  test('ADAPTERS_ENABLED=false → calls streamText via legacy path', async () => {
    mockGetFlag.mockReturnValue(false)
    await runAdapter(BASE_REQ)
    expect(mockStreamText).toHaveBeenCalledOnce()
  })

  test('ADAPTERS_ENABLED=false → resolveModel called with modelId from override', async () => {
    mockGetFlag.mockReturnValue(false)
    await runAdapter(BASE_REQ)
    expect(mockResolveModel).toHaveBeenCalledWith('test-model')
  })

  test('ADAPTERS_ENABLED=false → does NOT call streamAdapter', async () => {
    mockGetFlag.mockReturnValue(false)
    await runAdapter(BASE_REQ)
    expect(mockStreamAdapter).not.toHaveBeenCalled()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Block G — streamAdapterRaw flag dispatch (2 tests)
// ─────────────────────────────────────────────────────────────────────────────

describe('streamAdapterRaw — ADAPTERS_ENABLED flag dispatch', () => {
  test('ADAPTERS_ENABLED=false → calls streamText via legacy path', () => {
    mockGetFlag.mockReturnValue(false)
    streamAdapterRaw(BASE_REQ)
    expect(mockStreamText).toHaveBeenCalledOnce()
  })

  test('ADAPTERS_ENABLED=false → passes model through resolveModel', () => {
    mockGetFlag.mockReturnValue(false)
    streamAdapterRaw(BASE_REQ)
    expect(mockResolveModel).toHaveBeenCalledWith('test-model')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Block H — model resolution via stack routing (3 tests)
// ─────────────────────────────────────────────────────────────────────────────

describe('runAdapterLegacy — model resolution', () => {
  test('modelOverride.modelId takes precedence over stack routing', async () => {
    mockGetModelMeta.mockReturnValue({ ...DEFAULT_META, id: 'override-model' })
    await runAdapterLegacy({ ...BASE_REQ, modelOverride: { modelId: 'override-model' } })
    expect(mockGetModelMeta).toHaveBeenCalledWith('override-model')
  })

  test('no modelOverride → uses STACK_ROUTING[DEFAULT_STACK_ID][callType].primary', async () => {
    await runAdapterLegacy({ callType: 'worker', systemPrompt: '', messages: [] })
    // gemini stack, worker → gemini-flash per STACK_ROUTING mock
    expect(mockGetModelMeta).toHaveBeenCalledWith('gemini-flash')
  })

  test('unknown model → throws with informative message', async () => {
    mockGetModelMeta.mockReturnValue(undefined)
    await expect(runAdapterLegacy(BASE_REQ)).rejects.toThrow('runAdapterLegacy: unknown model')
  })
})
