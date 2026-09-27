import { describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  getAdapter: vi.fn(), onFinish: vi.fn(), title: vi.fn(),
}))

vi.mock('ai', () => ({
  createIdGenerator: () => () => 'msg-fixed',
  createUIMessageStream: ({ execute }: { execute: unknown }) => ({ execute }),
  createUIMessageStreamResponse: ({ stream }: { stream: unknown }) => ({ stream }),
}))
vi.mock('@/lib/providers/dispatcher', () => ({ getAdapter: mocks.getAdapter }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: () => false } }))
vi.mock('@/lib/synthesis/streaming_citation_validator', () => ({
  validateCitationsForStream: () => ({ gateResult: 'PASS', layer1Count: 0,
    layer2Verified: 0, layer2Leaked: 0, gateReason: 'ok', dataPart: null }),
}))
vi.mock('../onfinish_writethrough', () => ({ runOnFinishWriteThrough: mocks.onFinish }))
vi.mock('@/lib/conversations/title', () => ({ generateConversationTitle: mocks.title }))

import { runAdapterDispatch } from '../run_adapter_dispatch'
import type { ByokTurnRuntime } from '@/lib/pariprashna/pipeline/turn_runtime'

describe('runAdapterDispatch BYOK branch', () => {
  it('keeps Consult UI wire/on-finish while using exact Synthesizer without tools or shared adapter', async () => {
    const received: unknown[] = []
    const release = vi.fn()
    const stream = vi.fn((request: unknown) => {
      received.push(request)
      return new ReadableStream({
        start(controller) {
          controller.enqueue({ type: 'text_delta', text: 'Answer' })
          controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
            usage: { inputTokens: 1, outputTokens: 1, totalTokens: 2 } })
          controller.close()
        },
      })
    })
    const executor = { descriptor: { role: 'synthesizer' as const, providerId: 'openai' as const,
      connectionId: 'connection', modelId: 'model' }, generate: vi.fn(), stream }
    const runtime = {
      kind: 'byok', selection: { kind: 'default' }, plan: {}, safeSnapshot: {},
      snapshotId: '30000000-0000-4000-8000-000000000003',
      executors: { synthesizer: executor, planner: executor, deep_planner: executor, worker: executor },
      displayModelId: 'model', releaseAdmission: release,
    } as unknown as ByokTurnRuntime
    mocks.onFinish.mockReset().mockResolvedValue(undefined)
    mocks.getAdapter.mockReset()

    const response = await runAdapterDispatch({
      requestStartedAt: 0, userUid: 'alice', finalConversationId: 'conversation', chartId: 'chart',
      audienceTier: 'client', selectedStack: 'byok', isFirstTurn: false,
      lelContextEnabled: true, style: 'acharya', modelId: 'model',
      modelMeta: { provider: 'openai', maxInputTokens: 128_000 }, plannerModelId: 'planner',
      plan: { query_class: 'predictive', synthesis_guidance: '' }, bundle: { assets: [] },
      queryPlan: { tools_authorized: [] }, validToolResults: [], toolEventLog: [],
      plannerLatencyMs: 1, composeBundleMs: 1, toolFetchMs: 1, queryId: 'query',
      trimmedConversationHistory: [], queryText: 'Question', messages: [], emit: vi.fn(),
      nextSeq: (() => { let n = 0; return () => ++n })(),
      pendingStreamWriter: { onEvent: vi.fn(), onTextDelta: vi.fn(), clear: vi.fn() },
      fetchMsrSnippets: vi.fn(async () => new Map()), byokRuntime: runtime,
    }) as unknown as { stream: { execute(args: { writer: { write(event: unknown): void } }): Promise<void> } }
    const events: Array<Record<string, unknown>> = []
    await response.stream.execute({ writer: { write: event => events.push(event as Record<string, unknown>) } })

    expect(mocks.getAdapter).not.toHaveBeenCalled()
    expect(stream).toHaveBeenCalledOnce()
    expect(received[0]).not.toHaveProperty('tools')
    expect(received[0]).toMatchObject({ maxOutputTokens: 16_384 })
    expect(events.map(event => event.type)).toContain('text-start')
    expect(events).toContainEqual({ type: 'text-delta', id: 'text-0', delta: 'Answer' })
    expect(events.map(event => event.type)).toContain('finish')
    expect(mocks.onFinish).toHaveBeenCalledOnce()
    expect(release).toHaveBeenCalledOnce()
  })

  it('releases admission exactly once when initial writer setup fails before synthesis', async () => {
    const release = vi.fn()
    const executor = { descriptor: { role: 'synthesizer' as const, providerId: 'openai' as const,
      connectionId: 'connection', modelId: 'model' }, generate: vi.fn(), stream: vi.fn() }
    const runtime = { kind: 'byok', selection: { kind: 'default' }, plan: {}, safeSnapshot: {},
      snapshotId: crypto.randomUUID(), executors: { synthesizer: executor, planner: executor,
        deep_planner: executor, worker: executor }, displayModelId: 'model', releaseAdmission: release,
    } as unknown as ByokTurnRuntime
    const response = await runAdapterDispatch({
      requestStartedAt: 0, userUid: 'alice', finalConversationId: 'conversation', chartId: 'chart',
      audienceTier: 'client', selectedStack: 'byok', isFirstTurn: false, lelContextEnabled: true,
      style: 'acharya', modelId: 'model', modelMeta: { provider: 'openai', maxInputTokens: 128_000 },
      plannerModelId: 'planner', plan: { query_class: 'predictive', synthesis_guidance: '' },
      bundle: { assets: [] }, queryPlan: { tools_authorized: [] }, validToolResults: [], toolEventLog: [],
      plannerLatencyMs: 1, composeBundleMs: 1, toolFetchMs: 1, queryId: 'query',
      trimmedConversationHistory: [], queryText: 'Question', messages: [], emit: vi.fn(),
      nextSeq: () => 1, pendingStreamWriter: { onEvent: vi.fn(), onTextDelta: vi.fn(), clear: vi.fn() },
      fetchMsrSnippets: vi.fn(async () => new Map()), byokRuntime: runtime,
    }) as unknown as { stream: { execute(args: { writer: { write(event: unknown): void } }): Promise<void> } }

    await expect(response.stream.execute({ writer: { write: () => { throw new Error('writer failed') } } }))
      .rejects.toThrow('writer failed')
    expect(executor.stream).not.toHaveBeenCalled()
    expect(release).toHaveBeenCalledOnce()
  })
})
