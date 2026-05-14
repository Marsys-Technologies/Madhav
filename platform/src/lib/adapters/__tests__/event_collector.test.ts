import { describe, test, expect } from 'vitest'
import { collectInteraction } from '../event_collector'
import type { ModelInteractionEvent, ModelInteraction } from '../types'

function makeFinishInteraction(overrides: Partial<ModelInteraction> = {}): ModelInteraction {
  return {
    modelId: 'test-model',
    provider: 'anthropic',
    intermediate: [],
    finishReason: 'stop',
    usage: {
      inputTokens: 10,
      outputTokens: 20,
      costUsd: 0.001,
      latencyMs: 100,
    },
    providerMeta: {},
    ...overrides,
  }
}

function makeStream(events: ModelInteractionEvent[]): ReadableStream<ModelInteractionEvent> {
  return new ReadableStream({
    start(controller) {
      for (const event of events) {
        controller.enqueue(event)
      }
      controller.close()
    },
  })
}

const NOW = Date.now()

describe('collectInteraction — basic collection', () => {
  test('text_delta events accumulate into finalText', async () => {
    const stream = makeStream([
      { type: 'text_delta', ts: NOW, text: 'Hello' },
      { type: 'text_delta', ts: NOW, text: ' World' },
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction({ finalText: 'Hello World' }) },
    ])
    const result = await collectInteraction(stream)
    expect(result.finalText).toBe('Hello World')
  })

  test('text_delta overrides finish interaction finalText', async () => {
    const stream = makeStream([
      { type: 'text_delta', ts: NOW, text: 'delta-' },
      { type: 'text_delta', ts: NOW, text: 'text' },
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction({ finalText: 'stale-text' }) },
    ])
    const result = await collectInteraction(stream)
    expect(result.finalText).toBe('delta-text')
  })

  test('finish event with no prior deltas uses finish.finalText', async () => {
    const stream = makeStream([
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction({ finalText: 'from-finish' }) },
    ])
    const result = await collectInteraction(stream)
    expect(result.finalText).toBe('from-finish')
  })
})

describe('collectInteraction — reasoning_delta', () => {
  test('reasoning_delta events accumulate into reasoning.text', async () => {
    const stream = makeStream([
      { type: 'reasoning_delta', ts: NOW, text: 'Step 1: ' },
      { type: 'reasoning_delta', ts: NOW, text: 'consider the chart' },
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction() },
    ])
    const result = await collectInteraction(stream)
    expect(result.reasoning?.text).toBe('Step 1: consider the chart')
  })

  test('no reasoning_delta → reasoning from finish event is preserved', async () => {
    const stream = makeStream([
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction({ reasoning: { text: 'preset', tokens: 5 } }) },
    ])
    const result = await collectInteraction(stream)
    expect(result.reasoning?.text).toBe('preset')
    expect(result.reasoning?.tokens).toBe(5)
  })

  test('reasoning_delta sets tokens to 0 (filled by adapter in finish)', async () => {
    const stream = makeStream([
      { type: 'reasoning_delta', ts: NOW, text: 'think' },
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction() },
    ])
    const result = await collectInteraction(stream)
    expect(result.reasoning?.tokens).toBe(0)
  })
})

describe('collectInteraction — intermediate events', () => {
  test('tool_call + tool_result events go into intermediate array', async () => {
    const stream = makeStream([
      { type: 'tool_call', ts: NOW, name: 'query_msr', args: {}, callId: 'c1' },
      { type: 'tool_result', ts: NOW, callId: 'c1', result: { data: 'ok' } },
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction() },
    ])
    const result = await collectInteraction(stream)
    expect(result.intermediate).toHaveLength(2)
    expect(result.intermediate[0].type).toBe('tool_call')
    expect(result.intermediate[1].type).toBe('tool_result')
  })

  test('status events go into intermediate array', async () => {
    const stream = makeStream([
      { type: 'status', ts: NOW, status: 'queued' },
      { type: 'status', ts: NOW, status: 'composing' },
      { type: 'finish', ts: NOW, interaction: makeFinishInteraction() },
    ])
    const result = await collectInteraction(stream)
    expect(result.intermediate).toHaveLength(2)
    expect(result.intermediate[0].type).toBe('status')
  })

  test('intermediate events preserve insertion order', async () => {
    const stream = makeStream([
      { type: 'tool_call',   ts: NOW + 1, name: 'a', args: {}, callId: 'c1' },
      { type: 'status',      ts: NOW + 2, status: 'composing' },
      { type: 'tool_result', ts: NOW + 3, callId: 'c1', result: {} },
      { type: 'finish',      ts: NOW + 4, interaction: makeFinishInteraction() },
    ])
    const result = await collectInteraction(stream)
    expect(result.intermediate[0].type).toBe('tool_call')
    expect(result.intermediate[1].type).toBe('status')
    expect(result.intermediate[2].type).toBe('tool_result')
  })
})

describe('collectInteraction — error handling', () => {
  test('error event throws with the event message', async () => {
    const stream = makeStream([
      { type: 'error', ts: NOW, error: { message: 'rate-limited', code: '429' } },
    ])
    await expect(collectInteraction(stream)).rejects.toThrow('rate-limited')
  })

  test('stream without finish event throws', async () => {
    const stream = makeStream([
      { type: 'text_delta', ts: NOW, text: 'partial' },
    ])
    await expect(collectInteraction(stream)).rejects.toThrow(
      'collectInteraction: stream ended without finish event',
    )
  })

  test('empty stream (no events) throws without finish event', async () => {
    const stream = makeStream([])
    await expect(collectInteraction(stream)).rejects.toThrow(
      'collectInteraction: stream ended without finish event',
    )
  })
})

describe('collectInteraction — finish event merging', () => {
  test('finish interaction fields are preserved when not overridden', async () => {
    const interaction = makeFinishInteraction({
      modelId: 'gemini-2.5-pro',
      provider: 'google',
      finishReason: 'length',
      usage: { inputTokens: 100, outputTokens: 50, costUsd: 0.01, latencyMs: 500 },
    })
    const stream = makeStream([{ type: 'finish', ts: NOW, interaction }])
    const result = await collectInteraction(stream)
    expect(result.modelId).toBe('gemini-2.5-pro')
    expect(result.provider).toBe('google')
    expect(result.finishReason).toBe('length')
    expect(result.usage.inputTokens).toBe(100)
  })

  test('providerMeta from finish event is preserved in the result', async () => {
    const interaction = makeFinishInteraction({
      providerMeta: { requestId: 'req-abc123', raw: { x: 1 } },
    })
    const stream = makeStream([{ type: 'finish', ts: NOW, interaction }])
    const result = await collectInteraction(stream)
    expect(result.providerMeta.requestId).toBe('req-abc123')
  })

  test('intermediate is replaced (not merged) with collected events', async () => {
    const interaction = makeFinishInteraction({
      intermediate: [{ type: 'status', ts: 0, payload: 'stale' }],
    })
    const stream = makeStream([
      { type: 'status', ts: NOW, status: 'queued' },
      { type: 'finish', ts: NOW, interaction },
    ])
    const result = await collectInteraction(stream)
    // Only the freshly collected status event should be in intermediate
    expect(result.intermediate).toHaveLength(1)
    expect((result.intermediate[0].payload as { type: string }).type).toBe('status')
  })
})
