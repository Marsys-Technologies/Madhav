/**
 * R11F-A-S1: anthropic/anthropic-tool-events.test.ts
 *
 * Verifies that the full tool_use round-trip produces the correct ChatEvent
 * sequence: tool_use_start → tool_use_input_delta → tool_use_complete.
 *
 * This test lives alongside the PROBE file to keep Anthropic-specific tool
 * event tests in one directory.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock 'ai' before importing the adapter
vi.mock('ai', () => ({
  streamText: vi.fn(),
  jsonSchema: vi.fn((schema: unknown) => schema),
}));

// Mock @ai-sdk/anthropic
vi.mock('@ai-sdk/anthropic', () => ({
  anthropic: vi.fn((modelId: string) => ({ modelId })),
}));

import { streamText } from 'ai';
import { AnthropicAdapter } from '../../../src/lib/providers/anthropic/adapter';

async function* makeStream(parts: unknown[]) {
  for (const p of parts) {
    yield p;
  }
}

/**
 * Full tool_use round-trip stream:
 *   tool-call-streaming-start → tool-call-delta × 2 → tool-call → finish(tool-calls)
 */
function makeFullToolRoundTripParts() {
  return [
    {
      type: 'tool-call-streaming-start',
      toolCallId: 'toolu_rndtrip_01',
      toolName: 'query_ephemeris',
    },
    {
      type: 'tool-call-delta',
      toolCallId: 'toolu_rndtrip_01',
      argsTextDelta: '{"date":',
    },
    {
      type: 'tool-call-delta',
      toolCallId: 'toolu_rndtrip_01',
      argsTextDelta: '"1984-02-05"}',
    },
    {
      type: 'tool-call',
      toolCallId: 'toolu_rndtrip_01',
      toolName: 'query_ephemeris',
      args: { date: '1984-02-05' },
    },
    {
      type: 'finish',
      finishReason: 'tool-calls',
      totalUsage: { inputTokens: 20, outputTokens: 8 },
    },
  ];
}

describe('R11F-A-S1: AnthropicAdapter tool_use round-trip event sequence', () => {
  let adapter: AnthropicAdapter;

  beforeEach(() => {
    adapter = new AnthropicAdapter();
    vi.mocked(streamText).mockReturnValue({
      fullStream: makeStream(makeFullToolRoundTripParts()),
    } as unknown as ReturnType<typeof streamText>);
  });

  it('produces correct ChatEvent sequence: tool_use_start → tool_use_input_delta → tool_use_complete', async () => {
    const events: Array<Record<string, unknown>> = [];
    for await (const e of adapter.chat({
      messages: [{ role: 'user', content: 'What are the planetary positions on 1984-02-05?' }],
      model: 'claude-sonnet-4-6',
      tools: [
        {
          name: 'query_ephemeris',
          description: 'Query planetary positions from the ephemeris',
          inputSchema: { type: 'object', properties: { date: { type: 'string' } } },
        },
      ],
    })) {
      events.push(e as Record<string, unknown>);
    }

    // Extract the tool-related events in order
    const toolEvents = events.filter((e) =>
      e.type === 'tool_use_start' ||
      e.type === 'tool_use_input_delta' ||
      e.type === 'tool_use_complete',
    );

    // Correct sequence: start → delta → delta → complete
    expect(toolEvents.map((e) => e.type)).toEqual([
      'tool_use_start',
      'tool_use_input_delta',
      'tool_use_input_delta',
      'tool_use_complete',
    ]);

    // Correct start event
    expect(toolEvents[0]).toMatchObject({
      type: 'tool_use_start',
      id: 'toolu_rndtrip_01',
      name: 'query_ephemeris',
    });

    // Correct delta events
    expect(toolEvents[1]).toMatchObject({
      type: 'tool_use_input_delta',
      id: 'toolu_rndtrip_01',
      partialJson: '{"date":',
    });
    expect(toolEvents[2]).toMatchObject({
      type: 'tool_use_input_delta',
      id: 'toolu_rndtrip_01',
      partialJson: '"1984-02-05"}',
    });

    // Correct complete event
    expect(toolEvents[3]).toMatchObject({
      type: 'tool_use_complete',
      id: 'toolu_rndtrip_01',
      name: 'query_ephemeris',
      input: { date: '1984-02-05' },
    });

    // message_stop should carry stopReason=tool_use
    const stopEvent = events.find((e) => e.type === 'message_stop');
    expect(stopEvent).toMatchObject({ type: 'message_stop', stopReason: 'tool_use' });
  });
});
