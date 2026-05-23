/**
 * B-S1: google/e2e-loop-roundtrip.test.ts
 *
 * E2E integration test proving that the Gemini agentic tool loop works end-to-end:
 *   1. GoogleAdapter.chat() receives tools in its request and forwards them to
 *      streamText() via the Vercel AI SDK ToolSet format (Break B2-G fix).
 *   2. A round-trip loop: tool_use response → tool result injected → final text.
 *   3. Iteration cap (MAX_ITERATIONS=8) is respected.
 *   4. B.11 floor context is preserved across iterations.
 *
 * Mock strategy: vi.mock('ai') intercepts streamText and lets us spy on what
 * streamParams are passed. This verifies the tools forwarding without hitting
 * the live Gemini API.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock 'ai' before importing the adapter or agentic_loop.
vi.mock('ai', () => ({
  streamText: vi.fn(),
  jsonSchema: vi.fn((schema: unknown) => schema),
}));

import { streamText } from 'ai';
import { GoogleAdapter } from '../../../src/lib/providers/google/adapter';
import {
  runAgenticLoop,
  GOOGLE_LOOP_CONFIG,
  AgenticLoopCapExceeded,
  MAX_ITERATIONS,
} from '../../../src/lib/synthesis/agentic_loop';
import {
  ITER1_TOOL_CALL_PARTS,
  ITER2_FINAL_TEXT_PARTS,
  ALWAYS_TOOL_CALL_PARTS,
  makeGeminiStream,
} from './fixtures/tool_use_stream';
import type { ChatTool } from '../../../src/lib/providers/types';

// ---------------------------------------------------------------------------
// Shared fixtures
// ---------------------------------------------------------------------------

const TEST_TOOLS: ChatTool[] = [
  {
    name: 'query_chart_facts',
    description: 'Query astrological chart facts from the L1 layer',
    inputSchema: {
      type: 'object',
      properties: {
        category: { type: 'string', description: 'Fact category (lagna, graha, etc.)' },
        limit: { type: 'number', description: 'Max results' },
      },
      required: ['category'],
    },
  },
];

/** B.11 floor context: MSR + UCN + CGM markers must survive across loop iterations. */
const B11_FLOOR_CONTEXT = `
=== MSR — Master Signal Register ===
Signal 001: Lagna lord Mars in 10H ...

=== UCN — Unified Chart Narrative ===
The chart shows a strong Raja Yoga formation ...

=== CGM — Causal Graph Model ===
Node: Lagna → Node: Mars in 10H → Node: Career excellence ...
`.trim();

/** Minimal tool executor: returns a fixed result for any tool call. */
const toolExecutor = vi.fn(async (_tc: { id: string; name: string; input: Record<string, unknown> }) =>
  JSON.stringify({ facts: ['Lagna lord Mars is in Aries in 10H', 'Vargottama condition'] }),
);

// ---------------------------------------------------------------------------
// Test 1: Round-trip — tools forwarded + tool result loop
// ---------------------------------------------------------------------------

describe('B-S1 TC1: Round-trip — tools forwarded and loop completes', () => {
  let adapter: GoogleAdapter;
  let callCount = 0;

  beforeEach(() => {
    adapter = new GoogleAdapter();
    callCount = 0;
    toolExecutor.mockClear();

    vi.mocked(streamText).mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        // Iteration 1: model calls a tool
        return { fullStream: makeGeminiStream(ITER1_TOOL_CALL_PARTS) } as unknown as ReturnType<typeof streamText>;
      }
      // Iteration 2: model emits final text
      return { fullStream: makeGeminiStream(ITER2_FINAL_TEXT_PARTS) } as unknown as ReturnType<typeof streamText>;
    });
  });

  it('AC.B2G.1: streamText is called with a tools param when request.tools is set', async () => {
    const events: unknown[] = [];
    for await (const event of runAgenticLoop(
      adapter,
      {
        messages: [{ role: 'user', content: `${B11_FLOOR_CONTEXT}\n\nUser: Tell me about the lagna.` }],
        model: 'gemini-2.5-pro',
        tools: TEST_TOOLS,
      },
      toolExecutor,
      GOOGLE_LOOP_CONFIG,
    )) {
      events.push(event);
    }

    // streamText must be called at least twice (2 iterations)
    expect(streamText).toHaveBeenCalledTimes(2);

    // First call must include a 'tools' key in its params (Break B2-G fix)
    const firstCallParams = vi.mocked(streamText).mock.calls[0][0] as Record<string, unknown>;
    expect(firstCallParams).toHaveProperty('tools');
    const toolsArg = firstCallParams.tools as Record<string, unknown>;
    expect(Object.keys(toolsArg)).toContain('query_chart_facts');
  });

  it('AC.B2G.2: tool events emitted in iteration 1 (start + delta + complete)', async () => {
    const events: Array<{ type: string }> = [];
    for await (const event of runAgenticLoop(
      adapter,
      {
        messages: [{ role: 'user', content: B11_FLOOR_CONTEXT + '\n\nUser: Read the chart.' }],
        model: 'gemini-2.5-pro',
        tools: TEST_TOOLS,
      },
      toolExecutor,
      GOOGLE_LOOP_CONFIG,
    )) {
      events.push(event);
    }

    const types = events.map((e) => e.type);
    expect(types).toContain('tool_use_start');
    expect(types).toContain('tool_use_input_delta');
    expect(types).toContain('tool_use_complete');
  });

  it('AC.B2G.3: final text_delta emitted in iteration 2 after tool result', async () => {
    const events: Array<{ type: string; text?: string }> = [];
    for await (const event of runAgenticLoop(
      adapter,
      {
        messages: [{ role: 'user', content: B11_FLOOR_CONTEXT + '\n\nUser: Read the chart.' }],
        model: 'gemini-2.5-pro',
        tools: TEST_TOOLS,
      },
      toolExecutor,
      GOOGLE_LOOP_CONFIG,
    )) {
      events.push(event as { type: string; text?: string });
    }

    const textDelta = events.find((e) => e.type === 'text_delta');
    expect(textDelta).toBeDefined();
    expect(textDelta?.text).toContain('Scorpio');
  });

  it('AC.B2G.4: toolExecutor is called exactly once (one tool call in iteration 1)', async () => {
    for await (const _ of runAgenticLoop(
      adapter,
      {
        messages: [{ role: 'user', content: B11_FLOOR_CONTEXT }],
        model: 'gemini-2.5-pro',
        tools: TEST_TOOLS,
      },
      toolExecutor,
      GOOGLE_LOOP_CONFIG,
    )) {
      // drain
    }

    expect(toolExecutor).toHaveBeenCalledTimes(1);
    const callArg = toolExecutor.mock.calls[0][0] as { name: string; input: Record<string, unknown> };
    expect(callArg.name).toBe('query_chart_facts');
    expect(callArg.input).toMatchObject({ category: 'lagna' });
  });

  it('AC.B2G.5: message_stop with stopReason function_calls in iteration 1, end_turn/stop in iteration 2', async () => {
    const stopEvents: Array<{ type: string; stopReason: string }> = [];
    for await (const event of runAgenticLoop(
      adapter,
      {
        messages: [{ role: 'user', content: B11_FLOOR_CONTEXT }],
        model: 'gemini-2.5-pro',
        tools: TEST_TOOLS,
      },
      toolExecutor,
      GOOGLE_LOOP_CONFIG,
    )) {
      if ((event as { type: string }).type === 'message_stop') {
        stopEvents.push(event as { type: string; stopReason: string });
      }
    }

    expect(stopEvents).toHaveLength(2);
    expect(stopEvents[0].stopReason).toBe('function_calls');
    expect(stopEvents[1].stopReason).toBe('stop');
  });
});

// ---------------------------------------------------------------------------
// Test 2: Iteration cap — AgenticLoopCapExceeded after MAX_ITERATIONS
// ---------------------------------------------------------------------------

describe('B-S1 TC2: Iteration cap — AgenticLoopCapExceeded at MAX_ITERATIONS', () => {
  let adapter: GoogleAdapter;

  beforeEach(() => {
    adapter = new GoogleAdapter();
    vi.mocked(streamText).mockClear();

    // Every streamText call returns a tool-call part — loop never terminates naturally.
    vi.mocked(streamText).mockImplementation(() => ({
      fullStream: makeGeminiStream(ALWAYS_TOOL_CALL_PARTS),
    }) as unknown as ReturnType<typeof streamText>);
  });

  it('AC.B2G.6: throws AgenticLoopCapExceeded after MAX_ITERATIONS iterations', async () => {
    const executor = vi.fn(async () => '{"result": "tool output"}');

    await expect(async () => {
      for await (const _ of runAgenticLoop(
        adapter,
        {
          messages: [{ role: 'user', content: 'Loop forever' }],
          model: 'gemini-2.5-pro',
          tools: TEST_TOOLS,
        },
        executor,
        GOOGLE_LOOP_CONFIG,
      )) {
        // drain — loop should throw before finishing
      }
    }).rejects.toThrow(AgenticLoopCapExceeded);
  });

  it('AC.B2G.7: error message references MAX_ITERATIONS', async () => {
    const executor = vi.fn(async () => '{"result": "x"}');
    try {
      for await (const _ of runAgenticLoop(
        adapter,
        { messages: [{ role: 'user', content: 'Loop' }], model: 'gemini-2.5-pro', tools: TEST_TOOLS },
        executor,
        GOOGLE_LOOP_CONFIG,
      )) {
        // drain
      }
    } catch (err) {
      expect(err).toBeInstanceOf(AgenticLoopCapExceeded);
      expect((err as AgenticLoopCapExceeded).message).toContain('MAX_ITERATIONS');
      expect((err as AgenticLoopCapExceeded).iterations).toBe(MAX_ITERATIONS);
    }
  });

  it('AC.B2G.8: streamText called exactly MAX_ITERATIONS times before cap triggers', async () => {
    const executor = vi.fn(async () => '{"result": "x"}');
    try {
      for await (const _ of runAgenticLoop(
        adapter,
        { messages: [{ role: 'user', content: 'Loop' }], model: 'gemini-2.5-pro', tools: TEST_TOOLS },
        executor,
        GOOGLE_LOOP_CONFIG,
      )) {
        // drain
      }
    } catch {
      // Expected — AgenticLoopCapExceeded
    }
    // checkIterationCap fires BEFORE the streamText call in iteration MAX_ITERATIONS+1,
    // so streamText is called exactly MAX_ITERATIONS times.
    expect(streamText).toHaveBeenCalledTimes(MAX_ITERATIONS);
  });
});

// ---------------------------------------------------------------------------
// Test 3: B.11 floor context preserved across iterations
// ---------------------------------------------------------------------------

describe('B-S1 TC3: B.11 floor — context preserved in subsequent requests', () => {
  let adapter: GoogleAdapter;
  let callCount = 0;

  beforeEach(() => {
    adapter = new GoogleAdapter();
    callCount = 0;
    vi.mocked(streamText).mockClear();

    vi.mocked(streamText).mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return { fullStream: makeGeminiStream(ITER1_TOOL_CALL_PARTS) } as unknown as ReturnType<typeof streamText>;
      }
      return { fullStream: makeGeminiStream(ITER2_FINAL_TEXT_PARTS) } as unknown as ReturnType<typeof streamText>;
    });
  });

  it('AC.B2G.9: second streamText call still contains the original user message with B.11 markers', async () => {
    const b11System = `${B11_FLOOR_CONTEXT}\n\nUser: Analyse the chart.`;
    const executor = vi.fn(async () => '{"facts": ["Mars in 10H"]}');

    for await (const _ of runAgenticLoop(
      adapter,
      {
        messages: [{ role: 'user', content: b11System }],
        model: 'gemini-2.5-pro',
        tools: TEST_TOOLS,
      },
      executor,
      GOOGLE_LOOP_CONFIG,
    )) {
      // drain
    }

    expect(streamText).toHaveBeenCalledTimes(2);

    // Both calls should have messages containing the original B.11 context.
    const secondCallParams = vi.mocked(streamText).mock.calls[1][0] as {
      messages: Array<{ role: string; content: string }>;
    };
    const allContent = secondCallParams.messages.map((m) => m.content).join('\n');
    expect(allContent).toContain('MSR');
    expect(allContent).toContain('UCN');
    expect(allContent).toContain('CGM');
  });

  it('AC.B2G.10: second call messages include tool-result turn appended by the loop', async () => {
    const executor = vi.fn(async () => '{"result": "Mars in 10H confirmed"}');

    for await (const _ of runAgenticLoop(
      adapter,
      {
        messages: [{ role: 'user', content: B11_FLOOR_CONTEXT }],
        model: 'gemini-2.5-pro',
        tools: TEST_TOOLS,
      },
      executor,
      GOOGLE_LOOP_CONFIG,
    )) {
      // drain
    }

    const secondCallParams = vi.mocked(streamText).mock.calls[1][0] as {
      messages: Array<{ role: string; content: unknown }>;
    };
    // The loop appends an assistant turn (tool_use) + user turn (tool_result).
    // So the second call should have 3 messages: original user + assistant + tool-result user.
    expect(secondCallParams.messages.length).toBeGreaterThanOrEqual(3);

    // Last message before the final iteration should be a user-role tool_result turn.
    const lastMsg = secondCallParams.messages[secondCallParams.messages.length - 1];
    expect(lastMsg.role).toBe('user');
  });
});
