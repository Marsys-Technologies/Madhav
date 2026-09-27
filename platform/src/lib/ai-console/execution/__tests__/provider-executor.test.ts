import { inspect } from 'node:util'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { LanguageModelV3 } from '@ai-sdk/provider'
import type { OwnedConnectionRuntimeBinding } from '../../providers/types'

vi.mock('server-only', () => ({}))

const mocks = vi.hoisted(() => ({ streamAdapterRaw: vi.fn() }))
vi.mock('@/lib/adapters/raw', () => ({ streamAdapterRaw: mocks.streamAdapterRaw }))

import { AiConsoleError } from '../../errors'
import { StructuredOutputValidationError } from '../structured-output-error'
import { createProviderRoleExecutor, type RoleExecutionRequest } from '../provider-executor'
import type { ResolvedRoleExecution } from '../types'

const connectionId = '00000000-0000-4000-8000-000000000008'
const model = { specificationVersion: 'v3', provider: 'test', modelId: 'dynamic-model' } as LanguageModelV3

function parts(values: unknown[], terminalError?: unknown) {
  return (async function* () {
    for (const value of values) yield value
    if (terminalError) throw terminalError
  })()
}

function raw(values: unknown[], terminalError?: unknown) {
  return { result: { fullStream: parts(values, terminalError) } }
}

function execution(overrides: Partial<ResolvedRoleExecution> = {}) {
  const disposals: ReturnType<typeof vi.fn>[] = []
  const createRuntimeBinding = vi.fn(async () => {
    const dispose = vi.fn()
    disposals.push(dispose)
    return { providerId: 'openai' as const, connectionId, modelId: 'dynamic-model', model, dispose }
  })
  const markRuntimeFailure = vi.fn(async () => undefined)
  const value: ResolvedRoleExecution = {
    role: 'worker', adapterType: 'provider',
    target: { kind: 'provider_model', providerId: 'openai', connectionId, modelId: 'dynamic-model' },
    capabilities: { supportsTools: true, supportsStructuredOutput: true },
    createRuntimeBinding, markRuntimeFailure, ...overrides,
  }
  return { value, createRuntimeBinding, markRuntimeFailure, disposals }
}

const request = {
  systemPrompt: 'system', messages: [{ role: 'user' as const, content: 'hello' }],
  responseSchema: { type: 'object' as const, properties: { ok: { type: 'boolean' as const } } },
}

describe('provider-backed RoleExecutor', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('returns text, structured output, tool calls, normalized usage, and the true safe identity', async () => {
    mocks.streamAdapterRaw.mockReturnValue(raw([
      { type: 'text-delta', text: '{"ok":true}' },
      { type: 'tool-call', toolName: 'lookup', input: { id: 4 }, toolCallId: 'call-1' },
      { type: 'finish', finishReason: 'tool-calls', totalUsage: { inputTokens: 7, outputTokens: 3 } },
    ]))
    const owned = execution()
    const executor = createProviderRoleExecutor(owned.value)
    const result = await executor.generate({ ...request, tools: [{ name: 'lookup', description: 'Lookup', parameters: { type: 'object' } }] })

    expect(result).toEqual(expect.objectContaining({
      text: '{"ok":true}', structured: { ok: true },
      toolCalls: [{ name: 'lookup', args: { id: 4 }, callId: 'call-1' }],
      usage: { inputTokens: 7, outputTokens: 3, totalTokens: 10 },
      finishReason: 'tool_calls', retryCount: 0,
    }))
    expect(executor.descriptor).toEqual({ role: 'worker', providerId: 'openai', connectionId, modelId: 'dynamic-model' })
    expect(mocks.streamAdapterRaw.mock.calls[0][0]).toMatchObject({
      disableSdkRetry: true,
      runtimeDescriptor: { providerId: 'openai', connectionId, modelId: 'dynamic-model' },
      tools: [{ name: 'lookup', description: 'Lookup', parameters: { type: 'object' } }],
    })
    expect(owned.disposals[0]).toHaveBeenCalledOnce()
  })

  it('rejects valid JSON that violates the requested schema', async () => {
    mocks.streamAdapterRaw.mockReturnValue(raw([
      { type: 'text-delta', text: '{"ok":"not-a-boolean"}' },
      { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 1, outputTokens: 1 } },
    ]))
    const owned = execution()
    const failure = await createProviderRoleExecutor(owned.value).generate(request).catch(error => error)
    expect(failure).toBeInstanceOf(StructuredOutputValidationError)
    expect(failure.candidateText()).toBe('{"ok":"not-a-boolean"}')
    expect(() => JSON.stringify(failure)).toThrow()
    expect(String(failure)).not.toContain('not-a-boolean')
  })

  it.each<[string, Partial<ResolvedRoleExecution>, RoleExecutionRequest]>([
    ['tools', { capabilities: { supportsTools: false, supportsStructuredOutput: true } }, { ...request, tools: [{ name: 'lookup', description: 'Lookup', parameters: { type: 'object' as const } }] }],
    ['structured output', { capabilities: { supportsTools: true, supportsStructuredOutput: false } }, request],
  ])('fails closed locally when exact target lacks %s capability', async (_name, override, input) => {
    const owned = execution(override)
    await expect(createProviderRoleExecutor(owned.value).generate(input)).rejects.toMatchObject({ code: 'AI_ROLE_INCOMPATIBLE' })
    expect(owned.createRuntimeBinding).not.toHaveBeenCalled()
    expect(mocks.streamAdapterRaw).not.toHaveBeenCalled()
  })

  it('retries one transient pre-output failure on the same exact target with fresh reauthorization', async () => {
    mocks.streamAdapterRaw
      .mockReturnValueOnce(raw([], new AiConsoleError('AI_RATE_LIMITED')))
      .mockReturnValueOnce(raw([
        { type: 'text-delta', text: 'done' },
        { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 2, outputTokens: 1 } },
      ]))
    const owned = execution()
    const result = await createProviderRoleExecutor(owned.value).generate({ ...request, responseSchema: undefined })

    expect(result.retryCount).toBe(1)
    expect(owned.createRuntimeBinding).toHaveBeenCalledTimes(2)
    expect(mocks.streamAdapterRaw.mock.calls.map(([value]) => value.runtimeDescriptor)).toEqual([
      { providerId: 'openai', connectionId, modelId: 'dynamic-model' },
      { providerId: 'openai', connectionId, modelId: 'dynamic-model' },
    ])
    expect(owned.markRuntimeFailure).not.toHaveBeenCalled()
    expect(owned.disposals.every(dispose => dispose.mock.calls.length === 1)).toBe(true)
  })

  it('marks only the terminal exact-version transient failure after the retry is exhausted', async () => {
    mocks.streamAdapterRaw.mockImplementation(() => raw([], new AiConsoleError('AI_PROVIDER_UNREACHABLE')))
    const owned = execution()
    await expect(createProviderRoleExecutor(owned.value).generate(request))
      .rejects.toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    expect(owned.createRuntimeBinding).toHaveBeenCalledTimes(2)
    expect(owned.markRuntimeFailure).toHaveBeenCalledOnce()
    expect(owned.markRuntimeFailure).toHaveBeenCalledWith(expect.objectContaining({
      code: 'AI_PROVIDER_UNREACHABLE', role: 'worker',
    }))
  })

  it.each([
    ['authentication', new AiConsoleError('AI_CONNECTION_INVALID')],
    ['billing', new AiConsoleError('AI_BILLING_UNAVAILABLE')],
    ['permission', new AiConsoleError('AI_PERMISSION_DENIED')],
    ['model', new AiConsoleError('AI_MODEL_UNAVAILABLE')],
  ])('never retries a %s failure', async (_name, failure) => {
    mocks.streamAdapterRaw.mockReturnValue(raw([], failure))
    const owned = execution()
    await expect(createProviderRoleExecutor(owned.value).generate(request)).rejects.toMatchObject({ code: failure.code })
    expect(owned.createRuntimeBinding).toHaveBeenCalledOnce()
    expect(owned.disposals[0]).toHaveBeenCalledOnce()
  })

  it('preserves the normalized terminal provider error if health marking fails', async () => {
    mocks.streamAdapterRaw.mockReturnValue(raw([], new AiConsoleError('AI_CONNECTION_INVALID')))
    const owned = execution()
    owned.markRuntimeFailure.mockRejectedValueOnce(new Error('internal persistence detail'))
    const error = await createProviderRoleExecutor(owned.value).generate(request).catch(value => value)
    expect(error).toMatchObject({ code: 'AI_CONNECTION_INVALID' })
    expect(String(error)).not.toContain('persistence')
  })

  it('never retries after a user-visible stream delta and disposes only after the stream fails', async () => {
    mocks.streamAdapterRaw.mockReturnValue(raw([
      { type: 'text-delta', text: 'visible' },
    ], new AiConsoleError('AI_PROVIDER_UNREACHABLE')))
    const owned = execution()
    const reader = createProviderRoleExecutor(owned.value).stream({ ...request, responseSchema: undefined }).getReader()
    expect(await reader.read()).toEqual({ done: false, value: { type: 'text_delta', text: 'visible' } })
    expect(owned.disposals[0]).not.toHaveBeenCalled()
    await expect(reader.read()).rejects.toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    expect(owned.createRuntimeBinding).toHaveBeenCalledOnce()
    expect(owned.disposals[0]).toHaveBeenCalledOnce()
  })

  it('never retries after a terminal finish was already emitted', async () => {
    mocks.streamAdapterRaw.mockReturnValue(raw([
      { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 1, outputTokens: 1 } },
    ], new AiConsoleError('AI_PROVIDER_UNREACHABLE')))
    const owned = execution()
    const reader = createProviderRoleExecutor(owned.value).stream(request).getReader()
    expect((await reader.read()).value).toMatchObject({ type: 'finish' })
    await expect(reader.read()).rejects.toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    expect(owned.createRuntimeBinding).toHaveBeenCalledOnce()
  })

  it('does not dispose a successful stream until its terminal finish event is consumed', async () => {
    let release!: () => void
    const gate = new Promise<void>(resolve => { release = resolve })
    mocks.streamAdapterRaw.mockReturnValue({ result: { fullStream: (async function* () {
      yield { type: 'text-delta', text: 'visible' }
      await gate
      yield { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 1, outputTokens: 1 } }
    })() } })
    const owned = execution()
    const reader = createProviderRoleExecutor(owned.value).stream({ ...request, responseSchema: undefined }).getReader()
    await reader.read()
    expect(owned.disposals[0]).not.toHaveBeenCalled()
    release()
    expect((await reader.read()).value).toMatchObject({ type: 'finish' })
    await reader.read()
    expect(owned.disposals[0]).toHaveBeenCalledOnce()
  })

  it('cancels the exact attempt, never retries, and disposes once after cancellation', async () => {
    let release!: () => void
    const blocked = new Promise<void>(resolve => { release = resolve })
    mocks.streamAdapterRaw.mockImplementation((input: { abortSignal: AbortSignal }) => ({
      result: { fullStream: (async function* () {
        yield { type: 'text-delta', text: 'first' }
        await blocked
        if (input.abortSignal.aborted) throw new DOMException('aborted', 'AbortError')
      })() },
    }))
    const owned = execution()
    const reader = createProviderRoleExecutor(owned.value).stream({ ...request, responseSchema: undefined }).getReader()
    await reader.read()
    const cancel = reader.cancel(); release(); await cancel
    expect(owned.createRuntimeBinding).toHaveBeenCalledOnce()
    expect(owned.disposals[0]).toHaveBeenCalledOnce()
  })

  it('does not dispatch after cancellation while exact-version reauthorization is pending', async () => {
    let release!: (value: OwnedConnectionRuntimeBinding) => void
    const pending = new Promise<OwnedConnectionRuntimeBinding>(resolve => { release = resolve })
    const dispose = vi.fn()
    const owned = execution()
    owned.createRuntimeBinding.mockReturnValueOnce(pending as never)
    const reader = createProviderRoleExecutor(owned.value).stream(request).getReader()
    const read = reader.read()
    await vi.waitFor(() => expect(owned.createRuntimeBinding).toHaveBeenCalledOnce())
    const cancellation = reader.cancel()
    release({ providerId: 'openai', connectionId, modelId: 'dynamic-model', model, dispose })
    await cancellation
    await read
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(mocks.streamAdapterRaw).not.toHaveBeenCalled()
    expect(dispose).toHaveBeenCalledOnce()
  })

  it('fails closed on an injected provider or model mismatch before adapter dispatch', async () => {
    const owned = execution()
    owned.createRuntimeBinding.mockResolvedValueOnce({
      providerId: 'anthropic', modelId: 'other-model', model, dispose: vi.fn(),
    } as never)
    const executor = createProviderRoleExecutor(owned.value)
    await expect(executor.generate(request)).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.streamAdapterRaw).not.toHaveBeenCalled()
  })

  it('fails closed when the owned binding came from a different connection with the same provider and model', async () => {
    const owned = execution()
    owned.createRuntimeBinding.mockResolvedValueOnce({
      providerId: 'openai', connectionId: '00000000-0000-4000-8000-000000000009',
      modelId: 'dynamic-model', model, dispose: vi.fn(),
    } as never)
    await expect(createProviderRoleExecutor(owned.value).generate(request)).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.streamAdapterRaw).not.toHaveBeenCalled()
  })

  it('keeps at most one unread event buffered and disposes on stalled-reader cancellation', async () => {
    let upstreamReads = 0
    mocks.streamAdapterRaw.mockReturnValue({ result: { fullStream: {
      [Symbol.asyncIterator]() { return this },
      async next() { upstreamReads++; return { done: false, value: { type: 'text-delta', text: String(upstreamReads) } } },
      async return() { return { done: true, value: undefined } },
    } } })
    const owned = execution()
    const output = createProviderRoleExecutor(owned.value).stream({ ...request, responseSchema: undefined })
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(upstreamReads).toBeLessThanOrEqual(1)
    await output.cancel()
    expect(owned.disposals[0]).toHaveBeenCalledOnce()
  })

  it('promptly disposes a stalled buffered stream when its external signal aborts', async () => {
    let upstreamReads = 0
    const upstreamReturn = vi.fn(async () => ({ done: true as const, value: undefined }))
    mocks.streamAdapterRaw.mockReturnValue({ result: { fullStream: {
      [Symbol.asyncIterator]() { return this },
      async next() {
        upstreamReads++
        return { done: false as const, value: { type: 'text-delta', text: String(upstreamReads) } }
      },
      return: upstreamReturn,
    } } })
    const abort = new AbortController()
    const owned = execution()
    const reader = createProviderRoleExecutor(owned.value)
      .stream({ ...request, responseSchema: undefined, abortSignal: abort.signal }).getReader()

    expect(await reader.read()).toEqual({ done: false, value: { type: 'text_delta', text: '1' } })
    await vi.waitFor(() => expect(upstreamReads).toBe(2))
    abort.abort()
    await vi.waitFor(() => expect(owned.disposals[0]).toHaveBeenCalledOnce())
    expect(upstreamReturn).toHaveBeenCalledOnce()
    expect(owned.createRuntimeBinding).toHaveBeenCalledOnce()
    expect(mocks.streamAdapterRaw).toHaveBeenCalledOnce()
    await expect(reader.read()).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
  })

  it('does not serialize or inspect the model, binding, credential, or credential version', () => {
    const owned = execution()
    const executor = createProviderRoleExecutor(owned.value)
    expect(JSON.stringify(executor)).toBe(JSON.stringify({ descriptor: executor.descriptor }))
    expect(inspect(executor)).not.toMatch(/credential|api.?key|headers|body|runtimeBinding|dynamic-model.*dynamic-model/i)
  })

  it('keeps the per-attempt model seam non-enumerable and non-serializable', async () => {
    mocks.streamAdapterRaw.mockReturnValue(raw([
      { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 0, outputTokens: 0 } },
    ]))
    const owned = execution()
    await createProviderRoleExecutor(owned.value).generate({ ...request, responseSchema: undefined })
    const sent = mocks.streamAdapterRaw.mock.calls[0][0]
    expect(Object.keys(sent.runtimeBinding)).not.toContain('model')
    expect(() => JSON.stringify(sent.runtimeBinding)).toThrow()
    expect(inspect(sent.runtimeBinding)).toBe('[RuntimeAdapterBinding REDACTED]')
    expect(JSON.stringify(sent.runtimeDescriptor)).not.toMatch(/credential|version|header|body|secret|api.?key/i)
  })
})
