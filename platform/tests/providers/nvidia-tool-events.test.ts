/**
 * F-S2: nvidia-tool-events.test.ts
 *
 * Verifies NVIDIA adapter chat() emits tool_use_start, tool_use_input_delta,
 * and tool_use_complete ChatEvents when the model returns finish_reason=tool_calls.
 *
 * NVIDIA NIM uses OpenAI-compat API; stream format is identical to OpenAI.
 *
 * Strategy: vi.hoisted() to declare a shared `mockCreate` stub that vi.mock can
 * reference at hoist time. Each test sets the resolved value before calling
 * adapter.chat().
 */

import { describe, it, expect, vi } from 'vitest'

// Declare the mock stub BEFORE vi.mock (vi.hoisted ensures it's available at hoist time).
const { mockCreate } = vi.hoisted(() => ({ mockCreate: vi.fn() }))

vi.mock('openai', () => {
  // Must be a real constructor (not arrow fn) so `new OpenAI(...)` works.
  function MockOpenAI() {
    return { chat: { completions: { create: mockCreate } } }
  }
  return { default: MockOpenAI }
})

import { NVIDIAAdapter } from '../../src/lib/providers/nvidia/adapter'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/** A 4-chunk stream simulating a single tool call (query_signals / MSR.001). */
async function* makeToolCallStream() {
  // Chunk 1: id + function.name arrive on the first chunk.
  yield {
    choices: [
      {
        delta: {
          tool_calls: [
            { index: 0, id: 'call_nim_abc', function: { name: 'query_signals', arguments: '' } },
          ],
        },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 2: partial function.arguments
  yield {
    choices: [
      {
        delta: { tool_calls: [{ index: 0, function: { arguments: '{"signal_id":' } }] },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 3: remaining function.arguments
  yield {
    choices: [
      {
        delta: { tool_calls: [{ index: 0, function: { arguments: '"MSR.001"}' } }] },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 4: finish signal
  yield {
    choices: [{ delta: {}, finish_reason: 'tool_calls' }],
    usage: { prompt_tokens: 10, completion_tokens: 5 },
  }
}

/** Collect all events from adapter.chat() with a fresh tool-call stream. */
async function collectToolCallEvents() {
  mockCreate.mockResolvedValue(makeToolCallStream())
  const adapter = new NVIDIAAdapter()
  const events: Array<Record<string, unknown>> = []
  for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'test' }], model: 'meta/llama-3.1-70b-instruct' })) {
    events.push(e as Record<string, unknown>)
  }
  return events
}

// ---------------------------------------------------------------------------
// Tests — tool call path
// ---------------------------------------------------------------------------

describe('F-S2: NVIDIAAdapter.chat() — tool_use event emission', () => {
  it('emits tool_use_start with correct id and name', async () => {
    const events = await collectToolCallEvents()
    const startEvent = events.find((e) => e.type === 'tool_use_start')
    expect(startEvent).toBeDefined()
    expect(startEvent).toMatchObject({ type: 'tool_use_start', id: 'call_nim_abc', name: 'query_signals' })
  })

  it('emits tool_use_input_delta with fully assembled arguments JSON', async () => {
    const events = await collectToolCallEvents()
    const deltaEvent = events.find((e) => e.type === 'tool_use_input_delta')
    expect(deltaEvent).toBeDefined()
    expect(deltaEvent).toMatchObject({
      type: 'tool_use_input_delta',
      id: 'call_nim_abc',
      partialJson: '{"signal_id":"MSR.001"}',
    })
  })

  it('emits tool_use_complete with parsed input object', async () => {
    const events = await collectToolCallEvents()
    const completeEvent = events.find((e) => e.type === 'tool_use_complete')
    expect(completeEvent).toBeDefined()
    expect(completeEvent).toMatchObject({
      type: 'tool_use_complete',
      id: 'call_nim_abc',
      name: 'query_signals',
      input: { signal_id: 'MSR.001' },
    })
  })

  it('emits message_stop with stopReason=tool_calls', async () => {
    const events = await collectToolCallEvents()
    const stopEvent = events.find((e) => e.type === 'message_stop')
    expect(stopEvent).toBeDefined()
    expect(stopEvent).toMatchObject({ type: 'message_stop', stopReason: 'tool_calls' })
  })

  it('emits events in order: tool_use_start → input_delta → complete → message_stop', async () => {
    const events = await collectToolCallEvents()
    const toolAndStop = events.filter((e) =>
      e.type === 'tool_use_start' ||
      e.type === 'tool_use_input_delta' ||
      e.type === 'tool_use_complete' ||
      e.type === 'message_stop',
    )
    expect(toolAndStop.map((e) => e.type)).toEqual([
      'tool_use_start',
      'tool_use_input_delta',
      'tool_use_complete',
      'message_stop',
    ])
  })

  it('emits exactly one message_stop for finish_reason=tool_calls (no double-emit)', async () => {
    const events = await collectToolCallEvents()
    const stopEvents = events.filter((e) => e.type === 'message_stop')
    expect(stopEvents).toHaveLength(1)
  })
})

// ---------------------------------------------------------------------------
// Tests — regular stop (no tools)
// ---------------------------------------------------------------------------

describe('F-S2: NVIDIAAdapter.chat() — regular stop (no tools) still works', () => {
  it('emits text_delta + message_stop(stop) for finish_reason=stop, no tool events', async () => {
    async function* normalStream() {
      yield { choices: [{ delta: { content: 'Hello' }, finish_reason: null }], usage: null }
      yield {
        choices: [{ delta: {}, finish_reason: 'stop' }],
        usage: { prompt_tokens: 5, completion_tokens: 2 },
      }
    }

    mockCreate.mockResolvedValue(normalStream())
    const adapter = new NVIDIAAdapter()
    const events: Array<Record<string, unknown>> = []
    for await (const e of adapter.chat({ messages: [{ role: 'user', content: 'hi' }], model: 'meta/llama-3.1-70b-instruct' })) {
      events.push(e as Record<string, unknown>)
    }

    expect(events.find((e) => e.type === 'text_delta')).toMatchObject({ type: 'text_delta', text: 'Hello' })
    expect(events.find((e) => e.type === 'message_stop')).toMatchObject({ type: 'message_stop', stopReason: 'stop' })
    expect(events.find((e) => e.type === 'tool_use_start')).toBeUndefined()
  })
})
