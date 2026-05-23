/**
 * F-S2: anthropic-tool-events.test.ts
 *
 * Verifies that AnthropicAdapter.chat() emits tool_use_start, tool_use_input_delta,
 * and tool_use_complete ChatEvents when the model returns tool-call parts.
 *
 * The Anthropic/Vercel AI SDK fullStream emits:
 *   tool-call-streaming-start → tool_use_start
 *   tool-call-delta           → tool_use_input_delta (partialJson = argsTextDelta)
 *   tool-call                 → tool_use_complete (input = parsed args)
 *   finish (finishReason='tool-calls') → message_stop with stopReason='tool_use'
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock 'ai' before importing the adapter
vi.mock('ai', () => ({
  streamText: vi.fn(),
}));

// Also mock @ai-sdk/anthropic so adapter.ts can import it without real credentials
vi.mock('@ai-sdk/anthropic', () => ({
  anthropic: vi.fn((modelId: string) => ({ modelId })),
}));

import { streamText } from 'ai';
import { AnthropicAdapter } from '../../src/lib/providers/anthropic/adapter';

// Helper: build an async iterable from an array of parts
async function* makeStream(parts: unknown[]) {
  for (const p of parts) {
    yield p;
  }
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/**
 * Simulates the fullStream for a single tool call:
 *   1. tool-call-streaming-start (id + name)
 *   2. tool-call-delta (first JSON fragment)
 *   3. tool-call-delta (second JSON fragment)
 *   4. tool-call (complete args object)
 *   5. finish with finishReason='tool-calls'
 */
function makeToolCallParts() {
  return [
    {
      type: 'tool-call-streaming-start',
      toolCallId: 'toolu_01abc',
      toolName: 'query_signals',
    },
    {
      type: 'tool-call-delta',
      toolCallId: 'toolu_01abc',
      argsTextDelta: '{"signal_id":',
    },
    {
      type: 'tool-call-delta',
      toolCallId: 'toolu_01abc',
      argsTextDelta: '"MSR.001"}',
    },
    {
      type: 'tool-call',
      toolCallId: 'toolu_01abc',
      toolName: 'query_signals',
      args: { signal_id: 'MSR.001' },
    },
    {
      type: 'finish',
      finishReason: 'tool-calls',
      totalUsage: { inputTokens: 10, outputTokens: 5 },
    },
  ];
}

/** Collect all events from adapter.chat() with a fresh tool-call stream. */
async function collectToolCallEvents() {
  vi.mocked(streamText).mockReturnValue({
    fullStream: makeStream(makeToolCallParts()),
  } as unknown as ReturnType<typeof streamText>);

  const adapter = new AnthropicAdapter();
  const events: Array<Record<string, unknown>> = [];
  for await (const e of adapter.chat({
    messages: [{ role: 'user', content: 'Use a tool' }],
    model: 'claude-sonnet-4-6',
  })) {
    events.push(e as Record<string, unknown>);
  }
  return events;
}

// ---------------------------------------------------------------------------
// Tests — tool call path
// ---------------------------------------------------------------------------

describe('F-S2: AnthropicAdapter.chat() — tool_use event emission', () => {
  let adapter: AnthropicAdapter;

  beforeEach(() => {
    adapter = new AnthropicAdapter();
  });

  it('emits tool_use_start with correct id and name', async () => {
    const events = await collectToolCallEvents();
    const startEvent = events.find((e) => e.type === 'tool_use_start');
    expect(startEvent).toBeDefined();
    expect(startEvent).toMatchObject({
      type: 'tool_use_start',
      id: 'toolu_01abc',
      name: 'query_signals',
    });
  });

  it('emits tool_use_input_delta for each argsTextDelta chunk', async () => {
    const events = await collectToolCallEvents();
    const deltaEvents = events.filter((e) => e.type === 'tool_use_input_delta');
    expect(deltaEvents).toHaveLength(2);
    expect(deltaEvents[0]).toMatchObject({
      type: 'tool_use_input_delta',
      id: 'toolu_01abc',
      partialJson: '{"signal_id":',
    });
    expect(deltaEvents[1]).toMatchObject({
      type: 'tool_use_input_delta',
      id: 'toolu_01abc',
      partialJson: '"MSR.001"}',
    });
  });

  it('emits tool_use_complete with parsed input object', async () => {
    const events = await collectToolCallEvents();
    const completeEvent = events.find((e) => e.type === 'tool_use_complete');
    expect(completeEvent).toBeDefined();
    expect(completeEvent).toMatchObject({
      type: 'tool_use_complete',
      id: 'toolu_01abc',
      name: 'query_signals',
      input: { signal_id: 'MSR.001' },
    });
  });

  it('emits message_stop with stopReason=tool_use when finishReason=tool-calls', async () => {
    const events = await collectToolCallEvents();
    const stopEvent = events.find((e) => e.type === 'message_stop');
    expect(stopEvent).toBeDefined();
    expect(stopEvent).toMatchObject({ type: 'message_stop', stopReason: 'tool_use' });
  });

  it('emits events in order: tool_use_start → input_delta(×2) → complete → usage → message_stop', async () => {
    const events = await collectToolCallEvents();
    const relevant = events.filter((e) =>
      e.type === 'tool_use_start' ||
      e.type === 'tool_use_input_delta' ||
      e.type === 'tool_use_complete' ||
      e.type === 'usage' ||
      e.type === 'message_stop',
    );
    expect(relevant.map((e) => e.type)).toEqual([
      'tool_use_start',
      'tool_use_input_delta',
      'tool_use_input_delta',
      'tool_use_complete',
      'usage',
      'message_stop',
    ]);
  });

  it('emits exactly one message_stop for finish=tool-calls (no double-emit)', async () => {
    const events = await collectToolCallEvents();
    const stopEvents = events.filter((e) => e.type === 'message_stop');
    expect(stopEvents).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// Tests — regular stop (no tools) still works
// ---------------------------------------------------------------------------

describe('F-S2: AnthropicAdapter.chat() — regular stop (no tools) still works', () => {
  it('emits text_delta + thinking_delta + message_stop(end_turn) without tool events', async () => {
    const mockParts = [
      { type: 'text-delta', text: 'Hello' },
      { type: 'reasoning-delta', text: 'I think...' },
      {
        type: 'finish',
        finishReason: 'stop',
        totalUsage: { inputTokens: 5, outputTokens: 3 },
      },
    ];

    vi.mocked(streamText).mockReturnValue({
      fullStream: makeStream(mockParts),
    } as unknown as ReturnType<typeof streamText>);

    const adapter = new AnthropicAdapter();
    const events: Array<Record<string, unknown>> = [];
    for await (const e of adapter.chat({
      messages: [{ role: 'user', content: 'hi' }],
      model: 'claude-sonnet-4-6',
    })) {
      events.push(e as Record<string, unknown>);
    }

    expect(events.find((e) => e.type === 'text_delta')).toMatchObject({ type: 'text_delta', text: 'Hello' });
    expect(events.find((e) => e.type === 'thinking_delta')).toMatchObject({ type: 'thinking_delta', thinking: 'I think...' });
    expect(events.find((e) => e.type === 'message_stop')).toMatchObject({ type: 'message_stop', stopReason: 'stop' });
    expect(events.find((e) => e.type === 'tool_use_start')).toBeUndefined();
    expect(events.find((e) => e.type === 'tool_use_input_delta')).toBeUndefined();
    expect(events.find((e) => e.type === 'tool_use_complete')).toBeUndefined();
  });
});
