/**
 * tool_use_stream.ts — DeepSeek-format tool call stream fixtures for E2E tests.
 *
 * DeepSeek is OpenAI-compatible, so the stream format is identical to OpenAI.
 * The SDK streams tool calls as:
 *   1. delta with id + function.name (first chunk for each tool call index)
 *   2. delta with function.arguments fragments (may span multiple chunks)
 *   3. finish chunk with finish_reason='tool_calls'
 *
 * After tool results are injected, a follow-up stream yields a plain text reply
 * with finish_reason='stop'.
 *
 * DeepSeek-specific: usage may include prompt_cache_hit_tokens and
 * prompt_cache_miss_tokens (implicit cache telemetry).
 */

/** Single-tool-call stream: query_signals('MSR.001') */
export async function* toolCallStream() {
  // Chunk 1: id + function name
  yield {
    choices: [
      {
        delta: {
          tool_calls: [
            { index: 0, id: 'call_ds1', function: { name: 'query_signals', arguments: '' } },
          ],
        },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 2: partial arguments
  yield {
    choices: [
      {
        delta: { tool_calls: [{ index: 0, function: { arguments: '{"signal_id":' } }] },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 3: remaining arguments
  yield {
    choices: [
      {
        delta: { tool_calls: [{ index: 0, function: { arguments: '"MSR.042"}' } }] },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 4: finish signal
  yield {
    choices: [{ delta: {}, finish_reason: 'tool_calls' }],
    usage: {
      prompt_tokens: 120,
      completion_tokens: 25,
      prompt_cache_hit_tokens: 60,
      prompt_cache_miss_tokens: 60,
    },
  }
}

/** Final text stream after tool results injected (finish_reason='stop'). */
export async function* finalTextStream() {
  yield {
    choices: [{ delta: { content: 'Based on MSR.042 signal data: ' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: { content: 'Rahu in the 12th house indicates isolation themes.' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: {}, finish_reason: 'stop' }],
    usage: { prompt_tokens: 180, completion_tokens: 35, prompt_cache_hit_tokens: 90, prompt_cache_miss_tokens: 90 },
  }
}

/** Normal stop stream — no tool calls. Used to verify B.11 floor context is preserved. */
export async function* normalStopStream() {
  yield {
    choices: [{ delta: { content: 'Direct answer from B.11 floor context.' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: {}, finish_reason: 'stop' }],
    usage: { prompt_tokens: 50, completion_tokens: 10, prompt_cache_hit_tokens: 0, prompt_cache_miss_tokens: 50 },
  }
}
