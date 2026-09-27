import { beforeEach, describe, expect, it, vi } from 'vitest'

const { insertReceipt } = vi.hoisted(() => ({ insertReceipt: vi.fn() }))

vi.mock('../../repository', () => ({ insertRoleInvocationReceipt: insertReceipt }))

import { trackRoleExecutor } from '../tracked-executor'
import type { RoleExecutionEvent, RoleExecutor } from '../provider-executor'

function executor(options?: { fail?: boolean }): RoleExecutor {
  return {
    descriptor: { role: 'worker', providerId: 'openai', connectionId: 'connection-1', modelId: 'model-1' },
    async generate() {
      if (options?.fail) throw new Error('raw provider secret')
      return {
        text: 'private output', toolCalls: [], finishReason: 'stop', retryCount: 0,
        usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 },
      }
    },
    stream() {
      return new ReadableStream<RoleExecutionEvent>({
        start(controller) {
          controller.enqueue({ type: 'text_delta', text: 'private output' })
          controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
            usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 } })
          controller.close()
        },
      })
    },
  }
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

  it('records stream success only after complete consumption', async () => {
    const wrapped = trackRoleExecutor(executor(), { userId: 'user-1', snapshotId: crypto.randomUUID() })
    const reader = wrapped.stream({ systemPrompt: 'secret', messages: [] }).getReader()

    expect((await reader.read()).done).toBe(false)
    expect(insertReceipt).toHaveBeenCalledTimes(1)
    expect((await reader.read()).done).toBe(false)
    expect(insertReceipt).toHaveBeenCalledTimes(1)
    expect((await reader.read()).done).toBe(true)
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
})
