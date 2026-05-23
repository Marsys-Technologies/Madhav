/**
 * R11F-A-S1: PROBE_anthropic_tools_forwarding.test.ts
 *
 * Verifies that AnthropicAdapter.chat() forwards tool definitions and toolChoice
 * to streamText(). Promotes the previously-skipped describe block and adds three spy
 * assertions covering:
 *   A — tools array reaches streamText when request.tools is populated
 *   B — toolChoice is forwarded
 *   C — no tools key when request.tools is empty/absent
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock 'ai' before importing the adapter
vi.mock('ai', () => ({
  streamText: vi.fn(),
  jsonSchema: vi.fn((schema: unknown) => schema),
}));

// Mock @ai-sdk/anthropic so adapter.ts imports without real credentials
vi.mock('@ai-sdk/anthropic', () => ({
  anthropic: vi.fn((modelId: string) => ({ modelId })),
}));

import { streamText } from 'ai';
import { AnthropicAdapter } from '../../../src/lib/providers/anthropic/adapter';
import type { ChatRequest } from '../../../src/lib/providers/types';

// Helper: build an async iterable from parts
async function* makeStream(parts: unknown[]) {
  for (const p of parts) {
    yield p;
  }
}

// Minimal finish-only stream so adapter.chat() completes normally
function makeFinishStream() {
  return makeStream([
    {
      type: 'finish',
      finishReason: 'stop',
      totalUsage: { inputTokens: 1, outputTokens: 1 },
    },
  ]);
}

/** Drain the adapter's async iterator to completion. */
async function drainChat(request: ChatRequest): Promise<void> {
  const adapter = new AnthropicAdapter();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  for await (const _event of adapter.chat(request)) {
    // consume
  }
}

describe('R11F-A-S1: AnthropicAdapter.chat() — tools + toolChoice forwarding', () => {
  beforeEach(() => {
    vi.mocked(streamText).mockClear();
    vi.mocked(streamText).mockReturnValue({
      fullStream: makeFinishStream(),
    } as unknown as ReturnType<typeof streamText>);
  });

  it('Test A — tools array reaches streamText when request.tools is populated', async () => {
    const request: ChatRequest = {
      messages: [{ role: 'user', content: 'Use a tool' }],
      model: 'claude-sonnet-4-6',
      tools: [
        {
          name: 'query_ephemeris',
          description: 'Query planetary positions from the ephemeris',
          inputSchema: { type: 'object', properties: { date: { type: 'string' } }, required: ['date'] },
        },
      ],
    };

    await drainChat(request);

    const callArgs = vi.mocked(streamText).mock.calls[0][0];
    expect(callArgs.tools).toBeDefined();
    expect(Object.keys(callArgs.tools as Record<string, unknown>)).toContain('query_ephemeris');
  });

  it('Test B — toolChoice is forwarded', async () => {
    const request: ChatRequest = {
      messages: [{ role: 'user', content: 'Use a tool' }],
      model: 'claude-sonnet-4-6',
      tools: [
        {
          name: 'query_signals',
          description: 'Query MSR signals',
          inputSchema: { type: 'object', properties: {} },
        },
      ],
      toolsConfig: {
        mode: 'stop_reason',
        maxIterations: 8,
        tools: [],
        toolChoice: 'auto',
      },
    };

    await drainChat(request);

    const callArgs = vi.mocked(streamText).mock.calls[0][0];
    expect(callArgs.toolChoice).toBe('auto');
  });

  it('Test C — no tools key when request.tools is empty/absent', async () => {
    const request: ChatRequest = {
      messages: [{ role: 'user', content: 'Hello' }],
      model: 'claude-sonnet-4-6',
      // no tools field
    };

    await drainChat(request);

    const callArgs = vi.mocked(streamText).mock.calls[0][0];
    expect(callArgs.tools).toBeUndefined();
  });
});
