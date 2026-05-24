/**
 * tool_use_stream.ts — OpenAI-format tool call stream fixtures for E2E tests.
 *
 * Provides async generator functions that simulate OpenAI Chat Completions
 * streaming responses with tool calls. The OpenAI SDK streams tool calls as:
 *   1. delta with id + function.name (first chunk for each tool call index)
 *   2. delta with function.arguments fragments (may span multiple chunks)
 *   3. finish chunk with finish_reason='tool_calls'
 *
 * After tool results are injected, a follow-up stream yields a plain text reply
 * with finish_reason='stop'.
 */

/** Single-tool-call stream: query_signals('MSR.001') */
export async function* toolCallStream() {
  // Chunk 1: id + function name
  yield {
    choices: [
      {
        delta: {
          tool_calls: [
            { index: 0, id: 'call_t1', function: { name: 'query_signals', arguments: '' } },
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
        delta: { tool_calls: [{ index: 0, function: { arguments: '"MSR.001"}' } }] },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 4: finish signal
  yield {
    choices: [{ delta: {}, finish_reason: 'tool_calls' }],
    usage: { prompt_tokens: 100, completion_tokens: 20, prompt_tokens_details: { cached_tokens: 0 } },
  }
}

/** Final text stream after tool results injected (finish_reason='stop'). */
export async function* finalTextStream() {
  yield {
    choices: [{ delta: { content: 'Based on MSR.001 signal data: ' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: { content: 'Saturn is the dominant force.' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: {}, finish_reason: 'stop' }],
    usage: { prompt_tokens: 150, completion_tokens: 30, prompt_tokens_details: { cached_tokens: 0 } },
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
    usage: { prompt_tokens: 50, completion_tokens: 10, prompt_tokens_details: { cached_tokens: 0 } },
  }
}
