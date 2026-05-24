/**
 * tool_use_stream.ts — NVIDIA NIM-format tool call stream fixtures for E2E tests.
 *
 * NVIDIA NIM (llama-3.1-70b-instruct, llama-3.3-70b-instruct) is OpenAI-compatible,
 * so the stream format is identical to OpenAI.
 * The SDK streams tool calls as:
 *   1. delta with id + function.name (first chunk for each tool call index)
 *   2. delta with function.arguments fragments (may span multiple chunks)
 *   3. finish chunk with finish_reason='tool_calls'
 *
 * After tool results are injected, a follow-up stream yields a plain text reply
 * with finish_reason='stop'.
 *
 * Note: NVIDIA NIM does not emit cache telemetry; usage is prompt_tokens + completion_tokens only.
 */

/** Single-tool-call stream: query_signals('MSR.007') */
export async function* toolCallStream() {
  // Chunk 1: id + function name
  yield {
    choices: [
      {
        delta: {
          tool_calls: [
            { index: 0, id: 'call_nim1', function: { name: 'query_signals', arguments: '' } },
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
        delta: { tool_calls: [{ index: 0, function: { arguments: '"MSR.007"}' } }] },
        finish_reason: null,
      },
    ],
    usage: null,
  }
  // Chunk 4: finish signal
  yield {
    choices: [{ delta: {}, finish_reason: 'tool_calls' }],
    usage: { prompt_tokens: 110, completion_tokens: 22 },
  }
}

/** Final text stream after tool results injected (finish_reason='stop'). */
export async function* finalTextStream() {
  yield {
    choices: [{ delta: { content: 'Based on MSR.007 signal data: ' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: { content: 'Jupiter in 9H indicates dharmic wisdom.' }, finish_reason: null }],
    usage: null,
  }
  yield {
    choices: [{ delta: {}, finish_reason: 'stop' }],
    usage: { prompt_tokens: 160, completion_tokens: 28 },
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
    usage: { prompt_tokens: 55, completion_tokens: 12 },
  }
}
