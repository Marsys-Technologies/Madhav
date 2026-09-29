import { describe, expect, it, vi } from 'vitest'

import { AiConsoleError } from '../../errors'
import { createDefaultFallbackExecutor } from '../fallback-executor'
import type { RoleExecutionEvent, RoleExecutor } from '../provider-executor'

const usage = { inputTokens: 1, outputTokens: 1, totalTokens: 2 }

function executor(modelId: string, options: { generateError?: unknown; streamError?: unknown;
  streamText?: string } = {}): RoleExecutor {
  return {
    descriptor: { role: 'planner', providerId: 'openai', connectionId: `${modelId}-connection`, modelId },
    async generate() {
      if (options.generateError) throw options.generateError
      return { text: modelId, toolCalls: [], finishReason: 'stop', usage, retryCount: 0,
        fallbackUsed: false, activeModelId: modelId }
    },
    stream() {
      let textEmitted = false
      let finished = false
      return new ReadableStream<RoleExecutionEvent>({
        pull(controller) {
          if (options.streamText && !textEmitted) {
            textEmitted = true
            controller.enqueue({ type: 'text_delta', text: options.streamText })
            return
          }
          if (options.streamError) return controller.error(options.streamError)
          if (finished) return controller.close()
          finished = true
          controller.enqueue({ type: 'finish', finishReason: 'stop', usage, retryCount: 0,
            fallbackUsed: false, activeModelId: modelId })
        },
      })
    },
  }
}

describe('selected to default role fallback', () => {
  it('keeps the selected executor when it succeeds', async () => {
    const selected = executor('selected')
    const fallback = executor('default')
    const fallbackSpy = vi.spyOn(fallback, 'generate')

    await expect(createDefaultFallbackExecutor(selected, fallback).generate({
      systemPrompt: 'system', messages: [],
    })).resolves.toMatchObject({ text: 'selected', fallbackUsed: false, activeModelId: 'selected' })
    expect(fallbackSpy).not.toHaveBeenCalled()
  })

  it('switches exactly once to Default after an eligible selected execution failure', async () => {
    const selected = executor('selected', { generateError: new AiConsoleError('AI_CLI_UNREACHABLE', 'planner') })
    const fallback = executor('default')
    const fallbackSpy = vi.spyOn(fallback, 'generate')

    await expect(createDefaultFallbackExecutor(selected, fallback).generate({
      systemPrompt: 'system', messages: [],
    })).resolves.toMatchObject({ text: 'default', fallbackUsed: true, activeModelId: 'default' })
    expect(fallbackSpy).toHaveBeenCalledOnce()
  })

  it('keeps the role on Default for later calls in the same turn after selected fails', async () => {
    const selected = executor('selected', { generateError: new AiConsoleError('AI_CLI_UNREACHABLE', 'planner') })
    const fallback = executor('default')
    const selectedSpy = vi.spyOn(selected, 'generate')
    const fallbackSpy = vi.spyOn(fallback, 'generate')
    const wrapped = createDefaultFallbackExecutor(selected, fallback)

    await wrapped.generate({ systemPrompt: 'first', messages: [] })
    await expect(wrapped.generate({ systemPrompt: 'repair', messages: [] })).resolves.toMatchObject({
      text: 'default', fallbackUsed: true, activeModelId: 'default',
    })
    expect(selectedSpy).toHaveBeenCalledOnce()
    expect(fallbackSpy).toHaveBeenCalledTimes(2)
  })

  it('does not bypass a permission failure or an aborted turn', async () => {
    const fallback = executor('default')
    const fallbackSpy = vi.spyOn(fallback, 'generate')
    await expect(createDefaultFallbackExecutor(
      executor('selected', { generateError: new AiConsoleError('AI_PERMISSION_DENIED', 'planner') }), fallback,
    ).generate({ systemPrompt: 'system', messages: [] })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })

    const controller = new AbortController()
    controller.abort()
    await expect(createDefaultFallbackExecutor(
      executor('selected', { generateError: new AiConsoleError('AI_CLI_UNREACHABLE', 'planner') }), fallback,
    ).generate({ systemPrompt: 'system', messages: [], abortSignal: controller.signal }))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    expect(fallbackSpy).not.toHaveBeenCalled()
  })

  it('falls back a synthesis stream only before selected output becomes visible', async () => {
    const fallback = executor('default')
    const wrapped = createDefaultFallbackExecutor(
      executor('selected', { streamError: new AiConsoleError('AI_PROVIDER_UNREACHABLE', 'planner') }), fallback)
    const reader = wrapped.stream({ systemPrompt: 'system', messages: [] }).getReader()
    await expect(reader.read()).resolves.toMatchObject({ done: false, value: {
      type: 'finish', fallbackUsed: true, activeModelId: 'default',
    } })
    await expect(reader.read()).resolves.toEqual({ done: true, value: undefined })

    const fallbackStream = vi.spyOn(fallback, 'stream')
    const partial = createDefaultFallbackExecutor(executor('selected', {
      streamText: 'partial', streamError: new AiConsoleError('AI_PROVIDER_UNREACHABLE', 'planner'),
    }), fallback).stream({ systemPrompt: 'system', messages: [] }).getReader()
    await expect(partial.read()).resolves.toMatchObject({ value: { type: 'text_delta', text: 'partial' } })
    await expect(partial.read()).rejects.toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    expect(fallbackStream).not.toHaveBeenCalled()
  })
})
