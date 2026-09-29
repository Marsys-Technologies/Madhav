import { beforeEach, describe, expect, it, vi } from 'vitest'

const { insertReceipt } = vi.hoisted(() => ({ insertReceipt: vi.fn() }))

vi.mock('../../repository', () => ({ insertRoleInvocationReceipt: insertReceipt }))

import { trackRoleExecutor } from '../tracked-executor'
import type { RoleExecutionEvent, RoleExecutor } from '../provider-executor'
import { setSafeExecutionStreamFacts } from '../execution-facts'

const connectionId = '10000000-0000-4000-8000-000000000003'
const conversationId = '10000000-0000-4000-8000-000000000004'
const correlationId = '10000000-0000-4000-8000-000000000005'

function executor(options?: { fail?: boolean }): RoleExecutor {
  return {
    descriptor: { role: 'worker', providerId: 'openai', connectionId, modelId: 'model-1' },
    async generate() {
      if (options?.fail) throw new Error('raw provider secret')
      return {
        text: 'private output', toolCalls: [], finishReason: 'stop', retryCount: 0,
        fallbackUsed: false, activeModelId: 'model-1',
        usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 },
      }
    },
    stream() {
      return new ReadableStream<RoleExecutionEvent>({
        start(controller) {
          controller.enqueue({ type: 'text_delta', text: 'private output' })
          controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
            fallbackUsed: false, activeModelId: 'model-1',
            usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 } })
          controller.close()
        },
      })
    },
  }
}

function observation(write: (input: unknown) => Promise<void>) {
  const target = { kind: 'provider_model' as const, providerId: 'openai' as const, connectionId, modelId: 'model-1' }
  return { snapshot: {
    source: 'pariprashna' as const, userId: 'user-1', correlationId, conversationId,
    selection: { kind: 'default' as const },
    resolvedChoice: { kind: 'provider_model' as const, connectionId, modelId: 'model-1' },
    configurationVersion: null,
    roles: { synthesizer: target, planner: target, deep_planner: target, worker: target },
  }, write }
}

describe('trackRoleExecutor', () => {
  beforeEach(() => insertReceipt.mockReset().mockResolvedValue(undefined))

  it('writes a unique start immediately before generate and a success after completion', async () => {
    const wrapped = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID() })

    await wrapped.generate({ systemPrompt: 'private prompt', messages: [] })

    expect(insertReceipt).toHaveBeenCalledTimes(2)
    const start = insertReceipt.mock.calls[0][0]
    const terminal = insertReceipt.mock.calls[1][0]
    expect(start).toMatchObject({ role: 'worker', phase: 'start', status: 'started' })
    expect(terminal).toMatchObject({ role: 'worker', invocationId: start.invocationId,
      phase: 'terminal', status: 'succeeded' })
    expect(JSON.stringify(insertReceipt.mock.calls)).not.toContain('private prompt')
    expect(JSON.stringify(insertReceipt.mock.calls)).not.toContain('private output')
  })

  it('normalizes generate failures and records exactly one failed terminal', async () => {
    const wrapped = trackRoleExecutor(executor({ fail: true }), { userId: 'user-1', snapshotId: crypto.randomUUID() })

    await expect(wrapped.generate({ systemPrompt: 'secret', messages: [] })).rejects.toMatchObject({
      code: 'AI_EXECUTION_FAILED', role: 'worker',
    })

    expect(insertReceipt).toHaveBeenCalledTimes(2)
    expect(insertReceipt.mock.calls[1][0]).toMatchObject({ phase: 'terminal', status: 'failed',
      errorCode: 'AI_EXECUTION_FAILED' })
    expect(JSON.stringify(insertReceipt.mock.calls)).not.toContain('raw provider secret')
  })

  it('records cancelled only after a stream reader cancels and never records success', async () => {
    const wrapped = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID() })
    const reader = wrapped.stream({ systemPrompt: 'secret', messages: [] }).getReader()

    await reader.read()
    await reader.cancel()

    expect(insertReceipt).toHaveBeenCalledTimes(2)
    expect(insertReceipt.mock.calls[1][0]).toMatchObject({ phase: 'terminal', status: 'cancelled',
      errorCode: 'AI_EXECUTION_FAILED' })
  })

  it('records stream success before exposing the semantic finish event', async () => {
    const wrapped = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID() })
    const reader = wrapped.stream({ systemPrompt: 'secret', messages: [] }).getReader()

    expect((await reader.read()).done).toBe(false)
    expect(insertReceipt).toHaveBeenCalledTimes(1)
    expect((await reader.read()).done).toBe(false)
    expect(insertReceipt).toHaveBeenCalledTimes(2)
    expect(insertReceipt.mock.calls[1][0]).toMatchObject({ phase: 'terminal', status: 'succeeded' })
    expect((await reader.read()).done).toBe(true)
  })

  it('terminalizes success at finish even when delegate EOF never arrives', async () => {
    const delegate = executor()
    delegate.stream = () => new ReadableStream<RoleExecutionEvent>({
      start(controller) {
        controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
          fallbackUsed: false, activeModelId: 'model-1',
          usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 } })
      },
    })
    const reader = trackRoleExecutor(delegate, {
      userId: 'user-1', snapshotId: crypto.randomUUID(),
    }).stream({ systemPrompt: 'secret', messages: [] }).getReader()

    await expect(reader.read()).resolves.toMatchObject({ done: false, value: { type: 'finish' } })
    expect(insertReceipt.mock.calls[1][0]).toMatchObject({ phase: 'terminal', status: 'succeeded' })
    await reader.cancel()
  })

  it('keeps success terminal after cancellation following finish', async () => {
    const reader = trackRoleExecutor(executor(), {
      userId: 'user-1', snapshotId: crypto.randomUUID(),
    }).stream({ systemPrompt: 'secret', messages: [] }).getReader()

    await reader.read()
    await reader.read()
    await reader.cancel()

    expect(insertReceipt).toHaveBeenCalledTimes(2)
    expect(insertReceipt.mock.calls[1][0]).toMatchObject({ phase: 'terminal', status: 'succeeded' })
  })

  it('fails before calling the delegate when the start receipt cannot commit', async () => {
    const delegate = executor()
    const spy = vi.spyOn(delegate, 'generate')
    insertReceipt.mockRejectedValueOnce(new Error('db unavailable'))
    const wrapped = trackRoleExecutor(delegate, { userId: 'user-1', snapshotId: crypto.randomUUID() })

    await expect(wrapped.generate({ systemPrompt: 'secret', messages: [] })).rejects.toThrow('db unavailable')
    expect(spy).not.toHaveBeenCalled()
  })

  it('commits a cancelled terminal and never starts the delegate when cancelled during the start receipt', async () => {
    let releaseStart!: () => void
    insertReceipt.mockImplementationOnce(() => new Promise<void>(resolve => { releaseStart = resolve }))
      .mockResolvedValue(undefined)
    const delegate = executor()
    const streamSpy = vi.spyOn(delegate, 'stream')
    const reader = trackRoleExecutor(delegate, {
      userId: 'user-1', snapshotId: crypto.randomUUID(),
    }).stream({ systemPrompt: 'secret', messages: [] }).getReader()

    const pendingRead = reader.read()
    await vi.waitFor(() => expect(insertReceipt).toHaveBeenCalledTimes(1))
    const cancellation = reader.cancel()
    releaseStart()
    await cancellation
    await pendingRead

    expect(streamSpy).not.toHaveBeenCalled()
    expect(insertReceipt).toHaveBeenCalledTimes(2)
    expect(insertReceipt.mock.calls[1][0]).toMatchObject({
      invocationId: insertReceipt.mock.calls[0][0].invocationId,
      phase: 'terminal', status: 'cancelled',
    })
  })

  it('cancels an in-flight delegate pull and records one cancelled terminal', async () => {
    let delegateCancelled = false
    const delegate = executor()
    delegate.stream = () => new ReadableStream<RoleExecutionEvent>({
      pull: () => new Promise<void>(() => undefined),
      cancel: () => { delegateCancelled = true },
    })
    const reader = trackRoleExecutor(delegate, {
      userId: 'user-1', snapshotId: crypto.randomUUID(),
    }).stream({ systemPrompt: 'secret', messages: [] }).getReader()

    void reader.read()
    await vi.waitFor(() => expect(insertReceipt).toHaveBeenCalledTimes(1))
    await reader.cancel()

    expect(delegateCancelled).toBe(true)
    expect(insertReceipt).toHaveBeenCalledTimes(2)
    expect(insertReceipt.mock.calls[1][0]).toMatchObject({ phase: 'terminal', status: 'cancelled' })
  })

  it('observes exact terminal facts only after the durable terminal receipt', async () => {
    const write = vi.fn(async input => { expect(insertReceipt.mock.calls.at(-1)?.[0]).toMatchObject({
      phase: 'terminal', status: 'succeeded',
    }); expect(input).toMatchObject({
      role: 'worker', terminal_status: 'success', input_tokens: 1, output_tokens: 2,
      retry_count: 0, fallback_used: false,
    }) })
    const wrapped = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID(),
      observation: observation(write) })

    await wrapped.generate({ systemPrompt: 'private prompt', messages: [] })

    expect(write).toHaveBeenCalledTimes(1)
    expect(JSON.stringify(write.mock.calls)).not.toContain('private prompt')
    expect(JSON.stringify(write.mock.calls)).not.toContain('private output')
  })

  it('does not delay generate after a durable terminal receipt when telemetry never settles', async () => {
    const write = vi.fn(() => new Promise<void>(() => undefined))
    const wrapped = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID(),
      observation: observation(write) })

    await expect(Promise.race([
      wrapped.generate({ systemPrompt: 'private prompt', messages: [] }),
      new Promise((_, reject) => setTimeout(() => reject(new Error('telemetry blocked result')), 100)),
    ])).resolves.toMatchObject({ finishReason: 'stop' })
    expect(write).toHaveBeenCalledOnce()
  })

  it('keeps an Observatory failure non-fatal without repeating execution or receipts', async () => {
    const delegate = executor()
    const execute = vi.spyOn(delegate, 'generate')
    const write = vi.fn().mockRejectedValue(new Error('telemetry unavailable'))
    vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    const wrapped = trackRoleExecutor(delegate, { userId: 'user-1', snapshotId: crypto.randomUUID(),
      observation: observation(write) })

    await expect(wrapped.generate({ systemPrompt: 'private prompt', messages: [] })).resolves.toMatchObject({
      finishReason: 'stop',
    })
    expect(execute).toHaveBeenCalledTimes(1)
    expect(insertReceipt).toHaveBeenCalledTimes(2)
    expect(write).toHaveBeenCalledTimes(1)
  })

  it('observes stream usage once after complete consumption', async () => {
    const write = vi.fn().mockResolvedValue(undefined)
    const reader = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID(),
      observation: observation(write) }).stream({ systemPrompt: 'private prompt', messages: [] }).getReader()

    while (!(await reader.read()).done) { /* consume */ }

    expect(write).toHaveBeenCalledTimes(1)
    expect(write.mock.calls[0][0]).toMatchObject({ terminal_status: 'success', total_tokens: 3,
      retry_count: 0 })
  })

  it('does not delay a stream finish event when telemetry never settles', async () => {
    const write = vi.fn(() => new Promise<void>(() => undefined))
    const reader = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID(),
      observation: observation(write) }).stream({ systemPrompt: 'private prompt', messages: [] }).getReader()

    await reader.read()
    await expect(Promise.race([
      reader.read(),
      new Promise((_, reject) => setTimeout(() => reject(new Error('telemetry blocked stream')), 100)),
    ])).resolves.toMatchObject({ done: false, value: { type: 'finish' } })
    expect(write).toHaveBeenCalledOnce()
  })

  it('records retry_count 0 when cancelled before delegate execution', async () => {
    let releaseStart!: () => void
    insertReceipt.mockImplementationOnce(() => new Promise<void>(resolve => { releaseStart = resolve }))
      .mockResolvedValue(undefined)
    const write = vi.fn().mockResolvedValue(undefined)
    const reader = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID(),
      observation: observation(write) }).stream({ systemPrompt: 'secret', messages: [] }).getReader()

    const pendingRead = reader.read()
    await vi.waitFor(() => expect(insertReceipt).toHaveBeenCalledOnce())
    const cancelling = reader.cancel()
    releaseStart()
    await cancelling
    await pendingRead
    await vi.waitFor(() => expect(write).toHaveBeenCalledOnce())
    expect(write.mock.calls[0][0]).toMatchObject({ terminal_status: 'cancelled', retry_count: 0 })
  })

  it('records retry_count 1 when cancelled after one delegate retry', async () => {
    const write = vi.fn().mockResolvedValue(undefined)
    const delegate = executor()
    delegate.stream = () => {
      const stream = new ReadableStream<RoleExecutionEvent>({
        pull() {
          setSafeExecutionStreamFacts(stream, { retryCount: 1 })
          return new Promise<void>(() => undefined)
        },
      })
      setSafeExecutionStreamFacts(stream, { retryCount: 0 })
      return stream
    }
    const reader = trackRoleExecutor(delegate, { userId: 'user-1', snapshotId: crypto.randomUUID(),
      observation: observation(write) }).stream({ systemPrompt: 'secret', messages: [] }).getReader()

    void reader.read()
    await vi.waitFor(() => expect(insertReceipt).toHaveBeenCalledOnce())
    await reader.cancel()
    await vi.waitFor(() => expect(write).toHaveBeenCalledOnce())
    expect(write.mock.calls[0][0]).toMatchObject({ terminal_status: 'cancelled', retry_count: 1 })
  })
})
