/**
 * tool_use_stream.ts — Gemini stream part fixtures for E2E tool-loop tests.
 *
 * Mirrors the Vercel AI SDK fullStream shape as produced by @ai-sdk/google.
 * Gemini emits complete tool calls (no streaming deltas), so tool-call parts
 * appear as a single 'tool-call' stream part followed by a 'finish' part with
 * finishReason='tool-calls' (Vercel AI SDK enum).
 *
 * The adapter maps finishReason='tool-calls' → stopReason='function_calls'
 * so that isToolUseSignal() with 'finish_reason_function_calls' recognises it.
 */

/** A Gemini 'tool-call' stream part (Vercel AI SDK shape). */
export interface GeminiToolCallPart {
  type: 'tool-call';
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
}

/** A Gemini 'text-delta' stream part. */
export interface GeminiTextDeltaPart {
  type: 'text-delta';
  text: string;
}

/** A Gemini 'finish' stream part with usage. */
export interface GeminiFinishPart {
  type: 'finish';
  finishReason: 'tool-calls' | 'stop' | 'length' | 'content-filter' | 'other';
  totalUsage: {
    inputTokens: number;
    outputTokens: number;
  };
}

export type GeminiStreamPart = GeminiToolCallPart | GeminiTextDeltaPart | GeminiFinishPart;

/**
 * Fixture: Iteration 1 — model calls query_chart_facts.
 * finishReason='tool-calls' → adapter maps to stopReason='function_calls'.
 * The loop should continue into iteration 2.
 */
export const ITER1_TOOL_CALL_PARTS: GeminiStreamPart[] = [
  {
    type: 'tool-call',
    toolCallId: 'call-iter1-001',
    toolName: 'query_chart_facts',
    args: { category: 'lagna', limit: 5 },
  },
  {
    type: 'finish',
    finishReason: 'tool-calls',
    totalUsage: { inputTokens: 120, outputTokens: 40 },
  },
];

/**
 * Fixture: Iteration 2 — model emits final text after tool results.
 * finishReason='stop' → loop terminates naturally.
 */
export const ITER2_FINAL_TEXT_PARTS: GeminiStreamPart[] = [
  {
    type: 'text-delta',
    text: 'Based on the chart facts, the Lagna is Scorpio.',
  },
  {
    type: 'finish',
    finishReason: 'stop',
    totalUsage: { inputTokens: 200, outputTokens: 30 },
  },
];

/**
 * Fixture: Iteration that causes cap to be exceeded.
 * Used to verify that AgenticLoopCapExceeded is raised after MAX_ITERATIONS.
 * Every iteration returns tool-calls so the loop never terminates naturally.
 */
export const ALWAYS_TOOL_CALL_PARTS: GeminiStreamPart[] = [
  {
    type: 'tool-call',
    toolCallId: 'call-cap-001',
    toolName: 'query_signals',
    args: { signal_id: 'MSR.001' },
  },
  {
    type: 'finish',
    finishReason: 'tool-calls',
    totalUsage: { inputTokens: 50, outputTokens: 20 },
  },
];

/**
 * Helper: create an async iterable from an array of parts.
 * Mirrors the fullStream interface returned by streamText().
 */
export async function* makeGeminiStream(parts: GeminiStreamPart[]) {
  for (const part of parts) {
    yield part;
  }
}
