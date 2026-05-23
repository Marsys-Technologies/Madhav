/**
 * F-S2: google-tool-events.test.ts
 *
 * Verifies that GoogleAdapter.chat() emits tool_use_start, tool_use_input_delta,
 * and tool_use_complete ChatEvents when the model returns tool-call parts.
 *
 * Gemini emits complete tool calls (no streaming deltas); the adapter synthesises
 * the three-event streaming protocol from a single tool-call part.
 * finish with finishReason='tool-calls' (Vercel AI SDK value) must map to
 * stopReason='function_calls' (Google canonical / isToolUseSignal compatible).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// --- Mock 'ai' before importing the adapter ---
vi.mock('ai', () => ({
  streamText: vi.fn(),
}));

import { streamText } from 'ai';
import { GoogleAdapter } from '../../src/lib/providers/google/adapter';

// Helper: build an async iterable from an array of parts
async function* makeStream(parts: unknown[]) {
  for (const p of parts) {
    yield p;
  }
}

describe('F-S2: GoogleAdapter.chat() — tool-call event emission', () => {
  let adapter: GoogleAdapter;

  beforeEach(() => {
    adapter = new GoogleAdapter();
  });

  it('emits tool_use_start, tool_use_input_delta, tool_use_complete, then message_stop=function_calls', async () => {
    const mockParts = [
      {
        type: 'tool-call',
        toolCallId: 'tc1',
        toolName: 'query_signals',
        args: { signal_id: 'MSR.001' },
      },
      {
        type: 'finish',
        finishReason: 'tool-calls',
        totalUsage: { inputTokens: 10, outputTokens: 5 },
      },
    ];

    vi.mocked(streamText).mockReturnValue({
      fullStream: makeStream(mockParts),
    } as unknown as ReturnType<typeof streamText>);

    const events = [];
    for await (const e of adapter.chat({
      messages: [{ role: 'user', content: 'Use a tool' }],
      model: 'gemini-2.5-pro',
    })) {
      events.push(e);
    }

    // Expected: tool_use_start, tool_use_input_delta, tool_use_complete, usage, message_stop
    const toolStart = events.find((e) => e.type === 'tool_use_start');
    const toolDelta = events.find((e) => e.type === 'tool_use_input_delta');
    const toolComplete = events.find((e) => e.type === 'tool_use_complete');
    const msgStop = events.find((e) => e.type === 'message_stop');

    // AC.S2.G.1: tool_use_start emitted
    expect(toolStart).toBeDefined();
    expect(toolStart).toMatchObject({ type: 'tool_use_start', id: 'tc1', name: 'query_signals' });

    // AC.S2.G.2: tool_use_input_delta emitted with full JSON args
    expect(toolDelta).toBeDefined();
    expect(toolDelta).toMatchObject({
      type: 'tool_use_input_delta',
      id: 'tc1',
      partialJson: '{"signal_id":"MSR.001"}',
    });

    // AC.S2.G.3: tool_use_complete emitted with parsed input
    expect(toolComplete).toBeDefined();
    expect(toolComplete).toMatchObject({
      type: 'tool_use_complete',
      id: 'tc1',
      name: 'query_signals',
      input: { signal_id: 'MSR.001' },
    });

    // AC.S2.G.4 (finish → message_stop): stopReason mapped to 'function_calls'
    expect(msgStop).toBeDefined();
    expect((msgStop as { type: string; stopReason: string }).stopReason).toBe('function_calls');
  });

  it('event ordering: start → input_delta → complete (before usage + message_stop)', async () => {
    const mockParts = [
      {
        type: 'tool-call',
        toolCallId: 'tc2',
        toolName: 'get_trace',
        args: { trace_id: 'T42' },
      },
      {
        type: 'finish',
        finishReason: 'tool-calls',
        totalUsage: { inputTokens: 20, outputTokens: 8 },
      },
    ];

    vi.mocked(streamText).mockReturnValue({
      fullStream: makeStream(mockParts),
    } as unknown as ReturnType<typeof streamText>);

    const events: { type: string }[] = [];
    for await (const e of adapter.chat({
      messages: [{ role: 'user', content: 'Use another tool' }],
      model: 'gemini-2.5-pro',
    })) {
      events.push(e);
    }

    const types = events.map((e) => e.type);
    const startIdx = types.indexOf('tool_use_start');
    const deltaIdx = types.indexOf('tool_use_input_delta');
    const completeIdx = types.indexOf('tool_use_complete');
    const stopIdx = types.indexOf('message_stop');

    expect(startIdx).toBeLessThan(deltaIdx);
    expect(deltaIdx).toBeLessThan(completeIdx);
    expect(completeIdx).toBeLessThan(stopIdx);
  });

  it('AC.S2.G.4: text_delta and thinking_delta still emit when no tool-call parts present', async () => {
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

    const events = [];
    for await (const e of adapter.chat({
      messages: [{ role: 'user', content: 'Hello' }],
      model: 'gemini-2.5-pro',
    })) {
      events.push(e);
    }

    const types = events.map((e) => e.type);
    expect(types).toContain('text_delta');
    expect(types).toContain('thinking_delta');
    expect(types).toContain('usage');
    expect(types).toContain('message_stop');
    // No tool events
    expect(types).not.toContain('tool_use_start');
    expect(types).not.toContain('tool_use_input_delta');
    expect(types).not.toContain('tool_use_complete');
    // Non-tool finish reason preserved
    const stop = events.find((e) => e.type === 'message_stop') as { stopReason: string } | undefined;
    expect(stop?.stopReason).toBe('stop');
  });
});
